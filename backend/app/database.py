"""Local SQLite initialization and read helpers for Phase 3."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 6

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_versions (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS import_runs (id TEXT PRIMARY KEY, source_path TEXT NOT NULL, source_sha256 TEXT NOT NULL, report_path TEXT NOT NULL, detected_count INTEGER NOT NULL, accounted_count INTEGER NOT NULL, inserted_count INTEGER NOT NULL DEFAULT 0, skipped_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL CHECK(status IN ('COMPLETE', 'REJECTED')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS resources (id TEXT PRIMARY KEY, occurrence_fingerprint TEXT NOT NULL UNIQUE, import_run_id TEXT NOT NULL REFERENCES import_runs(id), source_record_number TEXT, source_location TEXT NOT NULL, original_url TEXT NOT NULL, normalized_url TEXT, platform TEXT, platform_content_id TEXT, original_description TEXT, description_confidence TEXT NOT NULL, import_status TEXT NOT NULL CHECK(import_status IN ('IMPORTABLE', 'EXACT_DUPLICATE', 'INVALID', 'NEEDS_REVIEW')), reasons_json TEXT NOT NULL, exact_duplicate_of_resource_id TEXT REFERENCES resources(id), possible_duplicate_of_json TEXT NOT NULL, ai_title TEXT, ai_category TEXT, ai_subcategory TEXT, ai_tags_json TEXT NOT NULL DEFAULT '[]', ai_use_cases_json TEXT NOT NULL DEFAULT '[]', ai_cleaned_description TEXT, ai_summary TEXT, ai_keywords_json TEXT NOT NULL DEFAULT '[]', ai_provider TEXT, ai_model TEXT, ai_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(ai_status IN ('PENDING', 'COMPLETE', 'FAILED', 'SKIPPED')), ai_error TEXT, ai_processed_at TEXT, resource_type TEXT, favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0, 1)), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(import_status);
CREATE INDEX IF NOT EXISTS idx_resources_normalized_url ON resources(normalized_url);
CREATE INDEX IF NOT EXISTS idx_resources_platform_content_id ON resources(platform, platform_content_id);
CREATE INDEX IF NOT EXISTS idx_resources_import_run ON resources(import_run_id);
CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(ai_category);
CREATE INDEX IF NOT EXISTS idx_resources_platform ON resources(platform);
CREATE INDEX IF NOT EXISTS idx_resources_created_at ON resources(created_at);
CREATE INDEX IF NOT EXISTS idx_resources_favorite ON resources(favorite);
CREATE VIRTUAL TABLE IF NOT EXISTS resources_fts USING fts5(resource_id UNINDEXED, original_url, original_description, ai_title, ai_category, ai_subcategory, ai_tags, ai_use_cases, ai_cleaned_description, ai_summary, ai_keywords, platform);
CREATE TABLE IF NOT EXISTS search_history (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS collections (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, collection_type TEXT NOT NULL CHECK(collection_type IN ('SMART','MANUAL')), rule_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS collection_items (collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE, resource_id TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE, PRIMARY KEY(collection_id, resource_id));
CREATE TABLE IF NOT EXISTS link_checks (resource_id TEXT PRIMARY KEY REFERENCES resources(id) ON DELETE CASCADE, status_code INTEGER, ok INTEGER NOT NULL CHECK(ok IN (0,1)), error TEXT, checked_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE, kind TEXT NOT NULL DEFAULT 'NOTE', body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS activity_history (id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT REFERENCES resources(id) ON DELETE SET NULL, action TEXT NOT NULL, details_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS saved_searches (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, query_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS instance_key (id INTEGER PRIMARY KEY CHECK(id=1), key_b64 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS app_secrets (name TEXT PRIMARY KEY, encrypted_value TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS local_files (id TEXT PRIMARY KEY, resource_id TEXT REFERENCES resources(id) ON DELETE SET NULL, original_name TEXT NOT NULL, stored_path TEXT NOT NULL UNIQUE, mime_type TEXT NOT NULL, size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _rebuild_fts_if_needed(connection: sqlite3.Connection) -> None:
    """Keep FTS synchronized without rebuilding the whole index on every request."""
    resource_count = connection.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    fts_count = connection.execute("SELECT COUNT(*) FROM resources_fts").fetchone()[0]
    if resource_count == fts_count:
        return
    connection.execute("DELETE FROM resources_fts")
    connection.execute("""INSERT INTO resources_fts(resource_id, original_url, original_description, ai_title, ai_category, ai_subcategory, ai_tags, ai_use_cases, ai_cleaned_description, ai_summary, ai_keywords, platform)
        SELECT id, original_url, COALESCE(original_description,''), COALESCE(ai_title,''), COALESCE(ai_category,''), COALESCE(ai_subcategory,''), COALESCE(ai_tags_json,''), COALESCE(ai_use_cases_json,''), COALESCE(ai_cleaned_description,''), COALESCE(ai_summary,''), COALESCE(ai_keywords_json,''), COALESCE(platform,'') FROM resources""")


def initialize(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(resources)")}
        migrations = {
            "ai_title": "ALTER TABLE resources ADD COLUMN ai_title TEXT",
            "ai_category": "ALTER TABLE resources ADD COLUMN ai_category TEXT",
            "ai_subcategory": "ALTER TABLE resources ADD COLUMN ai_subcategory TEXT",
            "ai_tags_json": "ALTER TABLE resources ADD COLUMN ai_tags_json TEXT NOT NULL DEFAULT '[]'",
            "ai_use_cases_json": "ALTER TABLE resources ADD COLUMN ai_use_cases_json TEXT NOT NULL DEFAULT '[]'",
            "ai_cleaned_description": "ALTER TABLE resources ADD COLUMN ai_cleaned_description TEXT",
            "ai_summary": "ALTER TABLE resources ADD COLUMN ai_summary TEXT",
            "ai_keywords_json": "ALTER TABLE resources ADD COLUMN ai_keywords_json TEXT NOT NULL DEFAULT '[]'",
            "ai_provider": "ALTER TABLE resources ADD COLUMN ai_provider TEXT",
            "ai_model": "ALTER TABLE resources ADD COLUMN ai_model TEXT",
            "ai_status": "ALTER TABLE resources ADD COLUMN ai_status TEXT NOT NULL DEFAULT 'PENDING'",
            "ai_error": "ALTER TABLE resources ADD COLUMN ai_error TEXT",
            "ai_processed_at": "ALTER TABLE resources ADD COLUMN ai_processed_at TEXT",
            "resource_type": "ALTER TABLE resources ADD COLUMN resource_type TEXT",
            "favorite": "ALTER TABLE resources ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0",
            "knowledge_state": "ALTER TABLE resources ADD COLUMN knowledge_state TEXT NOT NULL DEFAULT 'UNREAD'",
        }
        for name, statement in migrations.items():
            if name not in columns:
                connection.execute(statement)
        connection.execute("DROP TABLE IF EXISTS app_auth")
        connection.execute("DROP TABLE IF EXISTS bootstrap_guard")
        connection.execute("DROP TABLE IF EXISTS app_sessions")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_ai_status ON resources(ai_status)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(ai_category)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_platform ON resources(platform)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_created_at ON resources(created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_favorite ON resources(favorite)")
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS resources_fts USING fts5(resource_id UNINDEXED, original_url, original_description, ai_title, ai_category, ai_subcategory, ai_tags, ai_use_cases, ai_cleaned_description, ai_summary, ai_keywords, platform)")
        connection.execute("CREATE TABLE IF NOT EXISTS search_history (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        _rebuild_fts_if_needed(connection)
        connection.execute("INSERT OR IGNORE INTO schema_versions(version) VALUES (?)", (SCHEMA_VERSION,))


def database_summary(db_path: Path) -> dict[str, int | bool]:
    initialize(db_path)
    with connect(db_path) as connection:
        return {
            "ready": True,
            "schema_version": SCHEMA_VERSION,
            "resources": connection.execute("SELECT COUNT(*) FROM resources").fetchone()[0],
            "import_runs": connection.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0],
        }
