"""Employee directory and management routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Department, Document, Employee, User
from app.schemas import (
    DocumentSummaryOut,
    EmployeeCreateIn,
    EmployeeDetailOut,
    EmployeeListOut,
    EmployeeSummaryOut,
    EmployeeUpdateIn,
)

router = APIRouter(
    prefix="/api/employees",
    tags=["employees"],
    dependencies=[Depends(require_csrf)],
)


def _to_summary(emp: Employee) -> EmployeeSummaryOut:
    dept_name = emp.department.name if emp.department else None
    mgr_name = f"{emp.manager.first_name} {emp.manager.last_name}" if emp.manager else None
    return EmployeeSummaryOut(
        id=emp.id,
        employee_code=emp.employee_code,
        first_name=emp.first_name,
        last_name=emp.last_name,
        email=emp.email,
        phone=emp.phone,
        job_title=emp.job_title,
        department_id=emp.department_id,
        department_name=dept_name,
        manager_id=emp.manager_id,
        manager_name=mgr_name,
        employment_status=emp.employment_status,
        employment_type=emp.employment_type,
        hire_date=emp.hire_date,
        created_at=emp.created_at,
    )


@router.get("", response_model=EmployeeListOut)
def list_employees(
    query: str | None = Query(None, description="Search by name, email or code"),
    department_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeListOut:
    stmt = select(Employee)

    if query:
        term = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Employee.first_name.ilike(term),
                Employee.last_name.ilike(term),
                Employee.email.ilike(term),
                Employee.employee_code.ilike(term),
            )
        )

    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)

    if status:
        stmt = stmt.where(Employee.employment_status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Employee.last_name.asc()).offset(offset).limit(limit)
    employees = db.scalars(stmt).all()

    return EmployeeListOut(
        items=[_to_summary(emp) for emp in employees],
        total=total,
    )


@router.post("", response_model=EmployeeDetailOut, status_code=201)
def create_employee(
    payload: EmployeeCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeDetailOut:
    # Check for duplicate code or email
    existing = db.scalar(
        select(Employee).where(
            (Employee.employee_code == payload.employee_code)
            | (Employee.email == payload.email)
        )
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An employee with this code or email already exists",
        )

    emp = Employee(
        employee_code=payload.employee_code.strip(),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone.strip() if payload.phone else None,
        job_title=payload.job_title.strip(),
        department_id=payload.department_id,
        manager_id=payload.manager_id,
        employment_status=payload.employment_status,
        employment_type=payload.employment_type,
        hire_date=payload.hire_date,
        termination_date=payload.termination_date,
        salary=payload.salary,
        currency=payload.currency or "USD",
        notes=payload.notes or "",
        user_id=payload.user_id,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    summary = _to_summary(emp)
    return EmployeeDetailOut(
        **summary.model_dump(),
        salary=emp.salary,
        currency=emp.currency,
        notes=emp.notes,
        user_id=emp.user_id,
        termination_date=emp.termination_date,
        document_count=0,
    )


@router.get("/{employee_id}", response_model=EmployeeDetailOut)
def get_employee(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeDetailOut:
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    doc_count = db.scalar(
        select(func.count(Document.id)).where(Document.employee_id == emp.id)
    ) or 0

    summary = _to_summary(emp)
    return EmployeeDetailOut(
        **summary.model_dump(),
        salary=emp.salary,
        currency=emp.currency,
        notes=emp.notes or "",
        user_id=emp.user_id,
        termination_date=emp.termination_date,
        document_count=doc_count,
    )


@router.patch("/{employee_id}", response_model=EmployeeDetailOut)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeDetailOut:
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    data = payload.model_dump(exclude_unset=True)
    for field, val in data.items():
        if field in ("first_name", "last_name", "job_title", "employee_code") and val:
            setattr(emp, field, val.strip())
        elif field == "email" and val:
            setattr(emp, field, val.strip().lower())
        else:
            setattr(emp, field, val)

    db.commit()
    db.refresh(emp)

    doc_count = db.scalar(
        select(func.count(Document.id)).where(Document.employee_id == emp.id)
    ) or 0

    summary = _to_summary(emp)
    return EmployeeDetailOut(
        **summary.model_dump(),
        salary=emp.salary,
        currency=emp.currency,
        notes=emp.notes or "",
        user_id=emp.user_id,
        termination_date=emp.termination_date,
        document_count=doc_count,
    )


@router.get("/{employee_id}/documents", response_model=list[DocumentSummaryOut])
def get_employee_documents(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentSummaryOut]:
    """Retrieve all personnel and contract documents linked to an employee."""
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    docs = db.scalars(
        select(Document)
        .where(Document.employee_id == emp.id)
        .order_by(Document.created_at.desc())
    ).all()

    return [
        DocumentSummaryOut(
            id=d.id,
            title=d.title,
            status=d.status,
            template_id=d.template_id,
            employee_id=d.employee_id,
            candidate_id=d.candidate_id,
            category=d.category or "general",
            document_type=d.document_type or "custom",
            word_count=d.word_count or 0,
            version_count=len(d.versions),
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(emp)
    db.commit()
