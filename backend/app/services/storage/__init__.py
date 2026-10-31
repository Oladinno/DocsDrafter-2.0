"""Storage boundary.

Only this package knows about provider-specific upload/delete/signed-URL APIs;
document, job and route code depend on the :class:`StorageAdapter` protocol
alone. Production uses UploadThing's documented REST API (no official Python
SDK exists); ``local`` keeps files on disk for development and tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class StoredFile:
    key: str
    url: str | None
    size: int
    content_type: str


class StorageAdapter(Protocol):
    name: str

    def upload(self, data: bytes, *, filename: str, content_type: str) -> StoredFile: ...

    def signed_url(self, key: str, *, expires_in: int = 3600) -> str | None: ...

    def delete(self, key: str) -> None: ...


def get_storage():
    from app.config import settings

    if settings.uses_uploadthing:
        from app.services.storage.uploadthing import UploadThingStorage

        return UploadThingStorage(
            api_key=settings.uploadthing_api_key or "",
            app_id=settings.uploadthing_app_id or "",
            acl=settings.uploadthing_acl,
        )

    from app.services.storage.local import LocalStorage

    return LocalStorage(base_dir=settings.local_storage_dir)
