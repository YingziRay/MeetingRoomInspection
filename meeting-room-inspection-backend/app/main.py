from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.workers.scheduler import setup_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure uploads directory exists on startup
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    (upload_path / "standards").mkdir(parents=True, exist_ok=True)

    # 2. Start Scheduler
    setup_scheduler()

    yield

    # 3. Shutdown Scheduler
    shutdown_scheduler()



app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI meeting-room inspection backend",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads (local storage)
upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
(upload_path / "standards").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
