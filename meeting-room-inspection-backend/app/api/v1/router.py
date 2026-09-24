from fastapi import APIRouter

from app.api.v1.endpoints import (
    inspection_tasks,
    notifications,
    photos,
    results,
    rooms,
)

api_router = APIRouter()

api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(
    inspection_tasks.router, prefix="/inspection-tasks", tags=["inspection-tasks"]
)
api_router.include_router(photos.router, prefix="/photos", tags=["photos"])
api_router.include_router(results.router, prefix="/inspection-results", tags=["results"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)

