from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db

async def verify_admin_api_key(
    x_api_key: str | None = Header(None, description="Administrative API Key for protected endpoints")
) -> str:
    """Dependency to validate the X-API-Key header against settings.ADMIN_API_KEY."""
    if not x_api_key or x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    return x_api_key
