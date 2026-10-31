"""Templates: built-in and user-owned."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Template, User
from app.schemas import TemplateCreateIn, TemplateOut, TemplateSummaryOut
from app.services.content import ContentError, fill_placeholders, parse_content, plain_text

router = APIRouter(
    prefix="/api/templates", tags=["templates"], dependencies=[Depends(require_csrf)]
)


def _preview(template: Template) -> str:
    try:
        text = plain_text(parse_content(template.structure))
    except ContentError:
        return ""
    text = " ".join(text.split())
    return text[:220]


def _summary(template: Template) -> TemplateSummaryOut:
    return TemplateSummaryOut(
        id=template.id,
        slug=template.slug,
        name=template.name,
        description=template.description,
        category=template.category,
        icon=template.icon,
        is_builtin=template.is_builtin,
        fields=template.fields or [],
        preview=_preview(template),
    )


def _visible(user: User):
    return select(Template).where(
        (Template.is_builtin.is_(True)) | (Template.owner_id == user.id)
    )


@router.get("", response_model=list[TemplateSummaryOut])
def list_templates(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TemplateSummaryOut]:
    templates = db.scalars(
        _visible(user).order_by(Template.category, Template.name)
    ).all()
    if q:
        needle = q.strip().lower()
        templates = [
            t
            for t in templates
            if needle in t.name.lower() or needle in t.description.lower()
        ]
    return [_summary(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(
    template_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TemplateOut:
    template = db.get(Template, template_id)
    if template is None or (not template.is_builtin and template.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Template not found")
    summary = _summary(template)
    return TemplateOut(**summary.model_dump(), structure=template.structure or {})


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(
    payload: TemplateCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TemplateOut:
    try:
        structure = parse_content(payload.structure)
    except ContentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    slug = f"{payload.name.strip().lower().replace(' ', '-')[:60]}-{user.id[:8]}"
    template = Template(
        slug=slug,
        name=payload.name.strip(),
        description=payload.description,
        category=payload.category,
        icon="file",
        is_builtin=False,
        owner_id=user.id,
        structure=structure.model_dump(exclude_none=True),
        fields=[f.model_dump() for f in payload.fields],
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    summary = _summary(template)
    return TemplateOut(**summary.model_dump(), structure=template.structure)


@router.post("/{template_id}/preview", response_model=dict)
def preview_template(
    template_id: str,
    values: dict[str, str] | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Fill placeholders so the UI can preview a template before creating a doc."""
    template = db.get(Template, template_id)
    if template is None or (not template.is_builtin and template.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Template not found")
    filled = fill_placeholders(parse_content(template.structure), values or {})
    return {"content": filled.model_dump(exclude_none=True)}
