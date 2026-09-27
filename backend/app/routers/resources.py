"""Phase 7 resource capture API: validate, inspect duplicates, and safely save URLs.
Phase 14 polish: also supports non-URL resource capture (PDF/image/document/file)
via /resources/file, reusing the same manual-add data-integrity pattern as URL adds."""
from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from app.ai_organization import build_provider_from_env, organize_pending
from app.config import DB_PATH
from app.database import connect, initialize
from app.file_storage import save_local_file
from app.importers.phase2 import inspect_url

router = APIRouter(prefix="/resources", tags=["resources"])

# Extension -> resource_type category shown in the UI. Kept separate from
# _resource_type() below (which is for URL-based resources) since a local
# file resource has no platform to infer a type from.
_FILE_TYPE_BY_EXTENSION = {
    ".pdf": "PDF",
    ".png": "IMAGE", ".jpg": "IMAGE", ".jpeg": "IMAGE", ".webp": "IMAGE", ".gif": "IMAGE",
    ".docx": "DOCUMENT", ".txt": "DOCUMENT", ".md": "DOCUMENT",
}


def _file_resource_type(extension: str) -> str:
    return _FILE_TYPE_BY_EXTENSION.get(extension.lower(), "FILE")


def _resource_type(platform: str | None, url: str) -> str:
    path = url.lower().split("?", 1)[0].rstrip("/")
    if platform == "Instagram": return "Social Post"
    if platform == "YouTube": return "Video"
    if platform == "GitHub": return "Repository"
    if path.endswith(".pdf"): return "PDF"
    if platform in {"LinkedIn", "X/Twitter", "Facebook"}: return "Social Post"
    return "Website"


def _fingerprint(url: str, description: str | None) -> str:
    payload = f"manual\0{url}\0{description or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ResourceInput(BaseModel):
    url: str = Field(min_length=1, max_length=8192)
    description: str | None = Field(default=None, max_length=10000)
    organize_with_ai: bool = False
    confirm_possible_duplicate: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL is required")
        details = inspect_url(value)
        if details is None:
            raise ValueError("Enter a valid HTTP(S) URL")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value if value.strip() else None


def _check_url(connection, url: str) -> dict[str, Any]:
    details = inspect_url(url)
    if details is None:
        return {"status": "INVALID", "message": "Enter a valid HTTP(S) URL."}

    exact = connection.execute(
        "SELECT id, original_url, ai_title, original_description FROM resources WHERE original_url = ? ORDER BY created_at LIMIT 1",
        (url,),
    ).fetchone()
    if exact:
        return {"status": "EXACT_DUPLICATE", "message": "This exact URL already exists in your library.", "existing_resource_id": exact["id"]}

    possible = None
    if details.get("platform_content_id"):
        possible = connection.execute(
            "SELECT id, original_url, ai_title FROM resources WHERE platform = ? AND platform_content_id = ? ORDER BY created_at LIMIT 1",
            (details["platform"], details["platform_content_id"]),
        ).fetchone()
    if possible is None and details.get("normalized_url"):
        possible = connection.execute(
            "SELECT id, original_url, ai_title FROM resources WHERE normalized_url = ? ORDER BY created_at LIMIT 1",
            (details["normalized_url"],),
        ).fetchone()

    if possible:
        return {
            "status": "POSSIBLE_DUPLICATE",
            "message": "This URL appears to match an existing resource variant. Review before saving.",
            "existing_resource_id": possible["id"],
            "existing_url": possible["original_url"],
            "existing_title": possible["ai_title"],
            "normalized_url": details["normalized_url"],
            "platform": details["platform"],
            "platform_content_id": details["platform_content_id"],
        }

    return {"status": "NEW", "message": "No duplicate found.", **details}


@router.post("/check")
def check_resource(payload: ResourceInput):
    """Deterministically validate and inspect a URL without writing anything."""
    initialize(DB_PATH)
    with connect(DB_PATH) as connection:
        return _check_url(connection, payload.url)


@router.post("")
def add_resource(payload: ResourceInput):
    """Create one new manual resource. Existing data is never overwritten."""
    initialize(DB_PATH)
    with connect(DB_PATH) as connection:
        check = _check_url(connection, payload.url)
        if check["status"] == "INVALID":
            raise HTTPException(status_code=422, detail=check["message"])
        if check["status"] == "EXACT_DUPLICATE":
            return {**check, "created": False}
        if check["status"] == "POSSIBLE_DUPLICATE" and not payload.confirm_possible_duplicate:
            return {**check, "created": False, "requires_confirmation": True}

        details = inspect_url(payload.url)
        assert details is not None
        resource_id = str(uuid.uuid4())
        fingerprint = _fingerprint(payload.url, payload.description)
        # Extremely unlikely hash collision/identical manual occurrence: never overwrite.
        if connection.execute("SELECT 1 FROM resources WHERE occurrence_fingerprint = ?", (fingerprint,)).fetchone():
            return {"status": "EXACT_DUPLICATE", "message": "This exact resource occurrence already exists.", "created": False}

        description = payload.description
        run_id = str(uuid.uuid4())
        connection.execute(
            """INSERT INTO import_runs(
                id, source_path, source_sha256, report_path, detected_count, accounted_count,
                inserted_count, skipped_count, status
            ) VALUES (?, ?, ?, ?, 1, 1, 1, 0, 'COMPLETE')""",
            (run_id, "manual:add-resource", fingerprint, "manual:add-resource"),
        )
        connection.execute(
            """INSERT INTO resources(
                id, occurrence_fingerprint, import_run_id, source_record_number, source_location,
                original_url, normalized_url, platform, platform_content_id, original_description,
                description_confidence, import_status, reasons_json, possible_duplicate_of_json,
                resource_type, ai_status
            ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, 'CERTAIN', ?, ?, ?, ?, 'PENDING')""",
            (
                resource_id, fingerprint, run_id, "manual:add-resource",
                payload.url, details["normalized_url"], details["platform"], details["platform_content_id"],
                description,
                "NEEDS_REVIEW" if check["status"] == "POSSIBLE_DUPLICATE" else "IMPORTABLE",
                json.dumps(["Possible duplicate confirmed by user."] if check["status"] == "POSSIBLE_DUPLICATE" else [], ensure_ascii=False),
                json.dumps([check.get("existing_resource_id")] if check.get("existing_resource_id") else [], ensure_ascii=False),
                _resource_type(details["platform"], payload.url),
            ),
        )
        row = connection.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
        # Keep the Phase 5 FTS index current without changing original values.
        connection.execute(
            "INSERT INTO resources_fts(resource_id, original_url, original_description, ai_title, ai_category, ai_subcategory, ai_tags, ai_use_cases, ai_cleaned_description, ai_summary, ai_keywords, platform) VALUES (?, ?, ?, '', '', '', '', '', '', '', '', ?)",
            (resource_id, payload.url, description or "", details["platform"] or ""),
        )

    ai_result = None
    if payload.organize_with_ai:
        provider = build_provider_from_env()
        if provider is None:
            return {
                "status": "CREATED",
                "created": True,
                "resource_id": resource_id,
                "ai_status": "PENDING",
                "ai_message": "Resource saved. AI organization is pending because no AI provider is configured.",
            }
        ai_result = organize_pending(DB_PATH, provider, limit=1, resource_ids=[resource_id])

    return {
        "status": "CREATED",
        "created": True,
        "resource_id": resource_id,
        "import_status": "NEEDS_REVIEW" if check["status"] == "POSSIBLE_DUPLICATE" else "IMPORTABLE",
        "ai": ai_result,
    }


@router.post("/file")
async def add_file_resource(
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
):
    """Create one new manual resource from an uploaded local file (PDF, image,
    document, or other supported file type) — the non-URL counterpart to
    POST /resources. Follows the same rules as URL adds: never silently
    overwrite, never create a broken/partial resource, and the original
    file + filename are preserved exactly (see app/file_storage.py)."""
    initialize(DB_PATH)
    from pathlib import Path

    original_name = file.filename or "file"
    extension = Path(original_name).suffix.lower()
    description = description.strip() if description and description.strip() else None

    # Read fully before touching the database: lets us hash for duplicate
    # detection and pass a fresh, seekable stream to save_local_file without
    # depending on SpooledTemporaryFile's single-read semantics.
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="The selected file is empty.")

    content_hash = hashlib.sha256(file_bytes).hexdigest()

    with connect(DB_PATH) as connection:
        existing = connection.execute(
            "SELECT resource_id FROM local_files WHERE sha256 = ? AND resource_id IS NOT NULL",
            (content_hash,),
        ).fetchone()
        if existing:
            return {
                "status": "EXACT_DUPLICATE",
                "created": False,
                "message": "A file with identical content is already saved in your library.",
                "existing_resource_id": existing["resource_id"],
            }

        resource_id = str(uuid.uuid4())
        fingerprint = f"manual-file:{content_hash}"
        if connection.execute("SELECT 1 FROM resources WHERE occurrence_fingerprint = ?", (fingerprint,)).fetchone():
            return {"status": "EXACT_DUPLICATE", "created": False, "message": "This exact file already exists in your library."}

        run_id = str(uuid.uuid4())
        connection.execute(
            """INSERT INTO import_runs(
                id, source_path, source_sha256, report_path, detected_count, accounted_count,
                inserted_count, skipped_count, status
            ) VALUES (?, ?, ?, ?, 1, 1, 1, 0, 'COMPLETE')""",
            (run_id, "manual:add-resource-file", content_hash, "manual:add-resource-file"),
        )
        # Placeholder "URL": original_url is NOT NULL in the schema because
        # every resource was originally assumed to come from the deterministic
        # URL import pipeline. A local file genuinely has no URL — rather than
        # inventing a fake http(s) link (explicitly against the project's
        # data-integrity rules), this uses a clearly-marked, honest internal
        # scheme so the frontend/backend can tell at a glance this resource
        # is a local file, not a web link.
        placeholder_url = f"ideaos-file://{resource_id}"
        connection.execute(
            """INSERT INTO resources(
                id, occurrence_fingerprint, import_run_id, source_record_number, source_location,
                original_url, normalized_url, platform, platform_content_id, original_description,
                description_confidence, import_status, reasons_json, possible_duplicate_of_json,
                resource_type, ai_status
            ) VALUES (?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, ?, 'CERTAIN', 'IMPORTABLE', '[]', '[]', ?, 'SKIPPED')""",
            (
                resource_id, fingerprint, run_id, "manual:add-resource-file",
                placeholder_url, description, _file_resource_type(extension),
            ),
        )
        connection.execute(
            "INSERT INTO resources_fts(resource_id, original_url, original_description, ai_title, ai_category, ai_subcategory, ai_tags, ai_use_cases, ai_cleaned_description, ai_summary, ai_keywords, platform) VALUES (?, ?, ?, '', '', '', '', '', '', '', '', '')",
            (resource_id, placeholder_url, description or ""),
        )

    try:
        file_info = save_local_file(DB_PATH, io.BytesIO(file_bytes), original_name, file.content_type, resource_id=resource_id)
    except Exception as exc:
        # The file could not be stored (unsupported type, too large, disk
        # error, ...) — never leave a resource row with no file behind it.
        with connect(DB_PATH) as connection:
            connection.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
            connection.execute("DELETE FROM resources_fts WHERE resource_id = ?", (resource_id,))
            connection.execute("DELETE FROM import_runs WHERE id = ?", (run_id,))
        if isinstance(exc, ValueError):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        raise

    return {
        "status": "CREATED",
        "created": True,
        "resource_id": resource_id,
        "resource_type": _file_resource_type(extension),
        "file": file_info,
        "import_status": "IMPORTABLE",
    }


@router.get("/{resource_id}")
def get_resource(resource_id: str):
    initialize(DB_PATH)
    with connect(DB_PATH) as connection:
        row = connection.execute("SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Resource not found")
        item = dict(row)
        for field in ("ai_tags_json", "ai_use_cases_json", "ai_keywords_json", "reasons_json", "possible_duplicate_of_json"):
            try:
                item[field.removesuffix("_json")] = json.loads(item[field] or "[]")
            except (TypeError, json.JSONDecodeError):
                item[field.removesuffix("_json")] = []
            item.pop(field, None)
        item["favorite"] = bool(item["favorite"])
        return item


@router.patch("/{resource_id}/favorite")
def set_favorite(resource_id: str, payload: dict):
    favorite = payload.get("favorite")
    if not isinstance(favorite, bool):
        raise HTTPException(status_code=422, detail="favorite must be boolean")
    initialize(DB_PATH)
    with connect(DB_PATH) as connection:
        if not connection.execute("SELECT 1 FROM resources WHERE id=?", (resource_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Resource not found")
        connection.execute("UPDATE resources SET favorite=? WHERE id=?", (1 if favorite else 0, resource_id))
        return {"id": resource_id, "favorite": favorite}
