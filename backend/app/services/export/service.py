"""Export execution: render -> upload -> record metadata.

Runs inside a Celery worker in production and inline in development/tests.
The storage provider is reached only through the storage adapter.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.db import SessionLocal
from app.models import Document, Export
from app.services.content import parse_content, to_html, plain_text
from app.services.export import build_docx, render_pdf_from_docx, render_pdf_from_html
from app.services.storage import get_storage

_logger = logging.getLogger(__name__)

DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_MIME = "application/pdf"

MIME_BY_FORMAT = {"docx": DOCX_MIME, "pdf": PDF_MIME}


def export_file_name(title: str, fmt: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title or "document").strip("-").lower()
    slug = slug[:60] or "document"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{slug}-{stamp}.{fmt}"


def _meta_line(document: Document) -> str:
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
    words = document.word_count or 0
    return f"{document.title} · {words} words · exported {stamp}"


def perform_export(export_id: str) -> dict[str, Any]:
    db = SessionLocal()
    export: Export | None = None
    try:
        export = db.get(Export, export_id)
        if export is None:
            raise ValueError(f"export {export_id} not found")
        document = db.get(Document, export.document_id)
        if document is None:
            raise ValueError("document missing")

        export.status = "running"
        db.commit()

        content = parse_content(document.content)
        template_path: str | None = None
        if document.template_id:
            from app.models import Template

            template = db.get(Template, document.template_id)
            if template is not None and template.docx_path:
                template_path = template.docx_path

        fmt = export.format
        renderer = "python-docx"
        if fmt == "docx":
            data = build_docx(
                content,
                title=document.title,
                meta=_meta_line(document),
                template_path=template_path,
                source=document.source,
            )
        else:
            if settings.pdf_renderer == "libreoffice":
                docx_bytes = build_docx(
                    content,
                    title=document.title,
                    meta=_meta_line(document),
                    template_path=template_path,
                    source=document.source,
                )
                data = render_pdf_from_docx(docx_bytes, binary=settings.libreoffice_bin)
                renderer = "libreoffice"
            else:
                html = to_html(
                    content,
                    title=document.title,
                    meta=_meta_line(document),
                    include_document_title=True,
                )
                data = render_pdf_from_html(html)
                renderer = "playwright"

        storage = get_storage()
        stored = storage.upload(
            data,
            filename=export.file_name,
            content_type=MIME_BY_FORMAT[fmt],
        )
        export.status = "succeeded"
        export.storage_backend = storage.name
        export.storage_key = stored.key
        export.storage_url = stored.url
        export.size_bytes = stored.size
        export.renderer = renderer
        export.error = None
        export.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {"id": export.id, "status": "succeeded", "size": stored.size}
    except Exception as exc:  # noqa: BLE001 - job failures are recorded, not raised
        db.rollback()
        _logger.exception(
            "export %s failed while rendering/uploading: %s", export_id, exc
        )
        if export is not None:
            export = db.get(Export, export.id)
            if export is not None:
                export.status = "failed"
                export.error = str(exc)[:2000]
                export.completed_at = datetime.now(timezone.utc)
                db.commit()
        return {"id": export_id, "status": "failed", "error": str(exc)}
    finally:
        db.close()
