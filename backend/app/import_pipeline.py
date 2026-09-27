"""Phase 3 safe import of reconciled Phase 2 reports into local SQLite."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from collections import Counter
from pathlib import Path

from app.config import DB_PATH, SOURCE_IMPORTS_DIR
from app.database import connect, initialize


def _resource_type(platform: str | None, url: str) -> str:
    path = url.lower().split("?", 1)[0].rstrip("/")
    if platform == "Instagram": return "Social Post"
    if platform == "YouTube": return "Video"
    if platform == "GitHub": return "Repository"
    if path.endswith(".pdf"): return "PDF"
    if platform in {"LinkedIn", "X/Twitter", "Facebook"}: return "Social Post"
    return "Website"


VALID_STATUSES = {"IMPORTABLE", "EXACT_DUPLICATE", "INVALID", "NEEDS_REVIEW"}


class ImportValidationError(ValueError):
    """A Phase 2 report cannot safely enter the local database."""


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_and_validate(report_path: Path) -> dict:
    report_path = report_path.resolve(strict=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    records = report.get("records")
    if not isinstance(records, list):
        raise ImportValidationError("Report has no record list.")
    source = report.get("source", {})
    if not report.get("reconciled"):
        raise ImportValidationError("Refusing unreconciled report.")
    if not source.get("unchanged_during_extraction") or source.get("sha256_before") != source.get("sha256_after"):
        raise ImportValidationError("Refusing report whose source changed during Phase 2 extraction.")
    source_path = Path(source.get("path", ""))
    expected_hash = source.get("sha256_after")
    if not source_path.is_file() or _file_hash(source_path) != expected_hash:
        # Phase 2 reports may contain an absolute path from the machine where
        # extraction happened. A moved project must still be importable, but
        # only when a local source copy has the exact recorded SHA-256.
        candidates = []
        if SOURCE_IMPORTS_DIR.exists():
            candidates = [p for p in SOURCE_IMPORTS_DIR.rglob("*") if p.is_file()]
        matching = [p for p in candidates if _file_hash(p) == expected_hash]
        if len(matching) == 1:
            source_path = matching[0]
        else:
            raise ImportValidationError("Refusing report because its source file is missing/changed and no unique local source copy matches the recorded SHA-256.")
    detected = report.get("detected_url_occurrences")
    accounted = report.get("accounted_url_occurrences")
    if not isinstance(detected, int) or detected != accounted or detected != len(records):
        raise ImportValidationError("Report count does not match its record list.")
    counts = Counter(record.get("status") for record in records)
    if any(status not in VALID_STATUSES for status in counts):
        raise ImportValidationError("Report contains an unknown record status.")
    buckets = report.get("buckets", {})
    expected = {"importable": counts["IMPORTABLE"], "exact_duplicates": counts["EXACT_DUPLICATE"], "invalid": counts["INVALID"], "needs_review": counts["NEEDS_REVIEW"]}
    if buckets != expected:
        raise ImportValidationError("Report bucket counts do not match records.")
    return report


def _fingerprint(record: dict) -> str:
    # Stable across a growing CSV when its record number and content are retained.
    payload = "\0".join(str(record.get(key) or "") for key in ("source_record_number", "source_location", "original_url", "original_description"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def import_report(report_path: Path, db_path: Path = DB_PATH) -> dict[str, int | str]:
    report = _load_and_validate(report_path)
    initialize(db_path)
    run_id = str(uuid.uuid4())
    records = report["records"]
    record_to_resource: dict[int, str] = {}
    inserted = skipped = 0

    with connect(db_path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO import_runs(id, source_path, source_sha256, report_path, detected_count, accounted_count, inserted_count, skipped_count, status)
                   VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'COMPLETE')""",
                (run_id, report["source"]["path"], report["source"]["sha256_after"], str(report_path.resolve()),
                 report["detected_url_occurrences"], report["accounted_url_occurrences"]),
            )
            for record in records:
                fingerprint = _fingerprint(record)
                row = connection.execute("SELECT id FROM resources WHERE occurrence_fingerprint = ?", (fingerprint,)).fetchone()
                if row:
                    record_to_resource[record["record_number"]] = row["id"]
                    skipped += 1
                    continue
                resource_id = str(uuid.uuid5(uuid.NAMESPACE_URL, fingerprint))
                record_to_resource[record["record_number"]] = resource_id
                connection.execute(
                    """INSERT INTO resources(
                        id, occurrence_fingerprint, import_run_id, source_record_number, source_location,
                        original_url, normalized_url, platform, platform_content_id, original_description,
                        description_confidence, import_status, reasons_json, possible_duplicate_of_json, resource_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (resource_id, fingerprint, run_id, record.get("source_record_number"), record["source_location"],
                     record["original_url"], record.get("normalized_url"), record.get("platform"), record.get("platform_content_id"),
                     record.get("original_description"), record["description_confidence"], record["status"],
                     json.dumps(record.get("reasons", [])), json.dumps(record.get("possible_duplicate_of", [])),
                     _resource_type(record.get("platform"), record["original_url"])),
                )
                inserted += 1
            # Link only to an explicitly identified original occurrence; no automatic merging occurs.
            for record in records:
                duplicate_of = record.get("exact_duplicate_of")
                if duplicate_of and record["record_number"] in record_to_resource and duplicate_of in record_to_resource:
                    connection.execute("UPDATE resources SET exact_duplicate_of_resource_id = ? WHERE id = ?", (record_to_resource[duplicate_of], record_to_resource[record["record_number"]]))
            connection.execute("UPDATE import_runs SET inserted_count = ?, skipped_count = ? WHERE id = ?", (inserted, skipped, run_id))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return {"import_run_id": run_id, "detected": len(records), "inserted": inserted, "skipped_existing": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Idea Vault Phase 3 safe SQLite importer")
    parser.add_argument("report", type=Path, help="Reconciled Phase 2 reconciliation_report.json")
    parser.add_argument("--database", type=Path, default=DB_PATH)
    args = parser.parse_args()
    print(json.dumps(import_report(args.report, args.database), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


