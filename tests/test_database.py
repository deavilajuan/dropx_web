import os

from app import db
from app.models import User


def test_db_fresh_aplica_las_migraciones_y_crea_los_usuarios(app, monkeypatch):
    """Comprueba que las migraciones corren desde cero y que db:fresh borra las firmas."""
    for role in ('ADMIN', 'MANAGER', 'COURIER'):
        monkeypatch.setenv(f'SEED_{role}_NAME', role.title())
        monkeypatch.setenv(f'SEED_{role}_PASSWORD', 'clave-12345')
    firmas = app.instance_path + '/signatures'
    os.makedirs(firmas)
    open(firmas + '/9.png', 'w').close()

    result = app.test_cli_runner().invoke(args=['db:fresh', '--yes'])

    assert result.exit_code == 0, result.output
    assert os.listdir(firmas) == []
    with app.app_context():
        assert sorted(user.role for user in User.query.all()) == ['admin', 'courier', 'manager']
        assert 'origin_lat' in [column['name'] for column in db.inspect(db.engine).get_columns('packages')]
