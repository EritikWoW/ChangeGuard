from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_submission_status_is_available():
    response = client.get('/api/hackathon/submission-status')
    assert response.status_code == 200
    checks = response.json()['checks']
    assert any(item['name'] == '15-case benchmark dataset' and item['ready'] for item in checks)
    assert any(item['name'] == 'Same-model single-prompt baseline' and item['ready'] for item in checks)


def test_benchmark_markdown_export_after_smoke_run():
    run = client.post('/api/benchmarks/run')
    assert run.status_code == 200
    report = client.get('/api/hackathon/benchmarks/latest.md')
    assert report.status_code == 200
    assert '# ChangeGuard Benchmark Report' in report.text
    assert 'Decision accuracy' in report.text


def test_unknown_trajectory_is_404():
    response = client.get('/api/hackathon/analyses/does-not-exist/trajectory.json')
    assert response.status_code == 404


def test_unknown_github_review_is_404_without_network_call():
    response = client.post('/api/hackathon/github-review/does-not-exist')
    assert response.status_code == 404
