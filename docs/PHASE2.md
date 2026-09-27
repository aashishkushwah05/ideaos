# Phase 2 — Deterministic Import and Zero-Loss Reconciliation

## Scope completed

Phase 2 reads CSV and DOCX files deterministically, extracts explicit HTTP(S)
URL occurrences in source order, preserves the original URL and description,
and produces an auditable report. It does not create a database, call AI, or
modify source files.

## Run

From `backend/`:

```bash
python -m app.importers.phase2 "data/source_imports/your-source.csv" --output "data/import_reports/your-run"
```

The output directory must be new or empty. The command refuses to overwrite
an existing report. It writes:

- `reconciliation_report.json` — source checksums, category counts, and every record
- `extracted_records.csv` — the full reviewable record listing

A successful run requires both `reconciled: true` and
`unchanged_during_extraction: true`.

## Classification

Every URL occurrence receives exactly one status: `IMPORTABLE`,
`EXACT_DUPLICATE`, `INVALID`, or `NEEDS_REVIEW`. Instagram records sharing a
media ID but having different original URLs are retained and marked
`NEEDS_REVIEW`; they are never merged automatically.

## Supplied source verification

`all_urls_extracted (1).csv` was processed on 2026-09-11. Its SHA-256 before
and after extraction was
`a24085921678949cf46e96f8cca407e82f487c753e2278de0820ea30d40ae89c`.

Counts: 648 detected = 621 importable + 8 exact duplicates + 0 invalid + 19
needs review. The reconciliation passed. Phase 3 was not started.
