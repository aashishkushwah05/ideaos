# Phase 14 — One-Time Owner Access

> **REMOVED.** This activation/password system has been removed from the
> app entirely — IdeaOS now opens directly into the interface, with no
> owner password, session, or lockout. AI provider API keys are still
> encrypted at rest (see `backend/app/security.py`), just no longer
> gated behind unlocking a vault. This document is kept only as a
> historical record of what used to exist here.

## Local edition

Phase 14 introduces an owner-controlled, one-time activation flow for the local IdeaOS build.

- Owner password: chosen by the owner on first run, via `POST /setup/initialize`. There is no default, shared, or bootstrap password of any kind — the first password submitted becomes the only valid credential, hashed with a freshly generated random salt.
- The plaintext password is **never stored anywhere** — not in source, not in the database, not in a comment. IdeaOS stores only a salted scrypt verifier (random per-installation salt + hash).
- Users do **not** create their own access password in this local edition.
- Successful first activation creates a unique cryptographically random per-installation device access key.
- The device key is kept in browser local storage and is used only to restore the trusted local installation without asking for the owner password again.
- The vault key remains encrypted at rest; provider API credentials remain separate and encrypted locally.
- Five failed owner-password attempts trigger a 12-hour lockout.
- Sessions are long-lived for the local installation so normal browser reopening does not repeatedly prompt for access.
- Clearing browser local storage removes the device key; this is intentionally treated as loss of the local trusted-device credential.

## Production direction

The previously discussed production model remains deferred: owner master secret verification -> unique generated access key per installation -> access using that key. That is intended for the production layer, not this local bootstrap.

## Security note

Each installation generates its own random salt at first run — there is no shared default or bootstrap password to replace before distribution. If this repository is ever cloned or shared *before* first run, the new owner simply completes setup with their own password; nothing from a previous run is reusable, since setup can only run once per database.
