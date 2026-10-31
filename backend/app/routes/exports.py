"""Export endpoints: queue rendering, poll status, download after ownership check."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_csrf
from app.models import Document, DocumentVersion, Export, User
from app.schemas import ExportCreateIn, ExportListOut, ExportOut
from app.routes.documents import _latest_version, snapshot_version
from app.services.export.service import export_file_name
from app.services.storage import get_storage
from app.workers.dispatch import dispatch
from app.workers.tasks import EXPORT_TASK

router = APIRouter(prefix="/api", tags=["exports"], dependencies=[Depends(require_csrf)])


def _to_out(export: Export) -> ExportOut:
    out = ExportOut.model_validate(export)
    out.download_url = f"/api/exports/{export.id}/download" if export.status == "succeeded" else ""
    return out


def _owned_export(db: Session, export_id: str, user: User) -> Export:
    export = db.get(Export, export_id)
    if export is None or export.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


def _owned_document(db: Session, document_id: str, user: User) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/documents/{document_id}/exports", response_model=ExportOut, status_code=201)
def create_export(
    document_id: str,
    payload: ExportCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportOut:
    document = _owned_document(db, document_id, user)
    if payload.snapshot:
        # Records the state only when it is newer than the newest version.
        snapshot_version(
            db, document, kind="export", note=f"Snapshot before {payload.format.upper()} export"
        )
    latest = _latest_version(db, document)
    version_number: int | None = latest.version_number if latest else None

    export = Export(
        document_id=document.id,
        owner_id=user.id,
        format=payload.format,
        status="pending",
        file_name=export_file_name(document.title, payload.format),
        version_number=version_number,
    )
    db.add(export)
    db.commit()
    db.refresh(export)

    dispatch(EXPORT_TASK, export.id)

    db.expire(export)
    return _to_out(export)


@router.get("/documents/{document_id}/exports", response_model=ExportListOut)
def list_exports(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportListOut:
    document = _owned_document(db, document_id, user)
    rows = db.scalars(
        select(Export)
        .where(Export.document_id == document.id)
        .order_by(Export.created_at.desc())
    ).all()
    return ExportListOut(items=[_to_out(row) for row in rows])


@router.get("/exports/{export_id}", response_model=ExportOut)
def get_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportOut:
    return _to_out(_owned_export(db, export_id, user))


@router.get("/exports/{export_id}/download")
def download_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    export = _owned_export(db, export_id, user)
    if export.status != "succeeded" or not export.storage_key:
        raise HTTPException(status_code=409, detail="Export is not ready")

    storage = get_storage()
    if storage.name == "local":
        data = storage.read(export.storage_key)  # type: ignore[attr-defined]
        media = (
            "application/pdf"
            if export.format == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return Response(
            content=data,
            media_type=media,
            headers={
                "Content-Disposition": f'attachment; filename="{export.file_name}"',
                "Cache-Control": "private, no-store",
            },
        )

    url = storage.signed_url(export.storage_key, expires_in=300) or export.storage_url
    if not url:
        raise HTTPException(status_code=404, detail="File is no longer available")
    return RedirectResponse(url, status_code=302)


@router.delete("/exports/{export_id}", status_code=204)
def delete_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    export = _owned_export(db, export_id, user)
    if export.storage_key:
        try:
            get_storage().delete(export.storage_key)
        except Exception:  # noqa: BLE001 - remote cleanup must not block deletion
            pass
    db.delete(export)
    db.commit()
