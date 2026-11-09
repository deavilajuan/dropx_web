from app.models import Package
from tests.conftest import suite_login

PAQUETE = {
    'sender_name': 'Ana', 'sender_phone': '3001234567', 'origin_address': 'Bocagrande',
    'recipient_name': 'Luis', 'recipient_phone': '3007654321', 'destination_address': 'Manga',
    'weight': '2.5', 'distance_km': '4',
}
CARTAGENA = {'origin_lat': '10.40', 'origin_lng': '-75.55', 'destination_lat': '10.42', 'destination_lng': '-75.50'}
BOGOTA = {'origin_lat': '4.65', 'origin_lng': '-74.08'}


def test_la_suite_exige_sesion(client):
    response = client.get('/suite/dashboard')
    assert response.status_code == 302
    assert '/suite/login' in response.headers['Location']


def test_el_repartidor_no_entra_a_la_suite(client):
    response = suite_login(client, 'courier@test.com')
    assert response.status_code == 200  # vuelve al login con un aviso
    assert client.get('/suite/dashboard').status_code == 302


def test_admin_y_manager_entran(client):
    for email in ('admin@test.com', 'manager@test.com'):
        assert suite_login(client, email).status_code == 302
        assert client.get('/suite/dashboard').status_code == 200
        client.get('/suite/logout')


def test_paginas_principales_cargan(client):
    suite_login(client, 'admin@test.com')
    for url in ('/suite/paquetes', '/suite/paquetes/nuevo', '/suite/paquetes/1', '/suite/mapa',
                '/suite/repartidores', '/suite/managers', '/suite/reportes'):
        assert client.get(url).status_code == 200, url


def test_crear_paquete_con_ubicaciones_en_cartagena(client, app):
    suite_login(client, 'manager@test.com')
    response = client.post('/suite/paquetes/nuevo', data=PAQUETE | CARTAGENA)
    assert response.status_code == 302
    with app.app_context():
        package = Package.query.filter_by(tracking_number='DX-000002').first()
        assert package.origin_lat == 10.40
        assert package.events[0].title == 'Guía generada'


def test_no_acepta_ubicaciones_fuera_de_cartagena(client, app):
    suite_login(client, 'manager@test.com')
    response = client.post('/suite/paquetes/nuevo', data=PAQUETE | BOGOTA)
    assert response.status_code == 200
    assert 'dentro de Cartagena' in response.get_data(as_text=True)
    with app.app_context():
        assert Package.query.count() == 1


def test_el_peso_debe_ser_valido(client):
    suite_login(client, 'manager@test.com')
    response = client.post('/suite/paquetes/nuevo', data=PAQUETE | {'weight': '0'})
    assert 'peso mayor que cero' in response.get_data(as_text=True)


def test_reportes_solo_para_admin(client):
    suite_login(client, 'manager@test.com')
    assert client.get('/suite/reportes').status_code == 302


def test_reporte_en_csv(client):
    suite_login(client, 'admin@test.com')
    response = client.get('/suite/reportes?tipo=paquetes&desde=2000-01-01&descargar=1')
    assert response.mimetype == 'text/csv'
    assert response.data.startswith('﻿'.encode('utf-8'))
    assert b'DX-000001' in response.data


def test_solo_admin_elimina_paquetes(client, app):
    suite_login(client, 'manager@test.com')
    assert client.post('/suite/paquetes/1/eliminar').status_code == 302
    with app.app_context():
        assert Package.query.count() == 1
    client.get('/suite/logout')
    suite_login(client, 'admin@test.com')
    client.post('/suite/paquetes/1/eliminar')
    with app.app_context():
        assert Package.query.count() == 0
