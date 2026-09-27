# CLAUDE.md — AI Idea Vault

This file is the standing reference for any AI assistant (or human) working
on this codebase. It summarizes the rules from the original project skill.
When in doubt, these rules win over convenience or speed.

## What this project is

A **local-first personal knowledge library** for saving and organizing
resources (links + short descriptions) from Instagram, YouTube, LinkedIn,
GitHub, X/Twitter, Facebook, websites, and other platforms. The library is
expected to grow from hundreds to thousands of resources over time, imported
incrementally from DOCX/CSV files that the user updates daily.

**Primary objective:** reliable organization and retrieval of saved
resources without ever losing original data.

## Non-negotiable core principle: DATA INTEGRITY FIRST

Never:
- silently skip, delete, or overwrite a URL or description
- invent a URL or a missing description
- merge two resources without evidence that they're the same
- report an import as "successful" when counts don't reconcile

If something is uncertain, mark the record `NEEDS_REVIEW` instead of
guessing. **Preserving original data is more important than speed or a
clean-looking dataset.**

## Source of truth flow

```
SOURCE FILE (DOCX/CSV)
  → deterministic extraction
  → normalization
  → duplicate detection
  → validation
  → SQLite insertion
  → (optional) AI organization
```

- The SQLite database is the working source of truth **after** a successful
  import.
- URL extraction and counting must be **deterministic** (plain code), never
  delegated to AI.
- AI is never responsible for deciding whether a URL existed in the source
  file, or for the total count of URLs.

## Zero-miss import rule

Before any import is reported complete:

```
Detected URL occurrences == Imported + Duplicate + Invalid + Needs Review
```

If the numbers don't reconcile: **stop**, do not claim success, and report
the discrepancy with the affected records identified.

## URL handling

- Always track: total occurrences, unique URLs, exact duplicate
  occurrences, possible variants, invalid URLs, and needs-review records —
  these are different numbers and must not be collapsed into one.
- Store both `original_url` and `normalized_url`. Never replace the
  original with the normalized form.
- For Instagram, compare the underlying reel/post/media ID, not just the
  full URL string (tracking/share query params can differ on the same
  resource).
- Classify comparisons as `EXACT_DUPLICATE`, `POSSIBLE_DUPLICATE`, or
  `UNIQUE`. Never auto-merge `POSSIBLE_DUPLICATE`.

## Description handling

- Store `original_description` (never destroyed) and, if needed,
  `cleaned_description`.
- AI-generated descriptions are stored separately from user-written ones.
- If the URL-to-description relationship is unclear, mark `NEEDS_REVIEW`
  rather than guessing.

## What AI may / may not do

AI **may** help generate: title, category, subcategory, tags, use cases,
cleaned description, searchable keywords.

AI **must not**: decide whether a source URL existed, determine total URL
counts, silently remove duplicates, or replace original user data. AI is an
organizer, not the source of truth.

## Incremental imports

The source file grows over time (e.g. 500 → 560 → 620 URLs across days).
On each import: detect only the new/unseen resources, run duplicate checks
before inserting, and only run AI processing on new or explicitly
reprocessed records. Do not reprocess the whole library on every import.

## Database

- SQLite, local file, created automatically — no manual setup required from
  the user.
- Use schema migrations/versioning when structure changes.
- Never make destructive schema changes without explicit confirmation and a
  safe migration path.

## Platform detection

Deterministic, from the URL itself, whenever possible (Instagram, YouTube,
LinkedIn, GitHub, X/Twitter, Facebook, Website/Other). Don't ask AI to
determine something code can determine reliably.

## Security & privacy

- Personal, local-first app — the database stays local.
- If an external AI API is used, send only the minimum text/metadata
  required, never the whole database.
- AI processing must be optional; core database/search/import must work
  without any AI API key configured.

## Terminology correction

When source text contains `cloude`, `cloude code`, `cloude skill`, or
`cloude opus` referring to Anthropic's assistant/tool, correct it to
`Claude`, `Claude Code`, `Claude Skill`, `Claude Opus`. Do **not** touch the
normal English word "cloud" (cloud computing/storage/hosting).

## Development process

Build in phases; do not attempt everything in one pass. Complete and test
one phase before starting the next.

1. Project architecture and setup ✅ (this phase)
2. Deterministic DOCX/CSV extraction and URL reconciliation
3. SQLite database and safe import pipeline
4. AI organization/classification
5. Dashboard, search, filtering
6. Add Resource, favorites, collections, Library Health
7. Testing, edge cases, performance, UI polish
8. Optional semantic search / local AI

## Coding rules

- Prefer simple, maintainable code. Avoid unnecessary dependencies.
- Don't rewrite working parts of the app without reason.
- Before modifying existing code: inspect relevant files, understand
  current architecture, identify dependencies, make the smallest safe
  change, then test it.
- After any change, report: files changed, what changed, how it was
  tested, and any remaining issues.

## Error handling

Errors are explicit, never silent. On a critical import/database error,
show: what failed, which record, why (if known), whether data was saved,
and what can be retried. Partial imports must be clearly labeled as
partial, never reported as complete.

---

## Current architecture (Phase 1)

```
ai-idea-vault/
├── backend/                 FastAPI app (Python)
│   ├── app/
│   │   ├── main.py          App entrypoint, CORS, /health, /
│   │   ├── config.py        Central paths/settings (no DB yet)
│   │   └── routers/         Empty, reserved for Phase 3+
│   ├── data/                Local SQLite file + source imports (gitignored)
│   ├── requirements.txt
│   └── .venv/                (created locally, not committed)
├── frontend/                 React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx           Minimal page, calls /api/health
│   │   ├── main.jsx
│   │   └── index.css         Tailwind v4 import + dark-mode base
│   └── vite.config.js        Dev proxy: /api/* → http://127.0.0.1:8000
├── docs/
│   └── ARCHITECTURE.md
├── CLAUDE.md                 (this file)
└── .gitignore
```

See `docs/ARCHITECTURE.md` for the full explanation and rationale.

**Phase 1 explicitly does NOT include:** database schema, CSV/DOCX
import logic, AI API calls, resource CRUD endpoints, search, or
deployment config. Do not add these until the corresponding phase is
explicitly requested.
