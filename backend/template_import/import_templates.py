"""Import the 23 CSV template rows into the backend database.

Run this against a dev/test database (TASK_MODE=inline, AUTO_CREATE_TABLES=true) to
seed user-owned templates. Each CSV row's metadata.templateConfig.blocks is already in
the project's Tiptap/ProseMirror block-JSON shape, so it is inserted as-is.

The mapping is:
  metadata.templateConfig.blocks  ->  Template.structure  (Tiptap block JSON)
  json_schema                     ->  Template.fields     (structured field defs)
  metadata.templateConfig.title   ->  Template.name       (falls back to CSV name)
  CSV name                        ->  Template.name

Empty text nodes and table/list/signature blocks are dropped because the editor
(ProseMirror/Tiptap) rejects them; placeholders stay as {{key}} text nodes.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.db import SessionLocal  # noqa: E402
from app.models import Template  # noqa: E402
from app.seed import seed_templates  # noqa: E402

IMPORT_PATH = os.path.join(ROOT, "template_import", "templates_import.json")


def _import(owner_id: str | None = None) -> int:
    with open(IMPORT_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    db = SessionLocal()
    try:
        existing = {r[0] for r in db.query(Template.id).all()}
        created = 0
        for row in rows:
            if row["id"] in existing:
                continue  # builtin or already imported
            fields = []
            for f in row.get("fields") or []:
                fields.append(
                    {
                        "key": f["key"],
                        "label": f.get("label", f["key"].replace("_", " ").title()),
                        "kind": f.get("kind", "text"),
                        "required": f.get("required", False),
                        "placeholder": f.get("placeholder", ""),
                        "default": f.get("default", ""),
                    }
                )

            template = Template(
                slug=row["id"],
                name=row.get("name", row.get("templateConfig", {}).get("title", row["name"])),
                description=row.get("description", ""),
                category=row.get("category", "Imported"),
                icon=row.get("icon", "file"),
                is_builtin=False,
                owner_id=owner_id,
                structure=row.get("structure") or {"type": "doc", "content": []},
                fields=fields,
                created_at=row.get("created_at"),
            )
            db.add(template)
            created += 1
        db.commit()
        print(f"Imported {created} templates.")
        return created
    finally:
        db.close()


if __name__ == "__main__":
    _import()
