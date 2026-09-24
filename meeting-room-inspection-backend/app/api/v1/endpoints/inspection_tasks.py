from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_photo import InspectionPhoto
from app.models.inspection_result import InspectionResult
from app.models.inspection_task import InspectionTask
from app.models.meeting_room import MeetingRoom
from app.schemas.result import ResultResponse
from app.schemas.task import (
    TaskGenerateRequest,
    TaskResponse,
    TaskStartResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
)
from app.services.ai_service import get_ai_service
from app.services.notification_service import get_notification_service

router = APIRouter()




@router.post("/generate", response_model=list[TaskResponse])
def generate_tasks(
    payload: TaskGenerateRequest,
    db: Session = Depends(get_db),
):
    rooms = db.scalars(
        select(MeetingRoom).where(
            MeetingRoom.status == "ACTIVE",
            MeetingRoom.inspection_enabled.is_(True),
        )
    ).all()

    created: list[InspectionTask] = []

    for room in rooms:
        existing = db.scalar(
            select(InspectionTask).where(
                InspectionTask.room_id == room.id,
                InspectionTask.inspection_date == payload.inspection_date,
                InspectionTask.period == payload.period,
            )
        )
        if existing:
            created.append(existing)
            continue

        task_no = (
            f"IR-{payload.inspection_date.strftime('%Y%m%d')}-"
            f"{room.id}-{payload.period}"
        )
        task = InspectionTask(
            task_no=task_no,
            room_id=room.id,
            inspection_date=payload.inspection_date,
            period=payload.period,
            status="PENDING",
        )
        db.add(task)
        created.append(task)

    db.commit()
    for task in created:
        db.refresh(task)

    return created


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    return task


@router.post("/{task_id}/start", response_model=TaskStartResponse)
def start_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")

    if task.status != "PENDING":
        raise HTTPException(status_code=409, detail="TASK_ALREADY_STARTED_OR_COMPLETED")

    now = datetime.now(timezone.utc)
    task.status = "IN_PROGRESS"
    task.started_at = now
    db.commit()
    db.refresh(task)

    return TaskStartResponse(
        task_id=task.id,
        status=task.status,
        started_at=task.started_at,
    )


@router.post("/{task_id}/submit", response_model=TaskSubmitResponse)
def submit_task(
    task_id: int,
    payload: TaskSubmitRequest,
    db: Session = Depends(get_db),
):
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")

    if task.status != "WAITING_CONFIRM":
        raise HTTPException(
            status_code=409,
            detail=f"SUBMIT_NOT_ALLOWED: Task current status is '{task.status}', must be 'WAITING_CONFIRM'",
        )

    # 1. Require both FRONT and REAR photos uploaded
    photos = db.scalars(
        select(InspectionPhoto).where(InspectionPhoto.task_id == task_id)
    ).all()
    uploaded_types = {p.photo_type for p in photos}
    if not {"FRONT", "REAR"}.issubset(uploaded_types):
        missing = {"FRONT", "REAR"} - uploaded_types
        raise HTTPException(
            status_code=400,
            detail=f"INCOMPLETE_PHOTOS: Missing perspectives {list(missing)}. Both FRONT and REAR are required.",
        )

    # 2. Check all indicator results
    results = db.scalars(
        select(InspectionResult).where(InspectionResult.task_id == task_id)
    ).all()
    if not results:
        raise HTTPException(
            status_code=400,
            detail="NO_INSPECTION_RESULTS: Please run AI analysis before submitting.",
        )

    now = datetime.now(timezone.utc)

    # If confirm_all or force_confirm_uncertain is True, auto-resolve remaining UNCERTAIN
    for r in results:
        if payload.confirm_all and (not r.final_status or r.final_status == "UNCERTAIN"):
            r.human_status = "NORMAL" if r.ai_status in ("NORMAL", "UNCERTAIN") else r.ai_status
            r.final_status = r.human_status
            r.confirmed_by = payload.inspector_id or "inspector"
            r.confirmed_at = now
        elif payload.force_confirm_uncertain and r.final_status == "UNCERTAIN":
            r.human_status = "NORMAL"
            r.human_remark = r.human_remark or "巡检员现场复核兜底确认正常"
            r.final_status = "NORMAL"
            r.confirmed_by = payload.inspector_id or "inspector"
            r.confirmed_at = now

    # Check for any lingering unresolved UNCERTAIN
    unresolved_uncertain = [r for r in results if r.final_status == "UNCERTAIN"]
    if unresolved_uncertain:
        raise HTTPException(
            status_code=400,
            detail=f"UNRESOLVED_INDICATORS: {len(unresolved_uncertain)} indicator(s) are UNCERTAIN. Please review or enable force_confirm_uncertain.",
        )

    # 3. Calculate metrics
    normal_count = sum(1 for r in results if r.final_status == "NORMAL")
    abnormal_count = sum(1 for r in results if r.final_status == "ABNORMAL")
    uncertain_count = sum(1 for r in results if r.final_status == "UNCERTAIN")

    # 4. Finalize Task
    task.status = "COMPLETED"
    task.inspector_id = payload.inspector_id or "inspector"
    task.completed_at = now

    db.commit()
    db.refresh(task)

    # 5. Push alert if abnormal indicators exist
    if abnormal_count > 0:
        room = db.get(MeetingRoom, task.room_id)
        room_name = room.room_name if room else f"会议室 #{task.room_id}"
        abnormal_list = []
        for r in results:
            if r.final_status == "ABNORMAL":
                ind = db.get(InspectionIndicator, r.indicator_id)
                ind_name = ind.indicator_name if ind else f"指标 #{r.indicator_id}"
                reason = r.human_remark or r.ai_reason or "存在异常"
                abnormal_list.append({"name": ind_name, "reason": reason})

        notifier = get_notification_service()
        notifier.notify_abnormal_alert(
            room_name=room_name,
            task_no=task.task_no,
            abnormal_items=abnormal_list,
        )

    msg = "巡检全部正常，完成归档" if abnormal_count == 0 else f"巡检已提交，发现 {abnormal_count} 项异常已发送群告警并归档"

    return TaskSubmitResponse(
        task_id=task.id,
        status=task.status,
        completed_at=task.completed_at,
        normal=normal_count,
        abnormal=abnormal_count,
        uncertain=uncertain_count,
        message=msg,
    )




@router.post("/{task_id}/analyze", response_model=list[ResultResponse])
def analyze_task_inspection(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger VLM AI analysis for all uploaded inspection photos in this task.
    Idempotently populates or updates inspection_result and advances task status to WAITING_CONFIRM.
    """
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")

    ai_service = get_ai_service()
    try:
        results = ai_service.run_task_inspection(db, task_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}",
        )

