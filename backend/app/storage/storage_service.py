"""
Abstract storage service for SOMA media files.

Design:
- Abstract interface (StorageService) compatible with local FS, S3, Cloudflare R2, MinIO.
- LocalStorageService: default implementation using the local filesystem.
- S3StorageService: stub for LOT 12 (boto3 / aiobotocore).
- The DB never stores raw bytes — only: url, key, content_type, size_bytes, owner_id, created_at.
- Files are uploaded via store_file() → returns StoredFile with permanent URL.
- Deletion via delete_file(key).

Usage:
    storage = get_storage_service()
    stored = await storage.store_file(
        file_bytes=data,
        filename="photo.jpg",
        content_type="image/jpeg",
        owner_id=user_id,
        folder="nutrition/photos",
    )
    # stored.url → "http://localhost:8000/media/nutrition/photos/uuid_photo.jpg"
"""
from __future__ import annotations

import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StoredFile:
    """Metadata of a stored file (what gets persisted in DB)."""
    key: str              # Unique storage key / object path
    url: str              # Public-facing URL
    filename: str         # Original filename
    content_type: str     # MIME type
    size_bytes: int
    owner_id: Optional[uuid.UUID] = None


class StorageService(ABC):
    """Abstract storage interface. Swap implementations without changing callers."""

    @abstractmethod
    async def store_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        owner_id: Optional[uuid.UUID] = None,
    ) -> StoredFile:
        """Upload file bytes, return StoredFile metadata."""

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete file by storage key. Returns True if deleted."""

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a (possibly pre-signed) URL for the given key."""

    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """Return True if the file exists in storage."""


class LocalStorageService(StorageService):
    """
    Local filesystem storage.
    Files are stored at {base_path}/{folder}/{uuid}_{filename}.
    URL: {base_url}/{folder}/{uuid}_{filename}
    """

    def __init__(self, base_path: str, base_url: str) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    async def store_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        owner_id: Optional[uuid.UUID] = None,
    ) -> StoredFile:
        safe_name = Path(filename).name.replace(" ", "_")
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        key = f"{folder}/{unique_name}"
        dest = self._base_path / folder / unique_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file_bytes)
        logger.debug("LocalStorage: stored %d bytes → %s", len(file_bytes), key)
        return StoredFile(
            key=key,
            url=f"{self._base_url}/{key}",
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            owner_id=owner_id,
        )

    async def delete_file(self, key: str) -> bool:
        path = self._base_path / key
        if path.exists():
            path.unlink()
            logger.debug("LocalStorage: deleted %s", key)
            return True
        return False

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        # Local storage: URL is permanent, expiry ignored
        return f"{self._base_url}/{key}"

    async def file_exists(self, key: str) -> bool:
        return (self._base_path / key).exists()


class S3StorageService(StorageService):
    """
    S3-compatible storage stub (AWS S3, Cloudflare R2, MinIO).
    Full implementation planned for LOT 12.
    Requires: aiobotocore or boto3 (async wrapper).
    """

    def __init__(self, bucket: str, region: str, endpoint_url: Optional[str] = None) -> None:
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        logger.warning(
            "S3StorageService is a stub — implement LOT 12 with aiobotocore. "
            "Falling back to LocalStorageService behavior."
        )

    async def store_file(self, file_bytes, filename, content_type, folder="uploads", owner_id=None):
        raise NotImplementedError("S3StorageService.store_file not yet implemented (LOT 12)")

    async def delete_file(self, key: str) -> bool:
        raise NotImplementedError("S3StorageService.delete_file not yet implemented (LOT 12)")

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("S3StorageService.get_url not yet implemented (LOT 12)")

    async def file_exists(self, key: str) -> bool:
        raise NotImplementedError("S3StorageService.file_exists not yet implemented (LOT 12)")


# ── Singleton ────────────────────────────────────────────────────────────────

_storage_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Return the configured StorageService singleton."""
    global _storage_instance
    if _storage_instance is None:
        from app.core.config import settings
        _storage_instance = LocalStorageService(
            base_path=getattr(settings, "STORAGE_PATH", "media"),
            base_url=getattr(settings, "MEDIA_BASE_URL", "http://localhost:8000/media"),
        )
    return _storage_instance
