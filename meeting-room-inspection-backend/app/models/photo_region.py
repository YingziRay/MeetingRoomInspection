from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PhotoRegion(Base):
    __tablename__ = "photo_region"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    standard_photo_id: Mapped[int] = mapped_column(
        ForeignKey("standard_photo.id"), index=True
    )
    region_code: Mapped[str] = mapped_column(String(50))
    region_name: Mapped[str] = mapped_column(String(100))
    x: Mapped[float] = mapped_column(Numeric(8, 6))
    y: Mapped[float] = mapped_column(Numeric(8, 6))
    width: Mapped[float] = mapped_column(Numeric(8, 6))
    height: Mapped[float] = mapped_column(Numeric(8, 6))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
