from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class TaskGenerateRequest(APIModel):
    inspection_date: date
    period: str = Field(min_length=1, max_length=20)


class TaskStartResponse(APIModel):
    task_id: int
    status: str
    started_at: datetime


class TaskResponse(APIModel):
    id: int
    task_no: str
    room_id: int
    inspection_date: date
    period: str
    inspector_id: str | None
    status: str
    due_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskSubmitRequest(APIModel):
    confirm_all: bool = False
    force_confirm_uncertain: bool = False
    inspector_id: str | None = "default_inspector"


class TaskSubmitResponse(APIModel):
    task_id: int
    status: str
    completed_at: datetime
    normal: int
    abnormal: int
    uncertain: int
    message: str | None = None

