from dataclasses import dataclass
from typing import Any
import cv2
import numpy as np
from app.core.config import settings


@dataclass
class ImageQualityResult:
    passed: bool
    status: str  # "PASS" | "BLURRY" | "TOO_DARK" | "OVEREXPOSED" | "LOW_RESOLUTION" | "INVALID"
    reason: str | None
    width: int
    height: int
    blur_score: float
    brightness: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "reason": self.reason,
            "width": self.width,
            "height": self.height,
            "blur_score": round(self.blur_score, 2),
            "brightness": round(self.brightness, 2),
        }


def assess_image_quality(file_bytes: bytes) -> ImageQualityResult:
    # 1. Decode bytes with OpenCV
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return ImageQualityResult(
            passed=False,
            status="INVALID",
            reason="无法解码图片文件，图片格式损坏或不支持",
            width=0,
            height=0,
            blur_score=0.0,
            brightness=0.0,
        )

    height, width = img.shape[:2]

    # 2. Resolution check
    if min(width, height) < settings.min_image_dimension:
        return ImageQualityResult(
            passed=False,
            status="LOW_RESOLUTION",
            reason=f"图片分辨率过低 ({width}x{height})，长宽不能小于 {settings.min_image_dimension}px",
            width=width,
            height=height,
            blur_score=0.0,
            brightness=0.0,
        )

    # 3. Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Brightness check (Mean intensity)
    brightness = float(np.mean(gray))
    if brightness < settings.min_brightness:
        return ImageQualityResult(
            passed=False,
            status="TOO_DARK",
            reason=f"光线过暗 (亮度评分 {brightness:.1f}/{settings.min_brightness:.1f})，请打开会议室灯光或调整角度重拍",
            width=width,
            height=height,
            blur_score=0.0,
            brightness=brightness,
        )
    if brightness > settings.max_brightness:
        return ImageQualityResult(
            passed=False,
            status="OVEREXPOSED",
            reason=f"画面严重过曝 (亮度评分 {brightness:.1f}/{settings.max_brightness:.1f})，请避开强光直射重拍",
            width=width,
            height=height,
            blur_score=0.0,
            brightness=brightness,
        )

    # 5. Blur check (Laplacian Variance)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < settings.min_blur_score:
        return ImageQualityResult(
            passed=False,
            status="BLURRY",
            reason=f"照片模糊、对焦不清晰或晃动 (清晰度评分 {blur_score:.1f}/{settings.min_blur_score:.1f})，请拿稳手机重新拍摄",
            width=width,
            height=height,
            blur_score=blur_score,
            brightness=brightness,
        )


    # 6. Passed
    return ImageQualityResult(
        passed=True,
        status="PASS",
        reason=None,
        width=width,
        height=height,
        blur_score=blur_score,
        brightness=brightness,
    )
