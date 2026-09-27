"""Phase 11 local file storage with safe names and SQLite metadata."""
from __future__ import annotations
import hashlib
import mimetypes
import re
import sqlite3
import uuid
from pathlib import Path
from typing import BinaryIO
from app.database import connect, initialize

MAX_FILE_BYTES = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf','.png','.jpg','.jpeg','.webp','.gif','.txt','.md','.docx','.csv','.json','.zip'}


def _safe_name(name: str) -> str:
    base = Path(name or 'file').name
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', base).strip('._') or 'file'
    return base[:180]


def save_local_file(db_path, stream: BinaryIO, original_name: str, content_type: str | None, resource_id: str | None = None) -> dict:
    initialize(db_path)
    if resource_id:
        with connect(db_path) as c:
            if not c.execute('SELECT 1 FROM resources WHERE id=?', (resource_id,)).fetchone():
                raise ValueError(f'No resource found with id {resource_id!r}; the file was not saved.')
    safe = _safe_name(original_name)
    ext = Path(safe).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f'Unsupported file type: {ext or "none"}')
    file_id = str(uuid.uuid4())
    root = Path(db_path).parent / 'files'
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f'{file_id}{ext}'
    digest = hashlib.sha256()
    size = 0
    try:
        with destination.open('wb') as out:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise ValueError(f'File exceeds {MAX_FILE_BYTES // (1024*1024)} MB limit')
                digest.update(chunk); out.write(chunk)
        detected = content_type or mimetypes.guess_type(safe)[0] or 'application/octet-stream'
        with connect(db_path) as c:
            c.execute('INSERT INTO local_files(id, resource_id, original_name, stored_path, mime_type, size_bytes, sha256) VALUES (?,?,?,?,?,?,?)', (file_id, resource_id, safe, str(destination.relative_to(Path(db_path).parent)), detected, size, digest.hexdigest()))
    except (ValueError, sqlite3.DatabaseError):
        # Never leave a file on disk that has no matching metadata row —
        # that's exactly the kind of orphaned/untracked state the project's
        # data-integrity rules rule out. Covers the size-limit abort above
        # and any database failure (e.g. a resource_id that was deleted in
        # a race between the check above and this insert).
        destination.unlink(missing_ok=True)
        raise
    return {'file_id': file_id, 'resource_id': resource_id, 'original_name': safe, 'mime_type': detected, 'size_bytes': size, 'sha256': digest.hexdigest(), 'stored_path': str(destination.relative_to(Path(db_path).parent))}
