from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.psf import router as psf_router
from app.api.v1.recipients import router as recipients_router
from app.api.v1.reports import router as reports_router
from app.api.v1.whatsapp import router as whatsapp_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(psf_router)
api_router.include_router(recipients_router)
api_router.include_router(reports_router)
api_router.include_router(whatsapp_router)
