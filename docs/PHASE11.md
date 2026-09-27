# Phase 11 — Files & Local Storage

Added local file storage for PDFs, images, screenshots, text, Markdown, DOCX, CSV, JSON and ZIP files. Files are stored outside SQLite; SQLite stores metadata, resource association, size and SHA-256.

Endpoint: `POST /files`.

Cloud storage is intentionally not implemented at this stage.
