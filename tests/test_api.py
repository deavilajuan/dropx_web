import base64

from app import db
from app.models import Package
from tests.conftest import PASSWORD, api_headers

PNG = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'0' * 20).decode()


def change_status(client, headers, status, **extra):
    return client.patch('/api/packages/1/status', json={'status': status, **extra}, headers=headers)


def test_login_correcto_devuelve_token(client):
    response = client.post('/api/auth/login', json={'email': 'courier@test.com', 'password': PASSWORD})
    assert response.status_code == 200
    assert response.json['token']
    assert response.json['user']['role'] == 'courier'


def test_login_con_clave_incorrecta(client):
    response = client.post('/api/auth/login', json={'email': 'courier@test.com', 'password': 'mala'})
    assert response.status_code == 401


def test_paquetes_exigen_token(client):
    assert client.get('/api/packages').status_code == 401


def test_el_repartidor_solo_ve_sus_paquetes(client):
    assert len(client.get('/api/packages', headers=api_headers(client, 'courier@test.com')).json['packages']) == 1
    assert client.get('/api/packages', headers=api_headers(client, 'otro@test.com')).json['packages'] == []


def test_otro_repartidor_no_puede_cambiar_el_paquete(client):
    response = change_status(client, api_headers(client, 'otro@test.com'), 'picked_up')
    assert response.status_code == 404


def test_flujo_pendiente_recogido_entregado(client):
    headers = api_headers(client, 'courier@test.com')
    assert change_status(client, headers, 'picked_up').json['package']['status'] == 'picked_up'
    assert change_status(client, headers, 'delivered').json['package']['status'] == 'delivered'


def test_salto_de_estado_no_permitido(client):
    response = change_status(client, api_headers(client, 'courier@test.com'), 'delivered')
    assert response.status_code == 409


def test_entregado_ya_no_cambia(client):
    headers = api_headers(client, 'courier@test.com')
    change_status(client, headers, 'picked_up')
    change_status(client, headers, 'delivered')
    assert change_status(client, headers, 'picked_up').status_code == 409


def test_novedad_exige_motivo(client):
    headers = api_headers(client, 'courier@test.com')
    assert change_status(client, headers, 'issue').status_code == 400
    response = change_status(client, headers, 'issue', reason='Nadie en casa')
    assert response.json['package']['issueReason'] == 'Nadie en casa'


def test_el_motivo_se_limita_a_100_caracteres(client):
    response = change_status(client, api_headers(client, 'courier@test.com'), 'issue', reason='x' * 300)
    assert len(response.json['package']['issueReason']) == 100


def test_entrega_con_firma_guarda_el_archivo(client, app):
    headers = api_headers(client, 'courier@test.com')
    change_status(client, headers, 'picked_up')
    assert change_status(client, headers, 'delivered', signature=PNG).status_code == 200
    with app.app_context():
        assert db.session.get(Package, 1).signature_path.exists()


def test_firma_invalida_se_rechaza(client):
    headers = api_headers(client, 'courier@test.com')
    change_status(client, headers, 'picked_up')
    falsa = base64.b64encode(b'no soy una imagen').decode()
    assert change_status(client, headers, 'delivered', signature=falsa).status_code == 400
