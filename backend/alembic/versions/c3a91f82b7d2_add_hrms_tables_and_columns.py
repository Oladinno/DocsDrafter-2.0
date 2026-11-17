"""add hrms tables and columns

Revision ID: c3a91f82b7d2
Revises: b2f8a1c93e41
Create Date: 2026-11-17 08:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a91f82b7d2"
down_revision: Union[str, None] = "b2f8a1c93e41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table: add role
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=30), server_default="admin", nullable=False),
    )
    op.create_index("ix_users_role", "users", ["role"])

    # 2. Update documents table: add employee_id, candidate_id, category, document_type
    op.add_column(
        "documents",
        sa.Column("employee_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("candidate_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("category", sa.String(length=50), server_default="general", nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("document_type", sa.String(length=50), server_default="custom", nullable=False),
    )
    op.create_index("ix_documents_employee_id", "documents", ["employee_id"])
    op.create_index("ix_documents_candidate_id", "documents", ["candidate_id"])
    op.create_index("ix_documents_category", "documents", ["category"])

    # 3. Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("manager_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)
    op.create_index("ix_departments_code", "departments", ["code"], unique=True)

    # 4. Create employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("employee_code", sa.String(length=30), nullable=False),
        sa.Column("first_name", sa.String(length=60), nullable=False),
        sa.Column("last_name", sa.String(length=60), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("job_title", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("manager_id", sa.String(length=36), nullable=True),
        sa.Column("employment_status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column("employment_type", sa.String(length=30), server_default="full_time", nullable=False),
        sa.Column("hire_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("termination_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("salary", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=10), server_default="USD", nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"], unique=True)
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_manager_id", "employees", ["manager_id"])
    op.create_index("ix_employees_employment_status", "employees", ["employment_status"])

    # 5. Create job_postings table
    op.create_table(
        "job_postings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("employment_type", sa.String(length=30), server_default="full_time", nullable=False),
        sa.Column("location", sa.String(length=100), server_default="Remote", nullable=False),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("requirements", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_job_postings_title", "job_postings", ["title"])
    op.create_index("ix_job_postings_department_id", "job_postings", ["department_id"])
    op.create_index("ix_job_postings_status", "job_postings", ["status"])

    # 6. Create candidates table
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("first_name", sa.String(length=60), nullable=False),
        sa.Column("last_name", sa.String(length=60), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("resume_url", sa.String(length=512), nullable=True),
        sa.Column("linkedin_url", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=60), server_default="direct", nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidates_email", "candidates", ["email"])

    # 7. Create candidate_applications table
    op.create_table(
        "candidate_applications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("job_posting_id", sa.String(length=36), nullable=False),
        sa.Column("stage", sa.String(length=30), server_default="applied", nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("offer_document_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["offer_document_id"], ["documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_candidate_applications_candidate_id", "candidate_applications", ["candidate_id"])
    op.create_index("ix_candidate_applications_job_posting_id", "candidate_applications", ["job_posting_id"])
    op.create_index("ix_candidate_applications_stage", "candidate_applications", ["stage"])

    # Add foreign keys back to documents table
    op.create_foreign_key(
        "fk_documents_employee_id",
        "documents",
        "employees",
        ["employee_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_documents_candidate_id",
        "documents",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_candidate_id", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_employee_id", "documents", type_="foreignkey")

    op.drop_table("candidate_applications")
    op.drop_table("candidates")
    op.drop_table("job_postings")
    op.drop_table("employees")
    op.drop_table("departments")

    op.drop_index("ix_documents_category", table_name="documents")
    op.drop_index("ix_documents_candidate_id", table_name="documents")
    op.drop_index("ix_documents_employee_id", table_name="documents")
    op.drop_column("documents", "document_type")
    op.drop_column("documents", "category")
    op.drop_column("documents", "candidate_id")
    op.drop_column("documents", "employee_id")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "role")
