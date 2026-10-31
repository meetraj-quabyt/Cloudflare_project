import os
from pathlib import Path

from app.storage.base import StorageBase

BASE_DIR = Path(__file__).parent.parent.parent.parent / "uploads"


class LocalStorage(StorageBase):
    def __init__(self):
        self.base = BASE_DIR
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # prevent directory traversal
        safe = os.path.basename(key)
        return self.base / safe

    def is_local(self) -> bool:
        return True

    def presign_upload(self, key: str, session_id: str, expires: int) -> str:
        return f"/api/v1/uploads/{session_id}/local"

    def presign_download(self, key: str, file_id: str, expires: int) -> str:
        return f"/api/v1/files/{file_id}/download"

    async def head_object(self, key: str) -> dict | None:
        path = self._path(key)
        if not path.exists():
            return None
        return {
            "size": path.stat().st_size,
            "content_type": None,
            "etag": None,
        }

    async def delete_object(self, key: str) -> bool:
        path = self._path(key)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def store_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()