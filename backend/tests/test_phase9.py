from fastapi.testclient import TestClient
from app import config
from app.database import initialize
from app.main import app


def setup_client(tmp_path, monkeypatch):
    db = tmp_path / 'vault.db'
    initialize(db)
    import app.agent as agent
    monkeypatch.setattr(agent, 'DB_PATH', db)
    monkeypatch.setattr(config, 'DB_PATH', db)  # see test_phase7.py for why
    return TestClient(app)


def test_agent_exposes_only_whitelisted_tools(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    data = client.get('/agent/tools').json()
    names = {x['name'] for x in data['tools']}
    assert 'search_resources' in names
    assert 'get_resource' in names
    assert 'get_library_health' in names
    assert 'execute_sql' not in names
    assert 'shell' not in names


def test_agent_runs_controlled_search(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    body = client.post('/agent/run', json={'task': 'find AI agents'}).json()
    assert body['status'] == 'COMPLETE'
    assert body['steps'][0]['tool'] == 'search_resources'
    assert body['mode'] == 'fallback'


def test_write_tools_require_confirmation(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    result = client.post('/agent/run', json={'task': 'create a collection for AI'}).json()
    assert result['status'] == 'COMPLETE'
    assert all(step.get('status') != 'EXECUTED_WRITE' for step in result.get('steps', []))


def test_empty_task_rejected(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.post('/agent/run', json={'task': ''})
    assert response.status_code == 422
