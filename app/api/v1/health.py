from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.services.scheduler_service import scheduler

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Application Health Check")
def health_check(db: Session = Depends(get_db)):
    """Public health status check for server monitoring and readiness probes."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        app_name=settings.APP_NAME,
        version="1.0.0",
        database=db_status,
        scheduler_running=scheduler.running
    )
