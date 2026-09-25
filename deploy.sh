#!/bin/bash
set -e

echo "=================================================="
echo "  AI 会议室智能巡检系统 —— 一键构建与容器化启动"
echo "=================================================="

# 1. Check docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker，请先安装 Docker / Docker Desktop"
    exit 1
fi

# 2. Check .env
if [ ! -f "meeting-room-inspection-backend/.env" ]; then
    echo "⚠️ 未找到 meeting-room-inspection-backend/.env，正在从模板生成..."
    cp meeting-room-inspection-backend/.env.example meeting-room-inspection-backend/.env
fi

# 3. Detect LAN IP and auto-sync FRONTEND_URL for DingTalk notifications & mobile access
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
if [ -n "$LAN_IP" ]; then
    echo "📡 检测到当前局域网 IP: $LAN_IP"
    if grep -q '^FRONTEND_URL=' meeting-room-inspection-backend/.env; then
        sed -i '' "s|^FRONTEND_URL=.*|FRONTEND_URL=http://${LAN_IP}:5173|" meeting-room-inspection-backend/.env
    else
        echo "FRONTEND_URL=http://${LAN_IP}:5173" >> meeting-room-inspection-backend/.env
    fi
    echo "🔗 已自动同步钉钉推送跳转地址为: http://${LAN_IP}:5173"
else
    LAN_IP="localhost"
fi

# 4. Clean up legacy standalone postgres container if belonging to another project or unmanaged
LEGACY_PROJECT=$(docker inspect meeting-inspection-postgres --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>/dev/null || true)
if [ -n "$LEGACY_PROJECT" ] && [ "$LEGACY_PROJECT" != "meetingroominspection" ]; then
    echo "♻️ 检测到历史残留的旧数据库容器 (来自 $LEGACY_PROJECT)，正在平滑接管..."
    docker stop meeting-inspection-postgres 2>/dev/null || true
    docker rm meeting-inspection-postgres 2>/dev/null || true
fi

# 5. Check if local dev processes (like uvicorn/python) are occupying ports
if lsof -i :8000 | grep -v 'com.docke' | grep -q 'LISTEN'; then
    echo "⚠️ 提示: 检测到宿主机本地有非容器进程正在占用 8000 端口，可能与容器冲突。请确保已停止本地的 uvicorn 进程。"
fi

# 6. Build & start
echo "🚀 正在启动全栈容器群组 (Postgres + Backend + Frontend)..."
docker compose up -d

echo ""
echo "=================================================="
echo "🎉 部署完成！容器状态："
docker compose ps
echo "=================================================="
echo "📱 访问地址："
echo "   - 电脑端 H5 界面：http://localhost:5173"
echo "   - 手机端局域网访问：http://${LAN_IP}:5173"
echo "   - 后端 API 文档：http://localhost:8000/docs"
echo "=================================================="
