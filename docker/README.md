# Docker 部署指南

## 📋 概述

这个 Docker 配置提供了两种部署方案：

### 方案 1：仅 Web 服务（推荐用于群晖 NAS）

**适用场景：**
- 在群晖 NAS 上运行 Web 服务，查看和搜索截图
- 截图功能在本地 Mac/PC 运行，通过共享文件夹同步到 NAS

**优点：**
- ✅ 轻量级，资源占用少
- ✅ 不需要图形界面
- ✅ 适合 NAS 环境

### 方案 2：完整功能（需要特殊配置）

**适用场景：**
- 在 Linux 服务器上运行完整功能
- 需要 X11 转发或虚拟显示服务器

**限制：**
- ❌ 无法在标准 Docker 容器中直接截取屏幕
- ❌ 需要复杂的 X11 配置

---

## 🚀 快速开始（方案 1：仅 Web 服务）

### 1. 准备文件

确保以下文件存在：
```
live-monitor/
├── web_app.py
├── config.yaml
├── templates/
│   └── index.html
├── static/
│   └── css/
│       └── style.css
└── screenshots/  (可以挂载外部目录)
```

### 2. 在群晖 NAS 上部署

#### 方法 A：使用 Docker Compose（推荐）

1. 将整个项目上传到 NAS（或通过 Git 克隆）

2. 进入 `docker` 目录：
```bash
cd /volume1/docker/live-monitor/docker
```

3. 启动服务：
```bash
docker-compose up -d
```

4. 访问 Web 界面：
```
http://你的NAS IP:5001
```

#### 方法 B：使用群晖 Docker 图形界面

1. 在群晖 DSM 中打开 **Docker** 应用

2. 选择 **映像** → **新增** → **从文件添加**

3. 构建镜像：
```bash
cd /volume1/docker/live-monitor/docker
docker build -f Dockerfile.web -t live-monitor-web ..
```

4. 创建容器：
   - 映像：`live-monitor-web`
   - 端口映射：`5001:5001`
   - 卷挂载：
     - `/volume1/docker/live-monitor/screenshots` → `/app/screenshots`
     - `/volume1/docker/live-monitor/config.yaml` → `/app/config.yaml`

5. 启动容器

### 3. 配置截图同步

#### 选项 A：使用共享文件夹

1. 在 NAS 上创建共享文件夹：`/volume1/screenshots`

2. 在本地 Mac/PC 上：
   - 将截图保存目录设置为 NAS 共享文件夹
   - 或定期同步本地 `screenshots/` 到 NAS

#### 选项 B：使用 rsync 自动同步

在本地 Mac/PC 上创建同步脚本：

```bash
#!/bin/bash
# sync_to_nas.sh

SOURCE_DIR="$HOME/live-monitor/screenshots"
NAS_DIR="user@nas-ip:/volume1/screenshots"

rsync -av --delete "$SOURCE_DIR/" "$NAS_DIR/"
```

添加到 crontab（每 5 分钟同步一次）：
```bash
*/5 * * * * /path/to/sync_to_nas.sh
```

---

## 🔧 配置说明

### 环境变量

- `DEBUG`: 设置为 `True` 启用调试模式（默认：`False`）

### 端口

- 默认端口：`5001`
- 可在 `docker-compose.yml` 中修改

### 数据持久化

所有截图数据存储在挂载的 `screenshots/` 目录中，确保：
- 容器重启不会丢失数据
- 可以从外部访问和管理截图

---

## 📝 注意事项

### 1. 屏幕截图功能

**Docker 容器无法直接截取屏幕**，因为：
- Docker 容器是隔离的环境
- 无法访问宿主机的显示服务器
- 需要 X11 转发（复杂且不稳定）

**解决方案：**
- 在本地 Mac/PC 运行截图程序
- 通过共享文件夹或 rsync 同步到 NAS
- 在 NAS 上运行 Web 服务查看

### 2. GUI 界面

GUI (`gui.py`) 需要图形界面，不适合 Docker：
- 使用命令行方式配置
- 或通过 Web 界面管理（如果添加管理功能）

### 3. 性能考虑

- PaddleOCR 在 CPU 模式下运行较慢
- 如果 NAS 性能较低，建议：
  - 降低 OCR 频率
  - 使用更轻量的 OCR 方案
  - 或仅在本地进行 OCR 处理

---

## 🐛 故障排除

### Web 服务无法启动

1. 检查端口是否被占用：
```bash
docker logs live-monitor-web
```

2. 检查配置文件：
```bash
docker exec -it live-monitor-web cat /app/config.yaml
```

### 无法访问截图

1. 检查卷挂载：
```bash
docker exec -it live-monitor-web ls -la /app/screenshots
```

2. 检查文件权限：
```bash
# 在 NAS 上
chmod -R 755 /volume1/screenshots
```

### 性能问题

1. 查看容器资源使用：
```bash
docker stats live-monitor-web
```

2. 考虑增加资源限制或优化配置

---

## 📚 相关文档

- [群晖 Docker 使用指南](https://kb.synology.com/zh-cn/DSM/help/Docker/docker_desc)
- [Docker Compose 文档](https://docs.docker.com/compose/)

