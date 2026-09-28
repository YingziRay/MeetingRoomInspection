from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.common import APIModel, PageResponse


class AbnormalItemSummary(APIModel):
    indicator_code: str
    indicator_name: str
    category: str | None = None
    reason: str | None = None
    status: str = "ABNORMAL"


class TaskSummaryItem(APIModel):
    id: int
    task_no: str
    room_id: int
    room_name: str
    room_code: str
    building: str | None = None
    floor: str | None = None
    inspection_date: date
    period: str
    status: str
    inspector_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_indicators: int = 0
    normal_count: int = 0
    abnormal_count: int = 0
    uncertain_count: int = 0
    abnormal_summary: list[AbnormalItemSummary] = []
    front_photo_url: str | None = None
    rear_photo_url: str | None = None
    ac_panel_photo_url: str | None = None


class IndicatorStatItem(APIModel):
    indicator_id: int
    indicator_code: str
    indicator_name: str
    category: str | None = None
    count: int
    percent: float


class RoomStatItem(APIModel):
    room_id: int
    room_name: str
    room_code: str
    building: str | None = None
    floor: str | None = None
    total_tasks: int
    completed_tasks: int
    abnormal_tasks: int
    pass_rate: float


class DailyTrendItem(APIModel):
    date: str
    total: int
    completed: int
    abnormal: int


class DashboardStatsResponse(APIModel):
    start_date: str
    end_date: str
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    normal_tasks: int
    abnormal_tasks: int
    normal_rate: float
    total_abnormal_items: int
    top_abnormal_indicators: list[IndicatorStatItem]
    room_stats: list[RoomStatItem]
    daily_trends: list[DailyTrendItem]
