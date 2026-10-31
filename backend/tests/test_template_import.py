"""End-to-end template import test.

Verifies that the 23 CSV template rows can be imported into the backend
database and that the /api/templates endpoint + placeholder filling work for
both the builtin templates (seeded by conftest) and the imported templates.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import pytest

# Reuse the project root on sys.path so the import_templates module resolves.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import template data produced by template_import/convert.py.
IMPORT_PATH = os.path.join(ROOT, "template_import", "templates_import.json")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.models import Template  # noqa: E402
from app.seed import seed_templates  # noqa: E402

# The test DB is seeded with builtins by conftest. Insert the imported rows
# before the template tests run.
@pytest.fixture(scope="session", autouse=True)
def _seed_imported_templates():
    with open(IMPORT_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    # Make the fixture idempotent: drop any previously imported rows, then
    # re-insert all 23. The conftest resets the DB per session, so this is
    # safe; the check guards against the first run on an already-seeded DB.
    with SessionLocal() as db:
        existing_slugs = {r[0] for r in db.query(Template.slug).all()}
        for row in rows:
            if row["id"] in existing_slugs:
                continue
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
                name=row.get("name", ""),
                description=row.get("description", ""),
                category=row.get("category", "Imported"),
                icon=row.get("icon", "file"),
                is_builtin=False,
                owner_id="7519c7ce-65e1-4906-9c57-6a72a5f19d8f",
                structure=row.get("structure") or {"type": "doc", "content": []},
                fields=fields,
                created_at=datetime.fromisoformat(
                    row.get("created_at", "").replace("Z", "+00:00")
                )
                if row.get("created_at")
                else None,
            )
            db.add(template)
        db.commit()
    yield


def _client() -> tuple[TestClient, dict[str, str]]:
    """Return a TestClient and its CSRF/session cookies.

    Mirrors the existing conftest helper (register with CSRF, login with
    CSRF, then keep the session cookies for subsequent requests).
    """
    from app.main import app

    client = TestClient(app)
    csrf = client.get("/api/auth/csrf").json()["csrfToken"]

    # Register a dedicated user.
    client.post(
        "/api/auth/register",
        json={"email": "import@example.com", "password": "correct-horse-battery", "name": "Imported"},
        headers={"X-CSRF-Token": csrf},
    )

    # Login to establish a session. The CSRF middleware requires the cookie to
    # match the header, so pull the fresh CSRF token from the response.
    response = client.post(
        "/api/auth/login",
        json={"email": "import@example.com", "password": "correct-horse-battery"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200, response.text

    # Read the session + CSRF cookies set by login.
    cookies = {k: v for k, v in client.cookies.items()}
    return client, cookies


@pytest.fixture()
def template_client():
    return _client()


def test_conftest_seeds_builtins():
    with SessionLocal() as db:
        count = db.query(Template).filter(Template.is_builtin.is_(True)).count()
    assert count >= 5


def test_imported_templates_are_visible_and_hd():
    """All 23 CSV templates land in the DB and are returned by /api/templates."""
    client, cookies = _client()
    response = client.get(
        "/api/templates",
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    )
    assert response.status_code == 200, response.text
    templates = response.json()

    ids = {t["id"] for t in templates}
    with open(IMPORT_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    imported_ids = {r["id"] for r in rows}
    assert imported_ids.issubset(ids), "some imported templates are missing"

    with SessionLocal() as db:
        db_count = db.query(Template).filter(Template.is_builtin.is_(False)).count()
    assert db_count == 23, db_count

    # Spot-check that the fields are camelCase (schema keys -> field keys).
    poor = next(t for t in templates if t["name"] == "Poor Performance Letter")
    keys = [f["key"] for f in poor["fields"]]
    assert "employeeName" in keys
    assert "employeeAddress" in keys
    assert "companyName" in keys
    assert "durationOfObservation" in keys
    assert "specificInstancesOfPoorPerformance" in keys
    assert all(isinstance(f["required"], bool) for f in poor["fields"])

    # Confirm the structure parses as a document (no empty text nodes).
    from app.services.content import parse_content

    for t in templates:
        parse_content({"type": "doc", "content": t["structure"]["content"]})


def test_template_fields_are_served_as_expected():
    """Each imported template's fields carry label/kind/required/placeholder."""
    client, cookies = _client()
    response = client.get(
        "/api/templates",
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    )
    templates = response.json()

    by_slug = {t["slug"]: t for t in templates}
    assert "poor-performance-letter" in by_slug
    fields = by_slug["poor-performance-letter"]["fields"]
    assert len(fields) == 9
    assert fields[0]["key"] == "employeeName"
    assert fields[0]["label"] == "Employee's Name"
    assert fields[0]["kind"] == "string"
    assert fields[0]["required"] is True


def test_template_preview_fills_values():
    """Preview fills {{key}} with supplied values, no leftover placeholders."""
    client, cookies = _client()
    response = client.get(
        "/api/templates",
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    )
    templates = response.json()

    meeting = next(t for t in templates if t["slug"] == "meeting-notes")
    preview = client.post(
        f"/api/templates/{meeting['id']}/preview",
        json={"topic": "Roadmap sync", "date": "24 October 2026"},
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    ).json()

    assert "Roadmap sync" in str(preview["content"])
    assert "{{topic}}" not in str(preview["content"])
    assert "{{date}}" not in str(preview["content"])


def test_imported_template_create_document_fills_placeholders():
    """A document created from an imported template fills placeholders."""
    client, cookies = _client()
    response = client.get(
        "/api/templates",
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    )
    templates = response.json()

    poor = next(t for t in templates if t["name"] == "Poor Performance Letter")

    doc = client.post(
        "/api/documents",
        json={
            "templateId": poor["id"],
            "source": {
                "employeeName": "Ada",
                "employeeAddress": "1 Main St",
                "employeePosition": "Engineer",
                "companyName": "Acme",
                "specificInstancesOfPoorPerformance": "Missed deadlines",
                "durationOfObservation": "60 days",
                "yourName": "Ada",
                "yourPosition": "Engineer",
            },
        },
        headers={"X-CSRF-Token": cookies["csrfToken"]},
    )
    assert doc.status_code == 201, doc.text
    document = doc.json()
    text = str(document["content"])
    assert "Ada" in text
    assert "Acme" in text
    assert "{{" not in text, "placeholders must be filled before saving"
