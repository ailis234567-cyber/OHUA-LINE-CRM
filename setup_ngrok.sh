#!/bin/bash
# ngrok 快速设置脚本

echo "=" * 50
echo "🚀 ngrok 快速设置"
echo "=" * 50

# 检查是否已安装
if ! command -v ngrok &> /dev/null; then
    echo "📦 正在安装 ngrok..."
    
    # 检查是否有 Homebrew
    if command -v brew &> /dev/null; then
        brew install ngrok
    else
        echo "❌ 未找到 Homebrew"
        echo "请先安装 Homebrew: https://brew.sh"
        echo "或者手动下载 ngrok: https://ngrok.com/download"
        exit 1
    fi
else
    echo "✅ ngrok 已安装"
fi

echo ""
echo "📝 下一步："
echo "1. 访问 https://dashboard.ngrok.com/signup 注册账号"
echo "2. 获取 authtoken"
echo "3. 运行: ngrok config add-authtoken 你的token"
echo "4. 启动 Web 应用: python web_app.py"
echo "5. 运行: ngrok http 5001"
echo ""
echo "=" * 50

