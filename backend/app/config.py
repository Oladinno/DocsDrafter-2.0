"""Environment-driven application settings.

All provider keys stay server-side: nothing in this module is ever exposed to the
browser. Configuration is environment-driven so the same code runs locally, in
tests and on Railway.
"""

from __future__ import annotations

from functools import lru_cache

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core ------------------------------------------------------------------
    environment: str = "development"
    log_level: str = "info"
    secret_key: str = "dev-only-insecure-secret-key-change-me"
    database_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    task_mode: str = "inline"  # "celery" | "inline"
    auto_create_tables: bool = True
    # ``NoDecode`` keeps the env source from json.loads()-ing the raw value
    # (which would crash on plain https:// urls). The ``_split_origins``
    # validator below then accepts both JSON arrays and comma-separated lists.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

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
    uploadthing_acl: str = "public-read"
    local_storage_dir: str = ".data/files"

    # PDF -------------------------------------------------------------------
    pdf_renderer: str = "playwright"  # "playwright" | "libreoffice"
    libreoffice_bin: str = "soffice"

    @field_validator("database_url", mode="after")
    @classmethod
    def _psycopg_scheme(cls, value: str) -> str:
        # Managed providers (Railway, Supabase, ...) hand out bare
        # ``postgresql://`` URLs (or the legacy ``postgres://`` form), which
        # SQLAlchemy would route to the psycopg2 dialect. Some platforms /
        # past configs even pin ``postgresql+psycopg2://`` explicitly. This
        # project ships psycopg 3 only, so always make the dialect explicit.
        for prefix in ("postgres+psycopg2://", "postgresql+psycopg2://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://"):]
        return value

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
