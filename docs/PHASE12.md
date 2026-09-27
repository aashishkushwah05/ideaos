# Phase 12 — Secure First-Run Setup & Advanced Knowledge

## Scope
Phase 12 keeps IdeaOS web-first and local-first. Android remains frozen. The phase adds a friendly first-run security bootstrap and useful knowledge-management primitives.

### Secure setup
- First-run browser setup; no terminal required for normal users.
- User-chosen master password (minimum 8 characters) is never stored in plaintext.
- Password verification uses salted `scrypt` derivation.
- A unique per-installation instance key is generated and encrypted by the master-password-derived key.
- Session bearer tokens are random, short-lived, and stored server-side as SHA-256 hashes.
- Provider API keys can be stored encrypted locally with Fernet and are never returned to the frontend.
- Provider credentials remain backend-only; frontend never calls AI providers directly.
- Restarting the backend requires an unlock before encrypted provider secrets can be used.

### Advanced knowledge
- Knowledge states: UNREAD, READ_LATER, TO_LEARN, IN_PROGRESS, COMPLETED, ARCHIVED.
- Notes/highlights model, note listing, saved-search listing, and activity history.
- Existing smart collections remain durable.
- Backup primitive remains local-only.

### UX
- Welcome/unlock screen with password visibility toggle, clear error states, loading state, responsive layout, and reduced-motion compatibility.
- Settings includes encrypted provider credential entry.
- Terminal commands are a developer fallback only, not part of normal user setup.

## Security boundary
`Browser → FastAPI backend → provider/files/database`.
No provider API key belongs in React source, browser storage, Git, or public repository files.

## Future Phase 12 extension / Phase 13+ candidate
Native Android Share Sheet remains future work. The web PWA share-target capture introduced in Phase 11 remains available. A public GitHub distribution should use first-run local instance provisioning rather than shipping a shared secret in the repository.
