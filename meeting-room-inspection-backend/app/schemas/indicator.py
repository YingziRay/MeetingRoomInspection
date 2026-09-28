from datetime import datetime
from pydantic import Field
from app.schemas.common import APIModel


class IndicatorCreate(APIModel):
    indicator_name: str = Field(..., min_length=1, max_length=100)
    indicator_code: str | None = Field(default=None, max_length=50)
    category: str = Field(default="ENVIRONMENT", max_length=50)
    photo_perspective: str = Field(default="FRONT", max_length=20)
    description: str | None = None
    normal_condition: str | None = None
    abnormal_condition: str | None = None
    ai_supported: bool = True
    sort_order: int = 0


class IndicatorUpdate(APIModel):
    indicator_name: str | None = None
    category: str | None = None
    photo_perspective: str | None = None
    description: str | None = None
    normal_condition: str | None = None
    abnormal_condition: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class IndicatorResponse(APIModel):
    id: int
    indicator_code: str
    indicator_name: str
    category: str | None = None
    photo_perspective: str = "FRONT"
    is_custom: bool = False
    description: str | None = None
    normal_condition: str | None = None
    abnormal_condition: str | None = None
    ai_supported: bool = True
    enabled: bool = True
    sort_order: int = 0


class RoomIndicatorItem(APIModel):
    id: int
    room_id: int
    indicator_id: int
    indicator_code: str
    indicator_name: str
    category: str | None = None
    photo_perspective: str = "FRONT"
    is_custom: bool = False
    enabled: bool = True
    sort_order: int = 0


class RoomIndicatorBatchRequest(APIModel):
    indicator_ids: list[int] = Field(..., description="List of indicator IDs enabled for this room")


class StandardPhotoResponse(APIModel):
    id: int
    room_id: int
    photo_type: str
    photo_url: str
    shoot_position: str | None = None
    camera_direction: str | None = None
    version: int = 1
    status: str = "ACTIVE"
    created_at: datetime
