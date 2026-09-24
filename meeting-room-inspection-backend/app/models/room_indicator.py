from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RoomIndicator(Base):
    __tablename__ = "room_indicator"
    __table_args__ = (
        UniqueConstraint("room_id", "indicator_id", name="uq_room_indicator"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("meeting_room.id"), index=True)
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("inspection_indicator.id"), index=True
    )
    standard_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_id: Mapped[int | None] = mapped_column(
        ForeignKey("photo_region.id"), nullable=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
