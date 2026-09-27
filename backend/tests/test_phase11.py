import io, sqlite3
from app.database import initialize
from app.file_storage import save_local_file

def test_local_file_storage_is_hashed_and_recorded(tmp_path):
    db=tmp_path/'vault.db'; initialize(db)
    result=save_local_file(db, io.BytesIO(b'hello'), 'notes.txt', 'text/plain')
    assert result['size_bytes']==5
    assert len(result['sha256'])==64
    assert (tmp_path/result['stored_path']).exists()
    with sqlite3.connect(db) as c:
        assert c.execute('select count(*) from local_files').fetchone()[0]==1
