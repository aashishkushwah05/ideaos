"""Local secret storage for AI provider API keys.

The owner/admin activation-password system that used to gate this app has
been removed — IdeaOS now opens directly into the normal interface. What
remains here is unrelated to that gate and was explicitly preserved: AI
provider API keys are still encrypted at rest (Fernet), never stored in
plaintext, and never returned to the frontend except as a masked
last-4-characters summary.

The encryption key that protects those secrets used to be derived from the
owner's password and only available after "unlocking". Since there is no
password anymore, the key is instead a random value generated once per
installation and stored locally (see the `instance_key` table) — the app
loads it automatically on demand, with no prompt and no locked state.

Note for anyone upgrading from the old activation-password build: any
provider API key saved before this change was encrypted with a
password-derived key that no longer exists anywhere, so it cannot be
decrypted with the new instance key. read_secret() already treats a failed
decryption as "not configured" rather than raising, so this surfaces as a
simple "no key saved yet" in Settings rather than an error — the fix is
just to re-enter that provider's API key once.
"""
from __future__ import annotations
import base64, secrets, threading
from datetime import UTC, datetime
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from app.database import connect, initialize

_lock = threading.RLock()
_instance_key_cache: dict[str, bytes] = {}


def _fernet_key(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw)


def _get_or_create_instance_key(db_path: Path) -> bytes:
    """The local, password-free encryption key for app_secrets. Created
    once per installation and cached in-process afterward. Cached per
    database path — tests (and anything else that points at more than one
    database file within a single process) must not share one process's
    cached key across different databases."""
    global _instance_key_cache
    cache_key = str(db_path)
    with _lock:
        cached = _instance_key_cache.get(cache_key)
    if cached is not None:
        return cached
    initialize(db_path)
    with connect(db_path) as c:
        row = c.execute("SELECT key_b64 FROM instance_key WHERE id=1").fetchone()
        if row:
            key = base64.b64decode(row["key_b64"])
        else:
            key = secrets.token_bytes(32)
            c.execute("INSERT INTO instance_key(id, key_b64) VALUES (1, ?)", (base64.b64encode(key).decode(),))
    with _lock:
        _instance_key_cache[cache_key] = key
    return key


def store_secret(db_path: Path, name: str, value: str) -> None:
    if not value.strip():
        raise ValueError("Secret value is required.")
    key = _get_or_create_instance_key(db_path)
    encrypted = Fernet(_fernet_key(key)).encrypt(value.encode()).decode()
    with connect(db_path) as c:
        c.execute(
            "INSERT INTO app_secrets(name, encrypted_value, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET encrypted_value=excluded.encrypted_value, updated_at=excluded.updated_at",
            (name, encrypted, datetime.now(UTC).isoformat()),
        )


def read_secret(db_path: Path, name: str) -> str | None:
    key = _get_or_create_instance_key(db_path)
    initialize(db_path)
    with connect(db_path) as c:
        row = c.execute("SELECT encrypted_value FROM app_secrets WHERE name=?", (name,)).fetchone()
    if not row:
        return None
    try:
        return Fernet(_fernet_key(key)).decrypt(row["encrypted_value"].encode()).decode()
    except InvalidToken:
        # Most commonly: a secret saved under the old password-derived key,
        # from before the activation system was removed. Treated as "not
        # configured" rather than an error — see module docstring.
        return None


def secret_summary(db_path: Path, name: str) -> dict:
    """Safe, read-only view of a stored secret for display in Settings:
    whether one exists, and a masked form showing only its last 4
    characters. The full value is decrypted only transiently, in memory,
    and never returned or logged."""
    value = read_secret(db_path, name)
    if not value:
        return {"configured": False, "masked": None}
    tail = value[-4:] if len(value) >= 4 else value
    return {"configured": True, "masked": f"{'•' * 12}{tail}"}


def delete_secret(db_path: Path, name: str) -> bool:
    initialize(db_path)
    with connect(db_path) as c:
        cursor = c.execute("DELETE FROM app_secrets WHERE name=?", (name,))
    return cursor.rowcount > 0
