"""
Configuration settings for AI GrowthPilot backend.

NOTE ON GEMINI_API_KEY & PROCESS-GLOBAL STATE:
In this single-user portfolio and assessment platform, GEMINI_API_KEY is maintained as a
process-global configuration. Dynamic updates via /api/settings/gemini-key update the active
Gemini client instance in-memory for the running process.

For production multi-tenant deployments:
1. API keys must NOT be process-global; each organization or user must have an isolated,
   encrypted key stored in a secrets vault (e.g., AWS Secrets Manager, GCP Secret Manager)
   or passed per-request.
2. Administrative actions must be guarded by ADMIN_API_KEY or enterprise OAuth2/OIDC RBAC.
"""
import os
from typing import List
from pydantic_settings import BaseSettings

# Absolute path anchor for default SQLite database
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_PATH = os.path.join(_BASE_DIR, "growthpilot.db").replace("\\", "/")

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    DEMO_MODE: bool = False
    ADMIN_API_KEY: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
