# AI Idea Vault

A local-first personal knowledge library for saving and organizing links
from Instagram, YouTube, LinkedIn, GitHub, X/Twitter, Facebook, websites,
and other platforms.

> **Status:** Phase 5 — search and discovery. SQLite import is complete; AI enrichment is optional and never modifies original source data. See `CLAUDE.md` and `docs/ARCHITECTURE.md`.

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm

## Backend setup (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
- `GET /` — basic info
- `GET /health` — health check (used by the frontend)
- Interactive docs: `http://127.0.0.1:8000/docs`

## Frontend setup (React + Vite)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. It calls
`/api/health`, which Vite proxies to the backend at
`http://127.0.0.1:8000/health` (see `vite.config.js`).

## Verifying everything works

1. Start the backend (`uvicorn app.main:app --reload` from `backend/`).
2. Start the frontend (`npm run dev` from `frontend/`).
3. Open `http://localhost:5173` — you should see a green dot and
   `"status": "ok"` from the backend.
4. Optionally check the backend directly: `curl http://127.0.0.1:8000/health`.

If the dot is red, confirm the backend is running on port 8000 and that
nothing else is using that port.

## Project structure

See `docs/ARCHITECTURE.md` for the full breakdown and rationale.

## Development rules

See `CLAUDE.md` for the non-negotiable data-integrity rules and the
phased development plan this project follows.
