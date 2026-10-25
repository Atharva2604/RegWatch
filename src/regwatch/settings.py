"""12-Factor Application Configuration via Pydantic Settings."""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"

    # Supabase (Database & Storage)
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase API Key (service_role or anon)")

    # LLM Configuration
    groq_api_key: str = Field(default="", description="Groq API key for inference")
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = Field(default="", description="Optional Google Gemini API key fallback")

    # Ingestion & Scraping Policies
    user_agent: str = "RegWatch/1.0 (+https://github.com/RegWatch; compliance-monitoring-bot)"
    request_timeout_seconds: int = 20
    max_scrape_pages: int = 50
    rate_limit_rps: float = 0.5  # Requests per second per regulator host
    max_concurrent_requests: int = 2

    # Notification / Alerting Settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_recipients: list[str] = []
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of application settings."""
    return Settings()
