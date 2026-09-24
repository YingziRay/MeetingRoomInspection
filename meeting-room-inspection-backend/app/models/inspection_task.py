from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InspectionTask(Base):
    __tablename__ = "inspection_task"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "inspection_date",
            "period",
            name="uq_inspection_task_room_date_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("meeting_room.id"), index=True)
    inspection_date: Mapped[date] = mapped_column(Date, index=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    inspector_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
