"""Pruebas de la base de datos: migraciones y comandos."""
import os

from app import db
from app.models import User


def test_db_fresh_aplica_las_migraciones_y_crea_los_usuarios(app, monkeypatch):
    """Las migraciones corren desde cero, db:fresh crea los usuarios y borra las firmas."""
    # Nombres y contraseñas que db:fresh lee del .env
    for role in ('ADMIN', 'MANAGER', 'COURIER'):
        monkeypatch.setenv(f'SEED_{role}_NAME', role.title())
        monkeypatch.setenv(f'SEED_{role}_PASSWORD', 'clave-12345')

    # Una firma vieja que debe desaparecer
    firmas = app.instance_path + '/signatures'
    os.makedirs(firmas)
    open(firmas + '/9.png', 'w').close()

    result = app.test_cli_runner().invoke(args=['db:fresh', '--yes'])

    assert result.exit_code == 0, result.output
    assert os.listdir(firmas) == []
    with app.app_context():
        assert sorted(user.role for user in User.query.all()) == ['admin', 'courier', 'manager']
        # La última migración (ubicaciones) quedó aplicada
        assert 'origin_lat' in [column['name'] for column in db.inspect(db.engine).get_columns('packages')]
