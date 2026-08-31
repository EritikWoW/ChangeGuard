from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_demo_analysis():
    r = client.get('/api/analyses/demo')
    assert r.status_code == 200
    data = r.json()
    assert data['decision'] == 'block'
    assert len(data['evidence']) == 3
    assert len(data['claims']) == 4

def test_live_system_pages_api():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get('/api/settings').status_code == 200
    assert c.get('/api/dashboard').status_code == 200
    assert c.get('/api/reports').status_code == 200
    r = c.post('/api/benchmarks/run')
    assert r.status_code == 200
    assert r.json()['cases'] >= 10
