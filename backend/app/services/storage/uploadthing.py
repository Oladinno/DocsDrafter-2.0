"""UploadThing storage adapter (documented REST API, no SDK required).

Flow, per https://docs.uploadthing.com/uploading-files:

1. ``POST https://api.uploadthing.com/v7/prepareUpload`` with the API key header
   returns a presigned ingest URL.
2. ``PUT`` the raw bytes to that URL.
3. Store the returned file key/URL in PostgreSQL.

Private files are read through a short-lived HMAC-signed URL generated locally
(the same construction used by ``UTApi.generateSignedURL``): sign the URL with
the API key before appending ``signature``.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx

from app.services.storage import StoredFile

API_BASE = "https://api.uploadthing.com"


class UploadThingError(RuntimeError):
    pass


class UploadThingStorage:
    name = "uploadthing"

    def __init__(self, *, api_key: str, app_id: str, acl: str = "private") -> None:
        self.api_key = api_key
        self.app_id = app_id
        self.acl = acl

    def _headers(self) -> dict[str, str]:
        return {
            "x-uploadthing-api-key": self.api_key,
            "x-uploadthing-fe-package": "docsdrafter-backend",
            "Content-Type": "application/json",
        }

    def upload(self, data: bytes, *, filename: str, content_type: str) -> StoredFile:
        with httpx.Client(timeout=60.0) as client:
            prepare = client.post(
                f"{API_BASE}/v7/prepareUpload",
                headers=self._headers(),
                json={
                    "fileName": filename,
                    "fileSize": len(data),
                    "fileType": content_type,
                    "acl": self.acl,
                },
            )
            if prepare.status_code >= 400:
                raise UploadThingError(
                    f"prepareUpload failed ({prepare.status_code}): {prepare.text[:300]}"
                )
            payload = prepare.json()
            upload_url = payload.get("url")
            if not upload_url:
                raise UploadThingError(f"prepareUpload returned no url: {payload}")

            # Ingest endpoint accepts multipart/form-data for the binary payload.
            put = client.put(
                upload_url,
                files={"file": (filename, data, content_type)},
            )
            if put.status_code >= 400:
                raise UploadThingError(
                    f"upload failed ({put.status_code}): {put.text[:300]}"
                )

        key = str(payload.get("key") or payload.get("fileKey") or "")
        url = str(payload.get("url2") or payload.get("fileUrl") or payload.get("url") or "")
        # The presigned ingest URL is not the delivery URL; prefer an explicit one.
        if url.startswith("https://") and "ingest" in url:
            url = f"https://{self.app_id}.ufs.sh/f/{key}" if key else None
        if key and not url:
            url = f"https://{self.app_id}.ufs.sh/f/{key}"
        return StoredFile(
            key=key or url or filename,
            url=url or None,
            size=len(data),
            content_type=content_type,
        )

    def signed_url(self, key: str, *, expires_in: int = 3600) -> str | None:
        # generateSignedURL signs locally, capped at 7 days.
        expires_in = min(max(expires_in, 1), 604_800)
        expires_ms = int(time.time() * 1000) + expires_in * 1000
        base = f"https://{self.app_id}.ufs.sh/f/{key}?{urlencode({'expires': expires_ms})}"
        digest = hmac.new(self.api_key.encode(), base.encode(), hashlib.sha256).hexdigest()
        return f"{base}&signature=hmac-sha256%3D{digest}"

    def delete(self, key: str) -> None:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE}/v6/deleteFiles",
                headers=self._headers(),
                json={"fileKeys": [key]},
            )
            if response.status_code >= 400:
                raise UploadThingError(
                    f"deleteFiles failed ({response.status_code}): {response.text[:300]}"
                )
