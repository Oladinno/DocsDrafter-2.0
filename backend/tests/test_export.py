"""Export pipeline tests (DOCX, PDF, storage adapter, ownership)."""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.services.storage.uploadthing import UploadThingStorage
from tests.conftest import csrf_headers, register


def _document(client: TestClient, title: str = "Export me") -> dict:
    response = client.post(
        "/api/documents",
        json={
            "title": title,
            "content": {
                "type": "doc",
                "content": [
                    {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": title}]},
                    {"type": "paragraph", "content": [{"type": "text", "text": "A short body with "}, {"type": "text", "text": "emphasis", "marks": [{"type": "bold"}]}]},
                    {"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "First item"}]}]}]},
                ],
            },
        },
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _export(client: TestClient, document_id: str, fmt: str) -> dict:
    response = client.post(
        f"/api/documents/{document_id}/exports",
        json={"format": fmt},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_docx_export_produces_a_downloadable_file(client: TestClient) -> None:
    register(client)
    document = _document(client)
    export = _export(client, document["id"], "docx")

    assert export["status"] == "succeeded", export.get("error")
    assert export["fileName"].endswith(".docx")
    assert export["sizeBytes"] and export["sizeBytes"] > 5000
    assert export["versionNumber"], "exports snapshot a version"
    assert export["downloadUrl"]

    download = client.get(export["downloadUrl"])
    assert download.status_code == 200
    assert download.content[:2] == b"PK", "DOCX is a zip container"
    assert "Export me" in str(download.content) or len(download.content) > 5000


def test_export_records_the_version_it_rendered(client: TestClient) -> None:
    register(client)
    document = _document(client)
    before = client.get(f"/api/documents/{document['id']}/versions").json()
    export = _export(client, document["id"], "docx")
    after = client.get(f"/api/documents/{document['id']}/versions").json()
    assert export["versionNumber"] == before[0]["versionNumber"]
    assert len(after) == len(before), "identical content is not duplicated"


def test_pdf_export_renders_with_playwright(client: TestClient) -> None:
    register(client)
    document = _document(client, "PDF sample")
    export = _export(client, document["id"], "pdf")
    assert export["status"] == "succeeded", export.get("error")
    assert export["renderer"] == "playwright"
    assert export["fileName"].endswith(".pdf")

    download = client.get(export["downloadUrl"])
    assert download.status_code == 200
    assert download.content[:5] == b"%PDF-", download.content[:20]
    assert len(download.content) > 2000


def test_exports_are_isolated_between_accounts(client: TestClient) -> None:
    register(client, email="owner@example.com")
    document = _document(client)
    export = _export(client, document["id"], "docx")
    client.post("/api/auth/logout", headers=csrf_headers(client))

    register(client, email="other@example.com")
    assert client.get(f"/api/exports/{export['id']}").status_code == 404
    assert client.get(export["downloadUrl"]).status_code == 404
    listed = client.get(f"/api/documents/{document['id']}/exports")
    assert listed.status_code == 404


def test_delete_export_removes_file_and_row(client: TestClient) -> None:
    register(client)
    document = _document(client)
    export = _export(client, document["id"], "docx")
    deleted = client.delete(f"/api/exports/{export['id']}", headers=csrf_headers(client))
    assert deleted.status_code == 204
    assert client.get(f"/api/exports/{export['id']}").status_code == 404


def test_uploadthing_signed_url_matches_documented_hmac() -> None:
    storage = UploadThingStorage(api_key="sk_test", app_id="apptest", acl="private")
    url = storage.signed_url("abc123", expires_in=3600)
    assert url is not None

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    expires = int(query["expires"][0])
    assert expires > 0

    base = f"https://apptest.ufs.sh/f/abc123?expires={expires}"
    expected = hmac.new(b"sk_test", base.encode(), hashlib.sha256).hexdigest()
    assert query["signature"][0] == f"hmac-sha256={expected}"
