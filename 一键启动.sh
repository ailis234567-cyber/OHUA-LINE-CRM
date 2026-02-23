#!/bin/bash
# 一键启动 Web 应用和 ngrok

cd "$(dirname "$0")"

echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""
echo "🚀 一键启动在线网址服务"
echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 ngrok
if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok 未安装"
    echo ""
    echo "请先安装 ngrok:"
    echo "  brew install ngrok"
    echo ""
    echo "或者使用 localtunnel（无需安装）:"
    echo "  npm install -g localtunnel"
    echo "  lt --port 5001"
    exit 1
fi

# 检查 ngrok 配置
if ! ngrok config check &> /dev/null; then
    echo "⚠️  ngrok 未配置"
    echo ""
    echo "请先配置 ngrok:"
    echo "1. 访问 https://dashboard.ngrok.com/signup 注册"
    echo "2. 获取 authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. 运行: ngrok config add-authtoken 你的token"
    exit 1
fi

PORT=5001

echo "📱 启动 Web 应用 (端口 $PORT)..."
echo ""

# 启动 Web 应用（后台运行）
python web_app.py > web_app.log 2>&1 &
WEB_PID=$!

# 等待 Web 应用启动
echo "⏳ 等待 Web 应用启动..."
sleep 3

# 检查 Web 应用是否启动成功
if ! ps -p $WEB_PID > /dev/null; then
    echo "❌ Web 应用启动失败"
    echo "查看日志: cat web_app.log"
    exit 1
fi

echo "✅ Web 应用已启动 (PID: $WEB_PID)"
echo ""
echo "🌐 启动 ngrok..."
echo ""
echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""
echo "📝 重要提示："
echo "1. ngrok 会显示一个在线网址（如: https://xxx.ngrok-free.app）"
echo "2. 复制这个网址，可以在任何地方访问你的网站"
echo "3. 按 Ctrl+C 停止服务"
echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""
echo ""

# 启动 ngrok（前台运行，这样可以看到网址）
ngrok http $PORT

# 清理：当脚本退出时停止 Web 应用
echo ""
echo "🛑 正在停止 Web 应用..."
kill $WEB_PID 2>/dev/null
echo "✅ 已停止"

