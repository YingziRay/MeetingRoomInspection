from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InspectionPeriodConfig(Base):
    __tablename__ = "inspection_period_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    period_name: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[time] = mapped_column()
    deadline_time: Mapped[time] = mapped_column()
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=30)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
