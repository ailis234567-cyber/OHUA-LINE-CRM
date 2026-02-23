#!/usr/bin/env python3
"""
Linux 截图适配模块
用于替换 Mac 的 Retina 截图功能
"""

import subprocess
import cv2
import numpy as np
from pathlib import Path


def capture_region_linux(region):
    """
    Linux 截图函数
    使用 xdotool 或 scrot 进行截图
    """
    left = region['left']
    top = region['top']
    width = region['width']
    height = region['height']
    
    # 方法1: 使用 scrot（推荐）
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        # scrot 截图命令
        subprocess.run([
            'scrot',
            '-a', f'{left},{top},{width},{height}',
            tmp_path
        ], check=True, capture_output=True)
        
        # 读取图片
        img = cv2.imread(tmp_path)
        Path(tmp_path).unlink()
        
        if img is not None:
            return img
    except:
        pass
    
    # 方法2: 使用 import（PIL/Pillow）
    try:
        from PIL import ImageGrab
        bbox = (left, top, left + width, top + height)
        img_pil = ImageGrab.grab(bbox=bbox)
        img = np.array(img_pil)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img
    except:
        pass
    
    # 方法3: 使用 mss（跨平台，但需要 X11）
    try:
        import mss
        with mss.mss() as sct:
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
    except:
        pass
    
    raise Exception("无法截图：请安装 scrot 或确保有 X11 环境")


# 在 Linux 上可以替换 app.py 中的 capture_region 方法
# 或者修改 app.py 自动检测系统并使用相应的方法

