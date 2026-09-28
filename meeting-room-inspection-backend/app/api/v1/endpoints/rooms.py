import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_task import InspectionTask
from app.models.meeting_room import MeetingRoom
from app.models.room_indicator import RoomIndicator
from app.models.standard_photo import StandardPhoto
from app.schemas.indicator import (
    RoomIndicatorBatchRequest,
    RoomIndicatorItem,
    StandardPhotoResponse,
)
from app.schemas.room import (
    MeetingRoomCreate,
    MeetingRoomPage,
    MeetingRoomResponse,
    MeetingRoomUpdate,
)

router = APIRouter()


@router.get("", response_model=MeetingRoomPage)
def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    inspection_enabled: bool | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(MeetingRoom)
    count_stmt = select(func.count()).select_from(MeetingRoom)

    if status_filter:
        stmt = stmt.where(MeetingRoom.status == status_filter)
        count_stmt = count_stmt.where(MeetingRoom.status == status_filter)

    if inspection_enabled is not None:
        stmt = stmt.where(MeetingRoom.inspection_enabled == inspection_enabled)
        count_stmt = count_stmt.where(
            MeetingRoom.inspection_enabled == inspection_enabled
        )

    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        stmt.order_by(MeetingRoom.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return MeetingRoomPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=MeetingRoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(payload: MeetingRoomCreate, db: Session = Depends(get_db)):
    exists = db.scalar(
        select(MeetingRoom).where(MeetingRoom.room_code == payload.room_code)
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"会议室编号 {payload.room_code} 已存在",
        )

    room = MeetingRoom(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)

    # 自动关联系统默认启用的巡检指标
    default_indicators = db.scalars(
        select(InspectionIndicator)
        .where(InspectionIndicator.enabled.is_(True))
        .order_by(InspectionIndicator.sort_order)
    ).all()

    for idx, ind in enumerate(default_indicators):
        room_ind = RoomIndicator(
            room_id=room.id,
            indicator_id=ind.id,
            enabled=True,
            sort_order=idx + 1,
        )
        db.add(room_ind)

    # 如果有现成的基准图文件（如 RM301 标准模版），也可以建立关联
    db.commit()
    return room


@router.get("/{room_id}", response_model=MeetingRoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")
    return room


@router.patch("/{room_id}", response_model=MeetingRoomResponse)
def update_room(
    room_id: int,
    payload: MeetingRoomUpdate,
    db: Session = Depends(get_db),
):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    # 检查是否有巡检任务
    task_count = db.scalar(
        select(func.count()).select_from(InspectionTask).where(InspectionTask.room_id == room_id)
    ) or 0

    if task_count > 0:
        # 存在历史任务，进行软删除以保留历史台账
        room.status = "INACTIVE"
        room.inspection_enabled = False
        db.commit()
        return {"success": True, "message": f"该会议室已有 {task_count} 条巡检记录，已安全转为停用状态"}
    else:
        # 无任务关联，彻底清除关联配置
        db.query(RoomIndicator).filter(RoomIndicator.room_id == room_id).delete()
        db.query(StandardPhoto).filter(StandardPhoto.room_id == room_id).delete()
        db.delete(room)
        db.commit()
        return {"success": True, "message": "会议室已彻底删除"}


# ==================== 指标关联配置 ====================

@router.get("/{room_id}/indicators", response_model=list[RoomIndicatorItem])
def get_room_indicators(room_id: int, db: Session = Depends(get_db)):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    room_indicators = db.scalars(
        select(RoomIndicator)
        .where(RoomIndicator.room_id == room_id, RoomIndicator.enabled.is_(True))
        .order_by(RoomIndicator.sort_order)
    ).all()

    result = []
    for ri in room_indicators:
        ind = db.get(InspectionIndicator, ri.indicator_id)
        if ind:
            result.append(
                RoomIndicatorItem(
                    id=ri.id,
                    room_id=ri.room_id,
                    indicator_id=ind.id,
                    indicator_code=ind.indicator_code,
                    indicator_name=ind.indicator_name,
                    category=ind.category,
                    enabled=ri.enabled,
                    sort_order=ri.sort_order,
                )
            )
    return result


@router.put("/{room_id}/indicators", response_model=list[RoomIndicatorItem])
def update_room_indicators(
    room_id: int,
    payload: RoomIndicatorBatchRequest,
    db: Session = Depends(get_db),
):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    # 清理该会议室原有配置
    db.query(RoomIndicator).filter(RoomIndicator.room_id == room_id).delete()

    # 批量添加勾选的指标
    new_items = []
    for idx, ind_id in enumerate(payload.indicator_ids):
        ind = db.get(InspectionIndicator, ind_id)
        if not ind:
            continue
        ri = RoomIndicator(
            room_id=room_id,
            indicator_id=ind_id,
            enabled=True,
            sort_order=idx + 1,
        )
        db.add(ri)
        new_items.append((ri, ind))

    db.commit()

    return [
        RoomIndicatorItem(
            id=ri.id,
            room_id=ri.room_id,
            indicator_id=ind.id,
            indicator_code=ind.indicator_code,
            indicator_name=ind.indicator_name,
            category=ind.category,
            enabled=ri.enabled,
            sort_order=ri.sort_order,
        )
        for ri, ind in new_items
    ]


# ==================== 基准照片配置 ====================

@router.get("/{room_id}/standard-photos", response_model=list[StandardPhotoResponse])
def get_room_standard_photos(room_id: int, db: Session = Depends(get_db)):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    photos = db.scalars(
        select(StandardPhoto)
        .where(StandardPhoto.room_id == room_id, StandardPhoto.status == "ACTIVE")
        .order_by(StandardPhoto.id)
    ).all()

    return photos


@router.post("/{room_id}/standard-photos", response_model=StandardPhotoResponse)
async def upload_room_standard_photo(
    room_id: int,
    photo_type: str = Form(..., regex="^(FRONT|REAR|AC_PANEL)$"),
    shoot_position: str | None = Form(None),
    camera_direction: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    room = db.get(MeetingRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ROOM_NOT_FOUND")

    standards_dir = Path(settings.upload_dir) / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)

    # 生成安全文件名
    ext = Path(file.filename or "photo.jpg").suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    
    unique_suffix = uuid.uuid4().hex[:8]
    filename = f"{room.room_code}_{photo_type}_{unique_suffix}{ext}"
    dest_path = standards_dir / filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_url = f"/uploads/standards/{filename}"

    # 默认机位和镜头朝向字典
    default_positions = {
        "FRONT": "正向主会议桌视角",
        "REAR": "背向门框及后墙视角",
        "AC_PANEL": "墙面空调温控开关面板",
    }
    default_directions = {
        "FRONT": "正对白板及前侧投影",
        "REAR": "对准空调及后方设施",
        "AC_PANEL": "特写近拍空调控制面板屏幕及开关状态",
    }

    # 查找已有激活版本
    existing = db.scalar(
        select(StandardPhoto).where(
            StandardPhoto.room_id == room_id,
            StandardPhoto.photo_type == photo_type,
            StandardPhoto.status == "ACTIVE",
        )
    )

    if existing:
        existing.photo_url = photo_url
        if shoot_position:
            existing.shoot_position = shoot_position
        if camera_direction:
            existing.camera_direction = camera_direction
        existing.version += 1
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_photo = StandardPhoto(
            room_id=room_id,
            photo_type=photo_type,
            photo_url=photo_url,
            shoot_position=shoot_position or default_positions.get(photo_type, "特定设施机位"),
            camera_direction=camera_direction or default_directions.get(photo_type, "对准目标设施"),
            version=1,
            status="ACTIVE",
        )
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        return new_photo
