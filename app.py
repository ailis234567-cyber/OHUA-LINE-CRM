#!/usr/bin/env python3
"""
直播画面监控截图工具

功能：
1. 持续监控屏幕指定区域（QuickTime iPhone 镜像）
2. 使用 PaddleOCR 3.x 识别文字
3. 检测包含 "fafa" 的文本触发截图保存
4. 提取 ID 和编号进行去重
"""

import re
import time
import yaml
try:
    import mss
except ImportError:
    mss = None
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class ProductInfo:
    """商品信息"""
    product_id: str        # ID (如 "41")
    serial_number: str     # 编号 (如 "2532"，fafa 右边的数字)
    label_date: str        # 程序运行时的日期 (如 "11-17"，MM-DD 格式)
    raw_text: str          # 原始 OCR 文本
    timestamp: str         # 时间戳
    filepath: str = ""    # 保存的文件路径（可选）


class LiveMonitor:
    """直播画面监控器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化监控器"""
        self.config = self._load_config(config_path)
        self.ocr = None
        self.classifier = None  # 图像分类器
        self.save_dir = Path(self.config['storage']['save_dir'])
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件夹
        self.logs_dir = Path("./logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化图像分类器（如果启用）
        self._init_classifier()
        
        print("=" * 50)
        print("🎬 直播画面监控工具")
        print("=" * 50)
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ 配置文件 {config_path} 不存在，使用默认配置")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """默认配置"""
        return {
            'monitor_region': {
                'left': 100,
                'top': 100,
                'width': 400,
                'height': 800
            },
            'monitor': {
                'interval': 1.0,
                'trigger_keyword': 'fafa'
            },
            'ocr': {
                'use_gpu': False
            },
            'storage': {
                'save_dir': './screenshots',
                'format': 'png',
                'quality': 95
            }
        }
    
    
    def _init_classifier(self):
        """初始化图像分类器"""
        try:
            from image_classifier import create_classifier
            self.classifier = create_classifier(self.config)
            if self.classifier:
                print("✅ 图像分类器已启用")
        except ImportError:
            # 图像分类模块未安装，跳过
            pass
        except Exception as e:
            print(f"⚠️ 图像分类器初始化失败: {e}")
    
    def _init_ocr(self):
        """初始化 PaddleOCR 3.x"""
        if self.ocr is None:
            print("🔄 正在初始化 PaddleOCR...")
            try:
                from paddleocr import PaddleOCR
                # PaddleOCR 3.x 新版 API
                self.ocr = PaddleOCR(
                    use_textline_orientation=True,
                    lang='ch',
                )
                print("✅ PaddleOCR 初始化成功")
            except ImportError as e:
                print(f"❌ PaddleOCR 导入失败: {e}")
                print("请安装: pip install paddleocr paddlepaddle")
                raise
    
    def capture_region(self) -> np.ndarray:
        """截取屏幕指定区域"""
        import platform
        import subprocess
        import tempfile
        
        region = self.config['monitor_region']
        retina = self.config['storage'].get('retina', False)
        system = platform.system()
        
        # Mac 优先使用 screencapture（避免 mss 依赖）
        if system == 'Darwin' and (retina or mss is None):
            x = region['left']
            y = region['top']
            w = region['width']
            h = region['height']
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # 使用 macOS screencapture 截取 Retina 高清图
                subprocess.run([
                    'screencapture', '-R', f'{x},{y},{w},{h}', 
                    '-t', 'png', tmp_path
                ], check=True, capture_output=True)
                
                # 读取截图
                img = cv2.imread(tmp_path)
                Path(tmp_path).unlink()
                
                if img is not None:
                    return img
            except:
                # 如果失败，fallback 到普通模式
                if Path(tmp_path).exists():
                    Path(tmp_path).unlink()
        
        # Linux 或普通模式：使用 mss
        if mss is None:
            raise RuntimeError("缺少依赖 mss，请安装后再运行。")
        with mss.mss() as sct:
            monitor = {
                "left": region['left'],
                "top": region['top'],
                "width": region['width'],
                "height": region['height']
            }
            
            # 截图
            screenshot = sct.grab(monitor)
            
            # 转换为 numpy 数组 (BGRA -> BGR)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
    
    def do_ocr(self, image: np.ndarray) -> Tuple[str, List[str]]:
        """
        执行 OCR 识别
        
        Returns:
            (完整文本, 每行文本列表)
        """
        self._init_ocr()
        
        # PaddleOCR 3.x 使用 predict() 方法
        result = self.ocr.predict(image)
        
        lines = []
        # 新版返回格式: 列表，每个元素是一个字典，包含 'rec_texts', 'rec_scores' 等
        if result:
            for item in result:
                if 'rec_texts' in item and 'rec_scores' in item:
                    texts = item['rec_texts']
                    scores = item['rec_scores']
                    for text, score in zip(texts, scores):
                        # 降低置信度阈值，提高识别率（从0.5降到0.3）
                        if score > 0.3:
                            lines.append(text.strip())
        
        full_text = "\n".join(lines)
        
        # 保存OCR识别日志
        self._save_ocr_log(full_text, lines)
        
        return full_text, lines
    
    def _save_ocr_log(self, full_text: str, lines: List[str]):
        """保存OCR识别日志"""
        try:
            log_dir = Path("./logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"ocr_{datetime.now().strftime('%Y%m%d')}.log"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"\n{'='*60}\n"
            log_entry += f"[{timestamp}] OCR 识别结果\n"
            log_entry += f"{'='*60}\n"
            log_entry += f"完整文本:\n{full_text}\n\n"
            log_entry += f"逐行识别:\n"
            for i, line in enumerate(lines, 1):
                log_entry += f"  {i}. {line}\n"
            log_entry += f"{'='*60}\n"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            # 日志保存失败不影响主流程
            pass
    
    def check_trigger(self, lines: List[str]) -> bool:
        """
        检查是否触发（任意一行包含 fafa）
        
        Args:
            lines: OCR 识别的每行文本
            
        Returns:
            是否触发
        """
        keyword = self.config['monitor']['trigger_keyword'].lower()
        
        for line in lines:
            if keyword in line.lower():
                return True
        return False
    
    def extract_all_products(self, text: str, lines: List[str]) -> List[ProductInfo]:
        """
        从 OCR 文本中提取所有商品信息（支持多个标签）
        
        标签格式示例：
        ┌─────────────────┐
        │ fafa    2532    │  <- 2532 是编号
        │ れんくんママ      │
        │ ID: 41   ¥300   │  <- 41 是 ID
        └─────────────────┘
        
        注意：日期使用程序运行时的本地时间，不从标签提取
        
        Args:
            text: 完整 OCR 文本
            lines: 每行文本列表
            
        Returns:
            商品信息列表
        """
        products = []
        full_text = " ".join(lines)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 提取所有 ID: "ID: 41" 或 "ID:41" 或 "ID：41"
        id_patterns = [
            r'[Ii][Dd][：:]\s*(\d+)',
            r'[Ii][Dd]\s+(\d+)',
        ]
        
        all_ids = []
        for pattern in id_patterns:
            matches = re.findall(pattern, full_text)
            all_ids.extend(matches)
        
        # 去重并保持顺序
        seen_ids = set()
        unique_ids = []
        for id_val in all_ids:
            if id_val not in seen_ids:
                seen_ids.add(id_val)
                unique_ids.append(id_val)
        
        # 提取所有编号: 支持1-4位数字
        # 编号格式：1位数（如 1）、2位数（如 23）、3位数（如 961）、4位数（如 2532）
        # 重要：编号只在 "mtk" 或 "yeye" 右侧查找，不在 "ID" 行中查找（避免把ID误识别为编号）
        # 例如："mtk 1" 或 "yeye 123" 中的数字就是编号
        
        all_serials = []
        keyword = self.config['monitor']['trigger_keyword'].lower()
        
        # 获取所有ID值，用于排除（避免把ID误识别为编号）
        id_values = set(unique_ids)
        
        # 编号关键词列表：mtk 和 yeye
        serial_keywords = ['mtk', 'yeye']
        
        # 在所有行中查找包含 "mtk" 或 "yeye" 的行，提取编号
        # 编号可能在关键词右侧、左侧，或者相邻行（上一行或下一行）
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for serial_keyword in serial_keywords:
                if serial_keyword in line_lower:
                    keyword_pos = line_lower.find(serial_keyword)
                    if keyword_pos >= 0:
                        # 1. 首先在关键词右侧查找数字（支持1-4位）
                        after_keyword = line[keyword_pos + len(serial_keyword):]
                        numbers_after = re.findall(r'\b(\d{1,4})\b', after_keyword)
                        if numbers_after:
                            num = numbers_after[0]
                            all_serials.append(num)
                            break
                        
                        # 2. 如果右侧没有，在关键词左侧查找
                        if keyword_pos > 0:
                            before_keyword = line[:keyword_pos]
                            numbers_before = re.findall(r'\b(\d{1,4})\b', before_keyword)
                            if numbers_before:
                                num = numbers_before[-1]  # 取最后一个（最靠近关键词的）
                                all_serials.append(num)
                                break
                        
                        # 3. 如果当前行没有数字，检查上一行（编号可能在关键词上方）
                        if i > 0:
                            prev_line = lines[i-1]
                            numbers_prev = re.findall(r'\b(\d{1,4})\b', prev_line)
                            if numbers_prev:
                                num = numbers_prev[0]  # 取第一个数字
                                all_serials.append(num)
                                break
                        
                        # 4. 如果上一行也没有，检查下一行（编号可能在关键词下方）
                        if i < len(lines) - 1:
                            next_line = lines[i+1]
                            numbers_next = re.findall(r'\b(\d{1,4})\b', next_line)
                            if numbers_next:
                                num = numbers_next[0]  # 取第一个数字
                                all_serials.append(num)
                                break
        
        # 去重并保持顺序
        seen_serials = set()
        unique_serials = []
        for s in all_serials:
            # 不再排除ID值，因为编号和ID可能相同
            if s not in seen_serials:
                try:
                    num_value = int(s)
                    # 支持1-4位数字（1-9999）
                    if 1 <= num_value <= 9999:
                        seen_serials.add(s)
                        unique_serials.append(s)
                except ValueError:
                    continue
        
        # 使用程序运行时的本地日期（MM-DD 格式）
        current_date = datetime.now().strftime("%m-%d")
        
        # 为每个 ID 创建商品信息
        for i, product_id in enumerate(unique_ids):
            # 尝试配对编号（如果有多个编号，按顺序配对）
            serial_number = unique_serials[i] if i < len(unique_serials) else "unknown"
            
            products.append(ProductInfo(
                product_id=product_id,
                serial_number=serial_number,
                label_date=current_date,
                raw_text=text,
                timestamp=timestamp
            ))
        
        # 如果没有找到 ID，但有编号，也创建记录
        if not unique_ids and unique_serials:
            for serial in unique_serials:
                products.append(ProductInfo(
                    product_id="unknown",
                    serial_number=serial,
                    label_date=current_date,
                    raw_text=text,
                    timestamp=timestamp
                ))
        
        # 调试信息：显示提取结果
        if not unique_serials:
            # 没有找到编号的情况
            print(f"   🔍 调试: 编号提取结果")
            print(f"      - 找到的ID: {unique_ids}")
            print(f"      - 找到的编号: {unique_serials}")
            print(f"      - 编号关键词: {serial_keywords}")
            print(f"      - 完整文本: {text}")
            print(f"      - 所有行: {lines}")
            # 检查是否包含关键词
            for line in lines:
                line_lower = line.lower()
                for serial_keyword in serial_keywords:
                    if serial_keyword in line_lower:
                        print(f"      - 找到关键词 '{serial_keyword}' 在行: {line}")
                        keyword_pos = line_lower.find(serial_keyword)
                        after_keyword = line[keyword_pos + len(serial_keyword):]
                        print(f"      - 关键词右侧文本: '{after_keyword}'")
                        numbers_found = re.findall(r'\b(\d{1,4})\b', after_keyword)
                        print(f"      - 找到的数字: {numbers_found}")
        
        # 调试信息：显示提取结果（有ID但没有编号）
        if not unique_serials and unique_ids:
            # 有ID但没有编号的情况
            print(f"   🔍 调试: 找到 {len(unique_ids)} 个ID，但未找到编号")
            print(f"      - IDs: {unique_ids}")
            print(f"      - 完整文本: {text}")
            print(f"      - 所有行: {lines}")
        
        return products
    
    def is_duplicate(self, info: ProductInfo) -> bool:
        """
        检查是否重复（检查对应 ID/日期 文件夹里是否已有相同编号的截图）
        
        Args:
            info: 商品信息
            
        Returns:
            是否重复
        """
        # 检查对应 ID/日期 文件夹里是否存在该编号的截图（支持 jpg 和 png）
        date_folder = self.save_dir / f"ID_{info.product_id}" / info.label_date
        jpg_path = date_folder / f"{info.serial_number}.jpg"
        png_path = date_folder / f"{info.serial_number}.png"
        return jpg_path.exists() or png_path.exists()
    
    def save_screenshot(self, image: np.ndarray, info: ProductInfo) -> str:
        """
        保存截图到 ID/日期 对应的子文件夹
        
        Args:
            image: 截图
            info: 商品信息
            
        Returns:
            保存路径
        """
        # 按 ID/日期 创建子文件夹
        date_folder = self.save_dir / f"ID_{info.product_id}" / info.label_date
        date_folder.mkdir(parents=True, exist_ok=True)
        
        # 获取图片格式设置
        img_format = self.config['storage'].get('format', 'png').lower()
        
        # 直接用编号命名
        filename = f"{info.serial_number}.{img_format}"
        # 清理文件名中的非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        filepath = date_folder / filename
        
        # 保存图片
        if img_format == 'png':
            # PNG 无损压缩
            cv2.imwrite(str(filepath), image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        else:
            # JPEG 压缩
            quality = self.config['storage'].get('quality', 95)
            cv2.imwrite(str(filepath), image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        
        return str(filepath)
    
    def run_once(self) -> List[ProductInfo]:
        """
        执行一次检测（支持多标签）
        
        Returns:
            保存的商品信息列表（包含 ID、编号、日期等）
        """
        # 截图
        image = self.capture_region()
        
        # OCR
        text, lines = self.do_ocr(image)
        
        if not lines:
            return []
        
        # 检查触发
        if not self.check_trigger(lines):
            return []
        
        keyword = self.config['monitor']['trigger_keyword']
        print(f"🎯 检测到 {keyword}!")
        
        # 打印OCR识别结果（用于调试）
        print(f"   📝 OCR 识别文本:")
        for i, line in enumerate(lines, 1):
            print(f"      {i}. {line}")
        print(f"   📄 完整文本: {text}")
        
        # 提取所有商品信息
        products = self.extract_all_products(text, lines)
        if not products:
            print("⚠️ 无法提取 ID 和编号")
            print(f"   📝 OCR 识别文本:")
            for i, line in enumerate(lines, 1):
                print(f"      {i}. {line}")
            print(f"   📄 完整文本: {text}")
            print(f"   🔍 调试信息:")
            print(f"      - 触发关键词: {self.config['monitor']['trigger_keyword']}")
            # 显示提取到的所有数字
            all_numbers = re.findall(r'\d+', text)
            if all_numbers:
                print(f"      - 文本中的所有数字: {all_numbers}")
            else:
                print(f"      - 文本中未找到数字")
            return []
        
        # 如果编号是 "unknown"，也显示调试信息
        for info in products:
            if info.serial_number == "unknown":
                print(f"   ⚠️ 警告: ID {info.product_id} 的编号未识别到")
                print(f"   📝 OCR 识别文本:")
                for i, line in enumerate(lines, 1):
                    print(f"      {i}. {line}")
                # 显示提取到的所有数字
                all_numbers = re.findall(r'\d+', text)
                if all_numbers:
                    print(f"      - 文本中的所有数字: {all_numbers}")
        
        print(f"   📋 发现 {len(products)} 个标签")
        
        saved_products = []
        for info in products:
            print(f"      • ID: {info.product_id} | 日期: {info.label_date} | 编号: {info.serial_number}", end="")
            
            # 去重检查
            if self.is_duplicate(info):
                print(f" → 跳过(重复)")
                continue
            
            # 图像识别（如果启用）
            if self.classifier:
                try:
                    style_result = self.classifier.predict(image)
                    info.style_category = style_result.get('category', 'unknown')
                    style_confidence = style_result.get('confidence', 0.0)
                    if info.style_category != 'unknown':
                        print(f" | 款式: {info.style_category} ({style_confidence:.2f})", end="")
                except Exception as e:
                    print(f" | 图像识别失败: {e}", end="")
            
            # 保存
            filepath = self.save_screenshot(image, info)
            info.filepath = filepath  # 保存文件路径到对象中
            saved_products.append(info)
            print(f" → 已保存")
        
        if saved_products:
            print(f"💾 本次保存 {len(saved_products)} 张截图")
        
        return saved_products
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        duration = timedelta(seconds=int(seconds))
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        
        if duration.days > 0:
            return f"{duration.days}天 {hours}小时 {minutes}分钟 {secs}秒"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟 {secs}秒"
        elif minutes > 0:
            return f"{minutes}分钟 {secs}秒"
        else:
            return f"{secs}秒"
    
    def _save_log(self, start_time: datetime, end_time: datetime, 
                  detect_count: int, saved_count: int, saved_ids: dict):
        """保存运行日志"""
        duration = (end_time - start_time).total_seconds()
        duration_str = self._format_duration(duration)
        
        # 日志文件名：按日期
        log_filename = start_time.strftime("%Y-%m-%d") + ".log"
        log_path = self.logs_dir / log_filename
        
        # 构建日志内容
        log_content = []
        log_content.append("=" * 50)
        log_content.append(f"📅 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_content.append(f"📅 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_content.append(f"⏱️ 运行时长: {duration_str}")
        log_content.append(f"🔍 检测次数: {detect_count}")
        log_content.append(f"💾 保存截图: {saved_count} 张")
        
        if saved_ids:
            log_content.append(f"📁 保存详情:")
            for id_val, count in sorted(saved_ids.items()):
                log_content.append(f"   • ID_{id_val}: {count} 张")
        
        log_content.append("=" * 50)
        log_content.append("")
        
        # 追加到日志文件
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(log_content))
        
        print(f"📝 日志已保存: {log_path}")
    
    def run(self):
        """持续运行监控"""
        interval = self.config['monitor']['interval']
        
        print(f"\n📍 监控区域: {self.config['monitor_region']}")
        print(f"⏱️ 检测间隔: {interval} 秒")
        print(f"🔑 触发关键词: {self.config['monitor']['trigger_keyword']}")
        print(f"📂 保存目录: {self.save_dir.absolute()}")
        print(f"📁 截图按 ID 分类到子文件夹")
        print(f"📝 日志目录: {self.logs_dir.absolute()}")
        print(f"\n🚀 开始监控... (按 Ctrl+C 停止)\n")
        
        start_time = datetime.now()
        count = 0
        saved_count = 0
        saved_ids = {}  # 记录每个 ID 保存了几张
            
        try:
            while True:
                count += 1
                
                try:
                    results = self.run_once()
                    saved_count += len(results)
                    
                    # 统计每个 ID 保存的数量
                    for info in results:
                        id_val = info.product_id
                        saved_ids[id_val] = saved_ids.get(id_val, 0) + 1
                        
                except Exception as e:
                    print(f"❌ 检测出错: {e}")
                
                # 显示状态
                if count % 10 == 0:
                    print(f"📊 已检测 {count} 次，保存 {saved_count} 张")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n\n🛑 监控已停止")
            print(f"📊 总计检测 {count} 次，保存 {saved_count} 张截图")
            print(f"⏱️ 运行时长: {self._format_duration(duration)}")
            
            # 保存日志
            self._save_log(start_time, end_time, count, saved_count, saved_ids)


def select_region():
    """
    辅助功能：选择监控区域
    截取全屏并让用户确认区域坐标
    """
    print("📸 截取全屏以确定监控区域...")
    
    import platform
    import subprocess
    import tempfile

    system = platform.system()

    if system == 'Darwin':
        # macOS 使用 screencapture
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(['screencapture', '-t', 'png', tmp_path], check=True, capture_output=True)
            img = cv2.imread(tmp_path)
            Path(tmp_path).unlink()
            if img is None:
                raise RuntimeError("无法读取全屏截图")
        finally:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
    else:
        if mss is None:
            raise RuntimeError("缺少依赖 mss，请安装后再运行。")
        with mss.mss() as sct:
            # 截取主显示器
            screenshot = sct.grab(sct.monitors[1])
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 保存全屏截图
    cv2.imwrite("fullscreen.jpg", img)
    print(f"✅ 全屏截图已保存: fullscreen.jpg")
    print(f"   屏幕尺寸: {img.shape[1]} x {img.shape[0]}")
    print("\n请用图片编辑器打开 fullscreen.jpg，")
    print("找到 QuickTime 窗口的位置，记录左上角坐标和宽高，")
    print("然后更新 config.yaml 中的 monitor_region 配置。")


def test_ocr():
    """测试 OCR 功能"""
    print("🧪 测试 OCR 功能...")
    
    monitor = LiveMonitor()
    
    print("📸 截取监控区域...")
    image = monitor.capture_region()
    
    # 保存测试截图
    cv2.imwrite("test_capture.jpg", image)
    print(f"✅ 测试截图已保存: test_capture.jpg")
    
    print("🔍 执行 OCR...")
    text, lines = monitor.do_ocr(image)
    
    print("\n" + "=" * 40)
    print("OCR 识别结果:")
    print("=" * 40)
    for i, line in enumerate(lines, 1):
        print(f"{i}. {line}")
    print("=" * 40)
    
    # 检测触发
    triggered = monitor.check_trigger(lines)
    print(f"\n触发检测: {'✅ 是' if triggered else '❌ 否'}")
    
    if triggered:
        products = monitor.extract_all_products(text, lines)
        if products:
            print(f"\n📋 发现 {len(products)} 个标签:")
            for i, info in enumerate(products, 1):
                print(f"   {i}. ID: {info.product_id} | 日期: {info.label_date} | 编号: {info.serial_number}")
        else:
            print("⚠️ 未能提取商品信息")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "select":
            # 选择区域
            select_region()
        elif cmd == "test":
            # 测试 OCR
            test_ocr()
        elif cmd == "help":
            print("用法:")
            print("  python app.py          # 开始监控")
            print("  python app.py select   # 截取全屏，用于确定监控区域")
            print("  python app.py test     # 测试 OCR 识别")
            print("  python app.py help     # 显示帮助")
        else:
            print(f"未知命令: {cmd}")
            print("使用 'python app.py help' 查看帮助")
    else:
        # 正常运行
        monitor = LiveMonitor()
        monitor.run()


if __name__ == "__main__":
    main()

