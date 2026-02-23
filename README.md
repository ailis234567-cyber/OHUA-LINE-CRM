# 🎬 直播画面监控截图工具

监控 QuickTime iPhone 镜像画面，自动识别并保存商品截图

## ✨ 功能

- 📸 使用 `mss` 高效截取屏幕指定区域
- 🔍 PaddleOCR 3.x 识别画面文字
- 🎯 检测包含 "fafa" 的内容自动触发保存
- 🔢 自动提取商品 ID 和编号
- ⏭️ 基于 ID+编号 自动去重，避免重复保存

## 📦 安装

```bash
cd ~/live-monitor

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 🚀 使用

### 1️⃣ 确定监控区域

首先需要确定 QuickTime 窗口在屏幕上的位置：

```bash
python app.py select
```

这会截取全屏并保存为 `fullscreen.jpg`，打开查看 QuickTime 窗口的位置。

### 2️⃣ 配置区域坐标

编辑 `config.yaml`，设置监控区域：

```yaml
monitor_region:
  left: 100      # QuickTime 窗口左边距
  top: 100       # QuickTime 窗口上边距
  width: 400     # 窗口宽度
  height: 800    # 窗口高度
```

### 3️⃣ 测试 OCR

```bash
python app.py test
```

检查 OCR 是否正常工作，查看识别结果。

### 4️⃣ 开始监控

```bash
python app.py
```

程序会持续监控，当检测到 "fafa" 时自动截图保存。

按 `Ctrl+C` 停止。

## ⚙️ 配置说明

`config.yaml` 配置项：

```yaml
# 监控区域
monitor_region:
  left: 100       # X 坐标
  top: 100        # Y 坐标
  width: 400      # 宽度
  height: 800     # 高度

# 监控设置
monitor:
  interval: 1.0           # 检测间隔（秒）
  trigger_keyword: "fafa" # 触发关键词

# OCR 设置
ocr:
  use_gpu: false  # 是否使用 GPU

# 存储设置
storage:
  save_dir: "./screenshots"  # 保存目录
  quality: 95                # 图片质量
```

## 📂 输出

截图保存在 `screenshots/` 目录：

```
screenshots/
├── 20231125_143052_ID001_001.jpg      # 截图
├── 20231125_143052_ID001_001.txt      # OCR 文本
├── 20231125_143105_ID002_002.jpg
├── 20231125_143105_ID002_002.txt
└── history.txt                         # 去重记录
```

## 🔧 命令

```bash
python app.py          # 开始监控
python app.py select   # 截取全屏确定区域
python app.py test     # 测试 OCR
python app.py help     # 显示帮助
```

## ❓ 常见问题

### Q: 如何获取 QuickTime 窗口坐标？

1. 运行 `python app.py select` 截取全屏
2. 用预览或其他图片软件打开 `fullscreen.jpg`
3. 查看 QuickTime 窗口的左上角坐标和尺寸
4. 更新 `config.yaml`

### Q: OCR 识别不准确？

- 确保画面清晰，文字足够大
- 调整监控区域，只包含关键内容
- 检查 PaddleOCR 版本是否为 3.x

### Q: 如何修改触发关键词？

编辑 `config.yaml` 中的 `trigger_keyword`

