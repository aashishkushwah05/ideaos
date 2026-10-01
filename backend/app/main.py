"""IdeaOS local FastAPI entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.config import APP_NAME, APP_VERSION, FRONTEND_DEV_ORIGINS
from app.database import database_summary
from app.routers.ai import router as ai_router
from app.routers.search import router as search_router
from app.routers.resources import router as resources_router
from app.routers.imports import router as imports_router
from app.routers.intelligence import router as intelligence_router
from app.routers.agent import router as agent_router
from app.routers.providers import router as providers_router
from app.routers.files import router as files_router
from app.routers.advanced import router as advanced_router
from app.routers.setup import router as setup_router

app = FastAPI(title=APP_NAME, version=APP_VERSION, description="Local-first personal knowledge library — backend API.")
app.add_middleware(CORSMiddleware, allow_origins=FRONTEND_DEV_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# The owner/admin activation-password gate that used to sit here has been
# removed — IdeaOS opens directly. AI provider API keys remain encrypted at
# rest regardless (see app/security.py); that was a separate concern from
# this request-level gate and was intentionally left in place.
app.include_router(ai_router)
app.include_router(search_router)
app.include_router(resources_router)
app.include_router(imports_router)
app.include_router(intelligence_router)
app.include_router(agent_router)
app.include_router(providers_router)
app.include_router(files_router)
app.include_router(advanced_router)
app.include_router(setup_router)


@app.get("/")
def root():
    return {"app": APP_NAME, "version": APP_VERSION, "status": "ok"}


@app.get("/health")
def health_check():
    """Confirm backend availability and initialize/check only the local database."""
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION, "database": database_summary(config.DB_PATH)}
