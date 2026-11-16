"""Department management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Department, Employee, User
from app.schemas import (
    DepartmentCreateIn,
    DepartmentOut,
    DepartmentUpdateIn,
)

router = APIRouter(
    prefix="/api/departments",
    tags=["departments"],
    dependencies=[Depends(require_csrf)],
)


@router.get("", response_model=list[DepartmentOut])
def list_departments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DepartmentOut]:
    # Query departments with aggregated employee counts
    query = (
        select(
            Department,
            func.count(Employee.id).label("employee_count"),
        )
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.id)
        .order_by(Department.name.asc())
    )
    results = db.execute(query).all()

    items = []
    for dept, count in results:
        items.append(
            DepartmentOut(
                id=dept.id,
                name=dept.name,
                code=dept.code,
                description=dept.description or "",
                manager_id=dept.manager_id,
                created_at=dept.created_at,
                employee_count=count,
            )
        )
    return items


@router.post("", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DepartmentOut:
    existing = db.scalar(
        select(Department).where(
            (Department.name == payload.name) | (Department.code == payload.code)
        )
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A department with this name or code already exists",
        )

    dept = Department(
        name=payload.name.strip(),
        code=payload.code.strip().upper(),
        description=payload.description.strip(),
        manager_id=payload.manager_id,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        manager_id=dept.manager_id,
        created_at=dept.created_at,
        employee_count=0,
    )


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(
    department_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DepartmentOut:
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    count = db.scalar(
        select(func.count(Employee.id)).where(Employee.department_id == dept.id)
    ) or 0

    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description or "",
        manager_id=dept.manager_id,
        created_at=dept.created_at,
        employee_count=count,
    )


@router.patch("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: str,
    payload: DepartmentUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DepartmentOut:
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        dept.name = data["name"].strip()
    if "code" in data and data["code"] is not None:
        dept.code = data["code"].strip().upper()
    if "description" in data and data["description"] is not None:
        dept.description = data["description"].strip()
    if "manager_id" in data:
        dept.manager_id = data["manager_id"]

    db.commit()
    db.refresh(dept)

    count = db.scalar(
        select(func.count(Employee.id)).where(Employee.department_id == dept.id)
    ) or 0

    return DepartmentOut(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description or "",
        manager_id=dept.manager_id,
        created_at=dept.created_at,
        employee_count=count,
    )


@router.delete("/{department_id}", status_code=204)
def delete_department(
    department_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(dept)
    db.commit()
