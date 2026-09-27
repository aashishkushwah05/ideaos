from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai_organization import organize_pending
from app.model_providers import select_task_provider
from app.config import DB_PATH

router = APIRouter(prefix="/ai", tags=["AI organization"])

class OrganizeRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    resource_ids: list[str] | None = None

@router.post("/organize")
def organize(request: OrganizeRequest):
    provider = select_task_provider("organization")
    if provider is None:
        raise HTTPException(status_code=503, detail="AI is not configured. Set IDEAOS_AI_PROVIDER, IDEAOS_AI_ENDPOINT, IDEAOS_AI_API_KEY and IDEAOS_AI_MODEL (or use Ollama).")
    try:
        return organize_pending(DB_PATH, provider, request.limit, request.resource_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
