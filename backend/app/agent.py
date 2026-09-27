"""Phase 9: controlled AI agent orchestration.

The agent has no SQL/shell/filesystem access. It can only call the explicit
application tools declared below. Write operations are gated by confirmation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from app.config import DB_PATH
from app.database import connect, initialize
from app.model_providers import select_task_provider
from app.library_intelligence import (
    clusters, duplicate_candidates, knowledge_connections, library_health,
    recommendations, related_resources, roadmap, smart_collection,
)
from app.search import search_resources


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    handler: Callable[..., Any]
    write: bool = False


def _get_resource(resource_id: str) -> dict[str, Any] | None:
    initialize(DB_PATH)
    with connect(DB_PATH) as c:
        row = c.execute("SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        for field in ("ai_tags_json", "ai_use_cases_json", "ai_keywords_json", "reasons_json", "possible_duplicate_of_json"):
            try:
                item[field.removesuffix("_json")] = json.loads(item.get(field) or "[]")
            except (TypeError, json.JSONDecodeError):
                item[field.removesuffix("_json")] = []
            item.pop(field, None)
        item["favorite"] = bool(item.get("favorite"))
        return item


def _search(query: str, page_size: int = 24) -> dict[str, Any]:
    return search_resources(DB_PATH, q=query, page=1, page_size=max(1, min(page_size, 50)))


def _create_collection(name: str, rule: dict[str, Any], confirmed: bool = False) -> dict[str, Any]:
    if not confirmed:
        return {"status": "CONFIRMATION_REQUIRED", "message": "Creating a collection changes the library. Ask the user for confirmation first.", "name": name, "rule": rule}
    return smart_collection(DB_PATH, name, rule, 500)


def _add_resource(url: str, description: str | None = None, confirmed: bool = False) -> dict[str, Any]:
    if not confirmed:
        return {"status": "CONFIRMATION_REQUIRED", "message": "Adding a resource changes the library. Ask the user for confirmation first.", "url": url, "description": description}
    # Keep validation and persistence centralized in the resources router.
    from app.routers.resources import ResourceInput, add_resource
    return add_resource(ResourceInput(url=url, description=description))


def build_tool_registry() -> dict[str, AgentTool]:
    return {
        "search_resources": AgentTool("search_resources", "Search the user's saved library using a natural-language query.", _search),
        "search_by_intent": AgentTool("search_by_intent", "Find resources matching the user's intent, topic, or task.", _search),
        "get_resource": AgentTool("get_resource", "Retrieve one saved resource by stable ID.", _get_resource),
        "get_library_health": AgentTool("get_library_health", "Return library quality and intelligence health metrics.", lambda: library_health(DB_PATH)),
        "get_related_resources": AgentTool("get_related_resources", "Find resources related to a saved resource.", lambda resource_id, limit=8: related_resources(DB_PATH, resource_id, min(limit, 25))),
        "get_recommendations": AgentTool("get_recommendations", "Return explainable recommendations from the user's library.", lambda limit=12: recommendations(DB_PATH, min(limit, 50))),
        "find_duplicates": AgentTool("find_duplicates", "Find exact and possible duplicate candidates without deleting anything.", lambda limit=100: duplicate_candidates(DB_PATH, min(limit, 500))),
        "get_clusters": AgentTool("get_clusters", "Return knowledge clusters discovered in the library.", lambda: clusters(DB_PATH)),
        "get_connections": AgentTool("get_connections", "Return knowledge connections between saved resources.", lambda limit=100: knowledge_connections(DB_PATH, min(limit, 500))),
        "generate_roadmap": AgentTool("generate_roadmap", "Generate a learning roadmap primarily from resources already saved by the user.", lambda topic, study_days=7: roadmap(DB_PATH, topic, min(study_days, 30))),
        "create_collection": AgentTool("create_collection", "Create a smart collection after explicit user confirmation.", _create_collection, write=True),
        "add_resource": AgentTool("add_resource", "Save a URL after explicit user confirmation; validation stays centralized.", _add_resource, write=True),
    }


def tool_schemas() -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": "search_resources", "description": "Search saved resources.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "get_resource", "description": "Get a saved resource by ID.", "parameters": {"type": "object", "properties": {"resource_id": {"type": "string"}}, "required": ["resource_id"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "get_related_resources", "description": "Find resources related to one saved resource.", "parameters": {"type": "object", "properties": {"resource_id": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 25}}, "required": ["resource_id"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "get_library_health", "description": "Inspect library health.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
        {"type": "function", "function": {"name": "get_recommendations", "description": "Get explainable library recommendations.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "additionalProperties": False}}},
        {"type": "function", "function": {"name": "find_duplicates", "description": "Find duplicate candidates; never delete resources.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False}}},
        {"type": "function", "function": {"name": "generate_roadmap", "description": "Create a learning roadmap from saved resources.", "parameters": {"type": "object", "properties": {"topic": {"type": "string"}, "study_days": {"type": "integer", "minimum": 1, "maximum": 30}}, "required": ["topic"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "create_collection", "description": "Create a smart collection. Requires confirmed=true only after user approval.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "rule": {"type": "object"}, "confirmed": {"type": "boolean"}}, "required": ["name", "rule"], "additionalProperties": False}}},
        {"type": "function", "function": {"name": "add_resource", "description": "Add a URL. Requires confirmed=true only after user approval.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "description": {"type": ["string", "null"]}, "confirmed": {"type": "boolean"}}, "required": ["url"], "additionalProperties": False}}},
    ]


def execute_tool(name: str, arguments: dict[str, Any], confirmed: bool = False) -> Any:
    registry = build_tool_registry()
    tool = registry.get(name)
    if tool is None:
        raise ValueError(f"Unknown agent tool: {name}")
    args = dict(arguments)
    if tool.write:
        args["confirmed"] = confirmed and bool(args.get("confirmed", True))
    return tool.handler(**args)


def run_local_agent(task: str, max_steps: int = 8) -> dict[str, Any]:
    """Safe deterministic fallback when no model provider is configured."""
    if not task or not task.strip():
        raise ValueError("task is required")
    if max_steps < 1 or max_steps > 12:
        raise ValueError("max_steps must be 1..12")
    text, lower = task.strip(), task.strip().lower()
    steps: list[dict[str, Any]] = []
    if "roadmap" in lower or "study plan" in lower or "learning plan" in lower:
        topic = re.sub(r".*?(?:for|about|on)\s+", "", text, flags=re.I).strip() or text
        result = roadmap(DB_PATH, topic, 7)
        steps.append({"tool": "generate_roadmap", "result": {"resource_count": result["resource_count"]}})
        return {"status": "COMPLETE", "mode": "fallback", "task": text, "steps": steps, "output": result, "message": f"I built a roadmap from {result['resource_count']} saved resources."}
    if "duplicate" in lower:
        result = duplicate_candidates(DB_PATH, 100)
        steps.append({"tool": "find_duplicates", "result": {"count": len(result)}})
        return {"status": "COMPLETE", "mode": "fallback", "task": text, "steps": steps, "output": {"items": result}, "message": f"I found {len(result)} duplicate candidates."}
    result = _search(text)
    steps.append({"tool": "search_resources", "result": {"count": result["total"]}})
    return {"status": "COMPLETE", "mode": "fallback", "task": text, "steps": steps, "output": result, "message": f"I found {result['total']} matching resources."}


def run_agent(task: str, max_steps: int = 8, confirmed: bool = False) -> dict[str, Any]:
    """Run an optional model-backed tool-calling loop, with safe fallback."""
    provider = select_task_provider("agent")
    if provider is None or not hasattr(provider, "chat"):
        return run_local_agent(task, max_steps)

    system = (
        "You are the IdeaOS library agent. Use only the provided tools. "
        "The user's original URLs and descriptions are authoritative. Never invent saved resources. "
        "For write actions, the application enforces confirmation. Be concise and explain useful results."
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": task.strip()}]
    steps: list[dict[str, Any]] = []
    for _ in range(max_steps):
        response = provider.chat(messages, tools=tool_schemas())
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return {"status": "COMPLETE", "mode": "model", "task": task.strip(), "steps": steps, "message": message.get("content") or "I couldn't produce a response."}
        messages.append(message)
        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name")
            try:
                args = json.loads(function.get("arguments") or "{}")
                if not isinstance(args, dict): raise ValueError("tool arguments must be an object")
                result = execute_tool(name, args, confirmed=confirmed)
                steps.append({"tool": name, "status": "OK", "result": result})
                tool_content = json.dumps(result, ensure_ascii=False, default=str)[:12000]
            except Exception as exc:
                steps.append({"tool": name or "unknown", "status": "ERROR", "error": str(exc)})
                tool_content = json.dumps({"status": "ERROR", "error": str(exc)})
            messages.append({"role": "tool", "tool_call_id": call.get("id", name or "tool"), "content": tool_content})
    return {"status": "MAX_STEPS", "mode": "model", "task": task.strip(), "steps": steps, "message": "I stopped after the tool-call limit to avoid an uncontrolled loop."}
