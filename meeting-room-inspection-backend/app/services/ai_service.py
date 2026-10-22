from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.vision.base import VisionModelProvider
from app.integrations.vision.openai_provider import get_vision_provider
from app.models.ai_analysis_log import AIAnalysisLog
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_photo import InspectionPhoto
from app.models.inspection_result import InspectionResult
from app.models.inspection_task import InspectionTask
from app.models.photo_region import PhotoRegion
from app.models.room_indicator import RoomIndicator
from app.models.standard_photo import StandardPhoto


class AIInspectionService:
    def __init__(self, provider: VisionModelProvider | None = None):
        self.provider = provider or get_vision_provider()

    def run_task_inspection(self, db: Session, task_id: int) -> list[InspectionResult]:
        task = db.get(InspectionTask, task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")

        # 1. Fetch live uploaded photos for this task
        live_photos = db.scalars(
            select(InspectionPhoto).where(InspectionPhoto.task_id == task_id)
        ).all()

        if not live_photos:
            raise ValueError("No uploaded photos found for this inspection task")

        # 2. Mark task as AI_ANALYZING
        task.status = "AI_ANALYZING"
        db.commit()

        try:
            # 3. Load standard photos for this room
            standard_photos = db.scalars(
                select(StandardPhoto).where(
                    StandardPhoto.room_id == task.room_id,
                    StandardPhoto.status == "ACTIVE",
                )
            ).all()
            std_photo_map = {sp.photo_type: sp for sp in standard_photos}

            # 4. Load configured indicators and their regions for this room
            room_indicators = db.scalars(
                select(RoomIndicator)
                .where(
                    RoomIndicator.room_id == task.room_id,
                    RoomIndicator.enabled.is_(True),
                )
                .order_by(RoomIndicator.sort_order)
            ).all()

            # Build detailed indicator objects
            all_indicators_info = []
            for ri in room_indicators:
                indicator = db.get(InspectionIndicator, ri.indicator_id)
                if not indicator:
                    continue

                region = db.get(PhotoRegion, ri.region_id) if ri.region_id else None
                region_dict = None
                perspectives_list = []
                if region:
                    region_dict = {
                        "code": region.region_code,
                        "name": region.region_name,
                        "x": float(region.x),
                        "y": float(region.y),
                        "width": float(region.width),
                        "height": float(region.height),
                    }
                    # Find which photo_type this region belongs to
                    std_photo = db.get(StandardPhoto, region.standard_photo_id)
                    if std_photo and std_photo.photo_type:
                        perspectives_list = [std_photo.photo_type]

                if not perspectives_list:
                    raw_perspectives = getattr(indicator, "photo_perspective", "FRONT") or "FRONT"
                    perspectives_list = [p.strip() for p in raw_perspectives.split(",") if p.strip()]
                    # 若现场未拍 AC_PANEL 且指标仅有 AC_PANEL，允许平滑降级到 REAR 兜底
                    if "AC_PANEL" in perspectives_list and not any(lp.photo_type == "AC_PANEL" for lp in live_photos):
                        perspectives_list.append("REAR")

                all_indicators_info.append(
                    {
                        "indicator_id": indicator.id,
                        "indicator_code": indicator.indicator_code,
                        "indicator_name": indicator.indicator_name,
                        "category": indicator.category,
                        "normal_condition": indicator.normal_condition,
                        "abnormal_condition": indicator.abnormal_condition,
                        "region": region_dict,
                        "perspectives": perspectives_list,
                    }
                )

            # 5. Process each perspective (FRONT, REAR, AC_PANEL)
            # Pre-load existing records to prevent unique constraint violation on multi-perspective indicators
            existing_records = db.scalars(
                select(InspectionResult).where(InspectionResult.task_id == task_id)
            ).all()
            results_by_indicator: dict[int, InspectionResult] = {
                r.indicator_id: r for r in existing_records
            }

            for live_photo in live_photos:
                p_type = live_photo.photo_type
                std_photo = std_photo_map.get(p_type)

                # Gather indicators matching this perspective
                perspective_indicators = [
                    item for item in all_indicators_info if p_type in item["perspectives"]
                ]

                if not perspective_indicators:
                    continue

                std_image_path = std_photo.photo_url if std_photo else live_photo.photo_url
                live_image_path = live_photo.photo_url

                # Call VLM Provider
                analysis = self.provider.analyze(
                    standard_image_path=std_image_path,
                    live_image_path=live_image_path,
                    indicators=perspective_indicators,
                    photo_type=p_type,
                )

                # Record AI Analysis Log
                log = AIAnalysisLog(
                    task_id=task_id,
                    photo_id=live_photo.id,
                    model_name=analysis.model_name,
                    model_version="1.0",
                    prompt_version="v1.0",
                    request_json={"indicators": [i["indicator_code"] for i in perspective_indicators]},
                    response_json=analysis.raw_response,
                    latency_ms=analysis.latency_ms,
                    token_usage=analysis.token_usage,
                    status="SUCCESS",
                )
                db.add(log)

                # Map analysis results back to DB records
                result_lookup = {r.indicator_code: r for r in analysis.results}

                for ind_item in perspective_indicators:
                    ind_code = ind_item["indicator_code"]
                    ind_id = ind_item["indicator_id"]
                    r_data = result_lookup.get(ind_code)

                    ai_status = r_data.status if r_data else "UNCERTAIN"
                    ai_confidence = Decimal(str(round(r_data.confidence, 4))) if r_data else Decimal("0.5")
                    ai_reason = r_data.reason if r_data else "未识别到该项结果"
                    ai_bbox = r_data.bbox if r_data else None

                    p_label = {"FRONT": "前视角", "REAR": "后视角", "AC_PANEL": "空调面板"}.get(p_type, p_type)
                    current_reason_item = f"[{p_label}] {ai_reason}" if len(ind_item["perspectives"]) > 1 else ai_reason

                    # In-memory upsert to prevent unique constraint conflicts across perspectives
                    target_res = results_by_indicator.get(ind_id)

                    if not target_res:
                        target_res = InspectionResult(
                            task_id=task_id,
                            indicator_id=ind_id,
                            ai_status=ai_status,
                            ai_confidence=ai_confidence,
                            ai_reason=current_reason_item,
                            ai_bbox=ai_bbox,
                            final_status=ai_status,
                        )
                        db.add(target_res)
                        results_by_indicator[ind_id] = target_res
                    else:
                        # 综合多机位判定逻辑：异常优先（一票否决制）
                        if ai_status == "ABNORMAL":
                            target_res.ai_status = "ABNORMAL"
                            target_res.final_status = "ABNORMAL"
                            target_res.ai_confidence = max(target_res.ai_confidence or Decimal("0"), ai_confidence)
                            target_res.ai_reason = f"{target_res.ai_reason}; {current_reason_item}" if target_res.ai_reason else current_reason_item
                            if ai_bbox:
                                target_res.ai_bbox = ai_bbox
                        elif target_res.ai_status == "ABNORMAL":
                            target_res.ai_reason = f"{target_res.ai_reason}; {current_reason_item}"
                        else:
                            if ai_status == "NORMAL":
                                target_res.ai_status = "NORMAL"
                                target_res.final_status = "NORMAL"
                                target_res.ai_confidence = max(target_res.ai_confidence or Decimal("0"), ai_confidence)
                            target_res.ai_reason = f"{target_res.ai_reason}; {current_reason_item}" if target_res.ai_reason else current_reason_item

            # 6. Progress task status to WAITING_CONFIRM
            task.status = "WAITING_CONFIRM"
            db.commit()

            saved_results = list(results_by_indicator.values())
            # Refresh all results
            for r in saved_results:
                db.refresh(r)

            return saved_results
        except Exception as e:
            # 安全回滚：必须先 rollback 破坏的事务，再将状态重置为 IN_PROGRESS，破除前端死锁
            try:
                db.rollback()
                task = db.get(InspectionTask, task_id)
                if task:
                    task.status = "IN_PROGRESS"
                    db.commit()
                print(f"[AIInspectionService] Task {task_id} failed during analysis, rolled back to IN_PROGRESS: {e}")
            except Exception as rollback_err:
                print(f"[AIInspectionService] Failed to rollback task status: {rollback_err}")
                db.rollback()
            raise e


def get_ai_service() -> AIInspectionService:
    return AIInspectionService()
