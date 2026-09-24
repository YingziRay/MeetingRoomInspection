from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_result import InspectionResult
from app.schemas.result import (
    BatchConfirmRequest,
    ResultConfirmRequest,
    ResultConfirmResponse,
    ResultResponse,
)

router = APIRouter()


@router.get("/by-task/{task_id}", response_model=list[ResultResponse])
def list_results(task_id: int, db: Session = Depends(get_db)):
    results = (
        db.query(InspectionResult)
        .filter(InspectionResult.task_id == task_id)
        .order_by(InspectionResult.id)
        .all()
    )
    return results


@router.patch("/{result_id}/confirm", response_model=ResultConfirmResponse)
def confirm_result(
    result_id: int,
    payload: ResultConfirmRequest,
    db: Session = Depends(get_db),
):
    result = db.get(InspectionResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="RESULT_NOT_FOUND")

    now = datetime.now(timezone.utc)
    result.human_status = payload.human_status
    result.human_remark = payload.human_remark
    result.final_status = payload.human_status
    result.confirmed_by = "inspector"
    result.confirmed_at = now

    db.commit()
    db.refresh(result)
    return result


@router.post("/batch-confirm", response_model=list[ResultResponse])
def batch_confirm_results(
    payload: BatchConfirmRequest,
    db: Session = Depends(get_db),
):
    results = db.scalars(
        select(InspectionResult).where(InspectionResult.task_id == payload.task_id)
    ).all()
    if not results:
        raise HTTPException(status_code=404, detail="NO_RESULTS_FOR_TASK")

    result_map = {r.id: r for r in results}
    now = datetime.now(timezone.utc)

    # 1. Update specific designated items
    for item in payload.items:
        r = result_map.get(item.result_id)
        if r:
            r.human_status = item.human_status
            r.human_remark = item.human_remark
            r.final_status = item.human_status
            r.confirmed_by = "inspector"
            r.confirmed_at = now

    # 2. If confirm_all_as_ai is True, confirm all remaining items
    if payload.confirm_all_as_ai:
        for r in results:
            if not r.confirmed_at or r.final_status == "UNCERTAIN":
                status_to_use = "NORMAL" if r.ai_status in ("NORMAL", "UNCERTAIN") else r.ai_status
                r.human_status = status_to_use
                r.human_remark = r.human_remark or "人工一键全部核对通过"
                r.final_status = status_to_use
                r.confirmed_by = "inspector"
                r.confirmed_at = now

    db.commit()
    for r in results:
        db.refresh(r)

    return results
