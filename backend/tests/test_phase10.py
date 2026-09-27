import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import config
from app.database import initialize
from app.main import app
from app.model_providers import configured_providers, select_task_provider


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """These tests don't touch resource data, but every request still
    passes through app.main's auth-guard middleware, which checks
    app.config.DB_PATH. Without this, a real configured local installation
    on the machine running the tests would make every request 401."""
    db = tmp_path / 'vault.db'
    initialize(db)
    monkeypatch.setattr(config, 'DB_PATH', db)


def test_provider_registry_has_all_supported_providers():
    names = {p.name for p in configured_providers()}
    assert names == {'openai','kimi','nvidia','gemini','claude','ollama','custom'}


def test_provider_status_never_exposes_api_keys(monkeypatch):
    monkeypatch.setenv('IDEAOS_AI_PROVIDER', 'openai')
    monkeypatch.setenv('IDEAOS_AI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_AI_ENDPOINT', 'https://example.test/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_AI_API_KEY', 'super-secret-key')
    client = TestClient(app)
    payload = client.get('/ai/providers').json()
    raw = json.dumps(payload)
    assert 'super-secret-key' not in raw
    assert payload['providers'][0]['configured'] is True


def test_legacy_active_provider_configuration_is_supported(monkeypatch):
    monkeypatch.setenv('IDEAOS_AI_PROVIDER', 'openai')
    monkeypatch.setenv('IDEAOS_AI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_AI_ENDPOINT', 'https://example.test/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_AI_API_KEY', 'secret')
    provider = select_task_provider('agent')
    assert provider is not None
    assert provider.name == 'openai'
    assert provider.model == 'gpt-test'


def test_task_role_routes_to_named_provider(monkeypatch):
    monkeypatch.delenv('IDEAOS_AI_PROVIDER', raising=False)
    monkeypatch.setenv('IDEAOS_OPENAI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_OPENAI_ENDPOINT', 'https://example.test/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_OPENAI_API_KEY', 'secret')
    monkeypatch.setenv('IDEAOS_OPENAI_TASKS', 'agent,reasoning')
    provider = select_task_provider('reasoning')
    assert provider is not None and provider.name == 'openai'


def test_invalid_task_rejected(monkeypatch):
    try:
        select_task_provider('unknown')
    except ValueError as exc:
        assert 'Unsupported AI task' in str(exc)
    else:
        raise AssertionError('expected ValueError')


def test_unconfigured_provider_test_is_safe():
    client = TestClient(app)
    body = client.post('/ai/providers/openai/test', json={'task': 'simple'}).json()
    assert body['status'] in {'NOT_CONFIGURED', 'UNAVAILABLE'}
    assert 'api_key' not in json.dumps(body).lower()


def test_provider_test_success_with_mocked_http(monkeypatch):
    monkeypatch.setenv('IDEAOS_AI_PROVIDER', 'openai')
    monkeypatch.setenv('IDEAOS_AI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_AI_ENDPOINT', 'https://example.test/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_AI_API_KEY', 'secret')

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"choices":[{"message":{"content":"IDEAOS_PROVIDER_OK"}}]}'

    with patch('urllib.request.urlopen', return_value=FakeResponse()):
        client = TestClient(app)
        body = client.post('/ai/providers/openai/test', json={'task': 'agent'}).json()
    assert body['status'] == 'HEALTHY'
    assert body['response'] == 'IDEAOS_PROVIDER_OK'


def test_provider_test_error_is_reported_without_secret(monkeypatch):
    monkeypatch.setenv('IDEAOS_AI_PROVIDER', 'openai')
    monkeypatch.setenv('IDEAOS_AI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_AI_ENDPOINT', 'https://example.test/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_AI_API_KEY', 'secret')

    def fail(*args, **kwargs):
        raise RuntimeError('connection failed')

    with patch('urllib.request.urlopen', side_effect=fail):
        client = TestClient(app)
        body = client.post('/ai/providers/openai/test', json={'task': 'simple'}).json()
    assert body['status'] == 'ERROR'
    assert 'secret' not in json.dumps(body)


def test_provider_status_redacts_url_credentials_and_query(monkeypatch):
    monkeypatch.setenv('IDEAOS_OPENAI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_OPENAI_ENDPOINT', 'https://user:pass@example.test/v1/chat/completions?token=secret')
    monkeypatch.setenv('IDEAOS_OPENAI_API_KEY', 'secret-key')
    client = TestClient(app)
    payload = client.get('/ai/providers').json()
    item = next(p for p in payload['providers'] if p['name'] == 'openai')
    assert item['endpoint'] == 'https://example.test/v1/chat/completions'
    raw = json.dumps(payload)
    assert 'secret-key' not in raw and 'token=secret' not in raw and 'user:pass' not in raw


def test_provider_test_targets_named_provider_not_task_route(monkeypatch):
    monkeypatch.setenv('IDEAOS_OPENAI_MODEL', 'gpt-test')
    monkeypatch.setenv('IDEAOS_OPENAI_ENDPOINT', 'https://openai.example/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_OPENAI_API_KEY', 'secret')
    monkeypatch.setenv('IDEAOS_KIMI_MODEL', 'kimi-test')
    monkeypatch.setenv('IDEAOS_KIMI_ENDPOINT', 'https://kimi.example/v1/chat/completions')
    monkeypatch.setenv('IDEAOS_KIMI_API_KEY', 'secret2')

    class FakeResponse:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.body

    def fake_urlopen(req, timeout=None):
        assert 'kimi.example' in req.full_url
        return FakeResponse(b'{"choices":[{"message":{"content":"IDEAOS_PROVIDER_OK"}}]}')

    with patch('urllib.request.urlopen', side_effect=fake_urlopen):
        client = TestClient(app)
        body = client.post('/ai/providers/kimi/test', json={'task': 'agent'}).json()
    assert body['status'] == 'HEALTHY'
    assert body['provider'] == 'kimi'
