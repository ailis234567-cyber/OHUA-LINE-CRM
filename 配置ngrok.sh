#!/bin/bash
# 配置 ngrok authtoken

AUTHTOKEN="36ThduP2qwzn7vHLfg87kCYQnkG_6agLLUmUz2f9u7E1d773K"

echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""
echo "🔧 配置 ngrok authtoken"
echo "=" | tr -d '\n' && printf '=%.0s' {1..49} && echo ""

# 检查 ngrok 是否安装
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok 未安装"
    echo ""
    echo "请先安装 ngrok:"
    echo "  brew install ngrok"
    exit 1
fi

# 配置 authtoken
echo "📝 正在配置 authtoken..."
ngrok config add-authtoken $AUTHTOKEN

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ngrok 配置成功！"
    echo ""
    echo "下一步："
    echo "1. 启动 Web 应用: python web_app.py"
    echo "2. 启动 ngrok: ngrok http 5001"
    echo "3. 复制 ngrok 显示的网址即可访问"
else
    echo ""
    echo "❌ 配置失败，请检查 authtoken 是否正确"
fi

