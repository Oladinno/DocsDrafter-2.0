"""Built-in template seeding.

Templates are stored in the database. Two of them also ship a ``docxtpl``
skeleton so the templated DOCX path (placeholders rendered in Word, editable
output) is exercised; the files are generated on first run if missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Template

DOCX_DIR = Path(__file__).resolve().parent / "builtin_docx"


def _heading(text: str, level: int = 2) -> dict[str, Any]:
    if not text:
        return {"type": "heading", "attrs": {"level": level}, "content": []}
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _p(text: str) -> dict[str, Any]:
    # An empty text node is invalid in ProseMirror and crashes the editor.
    if not text:
        return {"type": "paragraph", "content": []}
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def _doc(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(blocks)}


def _bullets(*items: str) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [_p(item)]} for item in items
        ],
    }


BUILTIN_TEMPLATES: list[dict[str, Any]] = [
    {
        "slug": "blank",
        "name": "Blank document",
        "description": "Start from an empty page and shape it yourself.",
        "category": "Basics",
        "icon": "file",
        "fields": [],
        "structure": _doc(_p("")),
    },
    {
        "slug": "meeting-notes",
        "name": "Meeting notes",
        "description": "Agenda, attendees, decisions and follow-ups in one page.",
        "category": "Productivity",
        "icon": "users",
        "fields": [
            {"key": "topic", "label": "Meeting topic", "required": True, "placeholder": "Q4 planning"},
            {"key": "date", "label": "Date", "placeholder": "24 October 2026"},
            {"key": "attendees", "label": "Attendees", "placeholder": "Ana, Ben, Chris"},
        ],
        "structure": _doc(
            _heading("Meeting notes", 1),
            _p("Topic: {{topic}}"),
            _p("Date: {{date}}"),
            _p("Attendees: {{attendees}}"),
            _heading("Agenda", 2),
            _bullets("Item one", "Item two", "Item three"),
            _heading("Discussion", 2),
            _p(""),
            _heading("Decisions", 2),
            _bullets("Decision one", "Decision two"),
            _heading("Action items", 2),
            _p(""),
        ),
    },
    {
        "slug": "project-proposal",
        "name": "Project proposal",
        "description": "Objective, scope, timeline and budget for a new initiative.",
        "category": "Business",
        "icon": "briefcase",
        "docx": "project-proposal.docx",
        "fields": [
            {"key": "projectName", "label": "Project name", "required": True, "placeholder": "Atlas Migration"},
            {"key": "client", "label": "Client or team", "placeholder": "Platform team"},
            {"key": "author", "label": "Author", "placeholder": "Your name"},
            {"key": "date", "label": "Date", "placeholder": "24 October 2026"},
            {"key": "objective", "label": "Objective", "placeholder": "Reduce deployment time by half"},
        ],
        "structure": _doc(
            _heading("Project proposal", 1),
            _p("Project: {{projectName}}"),
            _p("Prepared for {{client}} by {{author}} - {{date}}"),
            _heading("Objective", 2),
            _p("{{objective}}"),
            _heading("Scope", 2),
            _bullets("In scope: ", "Out of scope: ", "Assumptions: "),
            _heading("Approach", 2),
            _p(""),
            _heading("Timeline", 2),
            _bullets("Week 1-2: discovery and design", "Week 3-6: implementation", "Week 7-8: rollout and review"),
            _heading("Risks", 2),
            _p(""),
            _heading("Next steps", 2),
            _p(""),
        ),
    },
    {
        "slug": "business-report",
        "name": "Business report",
        "description": "Findings, metrics and recommendations with an executive summary.",
        "category": "Business",
        "icon": "chart",
        "fields": [
            {"key": "reportTitle", "label": "Report title", "required": True, "placeholder": "Q3 performance"},
            {"key": "period", "label": "Reporting period", "placeholder": "Jul - Sep 2026"},
            {"key": "author", "label": "Prepared by", "placeholder": "Your name"},
        ],
        "structure": _doc(
            _heading("{{reportTitle}}", 1),
            _p("Period: {{period}} - Prepared by {{author}}"),
            _heading("Executive summary", 2),
            _p(""),
            _heading("Key metrics", 2),
            _bullets("Metric one: 0%", "Metric two: 0", "Metric three: 0"),
            _heading("Findings", 2),
            _p(""),
            _heading("Recommendations", 2),
            _bullets("Recommendation one", "Recommendation two"),
        ),
    },
    {
        "slug": "cover-letter",
        "name": "Cover letter",
        "description": "A concise letter tailored to a role and company.",
        "category": "Career",
        "icon": "mail",
        "docx": "cover-letter.docx",
        "fields": [
            {"key": "yourName", "label": "Your name", "required": True, "placeholder": "Jordan Lee"},
            {"key": "company", "label": "Company", "required": True, "placeholder": "Northwind"},
            {"key": "role", "label": "Role", "required": True, "placeholder": "Product Engineer"},
            {"key": "hiringManager", "label": "Hiring manager", "placeholder": "Alex Rivera"},
            {"key": "highlights", "label": "Key highlights", "placeholder": "shipped X, improved Y"},
        ],
        "structure": _doc(
            _heading("Cover letter", 1),
            _p("Dear {{hiringManager}},"),
            _p("I am applying for the {{role}} position at {{company}}."),
            _p("{{highlights}}"),
            _p("I would welcome the chance to discuss how I can contribute to {{company}}."),
            _p("Sincerely,"),
            _p("{{yourName}}"),
        ),
    },
]


def _write_docx_skeleton(path: Path, blocks: list[dict[str, Any]], source_fields: list[dict]) -> None:
    """Create a .docx skeleton whose text carries {{placeholder}} markers."""
    from docx import Document as DocxDocument
    from docx.shared import Pt, RGBColor

    document = DocxDocument()
    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    for block in blocks:
        text = "".join(node.get("text", "") for node in block.get("content", []))
        if block["type"] == "heading":
            level = int(block.get("attrs", {}).get("level", 1))
            paragraph = document.add_heading(text, level=min(level, 4))
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(0x30, 0x2C, 0x7A)
        elif block["type"] == "bulletList":
            for item in block.get("content", []):
                inner = item.get("content", [{}])[0]
                item_text = "".join(
                    node.get("text", "") for node in inner.get("content", [])
                )
                document.add_paragraph(item_text, style="List Bullet")
        else:
            document.add_paragraph(text)
    document.save(str(path))


def _ensure_docx_files() -> None:
    DOCX_DIR.mkdir(parents=True, exist_ok=True)
    for template in BUILTIN_TEMPLATES:
        name = template.get("docx")
        if not name:
            continue
        path = DOCX_DIR / name
        if not path.exists():
            _write_docx_skeleton(
                path, template["structure"]["content"], template["fields"]
            )
            # docxtpl needs the placeholders verbatim; python-docx wrote them
            # already because each paragraph is a single run.


def seed_templates(db: Session) -> int:
    _ensure_docx_files()
    existing = db.scalar(select(func.count()).select_from(Template)) or 0
    if existing:
        return 0
    created = 0
    for template in BUILTIN_TEMPLATES:
        docx_path = None
        if template.get("docx"):
            docx_path = str(DOCX_DIR / template["docx"])
        db.add(
            Template(
                slug=template["slug"],
                name=template["name"],
                description=template["description"],
                category=template["category"],
                icon=template.get("icon", "file"),
                is_builtin=True,
                structure=template["structure"],
                fields=template["fields"],
                docx_path=docx_path,
            )
        )
        created += 1
    db.commit()
    return created
