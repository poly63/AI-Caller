import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smartcall_ai.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    default_tenant_id: str = os.getenv("DEFAULT_TENANT_ID", "public")
    crm_sync_enabled: bool = os.getenv("CRM_SYNC_ENABLED", "false").lower() == "true"


settings = Settings()
