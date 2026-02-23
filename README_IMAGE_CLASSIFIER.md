# 🖼️ 图像识别功能说明

## 概述

系统支持集成图像识别模型来分析商品款式，可以自动识别截图中的商品类别。

## 支持的模型

### 1. **YOLOv8** (推荐)
- **优点**: 最新版本，速度快，精度高
- **模型大小**: 
  - `yolov8n.pt` (nano) - 约 6MB，最快
  - `yolov8s.pt` (small) - 约 22MB，平衡
  - `yolov8m.pt` (medium) - 约 52MB，更准确
- **安装**: `pip install ultralytics`
- **用途**: 目标检测，可以检测和定位图片中的物体

### 2. **YOLOv5**
- **优点**: 成熟稳定，社区支持好
- **模型大小**: 
  - `yolov5n` (nano) - 约 4MB
  - `yolov5s` (small) - 约 14MB
  - `yolov5m` (medium) - 约 42MB
- **安装**: `pip install torch torchvision`
- **用途**: 目标检测

### 3. **MobileNet**
- **优点**: 非常轻量，适合移动端
- **模型大小**: 约 10MB
- **安装**: `pip install torch torchvision`
- **用途**: 图像分类

## 安装步骤

### 1. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 YOLOv8 (推荐)
pip install ultralytics

# 或安装 YOLOv5
pip install torch torchvision

# 如果需要 GPU 支持
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 配置启用

编辑 `config.yaml`:

```yaml
image_classifier:
  enabled: true  # 启用图像识别
  model_type: yolov8n  # 使用 YOLOv8 nano 版本
  model_path: null  # 使用预训练模型
  use_gpu: false  # 是否使用 GPU
```

### 3. 使用自定义模型

如果你有自己的训练模型：

```yaml
image_classifier:
  enabled: true
  model_type: yolov8  # 或 yolov5
  model_path: ./models/my_style_model.pt  # 你的模型路径
  use_gpu: true
```

## 训练自定义模型

### 使用 YOLOv8 训练

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 训练自定义数据集
model.train(
    data='path/to/your/dataset.yaml',  # 数据集配置
    epochs=100,
    imgsz=640,
    batch=16
)
```

### 数据集格式

YOLOv8 需要的数据集格式：
```
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml  # 类别定义
```

## 性能对比

| 模型 | 速度 (CPU) | 速度 (GPU) | 精度 | 模型大小 |
|------|-----------|-----------|------|----------|
| YOLOv8n | ~50ms | ~10ms | 高 | 6MB |
| YOLOv8s | ~80ms | ~15ms | 很高 | 22MB |
| YOLOv5n | ~40ms | ~8ms | 中 | 4MB |
| YOLOv5s | ~70ms | ~12ms | 高 | 14MB |
| MobileNet | ~30ms | ~5ms | 中 | 10MB |

*测试环境: MacBook Pro M1, 640x640 输入*

## 使用建议

1. **首次使用**: 建议使用 `yolov8n`，速度快，模型小
2. **需要更高精度**: 使用 `yolov8s` 或 `yolov8m`
3. **CPU 运行**: 使用 `yolov8n` 或 `yolov5n`
4. **GPU 运行**: 可以使用更大的模型获得更好效果
5. **自定义训练**: 使用自己的数据集训练，效果最好

## 输出结果

启用图像识别后，控制台会显示：

```
🎯 检测到 ID!
   📝 OCR 识别文本:
      1. 9808
      2. mtk
      ...
   📋 发现 1 个标签
      • ID: 360 | 日期: 12-10 | 编号: 9808 | 款式: nail_art (0.95) → 已保存
```

## 注意事项

1. **首次运行**: 模型会自动下载，需要网络连接
2. **模型存储**: 模型会下载到 `~/.ultralytics/` 目录
3. **性能影响**: 图像识别会增加处理时间（约 30-100ms）
4. **内存占用**: 模型加载会占用一定内存（约 100-500MB）
5. **GPU 加速**: 如果有 NVIDIA GPU，启用 GPU 可以显著加速

## 故障排除

### 问题1: 模型下载失败
**解决**: 检查网络连接，或手动下载模型文件

### 问题2: 识别速度慢
**解决**: 
- 使用更小的模型（yolov8n）
- 启用 GPU 加速
- 降低输入图像分辨率

### 问题3: 识别不准确
**解决**:
- 使用更大的模型（yolov8s/m）
- 训练自定义模型
- 调整置信度阈值

## 进阶使用

### 自定义类别映射

在 `image_classifier.py` 中修改 `classify_style` 方法，添加类别映射：

```python
def classify_style(self, image, style_categories=None):
    result = self.predict(image)
    category = result.get('category', 'unknown')
    
    # 自定义映射
    style_map = {
        'nail_art': '美甲款式',
        'nail_sticker': '贴纸款式',
        # ...
    }
    
    return style_map.get(category, category)
```

### 批量处理

可以修改代码，对已保存的图片进行批量识别：

```python
from image_classifier import ImageClassifier
import cv2

classifier = ImageClassifier('yolov8n')
for image_path in Path('screenshots').rglob('*.png'):
    image = cv2.imread(str(image_path))
    result = classifier.predict(image)
    print(f"{image_path}: {result['category']}")
```










