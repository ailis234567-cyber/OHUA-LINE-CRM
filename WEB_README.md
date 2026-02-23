# 🌐 直播监控截图 Web 应用

提供图片搜索和查看功能的 Web 界面，客户可以通过 ID 或编号搜索自己的截图。

## ✨ 功能

- 🔍 **智能搜索**：通过 ID 或编号搜索图片
- 📊 **实时统计**：显示总图片数和 ID 数量
- 🖼️ **图片预览**：点击图片查看大图
- 📱 **响应式设计**：支持手机和电脑访问
- 🎨 **现代化界面**：美观的渐变设计和动画效果

## 🚀 启动方式

### 方法 1：使用启动脚本
```bash
./start_web.sh
```

### 方法 2：手动启动
```bash
cd /Users/huihui/live-monitor
source venv/bin/activate
python web_app.py
```

## 📖 使用说明

1. **启动服务器**
   - 运行 `./start_web.sh` 或 `python web_app.py`
   - 服务器将在 `http://localhost:5000` 启动

2. **访问网站**
   - 在浏览器中打开 `http://localhost:5000`
   - 如果是局域网访问，使用 `http://你的IP地址:5000`

3. **搜索图片**
   - 在搜索框输入 ID（如：125）或编号（如：2362）
   - 点击"搜索"按钮或按回车键
   - 查看搜索结果

4. **查看大图**
   - 点击任意图片卡片
   - 在弹窗中查看大图和详细信息
   - 点击关闭按钮或按 ESC 键关闭

## 🔧 API 接口

### 搜索图片
```
GET /api/search?q=搜索关键词
```

返回：
```json
{
  "query": "125",
  "count": 5,
  "results": [
    {
      "id": "125",
      "date": "11-19",
      "filename": "2362.png",
      "serial_number": "2362",
      "path": "ID_125/11-19/2362.png",
      "modified": "2024-11-19 18:30:15"
    }
  ]
}
```

### 获取统计信息
```
GET /api/stats
```

返回：
```json
{
  "total_images": 50,
  "total_ids": 10,
  "id_counts": {
    "125": 5,
    "131": 3,
    ...
  }
}
```

### 获取图片
```
GET /api/images/ID_125/11-19/2362.png
```

### 上传图片（可选）
```
POST /api/upload
Form Data:
  - file: 图片文件
  - id: 产品ID
  - serial: 编号
```

## 📁 目录结构

```
live-monitor/
├── web_app.py          # Flask Web 应用
├── templates/
│   └── index.html     # 前端页面
├── static/
│   └── css/
│       └── style.css  # 样式文件
└── screenshots/       # 截图目录（自动扫描）
    ├── ID_125/
    │   └── 11-19/
    │       └── 2362.png
    └── ...
```

## 🌍 局域网访问

如果需要让局域网内其他设备访问：

1. 查找本机 IP 地址：
   ```bash
   # Mac/Linux
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   ```

2. 其他设备访问：`http://你的IP地址:5000`

## 🔒 安全建议

如果需要在公网访问，建议：

1. 使用 Nginx 反向代理
2. 添加 HTTPS 支持
3. 添加身份验证
4. 限制访问 IP

## 📝 注意事项

- 图片路径基于 `config.yaml` 中的 `save_dir` 配置
- 自动扫描 `screenshots/` 目录下的所有图片
- 支持 PNG、JPG、JPEG 格式
- 图片按修改时间倒序排列（最新的在前）

## 🐛 故障排除

### 无法访问网站
- 检查防火墙设置
- 确认端口 5000 未被占用
- 检查 Flask 是否已安装：`pip install flask`

### 搜索无结果
- 确认 screenshots 目录下有图片
- 检查图片路径是否正确
- 查看浏览器控制台错误信息

### 图片无法显示
- 检查图片文件是否存在
- 确认文件权限
- 查看服务器日志

