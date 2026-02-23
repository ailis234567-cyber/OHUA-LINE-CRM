#!/usr/bin/env python3
"""
图像分类/识别模块
支持使用 YOLOv8、YOLOv5 或其他轻量级模型进行款式识别
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import torch


class ImageClassifier:
    """图像分类器"""
    
    def __init__(self, model_type: str = 'yolov8n', model_path: Optional[str] = None, use_gpu: bool = False):
        """
        初始化图像分类器
        
        Args:
            model_type: 模型类型 ('yolov8n', 'yolov5s', 'mobilenet', 'resnet')
            model_path: 自定义模型路径（可选）
            use_gpu: 是否使用GPU
        """
        self.model_type = model_type
        self.model_path = model_path
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model = None
        self.device = 'cuda' if self.use_gpu else 'cpu'
        
        print(f"🖼️  初始化图像分类器: {model_type}")
        print(f"   设备: {self.device}")
        
    def load_model(self):
        """加载模型"""
        try:
            if self.model_type.startswith('yolov8'):
                from ultralytics import YOLO
                if self.model_path:
                    self.model = YOLO(self.model_path)
                else:
                    # 使用预训练模型
                    model_name = 'yolov8n.pt'  # nano版本，最轻量
                    if self.model_type == 'yolov8s':
                        model_name = 'yolov8s.pt'
                    elif self.model_type == 'yolov8m':
                        model_name = 'yolov8m.pt'
                    self.model = YOLO(model_name)
                print(f"✅ YOLOv8 模型加载成功")
                
            elif self.model_type.startswith('yolov5'):
                import torch.hub
                if self.model_path:
                    self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
                else:
                    model_name = 'yolov5s'  # small版本
                    if self.model_type == 'yolov5n':
                        model_name = 'yolov5n'
                    elif self.model_type == 'yolov5m':
                        model_name = 'yolov5m'
                    self.model = torch.hub.load('ultralytics/yolov5', model_name)
                self.model.to(self.device)
                print(f"✅ YOLOv5 模型加载成功")
                
            elif self.model_type == 'mobilenet':
                # 使用 torchvision 的 MobileNet
                import torchvision.models as models
                self.model = models.mobilenet_v3_small(pretrained=True)
                self.model.eval()
                self.model.to(self.device)
                print(f"✅ MobileNet 模型加载成功")
                
            else:
                raise ValueError(f"不支持的模型类型: {self.model_type}")
                
        except ImportError as e:
            print(f"❌ 模型库导入失败: {e}")
            print(f"   请安装: pip install ultralytics torch torchvision")
            raise
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def predict(self, image: np.ndarray) -> Dict:
        """
        对图像进行预测
        
        Args:
            image: 输入图像 (numpy array, BGR格式)
            
        Returns:
            预测结果字典，包含：
            - category: 类别名称
            - confidence: 置信度
            - bbox: 边界框（如果使用检测模型）
        """
        if self.model is None:
            self.load_model()
        
        try:
            if self.model_type.startswith('yolov8'):
                # YOLOv8 推理
                results = self.model(image, verbose=False)
                result = results[0]
                
                # 获取检测结果
                if len(result.boxes) > 0:
                    # 取置信度最高的检测结果
                    box = result.boxes[0]
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    
                    return {
                        'category': class_name,
                        'confidence': confidence,
                        'bbox': bbox,
                        'all_detections': [
                            {
                                'category': self.model.names[int(box.cls[i])],
                                'confidence': float(box.conf[i]),
                                'bbox': box.xyxy[i].cpu().numpy().tolist()
                            }
                            for i in range(len(box))
                        ]
                    }
                else:
                    return {
                        'category': 'unknown',
                        'confidence': 0.0,
                        'bbox': None,
                        'all_detections': []
                    }
                    
            elif self.model_type.startswith('yolov5'):
                # YOLOv5 推理
                results = self.model(image)
                detections = results.pandas().xyxy[0]
                
                if len(detections) > 0:
                    # 取置信度最高的检测结果
                    best = detections.iloc[0]
                    return {
                        'category': best['name'],
                        'confidence': float(best['confidence']),
                        'bbox': [best['xmin'], best['ymin'], best['xmax'], best['ymax']],
                        'all_detections': [
                            {
                                'category': row['name'],
                                'confidence': float(row['confidence']),
                                'bbox': [row['xmin'], row['ymin'], row['xmax'], row['ymax']]
                            }
                            for _, row in detections.iterrows()
                        ]
                    }
                else:
                    return {
                        'category': 'unknown',
                        'confidence': 0.0,
                        'bbox': None,
                        'all_detections': []
                    }
                    
            elif self.model_type == 'mobilenet':
                # MobileNet 分类（需要预处理）
                import torchvision.transforms as transforms
                from PIL import Image
                
                transform = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                       std=[0.229, 0.224, 0.225])
                ])
                
                # 转换 BGR 到 RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
                input_tensor = transform(pil_image).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(input_tensor)
                    probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                    top_prob, top_idx = torch.topk(probabilities, 1)
                    
                    # 使用 ImageNet 类别名称（实际使用时需要替换为你的类别）
                    import json
                    try:
                        with open('imagenet_classes.json', 'r') as f:
                            class_names = json.load(f)
                        category = class_names[top_idx.item()]
                    except:
                        category = f"class_{top_idx.item()}"
                    
                    return {
                        'category': category,
                        'confidence': float(top_prob[0]),
                        'bbox': None,
                        'all_detections': []
                    }
                    
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            return {
                'category': 'error',
                'confidence': 0.0,
                'bbox': None,
                'all_detections': []
            }
    
    def classify_style(self, image: np.ndarray, style_categories: Optional[List[str]] = None) -> str:
        """
        识别款式类别（简化接口）
        
        Args:
            image: 输入图像
            style_categories: 款式类别列表（可选，用于映射）
            
        Returns:
            款式名称
        """
        result = self.predict(image)
        category = result.get('category', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        # 如果提供了类别映射，进行映射
        if style_categories:
            # 这里可以根据实际需求进行类别映射
            # 例如：将模型输出的类别映射到你的款式名称
            pass
        
        return category


def create_classifier(config: dict) -> Optional[ImageClassifier]:
    """
    根据配置创建分类器
    
    Args:
        config: 配置字典，包含 'image_classifier' 部分
        
    Returns:
        ImageClassifier 实例，如果未启用则返回 None
    """
    classifier_config = config.get('image_classifier', {})
    
    if not classifier_config.get('enabled', False):
        return None
    
    model_type = classifier_config.get('model_type', 'yolov8n')
    model_path = classifier_config.get('model_path', None)
    use_gpu = classifier_config.get('use_gpu', False)
    
    try:
        classifier = ImageClassifier(
            model_type=model_type,
            model_path=model_path,
            use_gpu=use_gpu
        )
        return classifier
    except Exception as e:
        print(f"⚠️ 图像分类器初始化失败: {e}")
        print(f"   将跳过图像分类功能")
        return None







