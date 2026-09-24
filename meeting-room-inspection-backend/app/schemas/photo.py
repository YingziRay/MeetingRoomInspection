from datetime import datetime
from pydantic import Field
from app.schemas.common import APIModel


class PhotoUploadResponse(APIModel):
    photo_id: int
    task_id: int
    photo_type: str
    photo_url: str
    quality_passed: bool
    quality_status: str
    quality_reason: str | None = None
    width: int
    height: int
    blur_score: float | None = None
    brightness: float | None = None


class PhotoDetailResponse(APIModel):
    id: int
    task_id: int
    photo_type: str
    photo_url: str
    original_filename: str | None = None
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    quality_status: str | None = None
    quality_reason: str | None = None
    created_at: datetime
