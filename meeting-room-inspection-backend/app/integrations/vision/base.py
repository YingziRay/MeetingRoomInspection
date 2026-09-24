from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class IndicatorVisionResult:
    indicator_code: str
    status: str  # "NORMAL" | "ABNORMAL" | "UNCERTAIN"
    confidence: float
    reason: str
    bbox: dict[str, Any] | None = None


@dataclass
class VisionAnalysisResponse:
    results: list[IndicatorVisionResult]
    model_name: str
    raw_response: dict[str, Any]
    token_usage: dict[str, Any]
    latency_ms: int


class VisionModelProvider(ABC):
    @abstractmethod
    def analyze(
        self,
        standard_image_path: str,
        live_image_path: str,
        indicators: list[dict[str, Any]],
        photo_type: str = "FRONT",
    ) -> VisionAnalysisResponse:
        """
        Analyze live inspection photo against standard photo using VLM.
        Returns structured results for each provided indicator.
        """
        raise NotImplementedError
