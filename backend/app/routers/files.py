from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import DB_PATH
from app.file_storage import save_local_file

router = APIRouter(prefix='/files', tags=['Local files'])

@router.post('')
async def upload(file: UploadFile = File(...), resource_id: str | None = None):
    try:
        return save_local_file(DB_PATH, file.file, file.filename or 'file', file.content_type, resource_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
