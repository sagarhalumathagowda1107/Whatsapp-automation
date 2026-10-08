from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Weekly WhatsApp PDF Report Automation System"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    ADMIN_API_KEY: str = "default-admin-key-change-me"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/whatsapp_reports"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if not v:
            return "postgresql+psycopg://postgres:postgres@localhost:5432/whatsapp_reports"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+psycopg://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # Meta WhatsApp Business Cloud API
    WHATSAPP_ACCESS_TOKEN: str = "mock_token"
    WHATSAPP_PHONE_NUMBER_ID: str = "mock_phone_number_id"
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = "mock_business_account_id"
    WHATSAPP_VERIFY_TOKEN: str = "mock_verify_token"
    WHATSAPP_API_VERSION: str = "v20.0"
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com"
    WHATSAPP_MOCK_MODE: bool = False

    # Report Configuration
    REPORT_STORAGE_PATH: str = "reports/generated"
    COMPANY_NAME: str = "Acme Corp Enterprise"

    # Scheduler Configuration
    REPORT_DAY: str = "MONDAY"  # MONDAY, TUESDAY, etc.
    REPORT_TIME: str = "09:00"  # HH:MM format
    REPORT_TIMEZONE: str = "Asia/Kolkata"
    WHATSAPP_MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
