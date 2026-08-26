"""Environment-backed configuration used across the voice backend."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Typed view of environment configuration for the voice backend."""
    # Google Calendar service-account credentials for event creation.
    calendar_id: str = os.getenv("CALENDAR_ID", "")
    service_account_json: str | None = os.getenv("SERVICE_ACCOUNT_JSON")
    service_account_file: str = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")

    # Google OAuth + session config for browser login flow.
    google_oauth_client_id: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    google_oauth_client_secret: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret")
    # OpenAI API key for Whisper STT and other OpenAI services.
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    # Environment: 'production' for cloud, 'development' for local
    environment: str = os.getenv("ENVIRONMENT", "development")
    # Internal backend-to-backend auth key (Sham <-> Ram).
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "")
    # Backend Agent connection used by Ram summary and upload endpoints.
    backend_agent_base_url: str = os.getenv("BACKEND_AGENT_BASE_URL", "").rstrip("/")
    backend_agent_internal_api_key: str = os.getenv("BACKEND_AGENT_INTERNAL_API_KEY", "")
    backend_agent_timeout_seconds: float = float(os.getenv("BACKEND_AGENT_TIMEOUT_SECONDS", "20"))
    backend_agent_knowledge_upload_url: str = os.getenv("BACKEND_AGENT_KNOWLEDGE_UPLOAD_URL","")
    vapi_public_key: str = os.getenv("VAPI_PUBLIC_KEY", "")
    app_db_path: str = os.getenv("APP_DB_PATH", "data/app.db")
    react_dev_url: str = os.getenv("REACT_DEV_URL", "http://localhost:5173")
    
   



settings = Settings()
