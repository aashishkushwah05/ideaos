# Phase 3 — SQLite Database and Safe Import

## Scope

Phase 3 imports only successfully reconciled Phase 2 reports into local SQLite.
AI, search, dashboard, and resource CRUD are intentionally outside this phase.

### Guarantees
- SQLite is initialized automatically with schema versioning.
- Original URL and original description are preserved exactly.
- Stable resource IDs are deterministic for the same source occurrence.
- Exact duplicates remain separate records and are linked to their original occurrence.
- Possible duplicates / needs-review records are preserved without auto-merging.
- Import requires Phase 2 reconciliation and exact source SHA-256 integrity.
- Imports are atomic: a database failure rolls the whole run back.
- Re-importing the same report is idempotent; existing occurrences are skipped, not duplicated.
- A moved project can resolve a source copy only when its SHA-256 exactly matches the Phase 2 report.
- Import history records detected/accounted/inserted/skipped counts.

## Run

From `backend/`:

```bash
python -m app.import_pipeline "data/import_reports/<run>/reconciliation_report.json"
```

Optional database path:

```bash
python -m app.import_pipeline "data/import_reports/<run>/reconciliation_report.json" --database "data/vault.db"
```

The Phase 2 source should normally be stored under `backend/data/source_imports/`.
If a report contains an old absolute source path, Phase 3 accepts a local source
copy only when its SHA-256 exactly matches the recorded hash.

## Incremental import

Run Phase 2 again against the growing source and import the new report. Existing
source occurrences are recognized by their occurrence fingerprint and skipped;
new occurrences are inserted. Old records are not sent through AI again later
unless explicitly requested by a future phase.

## Verification

```bash
python -m unittest discover -s tests -v
```

Phase 3 must pass atomicity, idempotency, changed-source rejection, and moved-project
exact-hash source resolution tests before it is considered complete.
