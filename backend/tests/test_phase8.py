import sqlite3
from fastapi.testclient import TestClient

from app import config
from app.database import initialize
from app.main import app
import app.routers.intelligence as intelligence_router
import app.routers.resources as resources_router


def setup_db(tmp_path, monkeypatch):
    db = tmp_path / "vault.db"
    monkeypatch.setattr(resources_router, "DB_PATH", db)
    monkeypatch.setattr(intelligence_router, "DB_PATH", db)
    monkeypatch.setattr(config, "DB_PATH", db)  # see test_phase7.py for why
    initialize(db)
    return db


def add(client, url, description):
    return client.post("/resources", json={"url": url, "description": description}).json()


def test_health_reconciles(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    add(client, "https://example.com/a", "AI agents")
    body = client.get("/intelligence/health").json()
    assert body["reconciled"] is True
    assert body["total_resources"] == 1
    assert body["accounted_for"] == 1


def test_related_resources_and_recommendations(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    first = add(client, "https://example.com/a", "AI agents")
    second = add(client, "https://example.com/b", "AI agents")
    with sqlite3.connect(db) as c:
        c.execute("UPDATE resources SET ai_category='AI', ai_tags_json='[\"agents\"]', favorite=1 WHERE id=?", (first["resource_id"],))
        c.execute("UPDATE resources SET ai_category='AI', ai_tags_json='[\"agents\"]' WHERE id=?", (second["resource_id"],))
    related = client.get(f"/intelligence/resources/{first['resource_id']}/related").json()["items"]
    assert related and related[0]["id"] == second["resource_id"]
    recs = client.get("/intelligence/recommendations").json()["items"]
    assert recs and recs[0]["id"] == second["resource_id"]


def test_smart_collection_and_roadmap(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    first = add(client, "https://example.com/a", "learn AI agents")
    with sqlite3.connect(db) as c:
        c.execute("UPDATE resources SET ai_category='AI', ai_status='COMPLETE', ai_title='AI Agents', ai_summary='Agents', ai_tags_json='[\"agents\"]' WHERE id=?", (first["resource_id"],))
    collection = client.post("/intelligence/collections/smart", json={"name":"AI","rule":{"category":"AI"}})
    assert collection.status_code == 200
    assert collection.json()["count"] == 1
    roadmap = client.post("/intelligence/roadmap", json={"topic":"AI agents", "study_days":2})
    assert roadmap.status_code == 200
    assert len(roadmap.json()["days"]) == 2


def test_duplicate_candidates(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    a = add(client, "https://www.instagram.com/reel/ABC/?igsh=one", "one")
    b = client.post("/resources", json={"url":"https://www.instagram.com/reel/ABC/?igsh=two", "description":"two", "confirm_possible_duplicate": True}).json()
    body = client.get("/intelligence/duplicates").json()
    assert len(body["items"]) == 1


def test_health_ai_and_link_diagnostics(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    first = add(client, "https://example.com/ok", "one")
    second = add(client, "https://example.com/review", "two")
    with sqlite3.connect(db) as c:
        c.execute("UPDATE resources SET ai_status='COMPLETE', ai_title='One', ai_summary='Summary' WHERE id=?", (first["resource_id"],))
        c.execute("UPDATE resources SET ai_status='FAILED', ai_error='provider error' WHERE id=?", (second["resource_id"],))
    body = client.get('/intelligence/health').json()
    assert body['ai_complete'] == 1
    assert body['ai_failed'] == 1
    assert body['missing_metadata'] == 1
    assert body['unverified_links'] == 2


def test_smart_collection_updates_existing_collection(tmp_path, monkeypatch):
    db = setup_db(tmp_path, monkeypatch)
    client = TestClient(app)
    a = add(client, 'https://example.com/a', 'a')
    b = add(client, 'https://example.com/b', 'b')
    with sqlite3.connect(db) as c:
        c.execute("UPDATE resources SET ai_category='AI' WHERE id=?", (a['resource_id'],))
        c.execute("UPDATE resources SET ai_category='Web' WHERE id=?", (b['resource_id'],))
    one = client.post('/intelligence/collections/smart', json={'name':'AI','rule':{'category':'AI'}}).json()
    assert one['count'] == 1
    with sqlite3.connect(db) as c:
        c.execute("UPDATE resources SET ai_category='AI' WHERE id=?", (b['resource_id'],))
    two = client.post('/intelligence/collections/smart', json={'name':'AI','rule':{'category':'AI'}}).json()
    assert two['count'] == 2
    items = client.get(f"/intelligence/collections/{two['id']}/items").json()['items']
    assert {x['id'] for x in items} == {a['resource_id'], b['resource_id']}
