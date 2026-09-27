from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import DB_PATH
from app.library_intelligence import (
    check_links, collection_items, clusters, duplicate_candidates, knowledge_connections,
    library_health, list_collections, recommendations, related_resources, roadmap,
    smart_collection, study_plan,
)

router = APIRouter(prefix="/intelligence", tags=["Library intelligence"])

class SmartCollectionInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rule: dict
    limit: int = Field(default=500, ge=1, le=500)

class RoadmapInput(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    study_days: int = Field(default=7, ge=1, le=30)

class LinkCheckInput(BaseModel):
    resource_ids: list[str] | None = None
    limit: int = Field(default=25, ge=1, le=100)

@router.get("/health")
def health(): return library_health(DB_PATH)

@router.get("/resources/{resource_id}/related")
def related(resource_id: str, limit: int = Query(8, ge=1, le=25)):
    return {"items": related_resources(DB_PATH, resource_id, limit)}

@router.get("/duplicates")
def duplicates(limit: int = Query(100, ge=1, le=500)):
    return {"items": duplicate_candidates(DB_PATH, limit)}

@router.get("/collections")
def collections(): return {"items": list_collections(DB_PATH)}

@router.get("/collections/{collection_id}/items")
def collection_detail(collection_id: int): return {"items": collection_items(DB_PATH, collection_id)}

@router.post("/collections/smart")
def create_smart_collection(payload: SmartCollectionInput):
    try: return smart_collection(DB_PATH, payload.name, payload.rule, payload.limit)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/recommendations")
def recommend(limit: int = Query(12, ge=1, le=50)):
    return {"items": recommendations(DB_PATH, limit)}

@router.get("/clusters")
def cluster(): return {"items": clusters(DB_PATH)}

@router.get("/connections")
def connections(limit: int = Query(100, ge=1, le=500)):
    return knowledge_connections(DB_PATH, limit)

@router.post("/roadmap")
def make_roadmap(payload: RoadmapInput): return roadmap(DB_PATH, payload.topic, payload.study_days)

@router.post("/study-plan")
def make_study_plan(payload: RoadmapInput): return study_plan(DB_PATH, payload.topic, payload.study_days)

@router.post("/links/check")
def links(payload: LinkCheckInput): return check_links(DB_PATH, payload.resource_ids, payload.limit)
