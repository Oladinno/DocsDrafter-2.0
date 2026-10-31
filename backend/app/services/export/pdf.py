"""PDF rendering paths.

* ``playwright`` - render the document as HTML/CSS in headless Chromium and
  print to PDF (web-native layouts).
* ``libreoffice`` - convert the generated DOCX, where DOCX-to-PDF formatting
  parity matters.

The renderer is selected by environment configuration so the API layer stays
implementation-agnostic.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class PDFRenderError(RuntimeError):
    pass


def render_pdf_from_html(html: str, *, timeout_ms: int = 30_000) -> bytes:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise PDFRenderError("playwright is not installed") from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--no-sandbox"])
            try:
                page = browser.new_page()
                page.set_content(html, wait_until="load", timeout=timeout_ms)
                pdf = page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise PDFRenderError(f"PDF rendering timed out: {exc}") from exc
    except Exception as exc:  # browser missing / crashed
        raise PDFRenderError(
            f"Chromium failed to render the PDF ({exc}). "
            "Run `playwright install chromium` in the build image."
        ) from exc
    return pdf


def render_pdf_from_docx(docx_bytes: bytes, *, binary: str = "soffice") -> bytes:
    """DOCX -> PDF via LibreOffice for layout parity."""
    resolved = shutil.which(binary)
    if not resolved:
        raise PDFRenderError(
            f"LibreOffice binary `{binary}` not found. Set LIBREOFFICE_BIN or use "
            "PDF_RENDERER=playwright."
        )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "document.docx"
        source.write_bytes(docx_bytes)
        result = subprocess.run(
            [
                resolved,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_dir),
                str(source),
            ],
            capture_output=True,
            timeout=120,
        )
        output = tmp_dir / "document.pdf"
        if result.returncode != 0 or not output.exists():
            raise PDFRenderError(
                f"LibreOffice conversion failed: {result.stderr.decode()[:400]}"
            )
        return output.read_bytes()
