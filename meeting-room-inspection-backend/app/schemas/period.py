from __future__ import annotations

from datetime import time
from typing import Optional
from pydantic import BaseModel, Field


class PeriodConfigOut(BaseModel):
    id: int
    period_code: str
    period_name: str
    start_time: time
    deadline_time: time
    enabled: bool
    reminder_enabled: bool
    reminder_minutes: int
    sort_order: int

    class Config:
        from_attributes = True


class PeriodConfigUpdate(BaseModel):
    period_name: Optional[str] = Field(None, max_length=50, description="时段名称")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}(:\d{2})?$", description="巡检启动与提醒时间 HH:MM")
    deadline_time: str = Field(..., pattern=r"^\d{2}:\d{2}(:\d{2})?$", description="巡检截止时间 HH:MM")
    enabled: bool = Field(True, description="是否启用该巡检时段")
    reminder_enabled: bool = Field(True, description="是否开启钉钉群提醒推送")
