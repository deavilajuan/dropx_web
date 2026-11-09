def test_paginas_publicas_cargan(client):
    for url in ('/', '/rastreo', '/ser-aliado', '/privacidad', '/terminos'):
        assert client.get(url).status_code == 200, url


def test_rastreo_de_una_guia_existente(client):
    html = client.get('/rastreo?guia=dx-000001').get_data(as_text=True)
    assert 'DX-000001' in html
    assert 'Pendiente' in html


def test_rastreo_de_una_guia_que_no_existe(client):
    response = client.get('/rastreo?guia=DX-999999')
    assert response.status_code == 200
    assert 'DX-000001' not in response.get_data(as_text=True)
