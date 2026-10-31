"""Environment-driven application settings.

All provider keys stay server-side: nothing in this module is ever exposed to the
browser. Configuration is environment-driven so the same code runs locally, in
tests and on Railway.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core ------------------------------------------------------------------
    environment: str = "development"
    secret_key: str = "dev-only-insecure-secret-key-change-me"
    database_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    task_mode: str = "inline"  # "celery" | "inline"
    auto_create_tables: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Sessions / CSRF -------------------------------------------------------
    cookie_secure: bool = False
    session_ttl_days: int = 14
    session_cookie_name: str = "dd_session"
    csrf_cookie_name: str = "dd_csrf"

    # AI --------------------------------------------------------------------
    ai_provider: str = "openai"  # "openai" (any compatible endpoint) | "mock"
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_max_tokens: int = 4096
    ai_timeout_seconds: float = 60.0

    # Storage ---------------------------------------------------------------
    storage_backend: str = "local"  # "uploadthing" | "local"
    uploadthing_api_key: str | None = None
    uploadthing_app_id: str | None = None
    uploadthing_acl: str = "private"
    local_storage_dir: str = ".data/files"

    # PDF -------------------------------------------------------------------
    pdf_renderer: str = "playwright"  # "playwright" | "libreoffice"
    libreoffice_bin: str = "soffice"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json

                return json.loads(text)
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def uses_uploadthing(self) -> bool:
        return (
            self.storage_backend == "uploadthing"
            and bool(self.uploadthing_api_key)
            and bool(self.uploadthing_app_id)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
