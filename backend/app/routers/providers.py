from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.model_providers import _build_named_provider, provider_config, provider_status

router = APIRouter(prefix="/ai/providers", tags=["AI providers"])


class ProviderTestInput(BaseModel):
    task: str = Field(default="simple", pattern="^(simple|organization|agent|reasoning)$")


@router.get("")
def providers():
    return {"providers": provider_status()}


@router.get("/health")
def provider_health():
    return {"providers": provider_status()}


@router.post("/{name}/test")
def test_provider(name: str, body: ProviderTestInput):
    cfg = provider_config(name)
    if not cfg:
        raise HTTPException(status_code=404, detail="Unknown provider")
    if not cfg.configured:
        return {"provider": name, "status": "NOT_CONFIGURED", "message": "Configure this provider on the local backend first."}
    # A connection test must test the provider the user clicked, regardless of task routing.
    provider = _build_named_provider(name)
    if provider is None:
        return {"provider": name, "status": "UNAVAILABLE", "message": "Provider configuration could not be loaded."}
    try:
        result = provider.chat(
            [
                {"role": "system", "content": "You are testing an IdeaOS AI provider connection. Reply with exactly: IDEAOS_PROVIDER_OK"},
                {"role": "user", "content": "Connection test. Reply with exactly: IDEAOS_PROVIDER_OK"},
            ]
        )
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"provider": name, "status": "HEALTHY", "model": provider.model, "response": str(content)[:200]}
    except Exception as exc:
        return {"provider": name, "status": "ERROR", "model": provider.model, "message": str(exc)[:500]}
