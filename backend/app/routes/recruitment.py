"""Recruitment & ATS (Applicant Tracking System) routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import (
    Candidate,
    CandidateApplication,
    Department,
    Document,
    Employee,
    JobPosting,
    Template,
    User,
)
from app.routes.documents import snapshot_version
from app.schemas import (
    ApplicationOut,
    ApplicationStageUpdateIn,
    CandidateCreateIn,
    CandidateOut,
    CandidateUpdateIn,
    DocumentOut,
    GenerateOfferLetterIn,
    JobPostingCreateIn,
    JobPostingOut,
    JobPostingUpdateIn,
)
from app.services.content import empty_doc, fill_placeholders, parse_content, word_count

router = APIRouter(
    prefix="/api/recruitment",
    tags=["recruitment"],
    dependencies=[Depends(require_csrf)],
)


# ============================================================================
# Job Postings
# ============================================================================


@router.get("/jobs", response_model=list[JobPostingOut])
def list_jobs(
    status: str | None = Query(None),
    department_id: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobPostingOut]:
    query = (
        select(JobPosting, func.count(CandidateApplication.id).label("applicant_count"))
        .outerjoin(CandidateApplication, CandidateApplication.job_posting_id == JobPosting.id)
        .group_by(JobPosting.id)
        .order_by(JobPosting.created_at.desc())
    )
    if status:
        query = query.where(JobPosting.status == status)
    if department_id:
        query = query.where(JobPosting.department_id == department_id)

    results = db.execute(query).all()
    out = []
    for job, count in results:
        dept_name = job.department.name if job.department else None
        out.append(
            JobPostingOut(
                id=job.id,
                title=job.title,
                department_id=job.department_id,
                department_name=dept_name,
                employment_type=job.employment_type,
                location=job.location,
                salary_range=job.salary_range,
                description=job.description,
                requirements=job.requirements,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                applicant_count=count,
            )
        )
    return out


@router.post("/jobs", response_model=JobPostingOut, status_code=201)
def create_job(
    payload: JobPostingCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPostingOut:
    job = JobPosting(
        title=payload.title.strip(),
        department_id=payload.department_id,
        employment_type=payload.employment_type,
        location=payload.location.strip(),
        salary_range=payload.salary_range.strip() if payload.salary_range else None,
        description=payload.description or "",
        requirements=payload.requirements or "",
        status=payload.status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    dept_name = job.department.name if job.department else None
    return JobPostingOut(
        id=job.id,
        title=job.title,
        department_id=job.department_id,
        department_name=dept_name,
        employment_type=job.employment_type,
        location=job.location,
        salary_range=job.salary_range,
        description=job.description,
        requirements=job.requirements,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        applicant_count=0,
    )


@router.patch("/jobs/{job_id}", response_model=JobPostingOut)
def update_job(
    job_id: str,
    payload: JobPostingUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPostingOut:
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    data = payload.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(job, field, val)

    db.commit()
    db.refresh(job)

    count = db.scalar(
        select(func.count(CandidateApplication.id)).where(
            CandidateApplication.job_posting_id == job.id
        )
    ) or 0

    dept_name = job.department.name if job.department else None
    return JobPostingOut(
        id=job.id,
        title=job.title,
        department_id=job.department_id,
        department_name=dept_name,
        employment_type=job.employment_type,
        location=job.location,
        salary_range=job.salary_range,
        description=job.description,
        requirements=job.requirements,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        applicant_count=count,
    )


# ============================================================================
# Candidates & Applications Pipeline
# ============================================================================


def _to_candidate_out(c: Candidate) -> CandidateOut:
    apps = [
        ApplicationOut(
            id=a.id,
            candidate_id=a.candidate_id,
            job_posting_id=a.job_posting_id,
            job_title=a.job_posting.title if a.job_posting else None,
            stage=a.stage,
            rating=a.rating,
            notes=a.notes or "",
            offer_document_id=a.offer_document_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in c.applications
    ]
    return CandidateOut(
        id=c.id,
        first_name=c.first_name,
        last_name=c.last_name,
        email=c.email,
        phone=c.phone,
        resume_url=c.resume_url,
        linkedin_url=c.linkedin_url,
        source=c.source,
        notes=c.notes or "",
        created_at=c.created_at,
        applications=apps,
    )


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(
    job_id: str | None = Query(None),
    stage: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CandidateOut]:
    stmt = select(Candidate).order_by(Candidate.created_at.desc())
    candidates = db.scalars(stmt).all()

    filtered = []
    for c in candidates:
        if job_id and not any(a.job_posting_id == job_id for a in c.applications):
            continue
        if stage and not any(a.stage == stage for a in c.applications):
            continue
        filtered.append(_to_candidate_out(c))
    return filtered


@router.post("/candidates", response_model=CandidateOut, status_code=201)
def create_candidate(
    payload: CandidateCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateOut:
    c = Candidate(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone.strip() if payload.phone else None,
        resume_url=payload.resume_url,
        linkedin_url=payload.linkedin_url,
        source=payload.source,
        notes=payload.notes or "",
    )
    db.add(c)
    db.flush()

    if payload.job_posting_id:
        job = db.get(JobPosting, payload.job_posting_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job posting not found")
        app = CandidateApplication(
            candidate_id=c.id,
            job_posting_id=job.id,
            stage="applied",
        )
        db.add(app)

    db.commit()
    db.refresh(c)
    return _to_candidate_out(c)


@router.patch("/applications/{application_id}/stage", response_model=ApplicationOut)
def update_application_stage(
    application_id: str,
    payload: ApplicationStageUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    app = db.get(CandidateApplication, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.stage = payload.stage
    if payload.notes is not None:
        app.notes = payload.notes
    if payload.rating is not None:
        app.rating = payload.rating

    db.commit()
    db.refresh(app)

    return ApplicationOut(
        id=app.id,
        candidate_id=app.candidate_id,
        job_posting_id=app.job_posting_id,
        job_title=app.job_posting.title if app.job_posting else None,
        stage=app.stage,
        rating=app.rating,
        notes=app.notes or "",
        offer_document_id=app.offer_document_id,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


# ============================================================================
# DocsDrafter HR Bridge: Offer Letter Generation
# ============================================================================


@router.post("/generate-offer-letter", response_model=DocumentOut)
def generate_offer_letter(
    payload: GenerateOfferLetterIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    """Generate an official offer letter document bound to Candidate record."""
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Locate template: specific template_id or default offer letter template
    template: Template | None = None
    if payload.template_id:
        template = db.get(Template, payload.template_id)
    if not template:
        template = db.scalar(
            select(Template).where(
                (Template.slug == "offer-letter") | (Template.name.ilike("%offer letter%"))
            )
        )

    # Prepare values for placeholders
    source_data: dict[str, Any] = {
        "candidate_name": f"{candidate.first_name} {candidate.last_name}",
        "candidate_email": candidate.email,
        "candidate_phone": candidate.phone or "",
        "job_title": payload.job_title,
        "salary": f"{payload.currency} {payload.salary:,}",
        "start_date": payload.start_date,
        "department": payload.department_name or "Operations",
        "manager_name": payload.manager_name or "Hiring Manager",
        **payload.custom_fields,
    }

    if template:
        parsed_structure = parse_content(template.structure)
        content = fill_placeholders(parsed_structure, source_data)
        title = f"Offer Letter - {candidate.first_name} {candidate.last_name}"
    else:
        content = empty_doc()
        title = f"Offer Letter - {candidate.first_name} {candidate.last_name}"

    # Create the document in DocsDrafter engine
    doc = Document(
        owner_id=user.id,
        template_id=template.id if template else None,
        candidate_id=candidate.id,
        category="recruitment",
        document_type="offer_letter",
        title=title,
        content=content.model_dump(exclude_none=True),
        source=source_data,
        word_count=word_count(content),
    )
    db.add(doc)
    db.flush()

    # Link document to the candidate's latest application if exists
    latest_app = db.scalar(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == candidate.id)
        .order_by(CandidateApplication.created_at.desc())
    )
    if latest_app:
        latest_app.offer_document_id = doc.id
        latest_app.stage = "offer"

    db.commit()
    db.refresh(doc)
    snapshot_version(db, doc, kind="manual", note="Generated Offer Letter")
    db.commit()

    return DocumentOut(
        id=doc.id,
        title=doc.title,
        status=doc.status,
        template_id=doc.template_id,
        employee_id=doc.employee_id,
        candidate_id=doc.candidate_id,
        category=doc.category,
        document_type=doc.document_type,
        word_count=doc.word_count,
        version_count=1,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        content=doc.content,
        source=doc.source,
    )
