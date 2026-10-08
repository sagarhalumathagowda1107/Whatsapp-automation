from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine
from app.db.models import Base
from app.api.v1.router import api_router
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Initializes database schema tables and starts background APScheduler on startup.
    Ensures graceful shutdown of background jobs on termination.
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Starting background weekly scheduler...")
    start_scheduler()

    yield

    logger.info("Shutting down background scheduler...")
    stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready backend system to automatically generate weekly PDF performance reports "
        "from PostgreSQL data and deliver them to active recipients via the official Meta WhatsApp Business Cloud API."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health Endpoint for Railway / Cloud Load Balancers
@app.get("/health", summary="Railway Health Check", tags=["Health Check"])
def root_health():
    return {"status": "healthy"}

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
