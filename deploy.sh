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

# 3. Build & start
echo "🚀 正在构建镜像并启动容器群组 (Postgres + Backend + Frontend)..."
docker compose up -d --build

echo ""
echo "=================================================="
echo "🎉 部署完成！容器状态："
docker compose ps
echo "=================================================="
echo "📱 访问地址："
echo "   - 前端 H5 界面：http://localhost:5173"
echo "   - 后端 API 文档：http://localhost:8000/docs"
echo "=================================================="
