"""Document CRUD, versions and template tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def _create(client: TestClient, title: str = "Roadmap", **extra) -> dict:
    response = client.post(
        "/api/documents",
        json={"title": title, **extra},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _count_empty_text(node) -> int:
    """Count ProseMirror-invalid empty text nodes anywhere in a payload."""
    hits = 0
    if isinstance(node, dict):
        if node.get("type") == "text" and not node.get("text"):
            hits += 1
        for value in node.values():
            hits += _count_empty_text(value)
    elif isinstance(node, list):
        for item in node:
            hits += _count_empty_text(item)
    return hits




def test_create_blank_document(client: TestClient) -> None:
    register(client)
    document = _create(client, "Blank one")
    assert document["title"] == "Blank one"
    assert document["status"] == "draft"
    assert document["versionCount"] == 1
    assert document["content"]["type"] == "doc"


def test_create_from_template_fills_placeholders(client: TestClient) -> None:
    register(client)
    templates = client.get("/api/templates").json()
    proposal = next(t for t in templates if t["slug"] == "project-proposal")
    assert proposal["fields"], "template should expose structured fields"

    response = client.post(
        "/api/documents",
        json={
            "templateId": proposal["id"],
            "source": {"projectName": "Atlas", "client": "Platform", "author": "Ada"},
        },
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["title"] == "Atlas"
    text = str(document["content"])
    assert "Atlas" in text
    assert "{{" not in text, "placeholders must be filled before saving"


def test_search_matches_title_and_body(client: TestClient) -> None:
    register(client)
    _create(client, "Quarterly plan")
    other = _create(client, "Notes")
    client.patch(
        f"/api/documents/{other['id']}",
        json={
            "content": {
                "type": "doc",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "mentions penguins"}]}
                ],
            }
        },
        headers=csrf_headers(client),
    )

    by_title = client.get("/api/documents", params={"q": "quarterly"}).json()
    assert [d["title"] for d in by_title["items"]] == ["Quarterly plan"]

    by_body = client.get("/api/documents", params={"q": "penguins"}).json()
    assert [d["title"] for d in by_body["items"]] == ["Notes"]


def test_update_creates_version_history_and_restore(client: TestClient) -> None:
    register(client)
    document = _create(client, "History")

    first = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "first draft"}]}],
    }
    updated = client.patch(
        f"/api/documents/{document['id']}",
        json={"content": first, "status": "in_review"},
        headers=csrf_headers(client),
    ).json()
    assert updated["status"] == "in_review"
    assert updated["wordCount"] == 2

    second = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "second draft"}]}],
    }
    client.patch(
        f"/api/documents/{document['id']}",
        json={"content": second},
        headers=csrf_headers(client),
    )

    versions = client.get(f"/api/documents/{document['id']}/versions").json()
    numbers = [v["versionNumber"] for v in versions]
    assert numbers == sorted(numbers, reverse=True)

    # Restore the state that contained "first draft".
    target = next(v for v in versions if v["versionNumber"] == 2)
    restored = client.post(
        f"/api/documents/{document['id']}/versions/{target['id']}/restore",
        json={},
        headers=csrf_headers(client),
    ).json()
    assert "first draft" in str(restored["content"])
    # The current state was already the newest version, so restoring adds none.
    assert restored["versionCount"] == 3


def test_manual_version_needs_a_note_and_skips_duplicates(client: TestClient) -> None:
    register(client)
    document = _create(client, "Snapshot")
    first = client.post(
        f"/api/documents/{document['id']}/versions",
        json={"note": "before rewrite"},
        headers=csrf_headers(client),
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/documents/{document['id']}/versions",
        json={"note": "no change"},
        headers=csrf_headers(client),
    )
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"], "identical state is not duplicated"


def test_invalid_content_is_rejected(client: TestClient) -> None:
    register(client)
    document = _create(client, "Invalid")
    response = client.patch(
        f"/api/documents/{document['id']}",
        json={"content": {"type": "doc", "content": [{"type": "alien"}]}},
        headers=csrf_headers(client),
    )
    assert response.status_code == 422
    assert "invalid document content" in response.json()["detail"]


def test_documents_are_isolated_between_accounts(client: TestClient) -> None:
    register(client, email="owner@example.com")
    document = _create(client, "Private")
    client.post("/api/auth/logout", headers=csrf_headers(client))

    register(client, email="intruder@example.com")
    assert client.get(f"/api/documents/{document['id']}").status_code == 404
    assert client.get("/api/documents").json()["total"] == 0
    response = client.patch(
        f"/api/documents/{document['id']}",
        json={"title": "hijacked"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 404


def test_delete_document(client: TestClient) -> None:
    register(client)
    document = _create(client, "Temporary")
    deleted = client.delete(
        f"/api/documents/{document['id']}", headers=csrf_headers(client)
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/documents/{document['id']}").status_code == 404


def test_template_preview_fills_values(client: TestClient) -> None:
    register(client)
    templates = client.get("/api/templates").json()
    meeting = next(t for t in templates if t["slug"] == "meeting-notes")
    preview = client.post(
        f"/api/templates/{meeting['id']}/preview",
        json={"topic": "Roadmap sync"},
        headers=csrf_headers(client),
    ).json()
    assert "Roadmap sync" in str(preview["content"])
    assert "{{topic}}" not in str(preview["content"])


def test_write_path_never_stores_empty_text_nodes(client: TestClient) -> None:
    register(client)
    document = _create(client, "Sanitize")
    bad = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": ""}, {"type": "text", "text": "ok"}],
            }
        ],
    }
    patched = client.patch(
        f"/api/documents/{document['id']}",
        json={"content": bad},
        headers=csrf_headers(client),
    )
    assert patched.status_code == 200, patched.text
    fetched = client.get(f"/api/documents/{document['id']}").json()
    assert _count_empty_text(fetched["content"]) == 0
    assert fetched["content"]["content"][0]["content"] == [{"type": "text", "text": "ok", "marks": []}]


def test_legacy_row_with_empty_text_is_sanitised_on_read(client: TestClient) -> None:
    """Rows written before the sanitizer fix must still open in the editor."""
    from app.db import SessionLocal
    from app.models import Document

    register(client)
    document = _create(client, "Legacy row")
    with SessionLocal() as db:
        row = db.get(Document, document["id"])
        assert row is not None
        row.content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}],
        }
        db.commit()

    fetched = client.get(f"/api/documents/{document['id']}").json()
    assert _count_empty_text(fetched["content"]) == 0
    assert fetched["content"]["content"][0]["content"] == []

