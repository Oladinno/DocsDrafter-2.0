"""Document CRUD, versions and status."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Document, DocumentVersion, Export, Template, User
from app.schemas import (
    DocumentCreateIn,
    DocumentListOut,
    DocumentOut,
    DocumentStatsOut,
    DocumentSummaryOut,
    DocumentUpdateIn,
    VersionCreateIn,
    VersionOut,
)
from app.services.content import (
    ContentError,
    empty_doc,
    fill_placeholders,
    parse_content,
    plain_text,
    word_count,
)

router = APIRouter(
    prefix="/api/documents", tags=["documents"], dependencies=[Depends(require_csrf)]
)

MAX_CONTENT_WORDS = 200_000


def _get_owned(db: Session, document_id: str, user: User) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _parse(data: Any):
    try:
        return parse_content(data)
    except ContentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _latest_version(db: Session, document: Document) -> DocumentVersion | None:
    return db.scalar(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    )


def _same(a: Any, b: Any) -> bool:
    return json.dumps(a or {}, sort_keys=True, default=str) == json.dumps(
        b or {}, sort_keys=True, default=str
    )


def snapshot_version(
    db: Session,
    document: Document,
    *,
    state: dict[str, Any] | None = None,
    kind: str = "autosave",
    note: str = "",
) -> DocumentVersion | None:
    """Record a document state. Skips when it duplicates the newest version."""
    state = state if state is not None else {
        "title": document.title,
        "status": document.status,
        "content": document.content,
    }
    latest = _latest_version(db, document)
    if latest is not None and _same(latest.content, state["content"]) and latest.title == state["title"]:
        return None
    document.version_counter = (document.version_counter or 0) + 1
    version = DocumentVersion(
        document_id=document.id,
        version_number=document.version_counter,
        title=state["title"],
        status=state.get("status", document.status),
        content=state["content"],
        note=note,
        kind=kind,
    )
    db.add(version)
    db.flush()
    return version


def _version_count(db: Session, document_id: str) -> int:
    rows = db.scalars(
        select(DocumentVersion.id).where(DocumentVersion.document_id == document_id)
    ).all()
    return len(rows)


def _version_counts(db: Session, owner_id: str) -> dict[str, int]:
    rows = db.execute(
        select(DocumentVersion.document_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(Document.owner_id == owner_id)
    ).all()
    counts: dict[str, int] = {}
    for (doc_id,) in rows:
        counts[doc_id] = counts.get(doc_id, 0) + 1
    return counts


def _summary(document: Document, version_count: int = 0) -> DocumentSummaryOut:
    return DocumentSummaryOut(
        id=document.id,
        title=document.title,
        status=document.status,
        template_id=document.template_id,
        word_count=document.word_count or 0,
        version_count=version_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _safe_content(data: Any) -> Any:
    """Re-sanitise stored JSON before it reaches the editor.

    Rows written before the empty-text-node fix would otherwise crash Tiptap
    ("Empty text nodes are not allowed") the moment the document is opened.
    """
    if not data or not isinstance(data, dict):
        return data or {}
    try:
        return parse_content(data).model_dump(exclude_none=True)
    except ContentError:
        return data


def _detail(document: Document, version_count: int = 0) -> DocumentOut:
    base = _summary(document, version_count)
    return DocumentOut(
        **base.model_dump(),
        content=_safe_content(document.content),
        source=document.source or {},
    )


@router.get("", response_model=DocumentListOut)
def list_documents(
    q: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default=None, max_length=30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListOut:
    stmt = select(Document).where(Document.owner_id == user.id)
    if status:
        stmt = stmt.where(Document.status == status)
    documents = db.scalars(stmt.order_by(Document.updated_at.desc())).all()

    if q:
        needle = q.strip().lower()
        matched: list[Document] = []
        for document in documents:
            haystack = document.title.lower()
            if needle in haystack:
                matched.append(document)
                continue
            try:
                if needle in plain_text(parse_content(document.content)).lower():
                    matched.append(document)
            except ContentError:
                continue
        documents = matched

    counts = _version_counts(db, user.id)
    items = [_summary(d, counts.get(d.id, 0)) for d in documents]
    return DocumentListOut(items=items, total=len(items))


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(
    payload: DocumentCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    template: Template | None = None
    if payload.template_id:
        template = db.get(Template, payload.template_id)
        if template is None or (not template.is_builtin and template.owner_id != user.id):
            raise HTTPException(status_code=404, detail="Template not found")
        content = fill_placeholders(_parse(template.structure), payload.source or {})
        source = dict(payload.source or {})
        title = payload.title.strip() or _title_from_template(template, source)
    else:
        content = _parse(payload.content) if payload.content else empty_doc()
        source = dict(payload.source or {})
        title = payload.title.strip() or "Untitled document"

    document = Document(
        owner_id=user.id,
        template_id=template.id if template else None,
        title=title[:255],
        content=content.model_dump(exclude_none=True),
        source=source,
        word_count=word_count(content),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    snapshot_version(db, document, kind="manual", note="Initial version")
    db.commit()
    return _detail(document, 1)


def _title_from_template(template: Template, source: dict[str, Any]) -> str:
    for field in template.fields:
        key = field.get("key") if isinstance(field, dict) else getattr(field, "key", None)
        if key and source.get(key):
            return str(source[key])[:255]
    return template.name[:255]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = _get_owned(db, document_id, user)
    return _detail(document, _version_count(db, document.id))


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: str,
    payload: DocumentUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = _get_owned(db, document_id, user)
    data = payload.model_dump(exclude_unset=True)

    content_changed = "content" in data and data["content"] is not None

    if data.get("title") is not None:
        title = data["title"].strip()
        document.title = (title or "Untitled document")[:255]
    if data.get("status") is not None:
        document.status = data["status"][:30]
    if data.get("source") is not None:
        document.source = dict(data["source"] or {})
    if content_changed:
        parsed = _parse(data["content"])
        document.content = parsed.model_dump(exclude_none=True)
        document.word_count = word_count(parsed)

    # Keep history: every saved state is recorded, unless it duplicates the
    # newest version (snapshot_version skips identical content).
    if content_changed:
        snapshot_version(db, document, kind="autosave")

    db.commit()
    db.refresh(document)
    return _detail(document, _version_count(db, document.id))


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    document = _get_owned(db, document_id, user)
    db.delete(document)
    db.commit()


@router.get("/{document_id}/stats", response_model=DocumentStatsOut)
def document_stats(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentStatsOut:
    document = _get_owned(db, document_id, user)
    content = parse_content(document.content)
    text = plain_text(content)
    words = word_count(content)
    versions = _version_count(db, document.id)
    exports = len(
        db.scalars(select(Export.id).where(Export.document_id == document.id)).all()
    )
    return DocumentStatsOut(
        words=words,
        characters=len(text),
        reading_minutes=max(1, round(words / 200)),
        versions=versions,
        exports=exports,
    )


# --- versions ---------------------------------------------------------------


@router.get("/{document_id}/versions", response_model=list[VersionOut])
def list_versions(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[VersionOut]:
    document = _get_owned(db, document_id, user)
    rows = db.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
    ).all()
    return [
        VersionOut.model_validate(row).model_copy(
            update={"content": _safe_content(row.content)}
        )
        for row in rows
    ]


@router.post("/{document_id}/versions", response_model=VersionOut, status_code=201)
def create_version(
    document_id: str,
    payload: VersionCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VersionOut:
    document = _get_owned(db, document_id, user)
    version = snapshot_version(db, document, kind="manual", note=payload.note)
    if version is None:
        latest = _latest_version(db, document)
        if latest is None:  # pragma: no cover - defensive
            raise HTTPException(status_code=409, detail="Nothing to snapshot")
        return VersionOut.model_validate(latest)
    db.commit()
    db.refresh(version)
    return VersionOut.model_validate(version)


@router.post("/{document_id}/versions/{version_id}/restore", response_model=DocumentOut)
def restore_version(
    document_id: str,
    version_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = _get_owned(db, document_id, user)
    version = db.get(DocumentVersion, version_id)
    if version is None or version.document_id != document.id:
        raise HTTPException(status_code=404, detail="Version not found")

    snapshot_version(
        db,
        document,
        kind="manual",
        note=f"Before restoring v{version.version_number}",
    )
    parsed = _parse(version.content)
    document.title = version.title
    document.status = version.status
    document.content = parsed.model_dump(exclude_none=True)
    document.word_count = word_count(parsed)
    db.commit()
    db.refresh(document)
    return _detail(document, _version_count(db, document.id))
