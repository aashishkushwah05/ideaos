# Architecture — AI Idea Vault

## Overview

AI Idea Vault is a **local-first** personal knowledge library. It stores
resources (a URL + a short description) saved from platforms like
Instagram, YouTube, LinkedIn, GitHub, X/Twitter, Facebook, and general
websites, and helps organize and search through them as the library grows
into the thousands.

"Local-first" means:
- The database is a single SQLite file on the user's own machine.
- No cloud hosting, no external database service, no account system.
- The app must remain fully usable (search, browse, add resources) without
  any AI API configured — AI is an optional enhancement layer, not a
  dependency.

## Why this stack

| Layer    | Choice                  | Why |
|----------|-------------------------|-----|
| Frontend | React + Vite            | Fast dev server, simple component model, large ecosystem for later features (search UI, filters, etc.) |
| Styling  | Tailwind CSS v4         | Utility-first, fast to iterate, good dark-mode support without a separate design system |
| Backend  | Python + FastAPI        | Good fit for the deterministic extraction/validation logic this project depends on (Phase 2/3), simple async I/O, automatic OpenAPI docs for free |
| Database | SQLite                  | Zero-config, single-file, perfectly suited to a single-user local-first app storing thousands (not millions) of rows |

No ORM, task queue, or auth system has been added — none are justified yet
by the current requirements, and the project rules explicitly discourage
unnecessary dependencies.

## High-level data flow (target end-state, not all built yet)

```
 ┌────────────────────┐
 │  Source DOCX/CSV     │  (grows daily; user's raw saved links)
 └─────────┬───────────┘
           │ Phase 2: deterministic extraction
           ▼
 ┌────────────────────┐
 │ URL reconciliation   │  total occurrences, unique URLs, duplicates,
 │ (code, not AI)       │  invalid URLs, needs-review — all counted
 └─────────┬───────────┘
           │ Phase 3: validated + reconciled records only
           ▼
 ┌────────────────────┐
 │   SQLite database     │  becomes source of truth after successful import
 └─────────┬───────────┘
           │ Phase 4 (optional, per-record): AI organization
           ▼
 ┌────────────────────┐
 │ title/category/tags/  │  stored separately from original_url /
 │ cleaned_description    │  original_description — never overwrites them
 └─────────┬───────────┘
           │ Phase 5/6
           ▼
 ┌────────────────────┐
 │ FastAPI REST API      │  /resources, /search, /import, /health, ...
 └─────────┬───────────┘
           │
           ▼
 ┌────────────────────┐
 │ React/Vite frontend   │  Dashboard, Search, Add Resource, Library Health
 └────────────────────┘
```

## Current state (Phase 1)

Only the foundation exists:

- **Backend**: a FastAPI app with `/` and `/health` endpoints and CORS
  configured for the Vite dev server. No database connection, no
  business logic yet.
- **Frontend**: a single page that calls `GET /api/health` (proxied by
  Vite to the backend at `http://127.0.0.1:8000/health`) and shows
  connectivity status. No resource UI yet.
- **Database**: not created yet. `backend/app/config.py` defines *where*
  the SQLite file will live (`backend/data/vault.db`) so later phases have
  one place to look, but nothing touches it in Phase 1.

## Why a dev proxy (`/api/*` → backend) instead of a hardcoded URL

`frontend/vite.config.js` proxies any frontend request to `/api/...` to
`http://127.0.0.1:8000/...` during local development. This means:
- Frontend code never hardcodes `http://127.0.0.1:8000` — it just calls
  `/api/health`, `/api/resources`, etc.
- If the backend port or host ever changes, only `vite.config.js` changes.
- Avoids CORS friction in the common case (same-origin requests from the
  browser's point of view), while CORS is still explicitly configured on
  the backend for cases where the proxy isn't used (e.g. hitting the API
  directly from a REST client).

## Directory structure

```
ai-idea-vault/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          FastAPI app, CORS, /, /health
│   │   ├── config.py        Paths/settings (DB path reserved, not used yet)
│   │   └── routers/         Empty — reserved for Phase 3+ route modules
│   ├── data/
│   │   ├── .gitkeep
│   │   └── source_imports/  Reserved for Phase 2 source files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          Health-check UI
│   │   ├── main.jsx
│   │   └── index.css        Tailwind v4 + dark-mode base styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       React + Tailwind plugins, /api proxy
├── docs/
│   └── ARCHITECTURE.md      (this file)
├── CLAUDE.md                 Project rules for AI-assisted development
└── .gitignore
```

## What's deliberately NOT here yet

Per the phased plan, the following are intentionally absent and should not
be added until their phase is requested:

- Database schema / SQLAlchemy models / migrations (Phase 3)
- DOCX/CSV parsing and URL reconciliation logic (Phase 2)
- Any AI API integration (Phase 4)
- `/resources`, `/search`, `/import` endpoints (Phase 3/5/6)
- Search, filters, favorites, collections UI (Phase 5/6)
- Library Health dashboard (Phase 6)
- Semantic search (Phase 8, optional)
- Any deployment/hosting configuration (out of scope — local-first only)

## Extending this later

- New backend routes should live in `backend/app/routers/` as separate
  modules (e.g. `resources.py`, `imports.py`) and be included into `main.py`
  via `app.include_router(...)` — the empty `routers/` package already
  anticipates this so Phase 3 doesn't need to restructure `main.py`.
- The database path and other settings should be read from
  `backend/app/config.py` rather than hardcoded elsewhere, so there's one
  place to change local paths.
