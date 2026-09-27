# Phase 9 — Controlled AI Agent

Added a safe application-level agent layer. The agent is limited to an explicit tool registry and never receives SQL, filesystem shell, or arbitrary database access.

Endpoints: `GET /agent/tools`, `POST /agent/run`.
