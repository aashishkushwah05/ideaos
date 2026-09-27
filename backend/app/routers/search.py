from fastapi import APIRouter, Query

from app.config import DB_PATH
from app.search import recent_searches, search_facets, search_resources

router = APIRouter(prefix="/resources", tags=["Resource search"])


@router.get("/search")
def search(
    q: str = Query(default="", max_length=500),
    category: str | None = Query(default=None, max_length=120),
    subcategory: str | None = Query(default=None, max_length=120),
    platform: str | None = Query(default=None, max_length=80),
    resource_type: str | None = Query(default=None, max_length=80),
    favorite: bool | None = None,
    ai_status: str | None = Query(default=None, max_length=20),
    import_status: str | None = Query(default=None, max_length=30),
    date_from: str | None = Query(default=None, max_length=40),
    date_to: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
):
    return search_resources(DB_PATH, q=q, category=category, subcategory=subcategory, platform=platform, resource_type=resource_type, favorite=favorite, ai_status=ai_status, import_status=import_status, date_from=date_from, date_to=date_to, page=page, page_size=page_size)


@router.get("/facets")
def facets():
    return search_facets(DB_PATH)


@router.get("/search/recent")
def recent(limit: int = Query(default=10, ge=1, le=50)):
    return {"items": recent_searches(DB_PATH, limit)}
