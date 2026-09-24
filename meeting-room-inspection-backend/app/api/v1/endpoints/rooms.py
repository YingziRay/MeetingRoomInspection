from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.meeting_room import MeetingRoom
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
    page_size: int = Query(20, ge=1, le=100),
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
            detail="room_code already exists",
        )

    room = MeetingRoom(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
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
