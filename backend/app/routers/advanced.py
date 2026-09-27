from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.config import DB_PATH
from app.advanced import set_state, note, saved_search

router=APIRouter(prefix='/advanced',tags=['Advanced features'])
class StateRequest(BaseModel): state:str=Field(min_length=1,max_length=30)
class NoteRequest(BaseModel): resource_id:str; body:str=Field(min_length=1,max_length=20000); kind:str='NOTE'
class SavedSearchRequest(BaseModel): name:str=Field(min_length=1,max_length=120); query:dict

@router.post('/resources/{resource_id}/state')
def state(resource_id,payload:StateRequest):
    try:return set_state(DB_PATH,resource_id,payload.state)
    except ValueError as e:raise HTTPException(422,str(e))
@router.post('/notes')
def create_note(payload:NoteRequest):
    try:return note(DB_PATH,payload.resource_id,payload.body,payload.kind)
    except ValueError as e:raise HTTPException(422,str(e))
@router.post('/saved-searches')
def create_saved_search(payload:SavedSearchRequest):return saved_search(DB_PATH,payload.name,payload.query)


@router.get('/resources/{resource_id}/notes')
def list_notes(resource_id: str):
    from app.database import initialize, connect
    initialize(DB_PATH)
    with connect(DB_PATH) as c:
        if not c.execute('SELECT 1 FROM resources WHERE id=?',(resource_id,)).fetchone():
            raise HTTPException(404, 'Resource not found')
        return {'notes':[dict(r) for r in c.execute('SELECT * FROM notes WHERE resource_id=? ORDER BY created_at DESC',(resource_id,)).fetchall()]}

@router.get('/saved-searches')
def list_saved_searches():
    from app.database import initialize, connect
    initialize(DB_PATH)
    with connect(DB_PATH) as c:
        rows=[dict(r) for r in c.execute('SELECT * FROM saved_searches ORDER BY created_at DESC').fetchall()]
    for row in rows:
        try: row['query']=json.loads(row.pop('query_json') or '{}')
        except json.JSONDecodeError: row['query']={}
    return {'saved_searches':rows}

@router.get('/activity')
def activity(limit: int = 50):
    from app.database import initialize, connect
    initialize(DB_PATH); limit=max(1,min(limit,200))
    with connect(DB_PATH) as c:
        rows=[dict(r) for r in c.execute('SELECT * FROM activity_history ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()]
    for row in rows:
        try: row['details']=json.loads(row.pop('details_json') or '{}')
        except json.JSONDecodeError: row['details']={}
    return {'activity':rows}
