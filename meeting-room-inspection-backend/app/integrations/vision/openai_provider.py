import base64
import io
import json
import time
from pathlib import Path
from typing import Any
from PIL import Image
from openai import OpenAI

from app.core.config import settings
from app.integrations.vision.base import (
    IndicatorVisionResult,
    VisionAnalysisResponse,
    VisionModelProvider,
)


def encode_image_for_vlm(image_path: str, max_dimension: int = 1600) -> str:
    """
    Reads image from local path, downsizes if larger than max_dimension, and returns base64 data URL.
    """
    path = Path(image_path)
    # If path starts with /uploads, strip leading slash
    if str(image_path).startswith("/uploads"):
        path = Path(str(image_path).lstrip("/"))

    if not path.exists():
        # Try relative to current working directory
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            path = cwd_path
        else:
            raise FileNotFoundError(f"Image not found at path: {image_path}")

    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        # Downscale proportionally if too large for faster API transfer
        if max(w, h) > max_dimension:
            scale = max_dimension / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_data}"


class OpenAIVisionProvider(VisionModelProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model_name = model_name or settings.vision_model

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def analyze(
        self,
        standard_image_path: str,
        live_image_path: str,
        indicators: list[dict[str, Any]],
        photo_type: str = "FRONT",
    ) -> VisionAnalysisResponse:
        start_time = time.time()

        # Fallback to Mock if no client configured
        if not self.client:
            return self._mock_analysis(indicators, start_time)

        # 1. Encode standard and live images
        std_b64 = encode_image_for_vlm(standard_image_path)
        live_b64 = encode_image_for_vlm(live_image_path)

        # 2. Build indicators prompt description
        indicators_desc = []
        for idx, item in enumerate(indicators, 1):
            region_str = "全图"
            if item.get("region"):
                r = item["region"]
                region_str = f"重点区域: x={r.get('x')}, y={r.get('y')}, width={r.get('width')}, height={r.get('height')} (归一化0~1坐标)"
            indicators_desc.append(
                f"{idx}. 【{item['indicator_name']}】 (编码: {item['indicator_code']})\n"
                f"   - 区域定位: {region_str}\n"
                f"   - 正常规范: {item.get('normal_condition', '无')}\n"
                f"   - 异常情况: {item.get('abnormal_condition', '无')}"
            )
        indicators_text = "\n".join(indicators_desc)

        prompt = f"""
你是一名专业的企业级会议室智能巡检专家。
请仔细对比提供的两张会议室图片：
- 图 1 是【标准规范基准参考图】（代表符合规范的标准状态）
- 图 2 是【现场实拍巡检照片】（巡检人员刚拍摄的实际现状，拍摄视角：{photo_type}）

请对以下 {len(indicators)} 个指定巡检指标进行逐项细致审核比对：
{indicators_text}

【判定与输出要求】：
1. 逐项审核图2现场实拍图是否符合正常标准；对比图1基准图判断是否存在设备开启未关、杂物散落、座椅未推入等异常。
2. 必须输出合法 JSON 对象，包含 "results" 列表。不要包含任何 Markdown 或额外废话。
3. status 只能为三种之一："NORMAL"（正常合格）、"ABNORMAL"（存在异常）、"UNCERTAIN"（由于光线或视角无法看清确定）。
4. confidence 为 0.0 到 1.0 的置信度浮点数。
5. reason 必须极为精炼客观（限 20 字以内），说明关键视觉依据。
6. bbox 若正常为 null；若异常，给出异常物体在图2现场图中的归一化边界框 {{"x": float, "y": float, "w": float, "h": float}}。

【JSON 格式示例】：
{{
  "results": [
    {{
      "indicator_code": "I001",
      "status": "NORMAL",
      "confidence": 0.95,
      "reason": "照明灯光已关闭熄灭",
      "bbox": null
    }}
  ]
}}
"""


        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "text", "text": "【图 1：标准规范基准图】"},
                            {"type": "image_url", "image_url": {"url": std_b64}},
                            {"type": "text", "text": "【图 2：现场实拍巡检图】"},
                            {"type": "image_url", "image_url": {"url": live_b64}},
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.time() - start_time) * 1000)
            raw_text = response.choices[0].message.content or "{}"


            # Strip possible markdown code fence
            clean_json_str = raw_text.strip()
            if clean_json_str.startswith("```"):
                lines = clean_json_str.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_json_str = "\n".join(lines).strip()

            parsed = json.loads(clean_json_str)
            raw_results = parsed.get("results", [])

            results: list[IndicatorVisionResult] = []
            for r in raw_results:
                results.append(
                    IndicatorVisionResult(
                        indicator_code=r.get("indicator_code", "UNKNOWN"),
                        status=r.get("status", "UNCERTAIN"),
                        confidence=float(r.get("confidence", 0.8)),
                        reason=r.get("reason", "AI分析完成"),
                        bbox=r.get("bbox"),
                    )
                )

            # Ensure all requested indicators are present
            detected_codes = {res.indicator_code for res in results}
            for ind in indicators:
                if ind["indicator_code"] not in detected_codes:
                    results.append(
                        IndicatorVisionResult(
                            indicator_code=ind["indicator_code"],
                            status="UNCERTAIN",
                            confidence=0.5,
                            reason="未检测到该指标状态",
                        )
                    )

            token_usage = {}
            if response.usage:
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return VisionAnalysisResponse(
                results=results,
                model_name=self.model_name,
                raw_response=parsed,
                token_usage=token_usage,
                latency_ms=latency_ms,
            )

        except Exception as e:
            # Fallback in case of parse/network error
            latency_ms = int((time.time() - start_time) * 1000)
            print(f"Error during VLM inference: {e}")
            fallback_results = [
                IndicatorVisionResult(
                    indicator_code=ind["indicator_code"],
                    status="UNCERTAIN",
                    confidence=0.5,
                    reason=f"AI调用异常: {str(e)}",
                )
                for ind in indicators
            ]
            return VisionAnalysisResponse(
                results=fallback_results,
                model_name=self.model_name,
                raw_response={"error": str(e)},
                token_usage={},
                latency_ms=latency_ms,
            )

    def _mock_analysis(
        self, indicators: list[dict[str, Any]], start_time: float
    ) -> VisionAnalysisResponse:
        results = []
        for ind in indicators:
            results.append(
                IndicatorVisionResult(
                    indicator_code=ind["indicator_code"],
                    status="NORMAL",
                    confidence=0.95,
                    reason=f"{ind['indicator_name']}状态正常，符合规范",
                    bbox=None,
                )
            )
        latency_ms = int((time.time() - start_time) * 1000)
        return VisionAnalysisResponse(
            results=results,
            model_name="mock-vision-v1",
            raw_response={"mode": "mock"},
            token_usage={"total_tokens": 0},
            latency_ms=latency_ms,
        )


def get_vision_provider() -> VisionModelProvider:
    return OpenAIVisionProvider()
