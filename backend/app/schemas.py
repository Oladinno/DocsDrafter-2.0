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
    role: str = "admin"
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
    employee_id: str | None = None
    candidate_id: str | None = None
    category: str = Field(default="general", max_length=50)
    document_type: str = Field(default="custom", max_length=50)
    content: dict[str, Any] | None = None
    source: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdateIn(APIModel):
    title: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=30)
    category: str | None = Field(default=None, max_length=50)
    document_type: str | None = Field(default=None, max_length=50)
    employee_id: str | None = None
    candidate_id: str | None = None
    content: dict[str, Any] | None = None
    source: dict[str, Any] | None = None


class DocumentSummaryOut(APIModel):
    id: str
    title: str
    status: str
    template_id: str | None = None
    employee_id: str | None = None
    candidate_id: str | None = None
    category: str = "general"
    document_type: str = "custom"
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


# ============================================================================
# HR & Recruitment Schemas
# ============================================================================


# --- Departments ---


class DepartmentBase(APIModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)
    description: str = Field(default="", max_length=500)
    manager_id: str | None = None


class DepartmentCreateIn(DepartmentBase):
    pass


class DepartmentUpdateIn(APIModel):
    name: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=500)
    manager_id: str | None = None


class DepartmentOut(DepartmentBase):
    id: str
    created_at: datetime
    employee_count: int = 0


# --- Employees ---


class EmployeeBase(APIModel):
    employee_code: str = Field(min_length=1, max_length=30)
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=30)
    job_title: str = Field(min_length=1, max_length=100)
    department_id: str | None = None
    manager_id: str | None = None
    employment_status: str = Field(default="active", max_length=30)
    employment_type: str = Field(default="full_time", max_length=30)
    hire_date: datetime | None = None
    termination_date: datetime | None = None
    salary: int | None = None
    currency: str = Field(default="USD", max_length=10)
    notes: str = Field(default="")
    user_id: str | None = None


class EmployeeCreateIn(EmployeeBase):
    pass


class EmployeeUpdateIn(APIModel):
    employee_code: str | None = Field(default=None, max_length=30)
    first_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=30)
    job_title: str | None = Field(default=None, max_length=100)
    department_id: str | None = None
    manager_id: str | None = None
    employment_status: str | None = Field(default=None, max_length=30)
    employment_type: str | None = Field(default=None, max_length=30)
    hire_date: datetime | None = None
    termination_date: datetime | None = None
    salary: int | None = None
    currency: str | None = Field(default=None, max_length=10)
    notes: str | None = None
    user_id: str | None = None


class EmployeeSummaryOut(APIModel):
    id: str
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    job_title: str
    department_id: str | None = None
    department_name: str | None = None
    manager_id: str | None = None
    manager_name: str | None = None
    employment_status: str
    employment_type: str
    hire_date: datetime | None = None
    created_at: datetime


class EmployeeDetailOut(EmployeeSummaryOut):
    salary: int | None = None
    currency: str = "USD"
    notes: str = ""
    user_id: str | None = None
    termination_date: datetime | None = None
    document_count: int = 0


class EmployeeListOut(APIModel):
    items: list[EmployeeSummaryOut]
    total: int = 0


# --- Recruitment: Job Postings ---


class JobPostingBase(APIModel):
    title: str = Field(min_length=1, max_length=150)
    department_id: str | None = None
    employment_type: str = Field(default="full_time", max_length=30)
    location: str = Field(default="Remote", max_length=100)
    salary_range: str | None = Field(default=None, max_length=100)
    description: str = Field(default="")
    requirements: str = Field(default="")
    status: str = Field(default="open", max_length=30)


class JobPostingCreateIn(JobPostingBase):
    pass


class JobPostingUpdateIn(APIModel):
    title: str | None = Field(default=None, max_length=150)
    department_id: str | None = None
    employment_type: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=100)
    salary_range: str | None = Field(default=None, max_length=100)
    description: str | None = None
    requirements: str | None = None
    status: str | None = Field(default=None, max_length=30)


class JobPostingOut(JobPostingBase):
    id: str
    department_name: str | None = None
    created_at: datetime
    updated_at: datetime
    applicant_count: int = 0


# --- Recruitment: Candidates & Applications ---


class CandidateBase(APIModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=30)
    resume_url: str | None = Field(default=None, max_length=512)
    linkedin_url: str | None = Field(default=None, max_length=512)
    source: str = Field(default="direct", max_length=60)
    notes: str = Field(default="")


class CandidateCreateIn(CandidateBase):
    job_posting_id: str | None = None


class CandidateUpdateIn(APIModel):
    first_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=30)
    resume_url: str | None = Field(default=None, max_length=512)
    linkedin_url: str | None = Field(default=None, max_length=512)
    source: str | None = Field(default=None, max_length=60)
    notes: str | None = None


class ApplicationOut(APIModel):
    id: str
    candidate_id: str
    job_posting_id: str
    job_title: str | None = None
    stage: str
    rating: int | None = None
    notes: str = ""
    offer_document_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationStageUpdateIn(APIModel):
    stage: str = Field(min_length=1, max_length=30)
    notes: str | None = None
    rating: int | None = None


class CandidateOut(CandidateBase):
    id: str
    created_at: datetime
    applications: list[ApplicationOut] = Field(default_factory=list)


# --- DocsDrafter HR Integration: Offer Letter Generation ---


class GenerateOfferLetterIn(APIModel):
    candidate_id: str
    job_posting_id: str | None = None
    template_id: str | None = None
    salary: int
    currency: str = "USD"
    start_date: str
    job_title: str
    department_name: str | None = None
    manager_name: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)

