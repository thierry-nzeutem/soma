"""Storage service — abstract file storage (local + S3-compatible)."""
from app.storage.storage_service import StorageService, LocalStorageService, get_storage_service

__all__ = ["StorageService", "LocalStorageService", "get_storage_service"]
