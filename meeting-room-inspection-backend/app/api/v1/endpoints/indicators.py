from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_indicator import InspectionIndicator
from app.schemas.indicator import IndicatorResponse

router = APIRouter()


@router.get("", response_model=list[IndicatorResponse])
def list_indicators(
    category: str | None = None,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
):
    stmt = select(InspectionIndicator)
    if enabled_only:
        stmt = stmt.where(InspectionIndicator.enabled.is_(True))
    if category:
        stmt = stmt.where(InspectionIndicator.category == category)

    indicators = db.scalars(stmt.order_by(InspectionIndicator.sort_order)).all()
    return indicators
