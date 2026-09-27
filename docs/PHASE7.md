# Phase 7 — Add Resource

## Scope
Phase 7 adds safe manual URL capture to the existing Phase 1–6 system. It does not implement later phases.

## Flow
1. Validate HTTP(S) URL deterministically.
2. Detect platform and resource type.
3. Normalize URL for comparison while preserving the original URL.
4. Check exact duplicate and possible variant duplicate against SQLite.
5. Save only when safe; possible variants require explicit user confirmation and are stored as `NEEDS_REVIEW`.
6. Preserve the original description exactly as entered.
7. Update the Phase 5 FTS index for the new resource.
8. Optionally request Phase 4 AI organization when a provider is configured; AI failure never rolls back the saved resource.

## Safety rules
- Existing records are never overwritten.
- Exact duplicates are not silently created.
- Possible duplicates are not automatically merged.
- Original URL and original description are never changed by AI.
- Every manual save receives a stable resource ID and an auditable import-run record.
- The database remains the source of truth.

## API
- `POST /resources/check` — read-only deterministic validation/duplicate check.
- `POST /resources` — create one resource after duplicate checks.

## Verification
Backend suite includes Phase 2–5 regression tests plus Phase 7 tests for read-only checking, preservation, FTS indexing, exact duplicates, and explicit possible-duplicate confirmation.
