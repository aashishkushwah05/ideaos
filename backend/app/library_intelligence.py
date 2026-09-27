"""Phase 8 — deterministic library intelligence with optional AI enrichment.

The database remains the source of truth. Intelligence only derives metadata,
relationships and diagnostics; it never silently deletes or rewrites resources.
"""
from __future__ import annotations

import json
import re
import sqlite3
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from app.database import connect, initialize


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _resource(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for field in ("ai_tags_json", "ai_use_cases_json", "ai_keywords_json", "reasons_json", "possible_duplicate_of_json"):
        if field in item:
            item[field.removesuffix("_json")] = _json_list(item[field])
            item.pop(field, None)
    if "favorite" in item:
        item["favorite"] = bool(item["favorite"])
    return item


def _tokenize(*values: str | None) -> set[str]:
    text = " ".join(v or "" for v in values).lower()
    return {t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", text) if len(t) > 1}


def library_health(db_path) -> dict[str, Any]:
    initialize(db_path)
    with connect(db_path) as c:
        total = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        importable = c.execute("SELECT COUNT(*) FROM resources WHERE import_status='IMPORTABLE'").fetchone()[0]
        duplicates = c.execute("SELECT COUNT(*) FROM resources WHERE import_status='EXACT_DUPLICATE'").fetchone()[0]
        review = c.execute("SELECT COUNT(*) FROM resources WHERE import_status='NEEDS_REVIEW'").fetchone()[0]
        invalid = c.execute("SELECT COUNT(*) FROM resources WHERE import_status='INVALID'").fetchone()[0]
        ai_pending = c.execute("SELECT COUNT(*) FROM resources WHERE ai_status='PENDING'").fetchone()[0]
        ai_failed = c.execute("SELECT COUNT(*) FROM resources WHERE ai_status='FAILED'").fetchone()[0]
        ai_complete = c.execute("SELECT COUNT(*) FROM resources WHERE ai_status='COMPLETE'").fetchone()[0]
        missing_metadata = c.execute("""SELECT COUNT(*) FROM resources
            WHERE (ai_title IS NULL OR TRIM(ai_title)='')
              AND (ai_summary IS NULL OR TRIM(ai_summary)='')""").fetchone()[0]
        last_import = c.execute("SELECT * FROM import_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        link_checked = c.execute("SELECT COUNT(*) FROM link_checks").fetchone()[0]
        broken = c.execute("SELECT COUNT(*) FROM link_checks WHERE ok=0 AND status_code=404").fetchone()[0]
        inaccessible = c.execute("SELECT COUNT(*) FROM link_checks WHERE ok=0 AND status_code IS NOT NULL AND status_code<>404").fetchone()[0]
        unverified = total - link_checked
        accounted = importable + duplicates + review + invalid
        quality_issues = review + duplicates + invalid + broken + ai_failed + missing_metadata
        score = 100 if total == 0 else max(0, min(100, round(100 - (quality_issues / total) * 100)))
        return {
            "total_resources": total,
            "importable": importable,
            "exact_duplicates": duplicates,
            "needs_review": review,
            "invalid": invalid,
            "accounted_for": accounted,
            "reconciled": total == accounted,
            "ai_pending": ai_pending,
            "ai_failed": ai_failed,
            "ai_complete": ai_complete,
            "missing_metadata": missing_metadata,
            "links_checked": link_checked,
            "unverified_links": max(0, unverified),
            "broken_links": broken,
            "inaccessible_links": inaccessible,
            "health_score": score,
            "last_import": dict(last_import) if last_import else None,
        }


def related_resources(db_path, resource_id: str, limit: int = 8) -> list[dict[str, Any]]:
    initialize(db_path)
    limit = min(max(limit, 1), 25)
    with connect(db_path) as c:
        target = c.execute("SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
        if not target:
            return []
        target_tags = set(_json_list(target["ai_tags_json"]))
        target_tokens = _tokenize(target["ai_title"], target["ai_summary"], target["original_description"])
        rows = c.execute("SELECT * FROM resources WHERE id<>?", (resource_id,)).fetchall()
        scored: list[tuple[int, dict[str, Any], list[str]]] = []
        for row in rows:
            reasons: list[str] = []
            score = 0
            if target["ai_category"] and row["ai_category"] == target["ai_category"]:
                score += 5; reasons.append("same category")
            if target["ai_subcategory"] and row["ai_subcategory"] == target["ai_subcategory"]:
                score += 3; reasons.append("same subcategory")
            if target["platform"] and row["platform"] == target["platform"]:
                score += 1; reasons.append("same platform")
            common_tags = target_tags & set(_json_list(row["ai_tags_json"]))
            if common_tags:
                score += min(8, len(common_tags) * 2); reasons.append(f"shared tags: {', '.join(sorted(common_tags)[:3])}")
            common_tokens = target_tokens & _tokenize(row["ai_title"], row["ai_summary"], row["original_description"])
            if common_tokens:
                score += min(4, len(common_tokens)); reasons.append("similar topic")
            if score:
                scored.append((score, _resource(row), reasons))
        scored.sort(key=lambda x: (-x[0], x[1].get("created_at", ""), x[1]["id"]))
        return [{**item, "related_score": score, "related_reason": "; ".join(reasons)} for score, item, reasons in scored[:limit]]


def duplicate_candidates(db_path, limit: int = 100) -> list[dict[str, Any]]:
    initialize(db_path)
    limit = min(max(limit, 1), 500)
    with connect(db_path) as c:
        rows = c.execute("""
            SELECT r1.id first_id, r2.id second_id,
                   r1.original_url first_url, r2.original_url second_url,
                   r1.ai_title first_title, r2.ai_title second_title,
                   r1.platform, r1.platform_content_id,
                   CASE WHEN r1.platform_content_id IS NOT NULL
                          AND r1.platform=r2.platform
                          AND r1.platform_content_id=r2.platform_content_id
                        THEN 'CONTENT_ID' ELSE 'NORMALIZED_URL' END AS match_type
            FROM resources r1 JOIN resources r2 ON r1.id < r2.id
            WHERE (r1.platform IS NOT NULL AND r1.platform=r2.platform
                   AND r1.platform_content_id IS NOT NULL AND r1.platform_content_id=r2.platform_content_id)
               OR (r1.normalized_url IS NOT NULL AND r1.normalized_url=r2.normalized_url)
            ORDER BY r1.created_at DESC, r2.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def _rule_match(row: sqlite3.Row, rule: dict[str, Any]) -> bool:
    mapping = {"category": "ai_category", "subcategory": "ai_subcategory"}
    for key, value in rule.items():
        if key == "favorite" and bool(row["favorite"]) != bool(value): return False
        if key in {"category", "subcategory", "platform", "resource_type", "ai_status", "import_status"}:
            if row[mapping.get(key, key)] != value: return False
    return True


def list_collections(db_path) -> list[dict[str, Any]]:
    initialize(db_path)
    with connect(db_path) as c:
        rows = c.execute("SELECT * FROM collections ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            count = c.execute("SELECT COUNT(*) FROM collection_items WHERE collection_id=?", (row["id"],)).fetchone()[0]
            result.append({**dict(row), "rule": json.loads(row["rule_json"] or "{}"), "count": count})
        return result


def smart_collection(db_path, name: str, rule: dict[str, Any], limit: int = 500) -> dict[str, Any]:
    initialize(db_path)
    name = name.strip()
    limit = min(max(limit, 1), 500)
    allowed = {"favorite", "category", "subcategory", "platform", "resource_type", "ai_status", "import_status"}
    if not name or not rule or any(k not in allowed for k in rule):
        raise ValueError("Unsupported or empty collection rule")
    with connect(db_path) as c:
        rows = c.execute("SELECT * FROM resources ORDER BY created_at DESC").fetchall()
        matches = [_resource(r) for r in rows if _rule_match(r, rule)][:limit]
        c.execute("INSERT INTO collections(name, rule_json, collection_type) VALUES (?, ?, 'SMART') ON CONFLICT(name) DO UPDATE SET rule_json=excluded.rule_json, collection_type='SMART'", (name, json.dumps(rule, ensure_ascii=False, sort_keys=True)))
        collection_id = c.execute("SELECT id FROM collections WHERE name=?", (name,)).fetchone()[0]
        c.execute("DELETE FROM collection_items WHERE collection_id=?", (collection_id,))
        c.executemany("INSERT OR IGNORE INTO collection_items(collection_id, resource_id) VALUES (?, ?)", [(collection_id, r["id"]) for r in matches])
        return {"id": collection_id, "name": name, "rule": rule, "count": len(matches), "items": matches}


def collection_items(db_path, collection_id: int) -> list[dict[str, Any]]:
    initialize(db_path)
    with connect(db_path) as c:
        rows = c.execute("SELECT r.* FROM resources r JOIN collection_items ci ON ci.resource_id=r.id WHERE ci.collection_id=? ORDER BY r.created_at DESC", (collection_id,)).fetchall()
        return [_resource(r) for r in rows]


def recommendations(db_path, limit: int = 12) -> list[dict[str, Any]]:
    initialize(db_path)
    limit = min(max(limit, 1), 50)
    with connect(db_path) as c:
        resources = c.execute("SELECT * FROM resources ORDER BY created_at DESC").fetchall()
        favorites = [r for r in resources if r["favorite"]]
        cat = Counter(r["ai_category"] for r in favorites if r["ai_category"])
        tags = Counter(t for r in favorites for t in _json_list(r["ai_tags_json"]))
        result = []
        for r in resources:
            if r["favorite"]: continue
            score = cat.get(r["ai_category"], 0) * 4
            score += sum(tags.get(t, 0) for t in _json_list(r["ai_tags_json"])) * 2
            if r["ai_status"] == "COMPLETE": score += 1
            if r["knowledge_state"] in {"UNREAD", "TO_LEARN", "IN_PROGRESS"}: score += 1
            if score:
                reasons = []
                if cat.get(r["ai_category"], 0): reasons.append(f"you favor {r['ai_category']}")
                shared = [t for t in _json_list(r["ai_tags_json"]) if tags.get(t)]
                if shared: reasons.append(f"matches saved interests: {', '.join(shared[:3])}")
                result.append((score, _resource(r), reasons))
        result.sort(key=lambda x: (-x[0], x[1].get("created_at", ""), x[1]["id"]))
        return [{**item, "recommendation_score": score, "recommendation_reason": "; ".join(reasons) or "matches your library activity"} for score, item, reasons in result[:limit]]


def clusters(db_path, limit: int = 50) -> list[dict[str, Any]]:
    initialize(db_path)
    with connect(db_path) as c:
        rows = c.execute("SELECT * FROM resources ORDER BY created_at DESC").fetchall()
    groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        key = row["ai_category"] or row["ai_subcategory"] or row["platform"] or "Uncategorized"
        groups[key].append(row)
    return [{"cluster": key, "count": len(members), "resource_ids": [r["id"] for r in members[:100]]} for key, members in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))[:limit]]


def knowledge_connections(db_path, limit: int = 100) -> dict[str, Any]:
    initialize(db_path)
    with connect(db_path) as c:
        rows = c.execute("SELECT id, ai_category, ai_subcategory, ai_tags_json FROM resources").fetchall()
    buckets: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        for key in [f"cat:{r['ai_category']}" if r['ai_category'] else None, *[f"tag:{t}" for t in _json_list(r['ai_tags_json'])]]:
            if key: buckets[key].append(r["id"])
    edge_scores: Counter[tuple[str, str]] = Counter()
    for ids in buckets.values():
        unique = list(dict.fromkeys(ids))
        for i, source in enumerate(unique):
            for target in unique[i + 1:]:
                edge_scores[tuple(sorted((source, target)))] += 1
    edges = [{"source": a, "target": b, "weight": w} for (a, b), w in edge_scores.most_common(limit)]
    return {"nodes": [{"id": r["id"]} for r in rows], "edges": edges}


def _topic_score(row: sqlite3.Row, topic_tokens: set[str]) -> int:
    fields = [row["ai_title"], row["ai_category"], row["ai_subcategory"], row["ai_summary"], " ".join(_json_list(row["ai_tags_json"])), " ".join(_json_list(row["ai_keywords_json"]))]
    hay = " ".join(x or "" for x in fields).lower()
    return sum(1 for token in topic_tokens if token in hay)


def roadmap(db_path, topic: str, study_days: int = 7) -> dict[str, Any]:
    initialize(db_path)
    study_days = min(max(study_days, 1), 30)
    topic_tokens = _tokenize(topic)
    with connect(db_path) as c:
        rows = c.execute("SELECT * FROM resources WHERE ai_status='COMPLETE' ORDER BY created_at DESC").fetchall()
    scored = [(s, _resource(r)) for r in rows if (s := _topic_score(r, topic_tokens)) > 0]
    scored.sort(key=lambda x: (-x[0], x[1].get("created_at", ""), x[1]["id"]))
    selected = [item for _, item in scored[:study_days * 3]]
    days = []
    for index in range(study_days):
        days.append({"day": index + 1, "resources": selected[index * 3:(index + 1) * 3], "focus": topic})
    return {"topic": topic.strip(), "days": days, "resource_count": len(selected), "generated_by": "deterministic-library-intelligence"}


def study_plan(db_path, topic: str, study_days: int = 7) -> dict[str, Any]:
    plan = roadmap(db_path, topic, study_days)
    for day in plan["days"]:
        day["objective"] = f"Study {topic.strip()} using your saved resources"
        day["completed"] = False
    return plan


def check_links(db_path, resource_ids: list[str] | None = None, limit: int = 25) -> dict[str, Any]:
    initialize(db_path)
    limit = min(max(limit, 1), 100)
    with connect(db_path) as c:
        if resource_ids:
            ids = list(dict.fromkeys(resource_ids))[:limit]
            placeholders = ",".join("?" for _ in ids)
            rows = c.execute(f"SELECT id, original_url FROM resources WHERE id IN ({placeholders})", ids).fetchall()
        else:
            rows = c.execute("SELECT r.id, r.original_url FROM resources r LEFT JOIN link_checks lc ON lc.resource_id=r.id WHERE lc.resource_id IS NULL ORDER BY r.created_at LIMIT ?", (limit,)).fetchall()
    checked = []
    for row in rows:
        ok = False; status = None; error = None; result = "NETWORK_ERROR"
        try:
            req = urllib.request.Request(row["original_url"], method="HEAD", headers={"User-Agent": "IdeaOS-LinkChecker/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status; ok = 200 <= status < 400
                result = "WORKING" if ok else ("REDIRECTED_OR_RESTRICTED" if status in {301,302,307,308,401,403} else "HTTP_ERROR")
        except urllib.error.HTTPError as exc:
            status = exc.code
            if exc.code in {405, 501}:
                try:
                    req = urllib.request.Request(row["original_url"], method="GET", headers={"User-Agent": "IdeaOS-LinkChecker/1.0", "Range": "bytes=0-1023"})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        status = response.status; ok = 200 <= status < 400; result = "WORKING" if ok else "HTTP_ERROR"
                except Exception as fallback_exc:
                    error = str(fallback_exc)[:500]
            else:
                error = str(exc)[:500]
        except Exception as exc:
            error = str(exc)[:500]
        if not ok and status == 404: result = "NOT_FOUND"
        elif not ok and status in {401,403}: result = "ACCESS_RESTRICTED"
        elif not ok and status is not None and result == "NETWORK_ERROR": result = "HTTP_ERROR"
        with connect(db_path) as c:
            c.execute("""INSERT INTO link_checks(resource_id,status_code,ok,error,checked_at)
                VALUES (?,?,?,?,?) ON CONFLICT(resource_id) DO UPDATE SET status_code=excluded.status_code,ok=excluded.ok,error=excluded.error,checked_at=excluded.checked_at""",
                      (row["id"], status, 1 if ok else 0, error, datetime.now(UTC).isoformat()))
        checked.append({"resource_id": row["id"], "url": row["original_url"], "ok": ok, "status_code": status, "result": result, "error": error})
    return {"checked": len(checked), "items": checked}
