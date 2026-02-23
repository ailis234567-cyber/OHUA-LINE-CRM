# 🚀 Linux VPS 部署指南

## 📦 打包部署

### 在本地 Mac 上打包

```bash
cd /Users/huihui/live-monitor
bash deploy/deploy.sh
```

这会创建一个 `live-monitor-vps.tar.gz` 压缩包。

---

## 📤 上传到 VPS

### 方法 1: 使用 scp

```bash
scp live-monitor-vps.tar.gz root@你的VPS_IP:/opt/
```

### 方法 2: 使用 rsync

```bash
rsync -avz live-monitor-vps/ root@你的VPS_IP:/opt/live-monitor/
```

---

## 🔧 在 VPS 上安装

### 1. SSH 连接到 VPS

```bash
ssh root@你的VPS_IP
```

### 2. 解压文件

```bash
cd /opt
tar -xzf live-monitor-vps.tar.gz
cd live-monitor-vps
```

### 3. 运行安装脚本

```bash
bash install.sh
```

安装脚本会自动：
- ✅ 安装 Python 3 和依赖
- ✅ 创建虚拟环境
- ✅ 安装 Python 包
- ✅ 创建 systemd 服务
- ✅ 配置自动启动

---

## ⚙️ 配置

### 1. 配置监控区域

```bash
cd /opt/live-monitor
source venv/bin/activate

# 截取全屏确定区域（需要 X11 环境）
python app.py select

# 编辑配置文件
nano config.yaml
```

**注意**：Linux 上需要设置：
- `retina: false`（Linux 不需要 Retina 模式）
- 根据实际屏幕设置监控区域坐标

### 2. 配置 Web 服务端口（可选）

如果需要修改端口，编辑 `web_app.py` 最后一行：
```python
app.run(host='0.0.0.0', port=5001, debug=False)  # 生产环境建议 debug=False
```

---

## 🚀 启动服务

### 启动监控服务

```bash
systemctl start live-monitor
systemctl enable live-monitor  # 开机自启
systemctl status live-monitor  # 查看状态
```

### 启动 Web 服务

```bash
systemctl start live-monitor-web
systemctl enable live-monitor-web  # 开机自启
systemctl status live-monitor-web  # 查看状态
```

---

## 🌐 访问 Web 界面

### 本地访问

```bash
# 在 VPS 上
curl http://localhost:5001
```

### 外网访问

1. **开放防火墙端口**

   Ubuntu/Debian:
   ```bash
   ufw allow 5001/tcp
   ```

   CentOS/RHEL:
   ```bash
   firewall-cmd --permanent --add-port=5001/tcp
   firewall-cmd --reload
   ```

2. **访问网址**

   ```
   http://你的VPS_IP:5001
   ```

---

## 📊 服务管理

### 查看服务状态

```bash
systemctl status live-monitor
systemctl status live-monitor-web
```

### 启动/停止/重启

```bash
# 监控服务
systemctl start live-monitor
systemctl stop live-monitor
systemctl restart live-monitor

# Web 服务
systemctl start live-monitor-web
systemctl stop live-monitor-web
systemctl restart live-monitor-web
```

### 查看日志

```bash
# 监控服务日志
journalctl -u live-monitor -f

# Web 服务日志
journalctl -u live-monitor-web -f

# 查看最近 100 行
journalctl -u live-monitor -n 100
```

---

## 🔍 故障排除

### 1. 无法截图

**问题**：Linux 需要 X11 图形环境

**解决**：
```bash
# 安装 Xvfb（虚拟显示）
apt-get install xvfb  # Ubuntu/Debian
yum install xorg-x11-server-Xvfb  # CentOS/RHEL

# 启动虚拟显示
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# 或者使用真实的 X11 服务器
```

### 2. Web 服务无法访问

**检查步骤**：
1. 检查服务是否运行：`systemctl status live-monitor-web`
2. 检查端口是否监听：`netstat -tlnp | grep 5001`
3. 检查防火墙：`ufw status` 或 `firewall-cmd --list-all`
4. 查看日志：`journalctl -u live-monitor-web -f`

### 3. OCR 识别失败

**检查**：
- PaddleOCR 是否正确安装
- 查看日志了解具体错误
- 检查是否有足够的磁盘空间

### 4. 权限问题

**解决**：
```bash
# 确保目录权限正确
chown -R root:root /opt/live-monitor
chmod +x /opt/live-monitor/venv/bin/*
```

---

## 🔒 安全建议

### 1. 使用 Nginx 反向代理（推荐）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 添加 HTTPS

使用 Let's Encrypt：
```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### 3. 限制访问 IP（可选）

在 Nginx 配置中添加：
```nginx
allow 你的IP;
deny all;
```

---

## 📝 目录结构

```
/opt/live-monitor/
├── app.py              # 主程序
├── web_app.py          # Web 服务
├── config.yaml         # 配置文件
├── requirements.txt    # Python 依赖
├── venv/              # 虚拟环境
├── screenshots/       # 截图目录
├── logs/              # 日志目录
├── templates/        # Web 模板
└── static/           # 静态文件
```

---

## 🔄 更新应用

```bash
# 1. 停止服务
systemctl stop live-monitor
systemctl stop live-monitor-web

# 2. 备份配置
cp config.yaml config.yaml.bak

# 3. 更新文件（上传新版本）

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. 恢复配置
cp config.yaml.bak config.yaml

# 6. 启动服务
systemctl start live-monitor
systemctl start live-monitor-web
```

---

## 📞 需要帮助？

查看日志了解详细错误：
```bash
journalctl -u live-monitor -n 50
journalctl -u live-monitor-web -n 50
```

