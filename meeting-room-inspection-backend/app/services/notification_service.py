import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any
import httpx

from app.core.config import settings


class NotificationService:
    def __init__(
        self,
        webhook_url: str | None = None,
        secret: str | None = None,
        frontend_url: str | None = None,
    ):
        self.webhook_url = webhook_url or settings.dingtalk_webhook_url
        self.secret = secret or settings.dingtalk_secret
        self.frontend_url = (frontend_url or settings.frontend_url).rstrip("/")

    def _generate_target_url(self) -> str | None:
        if not self.webhook_url:
            return None

        # DingTalk signature handling
        if "dingtalk.com" in self.webhook_url and self.secret:
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode("utf-8")
            string_to_sign = f"{timestamp}\n{self.secret}"
            string_to_sign_enc = string_to_sign.encode("utf-8")
            hmac_code = hmac.new(
                secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            sep = "&" if "?" in self.webhook_url else "?"
            return f"{self.webhook_url}{sep}timestamp={timestamp}&sign={sign}"

        return self.webhook_url

    def send_markdown(self, title: str, text: str) -> bool:
        url = self._generate_target_url()

        if not url:
            # Mock print when no webhook configured
            print(f"[Mock Group Notification]\nTitle: {title}\nContent:\n{text}\n-----------------------")
            return True

        # Build payload according to platform
        if "qyapi.weixin.qq.com" in url:
            # Enterprise WeChat (WeCom)
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"## {title}\n\n{text}",
                },
            }
        elif "feishu.cn" in url or "larksuite.com" in url:
            # Feishu / Lark
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title},
                        "template": "blue",
                    },
                    "elements": [
                        {"tag": "markdown", "content": text}
                    ],
                },
            }
        else:
            # DingTalk Default
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text,
                },
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                data = res.json()
                # Check response status
                if data.get("errcode") == 0 or data.get("StatusCode") == 0 or data.get("code") == 0:
                    print(f"✓ Notification pushed successfully to {url[:45]}...")
                    return True
                else:
                    print(f"Webhook push failed: {data}")
                    return False
        except Exception as e:
            print(f"Failed to post to webhook: {e}")
            return False

    def notify_new_inspection_tasks(
        self,
        tasks_info: list[dict[str, Any]],
        period_name: str,
        inspection_date: str,
        base_link_url: str | None = None,
    ) -> bool:
        """
        Push new inspection tasks notification to group chat.
        """
        title = f"📋 【巡检提醒】{inspection_date} {period_name}任务已发布"
        link_base = (base_link_url or self.frontend_url).rstrip("/")

        lines = [
            f"### 📋 【巡检提醒】{inspection_date} {period_name}",
            f"> 请相关巡检人员及时前往指定会议室进行拍照核验。",
            "",
            "**待巡检会议室列表：**",
        ]

        for t in tasks_info:
            room_name = t.get("room_name", "会议室")
            task_id = t.get("task_id")
            direct_url = f"{link_base}/#/inspect?taskId={task_id}"
            lines.append(f"- **{room_name}**：[👉 点击进入巡检]({direct_url})")

        lines.extend([
            "",
            "---",
            "💡 *提示：请先开启室内灯光，保持手机平稳，按地面机位标识拍摄前、后两张照片。*",
        ])

        return self.send_markdown(title, "\n".join(lines))

    def notify_abnormal_alert(
        self,
        room_name: str,
        task_no: str,
        abnormal_items: list[dict[str, str]],
    ) -> bool:
        """
        Push alert when abnormal indicators are confirmed.
        """
        title = f"⚠️ 【异常告警】{room_name} 巡检发现异常"
        lines = [
            f"### ⚠️ 【巡检异常告警】{room_name}",
            f"> 任务编号: `{task_no}`",
            "",
            "**异常项目清单：**",
        ]
        for item in abnormal_items:
            name = item.get("name", "未命名指标")
            reason = item.get("reason", "未说明原因")
            lines.append(f"- 🔴 **{name}**：{reason}")

        lines.extend([
            "",
            "---",
            "请行政/保洁运维人员尽快前往处理并恢复规范状态。",
        ])
        return self.send_markdown(title, "\n".join(lines))


def get_notification_service() -> NotificationService:
    return NotificationService()
