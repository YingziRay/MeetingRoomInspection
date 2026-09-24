from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class ResultResponse(APIModel):
    id: int
    task_id: int
    indicator_id: int
    ai_status: str | None
    ai_confidence: float | None
    ai_reason: str | None
    ai_bbox: dict | None
    human_status: str | None
    human_remark: str | None
    final_status: str | None
    confirmed_by: str | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ResultConfirmRequest(APIModel):
    human_status: str = Field(min_length=1, max_length=30)
    human_remark: str | None = None


class ResultConfirmResponse(ResultResponse):
    pass


class BatchConfirmItem(APIModel):
    result_id: int
    human_status: str = Field(..., description="NORMAL | ABNORMAL | UNCERTAIN")
    human_remark: str | None = None


class BatchConfirmRequest(APIModel):
    task_id: int
    confirm_all_as_ai: bool = False
    items: list[BatchConfirmItem] = Field(default_factory=list)

