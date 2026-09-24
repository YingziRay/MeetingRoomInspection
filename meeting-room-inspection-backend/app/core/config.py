from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Meeting Room Inspection API"
    environment: str = "dev"
    debug: bool = True

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/meeting_inspection"
    )

    cors_origins: str = "http://localhost:5173"
    api_v1_prefix: str = "/api/v1"

    # Storage settings
    storage_type: str = "local"  # "local" | "s3"
    upload_dir: str = "uploads"
    base_url: str = "http://localhost:8000"

    # Vision Model settings
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    vision_model: str = "deepseek-flash"

    # Image Quality Thresholds
    min_blur_score: float = 50.0    # cv2.Laplacian var: < 50 => Blurry
    min_brightness: float = 35.0    # gray.mean: < 35 => Too dark
    max_brightness: float = 230.0   # gray.mean: > 230 => Overexposed
    min_image_dimension: int = 480  # min(w, h) >= 480

    # Notification & Scheduler settings
    dingtalk_webhook_url: str | None = None
    dingtalk_secret: str | None = None
    frontend_url: str = "http://localhost:5173"
    scheduler_enabled: bool = True




    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
