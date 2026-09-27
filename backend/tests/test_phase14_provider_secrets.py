"""Phase 14 API-layer polish: masked provider credential view + removal.
Verifies the full key is never returned over the API, only a masked form."""
from fastapi.testclient import TestClient
from app import config
from app.database import initialize
from app.main import app
import app.routers.setup as setup_router


def setup_client(tmp_path, monkeypatch):
    db = tmp_path / "vault.db"
    initialize(db)
    monkeypatch.setattr(setup_router, "DB_PATH", db)
    monkeypatch.setattr(config, "DB_PATH", db)
    return TestClient(app), db


def test_no_secret_configured_returns_not_configured(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.get("/setup/providers/secret/openai")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert body["masked"] is None


def test_stored_secret_is_never_returned_in_full(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    real_key = "sk-supersecretlongapikeyvalue1234567890"
    client.post("/setup/providers/secret", json={"provider": "openai", "api_key": real_key})

    r = client.get("/setup/providers/secret/openai")
    body = r.json()
    assert body["configured"] is True
    assert real_key not in str(r.text)  # the actual secret must never appear in the response
    assert body["masked"].endswith(real_key[-4:])
    assert body["masked"] != real_key


def test_masked_secret_never_appears_in_provider_status_either(tmp_path, monkeypatch):
    """Regression: the existing /ai/providers listing must also stay clean."""
    client, db = setup_client(tmp_path, monkeypatch)
    real_key = "sk-anothersecretkeyvalue999999"
    client.post("/setup/providers/secret", json={"provider": "openai", "api_key": real_key})
    r = client.get("/ai/providers")
    assert real_key not in r.text


def test_remove_credential_clears_it(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    client.post("/setup/providers/secret", json={"provider": "openai", "api_key": "sk-willberemoved1234"})
    r = client.delete("/setup/providers/secret/openai")
    assert r.status_code == 200
    assert r.json()["removed"] is True

    after = client.get("/setup/providers/secret/openai").json()
    assert after["configured"] is False


def test_removing_a_never_configured_provider_is_reported_honestly(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.delete("/setup/providers/secret/gemini")
    assert r.status_code == 200
    assert r.json()["removed"] is False
