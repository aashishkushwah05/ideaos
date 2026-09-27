"""Knowledge-management primitives."""
from __future__ import annotations
import json, shutil
from pathlib import Path
from datetime import UTC, datetime
from app.database import connect, initialize


def set_state(db_path, resource_id: str, state: str) -> dict:
    allowed={'UNREAD','READ_LATER','TO_LEARN','IN_PROGRESS','COMPLETED','ARCHIVED'}
    if state not in allowed: raise ValueError('invalid state')
    initialize(db_path)
    with connect(db_path) as c:
        if not c.execute('SELECT 1 FROM resources WHERE id=?',(resource_id,)).fetchone(): raise ValueError('resource not found')
        c.execute('UPDATE resources SET knowledge_state=? WHERE id=?',(state,resource_id))
        c.execute('INSERT INTO activity_history(resource_id, action, details_json) VALUES (?,?,?)',(resource_id,'state_changed',json.dumps({'state':state})))
    return {'resource_id':resource_id,'state':state}


def note(db_path, resource_id: str, body: str, kind: str='NOTE') -> dict:
    if not body.strip(): raise ValueError('note body is required')
    initialize(db_path)
    with connect(db_path) as c:
        if not c.execute('SELECT 1 FROM resources WHERE id=?',(resource_id,)).fetchone(): raise ValueError('resource not found')
        cur=c.execute('INSERT INTO notes(resource_id, kind, body) VALUES (?,?,?)',(resource_id,kind,body.strip()))
        c.execute('INSERT INTO activity_history(resource_id, action, details_json) VALUES (?,?,?)',(resource_id,'note_created',json.dumps({'note_id':cur.lastrowid})))
        return {'id':cur.lastrowid,'resource_id':resource_id,'kind':kind,'body':body.strip()}


def saved_search(db_path, name: str, query: dict) -> dict:
    initialize(db_path)
    with connect(db_path) as c:
        c.execute('INSERT INTO saved_searches(name, query_json) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET query_json=excluded.query_json',(name.strip(),json.dumps(query,ensure_ascii=False)))
        row=c.execute('SELECT * FROM saved_searches WHERE name=?',(name.strip(),)).fetchone()
        return dict(row)


def backup(db_path, destination: str) -> dict:
    initialize(db_path)
    target=Path(destination); target.parent.mkdir(parents=True,exist_ok=True)
    with connect(db_path) as c: c.execute('PRAGMA wal_checkpoint(FULL)')
    shutil.copy2(db_path,target)
    return {'path':str(target),'size_bytes':target.stat().st_size}
