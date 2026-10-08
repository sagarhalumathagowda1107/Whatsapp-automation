from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str = "1.0.0"
    database: str = "connected"
    scheduler_running: bool = False
