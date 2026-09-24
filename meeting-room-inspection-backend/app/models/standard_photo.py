from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StandardPhoto(Base):
    __tablename__ = "standard_photo"
    __table_args__ = (
        UniqueConstraint("room_id", "photo_type", "version", name="uq_standard_photo_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("meeting_room.id"), index=True)
    photo_type: Mapped[str] = mapped_column(String(20))
    photo_url: Mapped[str] = mapped_column(String(500))
    photo_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    shoot_position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    camera_direction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
