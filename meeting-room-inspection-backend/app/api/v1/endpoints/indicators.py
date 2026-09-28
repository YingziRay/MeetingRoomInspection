import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_result import InspectionResult
from app.models.room_indicator import RoomIndicator
from app.schemas.indicator import (
    IndicatorCreate,
    IndicatorResponse,
    IndicatorUpdate,
)

router = APIRouter()


@router.get("", response_model=list[IndicatorResponse])
def list_indicators(
    category: str | None = None,
    enabled_only: bool = False,
    db: Session = Depends(get_db),
):
    stmt = select(InspectionIndicator)
    if enabled_only:
        stmt = stmt.where(InspectionIndicator.enabled.is_(True))
    if category:
        stmt = stmt.where(InspectionIndicator.category == category)

    indicators = db.scalars(
        stmt.order_by(InspectionIndicator.is_custom, InspectionIndicator.sort_order, InspectionIndicator.id)
    ).all()
    return indicators


@router.post("", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
def create_indicator(payload: IndicatorCreate, db: Session = Depends(get_db)):
    """
    人工新增自定义会议室巡检指标
    """
    # 检查重名
    exists_name = db.scalar(
        select(InspectionIndicator).where(
            InspectionIndicator.indicator_name == payload.indicator_name.strip()
        )
    )
    if exists_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"指标名称「{payload.indicator_name}」已存在，请勿重复添加",
        )

    # 自动生成唯一 indicator_code
    ind_code = payload.indicator_code
    if not ind_code:
        count = db.scalar(select(func.count()).select_from(InspectionIndicator)) or 0
        ind_code = f"CUST_{count + 1:03d}_{uuid.uuid4().hex[:4].upper()}"

    # 默认判定标准兜底提示词（保障 AI 视觉模型零样本推理效果）
    normal_cond = (
        payload.normal_condition.strip()
        if payload.normal_condition
        else f"{payload.indicator_name}处于整洁、关闭或规范就绪状态，无异常违规"
    )
    abnormal_cond = (
        payload.abnormal_condition.strip()
        if payload.abnormal_condition
        else f"{payload.indicator_name}存在随意摆放、破损、未关闭、脏污或未归位等异常情况"
    )

    max_sort = db.scalar(select(func.max(InspectionIndicator.sort_order))) or 0

    indicator = InspectionIndicator(
        indicator_code=ind_code,
        indicator_name=payload.indicator_name.strip(),
        category=payload.category or "ENVIRONMENT",
        photo_perspective=payload.photo_perspective or "FRONT",
        description=payload.description or f"人工新增的自定义巡检指标：{payload.indicator_name}",
        normal_condition=normal_cond,
        abnormal_condition=abnormal_cond,
        ai_supported=payload.ai_supported,
        is_custom=True,
        enabled=True,
        sort_order=payload.sort_order or (max_sort + 1),
    )

    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


@router.patch("/{indicator_id}", response_model=IndicatorResponse)
def update_indicator(
    indicator_id: int,
    payload: IndicatorUpdate,
    db: Session = Depends(get_db),
):
    """
    人工编辑巡检指标（支持更新名称、判定依据、核验视角与启用状态）
    """
    indicator = db.get(InspectionIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="INDICATOR_NOT_FOUND")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(indicator, field, value)

    db.commit()
    db.refresh(indicator)
    return indicator


@router.delete("/{indicator_id}")
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """
    删除指标：
    1. 系统预置核心指标（I001~I010）受保护，禁止物理删除；
    2. 自定义指标若已有历史巡检结果，自动转为安全软删除（enabled=False），保护历史台账；
    3. 自定义指标若无历史任务引用，彻底物理清理。
    """
    indicator = db.get(InspectionIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="INDICATOR_NOT_FOUND")

    # 保护系统核心默认项 (I001 ~ I010)
    preset_codes = {f"I{i:03d}" for i in range(1, 11)}
    if not getattr(indicator, "is_custom", False) or indicator.indicator_code in preset_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"「{indicator.indicator_name}」属于系统预置核心基准指标，受底层保护不可删除。若个别会议室不需要该指标，请在会议室详情中取消勾选即可。",
        )

    # 检查是否有历史巡检任务引用
    history_count = db.scalar(
        select(func.count())
        .select_from(InspectionResult)
        .where(InspectionResult.indicator_id == indicator_id)
    ) or 0

    if history_count > 0:
        # 已有历史台账数据，执行软删除
        indicator.enabled = False
        # 从各会议室解绑，防止后续任务再生成
        db.query(RoomIndicator).filter(RoomIndicator.indicator_id == indicator_id).delete()
        db.commit()
        return {
            "success": True,
            "message": f"该指标在历史巡检台账中已有 {history_count} 条留档记录，为保障历史台账真实性，已安全转为「停用下架」状态，不再参与未来巡检。",
        }
    else:
        # 无任何历史数据，彻底物理删除
        db.query(RoomIndicator).filter(RoomIndicator.indicator_id == indicator_id).delete()
        db.delete(indicator)
        db.commit()
        return {"success": True, "message": f"自定义指标「{indicator.indicator_name}」已彻底删除"}
