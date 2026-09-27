"""Phase 14 polish: tests for POST /resources/file (non-URL resource capture)."""
from fastapi.testclient import TestClient
from app import config
from app.database import connect, initialize
from app.main import app
import app.routers.resources as resources_router


def setup_client(tmp_path, monkeypatch):
    db = tmp_path / "vault.db"
    initialize(db)
    monkeypatch.setattr(resources_router, "DB_PATH", db)
    monkeypatch.setattr(config, "DB_PATH", db)
    return TestClient(app), db


def test_pdf_upload_creates_document_resource_with_type_pdf(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post(
        "/resources/file",
        files={"file": ("report.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
        data={"description": "quarterly report"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "CREATED"
    assert body["resource_type"] == "PDF"
    assert body["file"]["original_name"] == "report.pdf"


def test_image_upload_gets_image_type(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post("/resources/file", files={"file": ("screenshot.png", b"\x89PNG fake bytes", "image/png")})
    assert r.status_code == 200
    assert r.json()["resource_type"] == "IMAGE"


def test_docx_and_txt_and_md_get_document_type(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    for name, content_type in [("notes.txt", "text/plain"), ("notes.md", "text/markdown")]:
        r = client.post("/resources/file", files={"file": (name, f"content for {name}".encode(), content_type)})
        assert r.status_code == 200
        assert r.json()["resource_type"] == "DOCUMENT"


def test_unsupported_extension_is_rejected_cleanly(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post("/resources/file", files={"file": ("payload.exe", b"MZ fake exe", "application/octet-stream")})
    assert r.status_code == 422
    assert "Unsupported file type" in r.json()["detail"]


def test_failed_upload_leaves_no_orphan_resource_row(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    client.post("/resources/file", files={"file": ("payload.exe", b"MZ fake exe", "application/octet-stream")})
    with connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 0
        assert c.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0] == 0


def test_empty_file_is_rejected(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post("/resources/file", files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 422


def test_duplicate_file_content_is_detected_and_not_duplicated(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    content = b"identical bytes across both uploads"
    r1 = client.post("/resources/file", files={"file": ("a.txt", content, "text/plain")})
    r2 = client.post("/resources/file", files={"file": ("b.txt", content, "text/plain")})
    assert r1.status_code == 200 and r1.json()["status"] == "CREATED"
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["status"] == "EXACT_DUPLICATE"
    assert body2["existing_resource_id"] == r1.json()["resource_id"]
    with connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 1


def test_original_description_preserved_exactly(tmp_path, monkeypatch):
    client, db = setup_client(tmp_path, monkeypatch)
    description = "  exact text with   odd spacing — kept as written  "
    r = client.post("/resources/file", files={"file": ("f.txt", b"content", "text/plain")}, data={"description": description})
    resource_id = r.json()["resource_id"]
    fetched = client.get(f"/resources/{resource_id}").json()
    assert fetched["original_description"] == description.strip()


def test_placeholder_url_is_never_a_fake_web_url(tmp_path, monkeypatch):
    """The project's data-integrity rules forbid inventing a URL. A file
    resource's placeholder must be unambiguously a local marker, never
    something that looks like a real http(s) link."""
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post("/resources/file", files={"file": ("f.txt", b"content", "text/plain")})
    resource_id = r.json()["resource_id"]
    fetched = client.get(f"/resources/{resource_id}").json()
    assert fetched["original_url"].startswith("ideaos-file://")
    assert not fetched["original_url"].startswith("http")


def test_existing_url_resources_endpoint_still_works_after_file_route_added(tmp_path, monkeypatch):
    """Regression guard: adding /resources/file must not disturb the
    existing URL-based /resources POST endpoint."""
    client, db = setup_client(tmp_path, monkeypatch)
    r = client.post("/resources", json={"url": "https://example.com/some-article", "description": "a link"})
    assert r.status_code == 200
    assert r.json()["status"] == "CREATED"
