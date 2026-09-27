import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app import config
from app.database import initialize
from app.main import app
import app.routers.resources as resources_router


def setup_db(tmp_path, monkeypatch):
    db = tmp_path / "vault.db"
    monkeypatch.setattr(resources_router, "DB_PATH", db)
    # The global auth-guard middleware in app.main checks app.config.DB_PATH
    # directly (not any individual router's copy), so tests must redirect
    # it too — otherwise a real, already-configured local installation on
    # the machine running the tests would make every request 401.
    monkeypatch.setattr(config, "DB_PATH", db)
    initialize(db)
    return db


def test_check_is_read_only(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    response = client.post("/resources/check", json={"url": "https://example.com/a", "description": "keep this"})
    assert response.status_code == 200
    assert response.json()["status"] == "NEW"
    with sqlite3.connect(db) as c:
        assert c.execute("select count(*) from resources").fetchone()[0] == 0


def test_add_preserves_original_data_and_is_search_indexed(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    url = "https://www.instagram.com/reel/ABC123/?igsh=tracking"
    desc = "cloude skill — preserve exactly"
    response = client.post("/resources", json={"url": url, "description": desc})
    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    with sqlite3.connect(db) as c:
        row = c.execute("select original_url, original_description, platform, platform_content_id, import_status from resources").fetchone()
        assert row == (url, desc, "Instagram", "reel:ABC123", "IMPORTABLE")
        assert c.execute("select count(*) from resources_fts").fetchone()[0] == 1


def test_exact_duplicate_does_not_create_second_resource(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    payload = {"url": "https://example.com/x", "description": "one"}
    assert client.post("/resources", json=payload).json()["created"] is True
    second = client.post("/resources", json=payload).json()
    assert second["status"] == "EXACT_DUPLICATE"
    assert second["created"] is False
    with sqlite3.connect(db) as c:
        assert c.execute("select count(*) from resources").fetchone()[0] == 1


def test_possible_duplicate_requires_confirmation_then_is_review(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    first = {"url": "https://www.instagram.com/reel/XYZ789/?igsh=one", "description": "first"}
    variant = {"url": "https://www.instagram.com/reel/XYZ789/?igsh=two", "description": "variant"}
    assert client.post("/resources", json=first).json()["created"] is True
    check = client.post("/resources/check", json=variant).json()
    assert check["status"] == "POSSIBLE_DUPLICATE"
    blocked = client.post("/resources", json=variant).json()
    assert blocked["created"] is False
    variant["confirm_possible_duplicate"] = True
    saved = client.post("/resources", json=variant).json()
    assert saved["created"] is True
    with sqlite3.connect(db) as c:
        statuses = [r[0] for r in c.execute("select import_status from resources order by rowid")]
        assert statuses == ["IMPORTABLE", "NEEDS_REVIEW"]
