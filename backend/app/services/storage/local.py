"""Local disk storage adapter (development and tests)."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.services.storage import StoredFile

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class LocalStorage:
    name = "local"

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.base_dir / key

    def upload(self, data: bytes, *, filename: str, content_type: str) -> StoredFile:
        safe = _SAFE.sub("-", filename).strip("-") or "file"
        key = f"{uuid.uuid4().hex[:12]}-{safe}"
        path = self._path(key)
        path.write_bytes(data)
        return StoredFile(key=key, url=None, size=len(data), content_type=content_type)

    def signed_url(self, key: str, *, expires_in: int = 3600) -> str | None:
        # Served by the API after an ownership check; no public URL exists.
        return None

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def read(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()
