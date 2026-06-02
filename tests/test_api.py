from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
    assert 'PDF' in r.json()['modules']


def test_generate_example():
    payload = client.get('/api/example').json()
    r = client.post('/api/generate', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['budget']['recommended_sell_price'] > 0
    assert data['market']['summary']['coverage_percent'] >= 80
    assert data['validation']['human_approval_required'] is True
    assert data['review_board']['personas']
    assert data['guided_flow']['modo_rapido']
    assert data['cad_outputs']['terminal_schedule']
    assert data['api_activation']['services']
    assert 'mathtrust' in data['market']['summary']
    assert data['priceguard']['summary']['priceguard_score_percent'] >= 0
    assert data['starter_intelligence']['profiles']
    assert any(d['semaphore_color'] in {'verde','amarillo','rojo'} for d in data['market']['price_decisions'])


def test_exports():
    payload = client.get('/api/example').json()
    r = client.post('/api/export/markdown', json=payload)
    assert r.status_code == 200
    assert 'RFQ listo' in r.text
    r2 = client.post('/api/export/client-proposal', json=payload)
    assert r2.status_code == 200
    assert ('Propuesta técnica-comercial' in r2.text) or ('PRE-COTIZACIÓN' in r2.text)
    r3 = client.post('/api/export/bom-csv', json=payload)
    assert r3.status_code == 200
    assert 'component_id' in r3.text
    r4 = client.post('/api/export/bom-xlsx', json=payload)
    assert r4.status_code == 200
    assert r4.content[:2] == b'PK'
    r5 = client.post('/api/export/pdf', json=payload)
    assert r5.status_code == 200
    assert r5.content[:4] == b'%PDF'


def test_catalogs():
    assert client.get('/api/catalog/components').status_code == 200
    assert client.get('/api/catalog/suppliers').status_code == 200
    assert client.get('/api/catalog/prices').status_code == 200
    assert client.get('/api/catalog/starter-profiles').status_code == 200
    assert client.get('/api/priceguard/methodology').status_code == 200


def test_activation_and_cad_exports():
    payload = client.get('/api/example').json()
    status = client.get('/api/integrations/status')
    assert status.status_code == 200
    assert status.json()['release'] == 'V14 MathTrust Pro'
    env = client.get('/api/integrations/env-template')
    assert env.status_code == 200
    assert 'MELI_ENABLED' in env.text
    for endpoint, marker in [
        ('/api/export/cad/single-line-svg', 'E-001'),
        ('/api/export/cad/control-ladder-svg', 'E-002'),
        ('/api/export/cad/panel-layout-svg', 'E-003'),
        ('/api/export/cad/drawio', '<mxfile'),
        ('/api/export/cad/terminal-schedule-csv', 'terminal'),
        ('/api/export/cad/wire-schedule-csv', 'cable'),
    ]:
        r = client.post(endpoint, json=payload)
        assert r.status_code == 200
        assert marker in r.text

