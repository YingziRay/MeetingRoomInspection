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
            photo_type = "FRONT"  # Default fallback
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
                if std_photo:
                    photo_type = std_photo.photo_type
            else:
                # Default categorisation by indicator code
                if indicator.indicator_code in ("I002", "I003"):
                    photo_type = "REAR"

            all_indicators_info.append(
                {
                    "indicator_id": indicator.id,
                    "indicator_code": indicator.indicator_code,
                    "indicator_name": indicator.indicator_name,
                    "category": indicator.category,
                    "normal_condition": indicator.normal_condition,
                    "abnormal_condition": indicator.abnormal_condition,
                    "region": region_dict,
                    "photo_type": photo_type,
                }
            )

        # 5. Process each perspective (FRONT, REAR)
        saved_results: list[InspectionResult] = []

        for live_photo in live_photos:
            p_type = live_photo.photo_type
            std_photo = std_photo_map.get(p_type)

            # Gather indicators for this perspective
            perspective_indicators = [
                item for item in all_indicators_info if item["photo_type"] == p_type
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

                # Upsert inspection_result
                existing_res = db.scalar(
                    select(InspectionResult).where(
                        InspectionResult.task_id == task_id,
                        InspectionResult.indicator_id == ind_id,
                    )
                )

                if not existing_res:
                    res_record = InspectionResult(
                        task_id=task_id,
                        indicator_id=ind_id,
                        ai_status=ai_status,
                        ai_confidence=ai_confidence,
                        ai_reason=ai_reason,
                        ai_bbox=ai_bbox,
                        final_status=ai_status,
                    )
                    db.add(res_record)
                    saved_results.append(res_record)
                else:
                    existing_res.ai_status = ai_status
                    existing_res.ai_confidence = ai_confidence
                    existing_res.ai_reason = ai_reason
                    existing_res.ai_bbox = ai_bbox
                    existing_res.final_status = ai_status
                    saved_results.append(existing_res)

        # 6. Progress task status to WAITING_CONFIRM
        task.status = "WAITING_CONFIRM"
        db.commit()

        # Refresh all results
        for r in saved_results:
            db.refresh(r)

        return saved_results


def get_ai_service() -> AIInspectionService:
    return AIInspectionService()
