from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.storage.object_storage import get_storage_provider
from app.models.inspection_photo import InspectionPhoto
from app.models.inspection_task import InspectionTask
from app.schemas.photo import PhotoDetailResponse, PhotoUploadResponse
from app.services.image_quality_service import assess_image_quality

router = APIRouter()


@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_inspection_photo(
    task_id: int = Form(...),
    photo_type: str = Form(..., description="FRONT, REAR or AC_PANEL"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if photo_type not in ("FRONT", "REAR", "AC_PANEL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PHOTO_TYPE_INVALID: must be 'FRONT', 'REAR', or 'AC_PANEL'",
        )

    # Validate task
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TASK_NOT_FOUND",
        )

    # Read image bytes
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMPTY_FILE",
        )

    # 1. OpenCV Quality Assessment
    quality = assess_image_quality(content)

    # 2. Save file via Storage Provider
    storage = get_storage_provider()
    relative_url = storage.save(
        file_bytes=content,
        filename=file.filename or f"{photo_type.lower()}.jpg",
        subfolder=f"tasks/{task_id}",
    )

    # 3. Upsert InspectionPhoto (idempotent for task_id + photo_type)
    photo = db.scalar(
        select(InspectionPhoto).where(
            InspectionPhoto.task_id == task_id,
            InspectionPhoto.photo_type == photo_type,
        )
    )

    if not photo:
        photo = InspectionPhoto(
            task_id=task_id,
            photo_type=photo_type,
            photo_url=relative_url,
            original_filename=file.filename,
            width=quality.width,
            height=quality.height,
            file_size=len(content),
            quality_status=quality.status,
            quality_reason=quality.reason,
        )
        db.add(photo)
    else:
        photo.photo_url = relative_url
        photo.original_filename = file.filename
        photo.width = quality.width
        photo.height = quality.height
        photo.file_size = len(content)
        photo.quality_status = quality.status
        photo.quality_reason = quality.reason

    db.commit()
    db.refresh(photo)

    return PhotoUploadResponse(
        photo_id=photo.id,
        task_id=photo.task_id,
        photo_type=photo.photo_type,
        photo_url=photo.photo_url,
        quality_passed=quality.passed,
        quality_status=quality.status,
        quality_reason=quality.reason,
        width=quality.width,
        height=quality.height,
        blur_score=quality.blur_score,
        brightness=quality.brightness,
    )


@router.get("/by-task/{task_id}", response_model=list[PhotoDetailResponse])
def get_photos_by_task(task_id: int, db: Session = Depends(get_db)):
    photos = db.scalars(
        select(InspectionPhoto)
        .where(InspectionPhoto.task_id == task_id)
        .order_by(InspectionPhoto.id)
    ).all()
    return photos


@router.post("/presign")
def create_presigned_upload_url(
    task_id: int,
    photo_type: str,
    content_type: str,
    file_size: int,
    db: Session = Depends(get_db),
):
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")

    storage = get_storage_provider()
    object_key = f"tasks/{task_id}/{photo_type.lower()}_{file_size}.jpg"
    upload_url = storage.create_presigned_upload_url(object_key, content_type)

    return {
        "task_id": task_id,
        "photo_type": photo_type,
        "upload_url": upload_url,
        "expires_in": 600,
    }


@router.post("/complete")
def complete_photo_upload(
    task_id: int,
    photo_type: str,
    photo_url: str,
    width: int | None = None,
    height: int | None = None,
    file_size: int | None = None,
    db: Session = Depends(get_db),
):
    photo = db.scalar(
        select(InspectionPhoto).where(
            InspectionPhoto.task_id == task_id,
            InspectionPhoto.photo_type == photo_type,
        )
    )
    if not photo:
        photo = InspectionPhoto(
            task_id=task_id,
            photo_type=photo_type,
            photo_url=photo_url,
            width=width,
            height=height,
            file_size=file_size,
            quality_status="PASS",
        )
        db.add(photo)
    else:
        photo.photo_url = photo_url
        photo.width = width
        photo.height = height
        photo.file_size = file_size
        photo.quality_status = "PASS"

    db.commit()
    db.refresh(photo)

    return {
        "photo_id": photo.id,
        "quality_status": photo.quality_status,
    }
