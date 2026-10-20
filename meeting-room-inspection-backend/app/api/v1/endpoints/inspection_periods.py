from __future__ import annotations

from datetime import datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_period_config import InspectionPeriodConfig
from app.schemas.period import PeriodConfigOut, PeriodConfigUpdate
from app.workers.scheduler import generate_and_notify_period, reschedule_period_job

router = APIRouter()


def _parse_time_str(time_str: str) -> time:
    """Parse 'HH:MM' or 'HH:MM:SS' string into datetime.time object."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        return time(hour=int(parts[0]), minute=int(parts[1]))
    elif len(parts) == 3:
        return time(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]))
    raise ValueError(f"Invalid time format: {time_str}")


@router.get("", response_model=List[PeriodConfigOut], summary="获取所有巡检时段配置")
def get_inspection_periods(db: Session = Depends(get_db)):
    """获取巡检时段列表（上午/中午/晚间），按序号排序"""
    periods = db.scalars(
        select(InspectionPeriodConfig).order_by(InspectionPeriodConfig.sort_order)
    ).all()
    return periods


@router.put("/{period_code}", response_model=PeriodConfigOut, summary="更新巡检时段提醒与截止时间")
def update_inspection_period(
    period_code: str,
    payload: PeriodConfigUpdate,
    db: Session = Depends(get_db),
):
    """
    修改指定巡检时段的启动与推送时间、截止时间、启闭状态。
    修改后将自动动态更新后台定时调度器，无需重启服务。
    """
    period = db.scalar(
        select(InspectionPeriodConfig).where(
            InspectionPeriodConfig.period_code == period_code.upper()
        )
    )
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到巡检时段: {period_code}",
        )

    try:
        parsed_start = _parse_time_str(payload.start_time)
        parsed_deadline = _parse_time_str(payload.deadline_time)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"时间格式解析错误: {e}",
        )

    if parsed_start >= parsed_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"巡检启动与提醒时间 ({payload.start_time}) 必须早于截止时间 ({payload.deadline_time})",
        )

    # Update fields
    if payload.period_name:
        period.period_name = payload.period_name.strip()
    period.start_time = parsed_start
    period.deadline_time = parsed_deadline
    period.enabled = payload.enabled
    period.reminder_enabled = payload.reminder_enabled

    db.commit()
    db.refresh(period)

    # Dynamically reschedule APScheduler cron
    reschedule_period_job(
        period_code=period.period_code,
        hour=parsed_start.hour,
        minute=parsed_start.minute,
        enabled=period.enabled,
    )

    return period


@router.post("/{period_code}/trigger", summary="立即测试触发指定时段巡检及推送")
def trigger_inspection_period(
    period_code: str,
    db: Session = Depends(get_db),
):
    """手动测试触发：立即为今日该时段生成巡检任务并推送钉钉提醒"""
    period = db.scalar(
        select(InspectionPeriodConfig).where(
            InspectionPeriodConfig.period_code == period_code.upper()
        )
    )
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到巡检时段: {period_code}",
        )

    try:
        generate_and_notify_period(period.period_code)
        return {
            "status": "success",
            "message": f"已成功手动触发【{period.period_name}】巡检任务生成与推送",
            "period_code": period.period_code,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发失败: {str(e)}",
        )
