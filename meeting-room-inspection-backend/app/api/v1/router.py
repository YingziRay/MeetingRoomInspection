from fastapi import APIRouter

from app.api.v1.endpoints import (
    dashboard,
    indicators,
    inspection_tasks,
    notifications,
    photos,
    results,
    rooms,
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(
    indicators.router, prefix="/indicators", tags=["indicators"]
)
api_router.include_router(
    inspection_tasks.router, prefix="/inspection-tasks", tags=["inspection-tasks"]
)
api_router.include_router(photos.router, prefix="/photos", tags=["photos"])
api_router.include_router(results.router, prefix="/inspection-results", tags=["results"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)

