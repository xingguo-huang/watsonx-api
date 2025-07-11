from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN

from app.core.settings import settings

# This is a simple API key security scheme you can use if needed
# Not required for the current implementation but good to have

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if not api_key_header:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="API key is missing"
        )
    # In a real application, you would validate this against a database or config
    # For demo, we'll just check if it's not empty
    return api_key_header
