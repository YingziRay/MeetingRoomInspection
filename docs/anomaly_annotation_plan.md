# 巡检异常自动标绘与图片告警优化方案（备查文档）

本文档记录了当现场巡检产生异常（无论由 AI 自动检出或巡检员人工复核指出）时，如何在告警图片中直观体现异常区域的完整工程落地方案。后续随时可依据本设计快速接入。

---

## 核心实现机制：AI 优先 + ROI 兜底复合标绘引擎

### 1. 标绘坐标优先级规则
- **AI 检出的异常**：直接采用多模态大模型返回的精确归一化边界框 `ai_bbox: {"x", "y", "w", "h"}`。
- **人工手动指定的异常**：巡检员在手机端仅需勾选“异常”，无需手动画框；系统自动读取该指标在数据库 `photo_region` 中预绑定的基准区域坐标进行兜底标绘。

---

## 2. 后端绘图服务代码实现 (OpenCV)

在 `app/services/` 下新增 `annotation_service.py`：

```python
import cv2
import numpy as np
from pathlib import Path

def draw_anomalies_on_photo(
    image_path: str,
    anomalies: list[dict],
    output_filename: str = "alert_annotated.jpg",
) -> str:
    """
    在现场照片上自动绘制红色/橙色告警框及指标名称
    """
    path = Path(image_path)
    if not path.exists():
        return image_path

    img = cv2.imread(str(path))
    if img is None:
        return image_path

    h, w = img.shape[:2]

    for item in anomalies:
        box = item.get("bbox") or item.get("region_box")
        name = item.get("name", "异常项")
        is_human = item.get("is_human", False)

        if box:
            x1 = int(box["x"] * w)
            y1 = int(box["y"] * h)
            x2 = int((box["x"] + box["w"]) * w)
            y2 = int((box["y"] + box["h"]) * h)

            # 颜色：AI检出用高警示红 (0, 0, 255)，人工复核用明亮橙黄 (0, 165, 255)
            color = (0, 165, 255) if is_human else (0, 0, 255)

            # 1. 绘制矩形线框
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness=3)

            # 2. 标签背景与文字
            label = f"{'[人工]' if is_human else '[AI]'} {name}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, 2)
            cv2.rectangle(img, (x1, max(y1 - 25, 0)), (x1 + text_w + 6, max(y1, 25)), color, -1)
            cv2.putText(img, label, (x1 + 3, max(y1 - 6, 18)), font, font_scale, (255, 255, 255), 2)

    # 保存衍生图到同一任务目录下
    out_path = path.parent / output_filename
    cv2.imwrite(str(out_path), img)
    return str(out_path)
```

---

## 3. 工作群 Markdown 卡片嵌入

在 `app/services/notification_service.py` 的 `notify_abnormal_alert` 中，直接在消息尾部附加：
```markdown
### ⚠️ 【巡检异常告警】301会议室
- 🔴 **椅子**：多把座椅拉出未推入桌下

![现场异常标注图](http://[服务器IP]:8000/uploads/tasks/{task_id}/alert_annotated.jpg)
```

---

## 4. 后续快速唤醒指令
当需要实现此功能时，只需在对话中提出：
> **“请读取 docs/anomaly_annotation_plan.md 并开始实现异常自动标绘与群图片展示”**
即可无缝接续开发。
