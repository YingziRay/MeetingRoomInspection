from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InspectionResult(Base):
    __tablename__ = "inspection_result"
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "indicator_id",
            name="uq_inspection_result_task_indicator",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("inspection_task.id"), index=True)
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("inspection_indicator.id"), index=True
    )
    ai_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    human_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    human_remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
