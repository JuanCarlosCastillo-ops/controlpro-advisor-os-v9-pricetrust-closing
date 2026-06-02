from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_missing_nameplate_blocks_construction_and_lowers_score():
    payload = client.get('/api/example').json()
    payload['full_load_amps'] = None
    payload['field_photos_count'] = 0
    payload['short_circuit_available_ka'] = None
    r = client.post('/api/generate', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['validation']['human_approval_required'] is True
    assert data['release_gates']['construction_ready'] is False
    assert data['data_quality']['score_percent'] < 90
    assert data['quote_readiness']['score_percent'] < 95


def test_hoist_without_safety_does_not_quote_as_ready():
    payload = client.get('/api/example').json()
    payload['needs_brake'] = False
    payload['needs_limit_switches'] = False
    payload['needs_estop'] = False
    r = client.post('/api/generate', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['release_gates']['quote_ready'] is False
    assert any('Seguridad de izaje' in g['name'] and not g['passed'] for g in data['release_gates']['gates'])


def test_output_contains_traceability_sections():
    payload = client.get('/api/example').json()
    r = client.post('/api/generate', json=payload)
    data = r.json()
    assert data['assumption_ledger']
    assert data['consistency_audit']['checks']
    assert data['field_verification_plan']
    assert data['market']['price_truth_rule']
    assert data['output_quality_contract']['reglas_no_basura']
    assert data['review_board']['veredicto']
    assert data['cad_outputs']['wire_schedule']
    assert data['cad_outputs']['drawio_available'] is True
    assert data['priceguard']['methodology']['name'] == 'PriceGuard 9'
    assert data['premium_document_contract']['pdf']
