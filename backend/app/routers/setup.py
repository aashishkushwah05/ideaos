"""AI provider credential storage. The owner/admin activation endpoints
that used to live here (/status, /initialize, /unlock, /auto-unlock,
/lock) have been removed along with the rest of that system — see
app/security.py for details. These endpoints are unrelated to that gate:
they let Settings save, inspect (masked only), and remove encrypted
provider API keys."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.config import DB_PATH
from app.security import store_secret, secret_summary, delete_secret

router = APIRouter(prefix='/setup', tags=['AI provider credentials'])

class ProviderSecretInput(BaseModel):
    provider: str = Field(min_length=2, max_length=40)
    api_key: str = Field(min_length=1, max_length=4096)

@router.post('/providers/secret')
def provider_secret(body: ProviderSecretInput):
    try:
        store_secret(DB_PATH, f'provider:{body.provider.lower()}:api_key', body.api_key)
        return {'provider': body.provider.lower(), 'stored': True}
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get('/providers/secret/{provider}')
def get_provider_secret_summary(provider: str):
    """Never returns the actual key — only whether one is configured and a
    masked last-4-characters form, so Settings can show existing credentials
    without ever exposing them in full."""
    return {'provider': provider.lower(), **secret_summary(DB_PATH, f'provider:{provider.lower()}:api_key')}

@router.delete('/providers/secret/{provider}')
def remove_provider_secret(provider: str):
    removed = delete_secret(DB_PATH, f'provider:{provider.lower()}:api_key')
    return {'provider': provider.lower(), 'removed': removed}
