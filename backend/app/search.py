"""Phase 5 search and discovery services for the local SQLite library."""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from app.database import connect, initialize


def _fts_query(value: str) -> str:
    # FTS5-safe AND query. Keep punctuation out and quote each token.
    tokens = re.findall(r"[\w@+#.-]+", value, flags=re.UNICODE)
    return " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens[:20])


def _row_to_resource(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for field in ("ai_tags_json", "ai_use_cases_json", "ai_keywords_json", "reasons_json", "possible_duplicate_of_json"):
        if field in item:
            try:
                item[field.removesuffix("_json")] = json.loads(item[field] or "[]")
            except json.JSONDecodeError:
                item[field.removesuffix("_json")] = []
            del item[field]
    return item


def search_resources(
    db_path,
    *,
    q: str = "",
    category: str | None = None,
    subcategory: str | None = None,
    platform: str | None = None,
    resource_type: str | None = None,
    favorite: bool | None = None,
    ai_status: str | None = None,
    import_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 24,
) -> dict[str, Any]:
    initialize(db_path)
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    where: list[str] = []
    params: list[Any] = []
    join = ""

    clean_q = q.strip()
    if clean_q:
        fts = _fts_query(clean_q)
        if fts:
            join = " JOIN resources_fts ON resources_fts.resource_id = resources.id"
            where.append("resources_fts MATCH ?")
            params.append(fts)
        else:
            clean_q = ""

    filters = [
        (category, "resources.ai_category = ?"),
        (subcategory, "resources.ai_subcategory = ?"),
        (platform, "resources.platform = ?"),
        (resource_type, "resources.resource_type = ?"),
        (ai_status, "resources.ai_status = ?"),
        (import_status, "resources.import_status = ?"),
    ]
    for value, clause in filters:
        if value:
            where.append(clause); params.append(value)
    if favorite is not None:
        where.append("resources.favorite = ?"); params.append(1 if favorite else 0)
    if date_from:
        where.append("resources.created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("resources.created_at <= ?"); params.append(date_to)

    condition = " WHERE " + " AND ".join(where) if where else ""
    offset = (page - 1) * page_size
    with connect(db_path) as connection:
        total = connection.execute(f"SELECT COUNT(*) FROM resources{join}{condition}", params).fetchone()[0]
        rows = connection.execute(
            f"SELECT resources.* FROM resources{join}{condition} ORDER BY resources.created_at DESC, resources.id DESC LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()
        if clean_q:
            connection.execute("INSERT INTO search_history(query) VALUES (?)", (clean_q,))
        resources = [_row_to_resource(row) for row in rows]
    return {"items": resources, "total": total, "page": page, "page_size": page_size, "has_more": offset + len(resources) < total}


def search_facets(db_path) -> dict[str, list[str]]:
    initialize(db_path)
    with connect(db_path) as connection:
        result = {}
        for key, column in (("categories", "ai_category"), ("subcategories", "ai_subcategory"), ("platforms", "platform"), ("resource_types", "resource_type"), ("ai_statuses", "ai_status"), ("import_statuses", "import_status")):
            result[key] = [r[0] for r in connection.execute(f"SELECT DISTINCT {column} FROM resources WHERE {column} IS NOT NULL AND TRIM({column}) <> '' ORDER BY {column}")]
        return result


def recent_searches(db_path, limit: int = 10) -> list[str]:
    initialize(db_path)
    with connect(db_path) as connection:
        return [r[0] for r in connection.execute("SELECT query FROM search_history GROUP BY query ORDER BY MAX(id) DESC LIMIT ?", (min(max(1, limit), 50),))]
