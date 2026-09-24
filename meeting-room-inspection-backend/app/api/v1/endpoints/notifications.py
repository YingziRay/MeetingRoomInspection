from fastapi import APIRouter
from pydantic import BaseModel
from app.services.notification_service import get_notification_service

router = APIRouter()


class TestNotificationRequest(BaseModel):
    title: str = "🔔 【测试】会议室巡检群机器人推送测试"
    message: str = "这是一条来自 **AI 会议室智能巡检系统** 的连通性测试消息。\n\n- 服务状态: 正常运行\n- 调度引擎: 就绪\n- 当前环境: 本地开发测试"


@router.post("/test")
def test_notification(payload: TestNotificationRequest = TestNotificationRequest()):
    notifier = get_notification_service()
    success = notifier.send_markdown(
        title=payload.title,
        text=f"{payload.message}\n\n[👉 点击测试进入巡检系统]({notifier.frontend_url})",
    )
    return {
        "success": success,
        "webhook_configured": bool(notifier.webhook_url),
        "target_url": notifier.webhook_url[:30] + "..." if notifier.webhook_url else "MOCK_CONSOLE",
    }
