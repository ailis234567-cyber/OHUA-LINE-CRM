#!/bin/bash
# 打包部署脚本 - 在本地 Mac 上运行

set -e

echo "=========================================="
echo "📦 打包直播监控工具"
echo "=========================================="
echo ""

# 创建打包目录
PACKAGE_NAME="live-monitor-vps"
PACKAGE_DIR="./$PACKAGE_NAME"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

echo "📋 复制文件..."

# 复制核心文件
cp app.py $PACKAGE_DIR/
cp config.yaml $PACKAGE_DIR/
cp requirements.txt $PACKAGE_DIR/
cp README.md $PACKAGE_DIR/

# 复制 Web 相关文件
cp web_app.py $PACKAGE_DIR/
mkdir -p $PACKAGE_DIR/templates
cp templates/index.html $PACKAGE_DIR/templates/
mkdir -p $PACKAGE_DIR/static/css
cp static/css/style.css $PACKAGE_DIR/static/css/

# 复制部署文件
cp deploy/install.sh $PACKAGE_DIR/
chmod +x $PACKAGE_DIR/install.sh

# 创建部署说明
cat > $PACKAGE_DIR/DEPLOY.md << 'EOF'
# 🚀 Linux VPS 部署指南

## 快速部署

### 1. 上传文件到 VPS

```bash
# 使用 scp 上传
scp -r live-monitor-vps root@你的VPS_IP:/opt/

# 或使用 rsync
rsync -avz live-monitor-vps/ root@你的VPS_IP:/opt/live-monitor/
```

### 2. SSH 连接到 VPS

```bash
ssh root@你的VPS_IP
cd /opt/live-monitor
```

### 3. 运行安装脚本

```bash
bash install.sh
```

### 4. 配置监控区域

```bash
cd /opt/live-monitor
source venv/bin/activate
python app.py select  # 截取全屏
# 编辑 config.yaml 设置监控区域坐标
```

### 5. 启动服务

```bash
# 启动监控服务
systemctl start live-monitor
systemctl enable live-monitor  # 开机自启

# 启动 Web 服务
systemctl start live-monitor-web
systemctl enable live-monitor-web  # 开机自启
```

### 6. 访问 Web 界面

打开浏览器访问：`http://你的VPS_IP:5001`

## 服务管理

```bash
# 查看状态
systemctl status live-monitor
systemctl status live-monitor-web

# 启动/停止/重启
systemctl start live-monitor
systemctl stop live-monitor
systemctl restart live-monitor

# 查看日志
journalctl -u live-monitor -f
journalctl -u live-monitor-web -f
```

## 防火墙配置

如果无法访问 Web 界面，需要开放端口：

```bash
# Ubuntu/Debian (ufw)
ufw allow 5001/tcp

# CentOS/RHEL (firewalld)
firewall-cmd --permanent --add-port=5001/tcp
firewall-cmd --reload
```

## 注意事项

1. **Linux 截图**：Linux 使用 X11 截图，需要确保有图形环境
2. **Retina 模式**：Linux 不需要 Retina 模式，config.yaml 中应设置为 `retina: false`
3. **权限**：确保有截图权限
4. **依赖**：安装脚本会自动安装所需依赖

## 故障排除

### 无法截图
- 检查是否有 X11 环境
- 检查 DISPLAY 环境变量
- 可能需要安装 xvfb 用于虚拟显示

### Web 服务无法访问
- 检查防火墙设置
- 检查服务是否运行：`systemctl status live-monitor-web`
- 查看日志：`journalctl -u live-monitor-web -f`

### OCR 识别失败
- 检查 PaddleOCR 是否正确安装
- 查看日志了解具体错误
EOF

# 创建 .tar.gz 压缩包
echo "📦 创建压缩包..."
tar -czf ${PACKAGE_NAME}.tar.gz $PACKAGE_DIR

echo ""
echo "=========================================="
echo "✅ 打包完成！"
echo "=========================================="
echo ""
echo "📦 打包文件: ${PACKAGE_NAME}.tar.gz"
echo ""
echo "📝 部署步骤："
echo "1. 上传到 VPS:"
echo "   scp ${PACKAGE_NAME}.tar.gz root@你的VPS_IP:/opt/"
echo ""
echo "2. SSH 连接到 VPS:"
echo "   ssh root@你的VPS_IP"
echo ""
echo "3. 解压并安装:"
echo "   cd /opt"
echo "   tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "   cd ${PACKAGE_NAME}"
echo "   bash install.sh"
echo ""
echo "详细说明请查看: $PACKAGE_DIR/DEPLOY.md"
echo ""

