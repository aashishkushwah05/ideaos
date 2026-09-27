# Phase 5 — Search & Discovery

Phase 5 implements backend-first search and discovery so the Phase 6 frontend can consume stable APIs without coupling search behavior to UI code.

## Included
- SQLite FTS5 full-text index across original URL/description and AI-enriched fields.
- Search by title, description, tags, category, platform, URL, keywords and summary.
- Filters for category, subcategory, platform, resource type, favorites, AI status, import status and created date range.
- Pagination with `total` and `has_more`.
- Facet endpoint for UI filter menus.
- Recent-search history endpoint.
- Resource type metadata (`Social Post`, `Video`, `Repository`, `PDF`, `Website`).
- Index backfill for existing Phase 3/4 databases.

## API
- `GET /resources/search`
- `GET /resources/facets`
- `GET /resources/search/recent`

Example:
`/resources/search?q=Next.js%20authentication&platform=GitHub&page=1&page_size=24`

## Integrity
Search is read-only except for intentionally recording a search query in `search_history`. It never changes resource source data. AI metadata is searchable but never treated as authoritative for URL existence or reconciliation.

## Phase boundary
No dashboard, Add Resource workflow, AI agent, embeddings, semantic search, Android, cloud sync, or public deployment is included in Phase 5.
