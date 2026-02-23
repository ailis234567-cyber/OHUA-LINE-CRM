#!/bin/bash
# Linux VPS 部署安装脚本

set -e

echo "=========================================="
echo "🚀 直播监控截图工具 - Linux VPS 安装"
echo "=========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  请使用 root 用户运行此脚本"
    echo "   或使用: sudo bash install.sh"
    exit 1
fi

# 检测 Linux 发行版
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ 无法检测 Linux 发行版"
    exit 1
fi

echo "📦 检测到系统: $OS $VER"
echo ""

# 安装 Python 3 和 pip
echo "📦 安装 Python 3 和依赖..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git
    apt-get install -y libgl1-mesa-glx libglib2.0-0
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum install -y python3 python3-pip git
    yum install -y mesa-libGL glib2
else
    echo "⚠️  未识别的发行版，请手动安装 Python 3"
fi

# 创建应用目录
APP_DIR="/opt/live-monitor"
echo "📁 创建应用目录: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# 复制文件
echo "📋 复制应用文件..."
# 这里假设文件已经在这个目录，或者从 git 克隆
# 如果是打包文件，需要解压

# 创建虚拟环境
echo "🔧 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建配置文件（如果不存在）
if [ ! -f config.yaml ]; then
    echo "📝 创建默认配置文件..."
    cat > config.yaml << 'EOF'
# 屏幕监控截图配置

# 监控区域设置
monitor_region:
  left: 0
  top: 0
  width: 800
  height: 600

# 监控设置
monitor:
  interval: 1.0
  trigger_keyword: "ID"

# OCR 设置
ocr:
  use_gpu: false

# 存储设置
storage:
  save_dir: "./screenshots"
  format: "png"
  quality: 95
  retina: false  # Linux 通常不需要
EOF
fi

# 创建必要的目录
mkdir -p screenshots logs

# 创建 systemd 服务文件
echo "⚙️  创建 systemd 服务..."
cat > /etc/systemd/system/live-monitor.service << EOF
[Unit]
Description=直播监控截图工具
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建 Web 服务文件
cat > /etc/systemd/system/live-monitor-web.service << EOF
[Unit]
Description=直播监控截图 Web 服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo ""
echo "1. 配置监控区域："
echo "   cd $APP_DIR"
echo "   source venv/bin/activate"
echo "   python app.py select  # 截取全屏确定区域"
echo "   # 然后编辑 config.yaml 设置监控区域坐标"
echo ""
echo "2. 启动监控服务："
echo "   systemctl start live-monitor"
echo "   systemctl status live-monitor"
echo ""
echo "3. 启动 Web 服务："
echo "   systemctl start live-monitor-web"
echo "   systemctl status live-monitor-web"
echo ""
echo "4. 设置开机自启："
echo "   systemctl enable live-monitor"
echo "   systemctl enable live-monitor-web"
echo ""
echo "5. 查看日志："
echo "   journalctl -u live-monitor -f"
echo "   journalctl -u live-monitor-web -f"
echo ""
echo "6. 访问 Web 界面："
echo "   http://你的VPS_IP:5001"
echo ""

