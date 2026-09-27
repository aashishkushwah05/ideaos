"""Phase 4: optional, safe AI enrichment for resources already stored in SQLite."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.database import connect, initialize

CATEGORIES = {
    "AI", "Web Development", "Backend", "Frontend", "DevOps", "Cybersecurity",
    "Programming", "GitHub", "Productivity", "Business", "Startup", "Design",
    "Learning", "Career", "Marketing", "Automation", "Finance", "Other",
}

ORGANIZATION_SYSTEM_PROMPT = """You organize a user's personal knowledge library. Return ONLY valid JSON.
Do not invent URLs, facts, or missing details. Preserve the meaning of the user's text.
If the description clearly refers to Anthropic's assistant/tool, normalize cloude/cloude code/cloude skill/cloude opus to Claude/Claude Code/Claude Skill/Claude Opus. Never change normal uses of the word cloud.
Use one category from the allowed list. Keep tags short and useful. If information is uncertain, use a conservative value and do not invent specifics.
"""


def _clean_cloude(text: str | None) -> str | None:
    if text is None:
        return None
    # Context-sensitive enough for the known variants without touching normal "cloud".
    text = re.sub(r"\bcloude\s+code\b", "Claude Code", text, flags=re.I)
    text = re.sub(r"\bcloude\s+skill\b", "Claude Skill", text, flags=re.I)
    text = re.sub(r"\bcloude\s+opus\b", "Claude Opus", text, flags=re.I)
    text = re.sub(r"\bcloude\b", "Claude", text, flags=re.I)
    return text


@dataclass(frozen=True)
class OrganizationResult:
    title: str
    category: str
    subcategory: str | None
    tags: list[str]
    use_cases: list[str]
    cleaned_description: str | None
    summary: str | None
    keywords: list[str]


class AIProvider(Protocol):
    name: str
    model: str

    def organize(self, payload: dict[str, Any]) -> OrganizationResult: ...

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]: ...


class OpenAICompatibleProvider:
    """Small dependency-free client for OpenAI-compatible chat-completions APIs."""

    def __init__(self, endpoint: str, api_key: str, model: str, name: str = "openai-compatible", timeout: int = 60):
        self.endpoint, self.api_key, self.model, self.name, self.timeout = endpoint, api_key, model, name, timeout

    def organize(self, payload: dict[str, Any]) -> OrganizationResult:
        user_prompt = json.dumps({
            "task": "Organize this single resource.",
            "allowed_categories": sorted(CATEGORIES),
            "resource": payload,
            "output_schema": {
                "title": "string",
                "category": "string",
                "subcategory": "string or null",
                "tags": ["string"],
                "use_cases": ["string"],
                "cleaned_description": "string or null",
                "summary": "string or null",
                "keywords": ["string"],
            },
        }, ensure_ascii=False)
        body = json.dumps({
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": ORGANIZATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",
        }, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"AI provider request failed: {exc}") from exc
        try:
            content = raw["choices"][0]["message"]["content"]
            parsed = _parse_json_object(content)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(f"AI provider returned an invalid response: {exc}") from exc
        return validate_organization(parsed)

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"model": self.model, "temperature": 0.1, "messages": messages}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        request = urllib.request.Request(self.endpoint, data=json.dumps(body).encode("utf-8"), headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",
        }, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"AI provider request failed: {exc}") from exc
        if not isinstance(raw, dict) or not raw.get("choices"):
            raise RuntimeError("AI provider returned no choices")
        return raw


class OllamaProvider(OpenAICompatibleProvider):
    def __init__(self, endpoint: str = "http://127.0.0.1:11434/v1/chat/completions", model: str = "llama3.2"):
        super().__init__(endpoint, "ollama", model, "ollama")


def _parse_json_object(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I | re.S).strip()
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("response JSON must be an object")
    return value


def _string(value: Any, field: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string" + (" or null" if nullable else ""))
    return value.strip()


def _string_list(value: Any, field: str, max_items: int = 20) -> list[str]:
    if not isinstance(value, list) or len(value) > max_items:
        raise ValueError(f"{field} must be a list with at most {max_items} items")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} contains an invalid item")
        result.append(item.strip())
    return list(dict.fromkeys(result))


def validate_organization(data: dict[str, Any]) -> OrganizationResult:
    category = _string(data.get("category"), "category")
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of the allowed categories, got {category!r}")
    return OrganizationResult(
        title=_string(data.get("title"), "title"),
        category=category,
        subcategory=_string(data.get("subcategory"), "subcategory", nullable=True),
        tags=_string_list(data.get("tags"), "tags"),
        use_cases=_string_list(data.get("use_cases"), "use_cases"),
        cleaned_description=_string(data.get("cleaned_description"), "cleaned_description", nullable=True),
        summary=_string(data.get("summary"), "summary", nullable=True),
        keywords=_string_list(data.get("keywords"), "keywords"),
    )


def build_provider_from_env() -> AIProvider | None:
    provider = os.getenv("IDEAOS_AI_PROVIDER", "").strip().lower()
    if provider == "ollama":
        return OllamaProvider(os.getenv("IDEAOS_AI_ENDPOINT", "http://127.0.0.1:11434/v1/chat/completions"), os.getenv("IDEAOS_AI_MODEL", "llama3.2"))
    if provider in {"openai", "kimi", "nvidia", "gemini", "claude", "custom"}:
        endpoint = os.getenv("IDEAOS_AI_ENDPOINT", "").strip()
        key = os.getenv("IDEAOS_AI_API_KEY", "").strip()
        model = os.getenv("IDEAOS_AI_MODEL", "").strip()
        if not endpoint or not key or not model:
            return None
        return OpenAICompatibleProvider(endpoint, key, model, provider)
    return None


def resource_payload(row: Any) -> dict[str, Any]:
    return {
        "url": row["original_url"],
        "platform": row["platform"],
        "description": _clean_cloude(row["original_description"]),
    }


def organize_pending(db_path, provider: AIProvider, limit: int = 25, resource_ids: list[str] | None = None) -> dict[str, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    initialize(db_path)
    with connect(db_path) as connection:
        if resource_ids:
            placeholders = ",".join("?" for _ in resource_ids)
            rows = connection.execute(f"SELECT * FROM resources WHERE id IN ({placeholders}) AND (ai_status IS NULL OR ai_status = 'PENDING') LIMIT ?", (*resource_ids, limit)).fetchall()
        else:
            rows = connection.execute("SELECT * FROM resources WHERE ai_status IS NULL OR ai_status = 'PENDING' ORDER BY created_at, id LIMIT ?", (limit,)).fetchall()

    succeeded = failed = 0
    for row in rows:
        try:
            result = provider.organize(resource_payload(row))
            with connect(db_path) as connection:
                connection.execute("""UPDATE resources SET ai_title=?, ai_category=?, ai_subcategory=?, ai_tags_json=?, ai_use_cases_json=?, ai_cleaned_description=?, ai_summary=?, ai_keywords_json=?, ai_provider=?, ai_model=?, ai_status='COMPLETE', ai_error=NULL, ai_processed_at=? WHERE id=? AND (ai_status IS NULL OR ai_status='PENDING')""",
                    (result.title, result.category, result.subcategory, json.dumps(result.tags, ensure_ascii=False), json.dumps(result.use_cases, ensure_ascii=False), result.cleaned_description, result.summary, json.dumps(result.keywords, ensure_ascii=False), provider.name, provider.model, datetime.now(UTC).isoformat(), row["id"]))
            succeeded += 1
        except Exception as exc:
            with connect(db_path) as connection:
                connection.execute("UPDATE resources SET ai_status='FAILED', ai_error=?, ai_provider=?, ai_model=?, ai_processed_at=? WHERE id=?", (str(exc)[:2000], provider.name, provider.model, datetime.now(UTC).isoformat(), row["id"]))
            failed += 1
    return {"requested": len(rows), "succeeded": succeeded, "failed": failed}
