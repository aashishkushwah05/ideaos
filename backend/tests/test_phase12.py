import sqlite3
from fastapi.testclient import TestClient
from app import config
from app.database import initialize
from app.main import app
import app.routers.resources as rr
import app.routers.advanced as adv

def test_state_and_note(tmp_path,monkeypatch):
    db=tmp_path/'vault.db'; initialize(db); monkeypatch.setattr(rr,'DB_PATH',db); monkeypatch.setattr(adv,'DB_PATH',db); monkeypatch.setattr(config,'DB_PATH',db)
    c=TestClient(app); r=c.post('/resources',json={'url':'https://example.com/x','description':'x'}).json()['resource_id']
    assert c.post(f'/advanced/resources/{r}/state',json={'state':'TO_LEARN'}).status_code==200
    assert c.post('/advanced/notes',json={'resource_id':r,'body':'remember this'}).status_code==200
    with sqlite3.connect(db) as con:
        assert con.execute('select knowledge_state from resources where id=?',(r,)).fetchone()[0]=='TO_LEARN'
        assert con.execute('select count(*) from notes').fetchone()[0]==1


def test_provider_secrets_work_with_no_activation_or_password(tmp_path):
    """The owner/admin activation-password system has been removed — AI
    provider secrets must still be encrypted at rest and readable, with no
    setup/unlock step involved at all."""
    from app.security import read_secret, store_secret, delete_secret, secret_summary
    db = tmp_path / 'vault.db'
    assert read_secret(db, 'provider:openai:api_key') is None
    store_secret(db, 'provider:openai:api_key', 'secret-value')
    assert read_secret(db, 'provider:openai:api_key') == 'secret-value'
    summary = secret_summary(db, 'provider:openai:api_key')
    assert summary['configured'] is True
    assert 'secret-value' not in summary['masked']
    assert summary['masked'].endswith('alue')
    assert delete_secret(db, 'provider:openai:api_key') is True
    assert read_secret(db, 'provider:openai:api_key') is None


def test_secret_is_actually_encrypted_at_rest(tmp_path):
    """Regression: the raw stored value in app_secrets must never be the
    plaintext secret — only Fernet ciphertext."""
    from app.security import store_secret
    db = tmp_path / 'vault.db'
    store_secret(db, 'provider:openai:api_key', 'super-secret-plaintext-value')
    with sqlite3.connect(db) as con:
        row = con.execute("SELECT encrypted_value FROM app_secrets WHERE name=?", ('provider:openai:api_key',)).fetchone()
    assert row is not None
    assert 'super-secret-plaintext-value' not in row[0]
