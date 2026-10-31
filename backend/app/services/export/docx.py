"""DOCX generation.

Two rendering paths, chosen per template (the rendering implementation stays
behind this module so the API layer never cares):

* **Templated** - when a template ships a ``.docx`` skeleton, ``docxtpl``
  renders its ``{{placeholders}}`` with the document's source values and the
  generated body is appended. This keeps documents editable in Word.
* **Plain** - a fresh ``python-docx`` document built from the block content.

Formatting parity matters for PDF exports, so the DOCX produced here can also
be converted by LibreOffice (see ``app.services.export.pdf``).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from docx import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from app.services.content import (
    Block,
    BlockquoteNode,
    BulletListNode,
    CodeBlockNode,
    DocContent,
    DocContent as _Doc,
    HeadingNode,
    HorizontalRuleNode,
    Inline,
    OrderedListNode,
    ParagraphNode,
    HardBreakNode,
    ListItemNode,
    TextNode,
    text_of,
)

INDIGO = RGBColor(0x30, 0x2C, 0x7A)
SLATE = RGBColor(0x47, 0x45, 0x54)
CODE_FONT = "Consolas"


def _apply_marks(run, marks) -> None:
    for mark in marks or []:
        if mark.type == "bold":
            run.bold = True
        elif mark.type == "italic":
            run.italic = True
        elif mark.type == "strike":
            run.font.strike = True
        elif mark.type == "code":
            run.font.name = CODE_FONT
            run.font.size = Pt(9.5)
            shading = OxmlElement("w:shd")
            shading.set(qn("w:val"), "clear")
            shading.set(qn("w:fill"), "F3F2FF")
            run._element.get_or_add_rPr().append(shading)
        elif mark.type == "link":
            run.font.color.rgb = INDIGO
            run.font.underline = True


def _add_runs(paragraph, nodes: list[Inline]) -> None:
    for node in nodes:
        if isinstance(node, HardBreakNode):
            paragraph.add_run().add_break()
            continue
        if not isinstance(node, TextNode):
            continue
        if node.text == "":
            continue
        run = paragraph.add_run(node.text)
        _apply_marks(run, node.marks)


def _shade(paragraph, fill: str) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def _bottom_border(paragraph, color: str = "E6E8EF") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


LIST_STYLES = {0: "List Bullet", 1: "List Bullet 2"}
ORDERED_STYLES = {0: "List Number", 1: "List Number 2"}


def _style_or_fallback(document, preferred: str, fallback: str) -> str:
    styles = document.styles
    try:
        styles[preferred]
        return preferred
    except KeyError:
        return fallback


def append_blocks(document, blocks: list[Block], depth: int = 0) -> None:
    style_key = min(depth, 1)
    for block in blocks:
        if isinstance(block, ParagraphNode):
            if not block.content:
                document.add_paragraph()
                continue
            paragraph = document.add_paragraph()
            _add_runs(paragraph, block.content)
        elif isinstance(block, HeadingNode):
            level = block.level
            paragraph = document.add_paragraph()
            paragraph.style = document.styles[
                _style_or_fallback(document, f"Heading {level}", "Heading 1")
            ]
            _add_runs(paragraph, block.content)
            for run in paragraph.runs:
                run.font.color.rgb = INDIGO if level > 1 else RGBColor(0x17, 0x19, 0x23)
        elif isinstance(block, CodeBlockNode):
            paragraph = document.add_paragraph()
            run = paragraph.add_run(text_of(block) or " ")
            run.font.name = CODE_FONT
            run.font.size = Pt(9.5)
            _shade(paragraph, "F3F2FF")
            paragraph.paragraph_format.space_after = Pt(8)
        elif isinstance(block, BlockquoteNode):
            for inner in block.content:
                if isinstance(inner, list):
                    continue
                paragraph = document.add_paragraph()
                paragraph.paragraph_format.left_indent = Pt(18)
                _add_runs(paragraph, inner.content if isinstance(inner, (ParagraphNode, HeadingNode)) else [])
                for run in paragraph.runs:
                    run.italic = True
                    run.font.color.rgb = SLATE
        elif isinstance(block, (BulletListNode, OrderedListNode)):
            styles = LIST_STYLES if isinstance(block, BulletListNode) else ORDERED_STYLES
            fallback = _style_or_fallback(
                document, styles[style_key], "List Bullet" if isinstance(block, BulletListNode) else "List Number"
            )
            for item in block.content:
                first = True
                for inner in item.content:
                    if isinstance(inner, list):
                        continue
                    if isinstance(inner, (BulletListNode, OrderedListNode)):
                        append_blocks(document, [inner], depth + 1)
                        continue
                    paragraph = document.add_paragraph()
                    paragraph.style = document.styles[fallback]
                    if isinstance(inner, (ParagraphNode, HeadingNode, CodeBlockNode)):
                        if isinstance(inner, CodeBlockNode):
                            run = paragraph.add_run(text_of(inner))
                            run.font.name = CODE_FONT
                        else:
                            _add_runs(paragraph, inner.content)
                    if not first:
                        paragraph.paragraph_format.space_before = Pt(0)
                    first = False
        elif isinstance(block, HorizontalRuleNode):
            paragraph = document.add_paragraph()
            _bottom_border(paragraph)
        else:  # pragma: no cover - defensive
            continue


def _base_document() -> Any:
    document = DocxDocument()
    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    return document


def _load_template(path: str, source: dict[str, Any]):
    from docxtpl import DocxTemplate

    docx_path = Path(path)
    if not docx_path.exists():
        return None, None
    template = DocxTemplate(str(docx_path))
    context = {k: "" if v is None else str(v) for k, v in (source or {}).items()}
    template.render(context, auto_escape=False)
    return template, template.docx


def build_docx(
    content: DocContent,
    *,
    title: str = "Document",
    meta: str | None = None,
    template_path: str | None = None,
    source: dict[str, Any] | None = None,
    show_title: bool = True,
) -> bytes:
    document = None
    tpl = None
    if template_path:
        try:
            tpl, document = _load_template(template_path, source or {})
        except Exception:  # pragma: no cover - fall back to a plain document
            document = None
            tpl = None
    if document is None:
        document = _base_document()
        if show_title:
            heading = document.add_heading(title, level=0)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x17, 0x19, 0x23)
            if meta:
                p = document.add_paragraph()
                run = p.add_run(meta)
                run.font.size = Pt(8.5)
                run.font.color.rgb = SLATE
                _bottom_border(p)

    append_blocks(document, content.content)

    buffer = io.BytesIO()
    if tpl is not None:
        tpl.docx.save(buffer)
    else:
        document.save(buffer)
    return buffer.getvalue()
