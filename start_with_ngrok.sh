#!/bin/bash
# 启动 Web 应用并自动配置 ngrok

cd "$(dirname "$0")"
source venv/bin/activate

# 检查 ngrok 是否安装
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok 未安装"
    echo "运行: ./setup_ngrok.sh"
    exit 1
fi

# 检查 ngrok 是否已配置
if ! ngrok config check &> /dev/null; then
    echo "⚠️  ngrok 未配置"
    echo "请先运行: ngrok config add-authtoken 你的token"
    echo "获取 token: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

PORT=5001

echo "=" * 50
echo "🚀 启动 Web 应用和 ngrok"
echo "=" * 50
echo ""

# 启动 Web 应用（后台运行）
echo "📱 启动 Web 应用 (端口 $PORT)..."
python web_app.py > web_app.log 2>&1 &
WEB_PID=$!

# 等待 Web 应用启动
sleep 3

# 启动 ngrok
echo "🌐 启动 ngrok..."
ngrok http $PORT

# 清理：当脚本退出时停止 Web 应用
trap "kill $WEB_PID 2>/dev/null" EXIT

