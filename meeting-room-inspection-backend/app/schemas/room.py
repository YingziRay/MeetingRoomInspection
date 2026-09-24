from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel, PageResponse


class MeetingRoomBase(APIModel):
    room_code: str = Field(min_length=1, max_length=50)
    room_name: str = Field(min_length=1, max_length=100)
    building: str | None = None
    floor: str | None = None
    location_desc: str | None = None
    status: str = "ACTIVE"
    inspection_enabled: bool = True


class MeetingRoomCreate(MeetingRoomBase):
    pass


class MeetingRoomUpdate(APIModel):
    room_name: str | None = None
    building: str | None = None
    floor: str | None = None
    location_desc: str | None = None
    status: str | None = None
    inspection_enabled: bool | None = None


class MeetingRoomResponse(MeetingRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime


class MeetingRoomPage(PageResponse[MeetingRoomResponse]):
    pass
