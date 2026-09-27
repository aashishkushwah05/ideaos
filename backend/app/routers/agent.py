from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.agent import build_tool_registry, run_agent

router = APIRouter(prefix="/agent", tags=["AI agent"])

class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=2000)
    max_steps: int = Field(default=8, ge=1, le=12)
    confirmed: bool = False

@router.get("/tools")
def tools():
    return {"tools": [{"name": t.name, "description": t.description, "write": t.write} for t in build_tool_registry().values()]}

@router.post("/run")
def run(payload: AgentRequest):
    try:
        return run_agent(payload.task, payload.max_steps, payload.confirmed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
