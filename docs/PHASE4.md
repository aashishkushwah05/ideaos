# Phase 4 — AI Organization / Classification

Phase 4 adds an optional AI enrichment layer on top of the verified Phase 3 SQLite library.

## Safety rules
- Original URL and original description are never modified by AI.
- AI cannot decide URL existence, counts, duplicates, or source truth.
- AI is optional; the core app works without an API key.
- AI output is validated as strict structured JSON before being stored.
- Failed AI calls are marked `FAILED` with an error; source data remains intact.
- Only `PENDING` resources are processed by default; old completed resources are not reprocessed.
- Only URL, platform, and description are sent to the provider.

## AI fields
`ai_title`, `ai_category`, `ai_subcategory`, `ai_tags_json`, `ai_use_cases_json`, `ai_cleaned_description`, `ai_summary`, `ai_keywords_json`, `ai_provider`, `ai_model`, `ai_status`, `ai_error`, `ai_processed_at`.

## Provider configuration
The backend supports a dependency-free OpenAI-compatible HTTP provider plus local Ollama.

Environment variables for hosted providers:
- `IDEAOS_AI_PROVIDER=openai|kimi|nvidia|gemini|custom`
- `IDEAOS_AI_ENDPOINT=<provider chat-completions endpoint>`
- `IDEAOS_AI_API_KEY=<key>`
- `IDEAOS_AI_MODEL=<model>`

For Ollama:
- `IDEAOS_AI_PROVIDER=ollama`
- `IDEAOS_AI_MODEL=<local model>`
- optional `IDEAOS_AI_ENDPOINT`

## API
`POST /ai/organize` with `{ "limit": 25, "resource_ids": [...] }`.

No dashboard or search UI is part of Phase 4.
