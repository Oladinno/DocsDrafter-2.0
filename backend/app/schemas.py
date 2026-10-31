"""API request/response schemas (camelCase on the wire)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import AliasGenerator, BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )

    @field_serializer("*", mode="plain", when_used="json")
    def _serialize_datetimes(self, value: Any) -> Any:
        """Emit timezone-aware ISO-8601 (``...Z``) so clients never guess."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat().replace("+00:00", "Z")
        return value


# --- auth -------------------------------------------------------------------


class RegisterIn(APIModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=120)

    @field_validator("email")
    @classmethod
    def _lower(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class LoginIn(APIModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _lower_login(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(APIModel):
    id: str
    email: str
    name: str
    created_at: datetime


class CsrfOut(APIModel):
    csrf_token: str


# --- browser log ingestion ---------------------------------------------------


class ClientLogIn(APIModel):
    level: Literal["error", "warn", "info"] = "error"
    message: str = Field(min_length=1, max_length=2000)
    stack: str | None = Field(default=None, max_length=8000)
    url: str | None = Field(default=None, max_length=2048)
    user_agent: str | None = Field(default=None, max_length=400)


# --- templates ---------------------------------------------------------------


class TemplateField(APIModel):
    key: str
    label: str
    kind: str = "text"
    required: bool = False
    placeholder: str = ""
    default: str = ""


class TemplateSummaryOut(APIModel):
    id: str
    slug: str
    name: str
    description: str
    category: str
    icon: str
    is_builtin: bool
    fields: list[TemplateField] = Field(default_factory=list)
    preview: str = ""


class TemplateOut(TemplateSummaryOut):
    structure: dict[str, Any] = Field(default_factory=dict)


class TemplateCreateIn(APIModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="General", max_length=60)
    structure: dict[str, Any] = Field(default_factory=dict)
    fields: list[TemplateField] = Field(default_factory=list)


# --- documents ---------------------------------------------------------------


class DocumentCreateIn(APIModel):
    title: str = Field(default="", max_length=255)
    template_id: str | None = None
    content: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdateIn(APIModel):
    title: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=30)
    content: dict[str, Any] | None = None
    source: dict[str, Any] | None = None


class DocumentSummaryOut(APIModel):
    id: str
    title: str
    status: str
    template_id: str | None = None
    word_count: int = 0
    version_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentOut(DocumentSummaryOut):
    content: dict[str, Any] = Field(default_factory=dict)
    source: dict[str, Any] = Field(default_factory=dict)


class DocumentListOut(APIModel):
    items: list[DocumentSummaryOut]
    total: int = 0


class VersionCreateIn(APIModel):
    note: str = Field(default="", max_length=255)


class VersionOut(APIModel):
    id: str
    document_id: str
    version_number: int
    title: str
    status: str
    note: str
    kind: str
    created_at: datetime


class DocumentStatsOut(APIModel):
    words: int
    characters: int
    reading_minutes: int
    versions: int
    exports: int


# --- AI ----------------------------------------------------------------------


class AIGenerateIn(APIModel):
    operation: Literal["draft", "rewrite", "expand", "summarize"]
    document_id: str | None = None
    prompt: str = Field(default="", max_length=8000)
    selection: str = Field(default="", max_length=20000)
    instructions: str = Field(default="", max_length=2000)
    title: str = Field(default="", max_length=255)
    surrounding: str = Field(default="", max_length=6000)


class JobOut(APIModel):
    id: str
    kind: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AIOperationsOut(APIModel):
    items: list[dict[str, str]]


# --- exports -----------------------------------------------------------------


class ExportCreateIn(APIModel):
    format: Literal["docx", "pdf"] = "docx"
    snapshot: bool = True


class ExportOut(APIModel):
    id: str
    document_id: str
    format: str
    status: str
    file_name: str
    storage_backend: str
    size_bytes: int | None = None
    renderer: str | None = None
    version_number: int | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    download_url: str = ""


class ExportListOut(APIModel):
    items: list[ExportOut]


# --- health ------------------------------------------------------------------


class HealthOut(APIModel):
    status: str
    database: str
    storage: str
    tasks: str
    environment: str
