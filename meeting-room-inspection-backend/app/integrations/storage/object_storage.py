from abc import ABC, abstractmethod
from pathlib import Path
import uuid
from app.core.config import settings


class BaseStorageProvider(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, filename: str, subfolder: str = "inspections") -> str:
        """
        Saves file and returns the accessible URL or path.
        """
        raise NotImplementedError

    @abstractmethod
    def create_presigned_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_seconds: int = 600,
    ) -> str:
        raise NotImplementedError


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, upload_dir: str | None = None, base_url: str | None = None):
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str, subfolder: str = "inspections") -> str:
        target_dir = self.upload_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        # Ensure safe unique filename
        suffix = Path(filename).suffix or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        target_file = target_dir / unique_name

        with open(target_file, "wb") as f:
            f.write(file_bytes)

        # Return relative or absolute URL accessible via mounted static route
        return f"/uploads/{subfolder}/{unique_name}"

    def create_presigned_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_seconds: int = 600,
    ) -> str:
        # Local mock presigned URL pointing to local direct upload
        return f"{self.base_url}/api/v1/photos/upload"


class ObjectStorage(LocalStorageProvider):
    """
    Backward-compatible alias for existing imports.
    """
    pass


def get_storage_provider() -> BaseStorageProvider:
    if settings.storage_type == "local":
        return LocalStorageProvider()
    # S3/MinIO provider can be returned here when enabled
    return LocalStorageProvider()
