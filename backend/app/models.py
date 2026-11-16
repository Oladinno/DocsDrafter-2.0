"""SQLAlchemy models.

File contents are never stored in the database: exports live in the storage
provider (UploadThing in production) and PostgreSQL only keeps metadata plus
the provider's file key.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(30), default="admin", index=True)  # admin | hr_admin | recruiter | manager | employee
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    employee_profile: Mapped[Employee | None] = relationship(
        back_populates="user", uselist=False
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    csrf_token: Mapped[str] = mapped_column(String(128))
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="sessions")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), default="General")
    icon: Mapped[str] = mapped_column(String(40), default="file")
    is_builtin: Mapped[bool] = mapped_column(default=False)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Document structure (block JSON) with {{placeholder}} markers.
    structure: Mapped[dict[str, Any]] = mapped_column(JSON)
    # Field definitions the UI renders when starting from this template.
    fields: Mapped[list[Any]] = mapped_column(JSON, default=list)
    # Optional docxtpl .docx file (path) used for DOCX export parity.
    docx_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize a Template into a TemplateOut payload."""
        from app.services.content import plain_text, parse_content

        try:
            preview = " ".join(plain_text(parse_content(self.structure)).split())[:220]
        except Exception:
            preview = ""
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "is_builtin": self.is_builtin,
            "fields": self.fields or [],
            "preview": preview,
        }


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    employee_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), default="general", index=True)  # hr_contract | offer_letter | policy | general
    document_type: Mapped[str] = mapped_column(String(50), default="custom")  # offer_letter | nda | employment_contract | ...
    title: Mapped[str] = mapped_column(String(255), default="Untitled document")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Values supplied for the template's {{placeholders}}.
    source: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    version_counter: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    owner: Mapped[User] = relationship(back_populates="documents")
    employee: Mapped[Employee | None] = relationship(back_populates="documents")
    candidate: Mapped[Candidate | None] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.created_at.desc()",
    )
    exports: Mapped[list[Export]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    note: Mapped[str] = mapped_column(String(255), default="")
    kind: Mapped[str] = mapped_column(String(20), default="autosave")  # autosave | manual | export
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[Document] = relationship(back_populates="versions")


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    format: Mapped[str] = mapped_column(String(10))  # docx | pdf
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    storage_backend: Mapped[str] = mapped_column(String(30), default="local")
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    renderer: Mapped[str | None] = mapped_column(String(40), nullable=True)
    version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    document: Mapped[Document] = relationship(back_populates="exports")


class Job(Base):
    """Pollable background job (AI generation, ...)."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


Index("ix_documents_owner_updated", Document.owner_id, Document.updated_at)
Index("ix_exports_document_status", Export.document_id, Export.status)


# ============================================================================
# HR Management Models
# ============================================================================


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    manager_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    employees: Mapped[list[Employee]] = relationship(
        back_populates="department", foreign_keys="Employee.department_id"
    )
    job_postings: Mapped[list[JobPosting]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    job_title: Mapped[str] = mapped_column(String(100))
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employment_status: Mapped[str] = mapped_column(
        String(30), default="active", index=True
    )  # active | on_leave | terminated | onboarding
    employment_type: Mapped[str] = mapped_column(
        String(30), default="full_time"
    )  # full_time | part_time | contractor | intern
    hire_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped[User | None] = relationship(back_populates="employee_profile")
    department: Mapped[Department | None] = relationship(
        back_populates="employees", foreign_keys=[department_id]
    )
    manager: Mapped[Employee | None] = relationship(
        remote_side=[id], back_populates="direct_reports"
    )
    direct_reports: Mapped[list[Employee]] = relationship(
        back_populates="manager"
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="employee"
    )


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(150), index=True)
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employment_type: Mapped[str] = mapped_column(String(30), default="full_time")
    location: Mapped[str] = mapped_column(String(100), default="Remote")
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)  # draft | open | closed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    department: Mapped[Department | None] = relationship(back_populates="job_postings")
    applications: Mapped[list[CandidateApplication]] = relationship(
        back_populates="job_posting", cascade="all, delete-orphan"
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(String(60), default="direct")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    applications: Mapped[list[CandidateApplication]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="candidate"
    )


class CandidateApplication(Base):
    __tablename__ = "candidate_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    job_posting_id: Mapped[str] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(
        String(30), default="applied", index=True
    )  # applied | screening | interview | offer | hired | rejected
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 5
    notes: Mapped[str] = mapped_column(Text, default="")
    offer_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job_posting: Mapped[JobPosting] = relationship(back_populates="applications")
    offer_document: Mapped[Document | None] = relationship(foreign_keys=[offer_document_id])
