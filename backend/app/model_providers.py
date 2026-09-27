"""Phase 10: production-oriented multi-provider AI abstraction.

Providers are configured on the local backend only. API keys are never returned
by this module. The common chat contract keeps the agent and organizer
provider-agnostic while allowing native endpoints for providers that need them.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlsplit, urlunsplit
from typing import Any

from app.ai_organization import AIProvider, OllamaProvider, OpenAICompatibleProvider, build_provider_from_env
from app.config import DB_PATH
from app.security import read_secret


SUPPORTED_PROVIDERS = ("openai", "kimi", "nvidia", "gemini", "claude", "ollama", "custom")
TASKS = ("simple", "organization", "agent", "reasoning")


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    endpoint: str | None
    enabled: bool
    configured: bool
    task_roles: tuple[str, ...]


def _env(name: str, suffix: str) -> str:
    return os.getenv(f"IDEAOS_{name.upper()}_{suffix}", "").strip()


def configured_providers() -> list[ProviderConfig]:
    active = os.getenv("IDEAOS_AI_PROVIDER", "").strip().lower()
    configs: list[ProviderConfig] = []
    for name in SUPPORTED_PROVIDERS:
        model = _env(name, "MODEL")
        endpoint = _env(name, "ENDPOINT") or None
        key = read_secret(DB_PATH, f"provider:{name}:api_key") or _env(name, "API_KEY")
        # Backwards compatibility with the Phase 4/9 single-provider env vars.
        if name == active:
            model = model or os.getenv("IDEAOS_AI_MODEL", "").strip()
            endpoint = endpoint or os.getenv("IDEAOS_AI_ENDPOINT", "").strip() or None
            key = key or os.getenv("IDEAOS_AI_API_KEY", "").strip()
        if name == "ollama":
            model = model or (os.getenv("IDEAOS_AI_MODEL", "").strip() if active == name else "")
            endpoint = endpoint or (os.getenv("IDEAOS_AI_ENDPOINT", "").strip() if active == name else None)
        configured = bool(model) and (name == "ollama" or bool(key))
        enabled = configured and name == active
        roles_raw = _env(name, "TASKS") or (os.getenv("IDEAOS_AI_TASKS", "") if name == active else "")
        roles = tuple(x.strip().lower() for x in roles_raw.split(",") if x.strip() in TASKS)
        configs.append(ProviderConfig(name, model, endpoint, enabled, configured, roles))
    return configs


def provider_config(name: str) -> ProviderConfig | None:
    name = name.strip().lower()
    return next((p for p in configured_providers() if p.name == name), None)


def _build_named_provider(name: str) -> AIProvider | None:
    name = name.strip().lower()
    cfg = provider_config(name)
    if not cfg or not cfg.configured:
        return None
    if name == "ollama":
        return OllamaProvider(cfg.endpoint or "http://127.0.0.1:11434/v1/chat/completions", cfg.model)
    # OpenAI-compatible gateways include OpenAI, Kimi, NVIDIA and custom.
    # Gemini/Claude can be exposed through an OpenAI-compatible gateway by
    # setting their *_ENDPOINT; native adapters can be added without changing
    # the agent contract.
    key = read_secret(DB_PATH, f"provider:{name}:api_key") or _env(name, "API_KEY") or os.getenv("IDEAOS_AI_API_KEY", "").strip()
    endpoint = cfg.endpoint or ""
    if not endpoint or not key:
        return None
    return OpenAICompatibleProvider(endpoint, key, cfg.model, name)


def select_task_provider(task: str = "simple") -> AIProvider | None:
    """Resolve provider by task, then active provider, then first configured one."""
    task = task.strip().lower() or "simple"
    if task not in TASKS:
        raise ValueError(f"Unsupported AI task: {task}")
    for cfg in configured_providers():
        if task in cfg.task_roles:
            provider = _build_named_provider(cfg.name)
            if provider:
                return provider
    active = os.getenv("IDEAOS_AI_PROVIDER", "").strip().lower()
    if active:
        provider = _build_named_provider(active)
        if provider:
            return provider
    return build_provider_from_env()


def _safe_endpoint(endpoint: str | None) -> str | None:
    """Expose provider endpoints without credentials/query secrets."""
    if not endpoint:
        return None
    try:
        parts = urlsplit(endpoint)
        if parts.username or parts.password:
            host = parts.hostname or ""
            port = f":{parts.port}" if parts.port else ""
            netloc = f"{host}{port}"
            return urlunsplit((parts.scheme, netloc, parts.path, "", ""))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except ValueError:
        return None


def provider_status() -> list[dict[str, Any]]:
    """Safe status payload: never include keys, credentials, or URL queries."""
    return [
        {
            "name": p.name,
            "model": p.model,
            "endpoint": _safe_endpoint(p.endpoint),
            "enabled": p.enabled,
            "configured": p.configured,
            "task_roles": list(p.task_roles),
        }
        for p in configured_providers()
    ]
