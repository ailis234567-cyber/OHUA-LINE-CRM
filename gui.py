#!/usr/bin/env python3
"""
直播画面监控工具 - GUI 界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import yaml
import subprocess
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from app import LiveMonitor


class RegionSelector:
    """交互式区域选择器"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        
        # 创建全屏选择窗口
        self.selector = tk.Toplevel()
        self.selector.attributes('-fullscreen', True)
        self.selector.attributes('-alpha', 0.3)  # 半透明
        self.selector.attributes('-topmost', True)
        self.selector.configure(bg='black')
        self.selector.overrideredirect(True)
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(
            self.selector,
            highlightthickness=0,
            bg='black',
            cursor='crosshair'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.canvas.bind('<Button-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)
        self.selector.bind('<Escape>', self.cancel)
        self.selector.bind('<Return>', self.confirm)
        
        # 提示文字
        self.canvas.create_text(
            self.selector.winfo_screenwidth() // 2,
            50,
            text="点击并拖拽选择监控区域 | ESC 取消 | Enter 确认",
            fill='white',
            font=('Arial', 16, 'bold'),
            tags='hint'
        )
        
        # 坐标显示
        self.coord_text = self.canvas.create_text(
            self.selector.winfo_screenwidth() // 2,
            100,
            text="",
            fill='yellow',
            font=('Arial', 12),
            tags='coords'
        )
    
    def on_button_press(self, event):
        """鼠标按下"""
        self.start_x = event.x
        self.start_y = event.y
        # 删除之前的选择框和确认提示
        self.canvas.delete('selection')
        self.canvas.delete('confirm')
    
    def on_move(self, event):
        """鼠标移动"""
        if self.start_x is None or self.start_y is None:
            return
        
        # 删除之前的选择框
        self.canvas.delete('selection')
        
        # 计算选择区域
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        # 绘制选择框
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline='red',
            width=3,
            tags='selection'
        )
        
        # 更新坐标显示
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        self.canvas.itemconfig(
            self.coord_text,
            text=f"X: {x1}  Y: {y1}  宽: {width}  高: {height}"
        )
        
        self.current_rect = (x1, y1, x2, y2)
    
    def on_button_release(self, event):
        """鼠标释放"""
        if self.current_rect:
            # 显示确认对话框
            x1, y1, x2, y2 = self.current_rect
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 在画布上显示确认提示
            self.canvas.create_text(
                self.selector.winfo_screenwidth() // 2,
                self.selector.winfo_screenheight() - 100,
                text=f"已选择区域: X={x1}, Y={y1}, 宽={width}, 高={height} | 按 Enter 确认，ESC 取消",
                fill='lime',
                font=('Arial', 14, 'bold'),
                tags='confirm'
            )
    
    def confirm(self, event=None):
        """确认选择"""
        if not self.current_rect:
            self.cancel()
            return
        
        x1, y1, x2, y2 = self.current_rect
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # 更新 GUI 中的配置
        self.gui_app.left_var.set(str(left))
        self.gui_app.top_var.set(str(top))
        self.gui_app.width_var.set(str(width))
        self.gui_app.height_var.set(str(height))
        
        # 保存配置
        if self.gui_app.save_config_to_dict():
            self.gui_app.log(f"✅ 区域已选择: X={left}, Y={top}, 宽={width}, 高={height}")
            messagebox.showinfo("成功", f"监控区域已设置:\nX: {left}\nY: {top}\n宽: {width}\n高: {height}")
        
        self.selector.destroy()
    
    def cancel(self, event=None):
        """取消选择"""
        self.selector.destroy()
        self.gui_app.log("❌ 区域选择已取消")


class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 直播画面监控工具")
        self.root.geometry("800x700")
        
        self.monitor = None
        self.monitoring = False
        self.monitor_thread = None
        self.config_path = "config.yaml"
        
        # 加载配置
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 更新状态
        self.update_status()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {
                'monitor_region': {'left': 34, 'top': 34, 'width': 340, 'height': 666},
                'monitor': {'interval': 1.0, 'trigger_keyword': 'ID'},
                'storage': {'save_dir': './screenshots', 'format': 'png', 'retina': True}
            }
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            return False
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ 配置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 监控区域
        ttk.Label(config_frame, text="监控区域:").grid(row=0, column=0, sticky=tk.W, pady=2)
        region_frame = ttk.Frame(config_frame)
        region_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(region_frame, text="X:").grid(row=0, column=0)
        self.left_var = tk.StringVar(value=str(self.config['monitor_region']['left']))
        ttk.Entry(region_frame, textvariable=self.left_var, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(region_frame, text="Y:").grid(row=0, column=2, padx=(10, 0))
        self.top_var = tk.StringVar(value=str(self.config['monitor_region']['top']))
        ttk.Entry(region_frame, textvariable=self.top_var, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Label(region_frame, text="宽:").grid(row=0, column=4, padx=(10, 0))
        self.width_var = tk.StringVar(value=str(self.config['monitor_region']['width']))
        ttk.Entry(region_frame, textvariable=self.width_var, width=8).grid(row=0, column=5, padx=2)
        
        ttk.Label(region_frame, text="高:").grid(row=0, column=6, padx=(10, 0))
        self.height_var = tk.StringVar(value=str(self.config['monitor_region']['height']))
        ttk.Entry(region_frame, textvariable=self.height_var, width=8).grid(row=0, column=7, padx=2)
        
        # 检测间隔
        ttk.Label(config_frame, text="检测间隔(秒):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_var = tk.StringVar(value=str(self.config['monitor']['interval']))
        ttk.Entry(config_frame, textvariable=self.interval_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 触发关键词
        ttk.Label(config_frame, text="触发关键词:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.keyword_var = tk.StringVar(value=self.config['monitor']['trigger_keyword'])
        ttk.Entry(config_frame, textvariable=self.keyword_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 保存目录
        ttk.Label(config_frame, text="保存目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        dir_frame = ttk.Frame(config_frame)
        dir_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        self.save_dir_var = tk.StringVar(value=self.config['storage']['save_dir'])
        ttk.Entry(dir_frame, textvariable=self.save_dir_var, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="浏览", command=self.browse_dir).grid(row=0, column=1, padx=5)
        
        # 图片格式
        ttk.Label(config_frame, text="图片格式:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.format_var = tk.StringVar(value=self.config['storage'].get('format', 'png'))
        format_frame = ttk.Frame(config_frame)
        format_frame.grid(row=4, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(format_frame, text="PNG (高清)", variable=self.format_var, value="png").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(format_frame, text="JPG (压缩)", variable=self.format_var, value="jpg").grid(row=0, column=1, padx=5)
        
        # Retina 模式
        self.retina_var = tk.BooleanVar(value=self.config['storage'].get('retina', True))
        ttk.Checkbutton(config_frame, text="Retina 高清模式 (Mac)", variable=self.retina_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ 开始监控", command=self.start_monitoring, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ 停止监控", command=self.stop_monitoring, state=tk.DISABLED, width=15)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="🧪 测试 OCR", command=self.test_ocr, width=15).grid(row=0, column=2, padx=5)
        
        ttk.Button(control_frame, text="📸 选择区域", command=self.select_region, width=15).grid(row=0, column=3, padx=5)
        
        # Web 服务控制区域
        web_frame = ttk.LabelFrame(main_frame, text="🌐 Web 服务", padding="10")
        web_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        web_control_frame = ttk.Frame(web_frame)
        web_control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.web_start_btn = ttk.Button(web_control_frame, text="🚀 启动 Web 服务", command=self.start_web_server, width=18)
        self.web_start_btn.grid(row=0, column=0, padx=5)
        
        self.web_stop_btn = ttk.Button(web_control_frame, text="⏹️ 停止 Web 服务", command=self.stop_web_server, state=tk.DISABLED, width=18)
        self.web_stop_btn.grid(row=0, column=1, padx=5)
        
        self.ngrok_start_btn = ttk.Button(web_control_frame, text="🌐 启动 ngrok", command=self.start_ngrok, state=tk.DISABLED, width=18)
        self.ngrok_start_btn.grid(row=0, column=2, padx=5)
        
        self.ngrok_stop_btn = ttk.Button(web_control_frame, text="⏹️ 停止 ngrok", command=self.stop_ngrok, state=tk.DISABLED, width=18)
        self.ngrok_stop_btn.grid(row=0, column=3, padx=5)
        
        # 网址显示区域
        url_frame = ttk.Frame(web_frame)
        url_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(url_frame, text="在线网址:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.url_var = tk.StringVar(value="未启动")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50, state="readonly")
        url_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        self.copy_url_btn = ttk.Button(url_frame, text="📋 复制", command=self.copy_url, state=tk.DISABLED, width=10)
        self.copy_url_btn.grid(row=0, column=2, padx=5)
        
        self.open_url_btn = ttk.Button(url_frame, text="🔗 打开", command=self.open_url, state=tk.DISABLED, width=10)
        self.open_url_btn.grid(row=0, column=3, padx=5)
        
        # 添加打开 ngrok 控制台按钮
        self.open_ngrok_console_btn = ttk.Button(url_frame, text="📊 控制台", command=self.open_ngrok_console, state=tk.DISABLED, width=10)
        self.open_ngrok_console_btn.grid(row=0, column=4, padx=5)
        
        url_frame.columnconfigure(1, weight=1)
        
        # Web 服务状态
        self.web_status_label = ttk.Label(web_frame, text="Web 服务: 未运行", foreground="gray")
        self.web_status_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="📊 运行状态", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="状态: 未运行", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.detect_label = ttk.Label(status_frame, text="检测次数: 0")
        self.detect_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.saved_label = ttk.Label(status_frame, text="保存截图: 0 张")
        self.saved_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.time_label = ttk.Label(status_frame, text="运行时长: 00:00:00")
        self.time_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="📝 运行日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 运行状态变量
        self.detect_count = 0
        self.saved_count = 0
        self.start_time = None
        
        # Web 服务器和 ngrok 相关
        self.web_process = None
        self.ngrok_process = None
        self.web_running = False
        self.ngrok_running = False
        self.ngrok_url = ""
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self):
        """更新状态显示"""
        if self.monitoring:
            self.status_label.config(text="状态: 🟢 运行中", foreground="green")
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                hours, remainder = divmod(elapsed.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.time_label.config(text=f"运行时长: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.status_label.config(text="状态: ⚪ 未运行", foreground="gray")
            self.time_label.config(text="运行时长: 00:00:00")
        
        self.detect_label.config(text=f"检测次数: {self.detect_count}")
        self.saved_label.config(text=f"保存截图: {self.saved_count} 张")
        
        # 每秒更新一次
        self.root.after(1000, self.update_status)
        
        # 检查进程状态
        if self.web_process and self.web_process.poll() is not None:
            # Web 进程已结束
            if self.web_running:
                # 尝试读取错误信息
                error_info = ""
                try:
                    if self.web_process.stderr:
                        # 非阻塞读取错误输出
                        import select
                        if sys.platform != 'win32':
                            if select.select([self.web_process.stderr], [], [], 0)[0]:
                                error_data = self.web_process.stderr.read(1024)
                                if error_data:
                                    error_info = error_data.decode('utf-8', errors='ignore').strip()
                except Exception as e:
                    pass
                
                self.web_running = False
                self.web_start_btn.config(state=tk.NORMAL)
                self.web_stop_btn.config(state=tk.DISABLED)
                self.web_status_label.config(text="Web 服务: ❌ 已停止", foreground="red")
                
                if error_info:
                    # 提取关键错误信息
                    error_lines = error_info.split('\n')
                    key_errors = []
                    for line in error_lines:
                        if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'cannot', 'module']):
                            key_errors.append(line.strip())
                    
                    if key_errors:
                        error_msg = '\n'.join(key_errors[:3])  # 最多显示3行
                        self.log(f"⚠️ Web 服务器意外停止: {error_msg}")
                    else:
                        self.log("⚠️ Web 服务器意外停止")
                else:
                    self.log("⚠️ Web 服务器意外停止")
                
                if self.ngrok_running:
                    self.stop_ngrok()
        
        if self.ngrok_process and self.ngrok_process.poll() is not None:
            # ngrok 进程已结束
            if self.ngrok_running:
                # 读取错误信息
                try:
                    if self.ngrok_process.stderr:
                        # 尝试读取错误输出
                        import select
                        import sys
                        if sys.platform != 'win32':
                            # Unix 系统可以使用 select
                            if select.select([self.ngrok_process.stderr], [], [], 0)[0]:
                                error_msg = self.ngrok_process.stderr.read(1024).strip()
                                if error_msg:
                                    self.log(f"❌ ngrok 错误: {error_msg}")
                                    # 检查常见错误
                                    if 'authtoken' in error_msg.lower() or 'authentication' in error_msg.lower():
                                        self.root.after(0, lambda: messagebox.showerror(
                                            "ngrok 配置错误",
                                            f"ngrok 认证失败\n\n错误: {error_msg}\n\n请检查 authtoken:\nngrok config add-authtoken 你的token"
                                        ))
                except:
                    pass
                
                self.log("⚠️ ngrok 意外停止")
                self.handle_ngrok_stopped()
    
    def browse_dir(self):
        """选择保存目录"""
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if directory:
            self.save_dir_var.set(directory)
    
    def select_region(self):
        """交互式选择监控区域"""
        self.log("📸 启动区域选择工具...")
        self.log("提示: 点击并拖拽鼠标选择监控区域，按 ESC 取消")
        
        # 创建区域选择窗口
        RegionSelector(self.root, self)
    
    def test_ocr(self):
        """测试 OCR"""
        self.log("🧪 开始测试 OCR...")
        try:
            # 保存当前配置
            if not self.save_config_to_dict():
                return
            
            monitor = LiveMonitor(self.config_path)
            self.log("📸 截取监控区域...")
            image = monitor.capture_region()
            
            self.log("🔍 执行 OCR 识别...")
            text, lines = monitor.do_ocr(image)
            
            self.log(f"✅ OCR 识别完成，共识别 {len(lines)} 行")
            self.log("识别结果:")
            for i, line in enumerate(lines[:10], 1):  # 只显示前10行
                self.log(f"  {i}. {line}")
            if len(lines) > 10:
                self.log(f"  ... (还有 {len(lines) - 10} 行)")
            
            # 检测触发
            triggered = monitor.check_trigger(lines)
            self.log(f"触发检测: {'✅ 是' if triggered else '❌ 否'}")
            
            if triggered:
                products = monitor.extract_all_products(text, lines)
                if products:
                    self.log(f"📋 发现 {len(products)} 个标签:")
                    for i, info in enumerate(products, 1):
                        self.log(f"  {i}. ID: {info.product_id} | 日期: {info.label_date} | 编号: {info.serial_number}")
            
            messagebox.showinfo("测试完成", f"OCR 测试完成！\n识别了 {len(lines)} 行文字")
        except Exception as e:
            self.log(f"❌ 测试失败: {e}")
            messagebox.showerror("错误", f"OCR 测试失败: {e}")
    
    def save_config_to_dict(self):
        """将界面配置保存到字典"""
        try:
            self.config['monitor_region'] = {
                'left': int(self.left_var.get()),
                'top': int(self.top_var.get()),
                'width': int(self.width_var.get()),
                'height': int(self.height_var.get())
            }
            self.config['monitor'] = {
                'interval': float(self.interval_var.get()),
                'trigger_keyword': self.keyword_var.get()
            }
            self.config['storage'] = {
                'save_dir': self.save_dir_var.get(),
                'format': self.format_var.get(),
                'retina': self.retina_var.get()
            }
            return self.save_config()
        except ValueError as e:
            messagebox.showerror("错误", f"配置值无效: {e}\n请检查输入的数字")
            return False
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        # 保存配置
        if not self.save_config_to_dict():
            return
        
        self.monitoring = True
        self.detect_count = 0
        self.saved_count = 0
        self.start_time = datetime.now()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log("🚀 开始监控...")
        self.log(f"📍 监控区域: {self.config['monitor_region']}")
        self.log(f"⏱️ 检测间隔: {self.config['monitor']['interval']} 秒")
        self.log(f"🔑 触发关键词: {self.config['monitor']['trigger_keyword']}")
        
        # 在新线程中运行监控
        self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.log("🛑 监控已停止")
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.log(f"📊 总计检测 {self.detect_count} 次，保存 {self.saved_count} 张截图")
            self.log(f"⏱️ 运行时长: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def run_monitor(self):
        """运行监控（在单独线程中）"""
        try:
            monitor = LiveMonitor(self.config_path)
            interval = self.config['monitor']['interval']
            
            while self.monitoring:
                self.detect_count += 1
                
                try:
                    results = monitor.run_once()
                    if results:
                        self.saved_count += len(results)
                        self.log(f"💾 成功保存 {len(results)} 张截图:")
                        for info in results:
                            self.log(f"   ✅ ID: {info.product_id} | 编号: {info.serial_number} | 日期: {info.label_date}")
                            self.log(f"      保存路径: {info.filepath}")
                except Exception as e:
                    self.log(f"❌ 检测出错: {e}")
                
                # 每10次显示一次状态
                if self.detect_count % 10 == 0:
                    self.log(f"📊 已检测 {self.detect_count} 次，保存 {self.saved_count} 张")
                
                import time
                time.sleep(interval)
                
        except Exception as e:
            self.log(f"❌ 监控出错: {e}")
            self.monitoring = False
            self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
    
    def start_web_server(self):
        """启动 Web 服务器"""
        if self.web_running:
            return
        
        self.log("🚀 启动 Web 服务器...")
        
        try:
            # 获取 Python 解释器路径
            python_exe = sys.executable
            script_path = Path(__file__).parent / "web_app.py"
            
            # 启动 Web 应用
            self.web_process = subprocess.Popen(
                [python_exe, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.web_running = True
            self.web_start_btn.config(state=tk.DISABLED)
            self.web_stop_btn.config(state=tk.NORMAL)
            self.ngrok_start_btn.config(state=tk.NORMAL)
            self.web_status_label.config(text="Web 服务: 🟢 运行中 (端口 5001)", foreground="green")
            
            # 等待一下检查进程是否启动成功
            import time
            time.sleep(1)
            
            # 检查进程是否还在运行
            if self.web_process.poll() is not None:
                # 进程已退出，读取错误信息
                try:
                    stderr_output = self.web_process.stderr.read()
                    error_msg = ""
                    if stderr_output:
                        error_msg = stderr_output.strip()
                    
                    # 检查是否是端口占用错误
                    if "Address already in use" in error_msg or "端口" in error_msg:
                        # 尝试查找占用端口的进程
                        port_info = ""
                        try:
                            result = subprocess.run(['lsof', '-i', ':5001'], 
                                                  capture_output=True, text=True, timeout=2)
                            if result.returncode == 0 and result.stdout:
                                lines = result.stdout.strip().split('\n')
                                if len(lines) > 1:
                                    process_info = lines[1].split()
                                    if len(process_info) > 1:
                                        pid = process_info[1]
                                        cmd = process_info[0] if process_info[0] else '未知'
                                        port_info = f"\n\n占用进程: {cmd} (PID: {pid})\n停止命令: kill {pid}"
                        except:
                            pass
                        
                        full_error = f"端口 5001 已被占用{port_info}\n\n解决方案:\n1. 停止占用进程: kill {pid if port_info else 'PID'}\n2. 修改 web_app.py 中的端口号\n3. 使用其他端口启动"
                        self.log(f"❌ Web 服务器启动失败: 端口被占用{port_info}")
                        messagebox.showerror("Web 服务器启动失败 - 端口被占用", full_error)
                    else:
                        self.log(f"❌ Web 服务器启动失败: {error_msg}")
                        messagebox.showerror("Web 服务器启动失败", 
                                            f"错误信息:\n{error_msg}\n\n可能的原因:\n1. Flask 未安装\n2. 端口被占用\n3. 代码错误")
                    
                    self.web_running = False
                    self.web_start_btn.config(state=tk.NORMAL)
                    self.web_stop_btn.config(state=tk.DISABLED)
                    self.web_status_label.config(text="Web 服务: ❌ 启动失败", foreground="red")
                    return
                except Exception as e:
                    self.log(f"❌ 读取错误信息失败: {e}")
                    self.web_running = False
                    self.web_start_btn.config(state=tk.NORMAL)
                    self.web_stop_btn.config(state=tk.DISABLED)
                    self.web_status_label.config(text="Web 服务: ❌ 启动失败", foreground="red")
                    return
            
            self.log("✅ Web 服务器已启动 (http://localhost:5001)")
            
            # 监控进程输出和错误
            threading.Thread(target=self.monitor_web_output, daemon=True).start()
            threading.Thread(target=self.monitor_web_errors, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ 启动 Web 服务器失败: {e}")
            messagebox.showerror("错误", f"启动 Web 服务器失败: {e}")
            self.web_running = False
    
    def stop_web_server(self):
        """停止 Web 服务器"""
        if not self.web_running and not self.web_process:
            return
        
        self.log("⏹️ 停止 Web 服务器...")
        
        if self.web_process:
            try:
                # 先尝试优雅终止
                self.web_process.terminate()
                try:
                    self.web_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # 如果3秒内没有终止，强制杀死
                    self.log("⚠️ 进程未响应，强制终止...")
                    self.web_process.kill()
                    self.web_process.wait(timeout=2)
            except ProcessLookupError:
                # 进程已经不存在
                pass
            except Exception as e:
                self.log(f"⚠️ 停止进程时出错: {e}")
                # 尝试强制杀死
                try:
                    if self.web_process.poll() is None:
                        self.web_process.kill()
                except:
                    pass
            finally:
                self.web_process = None
        
        self.web_running = False
        self.web_start_btn.config(state=tk.NORMAL)
        self.web_stop_btn.config(state=tk.DISABLED)
        self.ngrok_start_btn.config(state=tk.DISABLED)
        self.web_status_label.config(text="Web 服务: ⚪ 未运行", foreground="gray")
        
        # 如果 ngrok 在运行，也停止它
        if self.ngrok_running:
            self.stop_ngrok()
        
        self.log("✅ Web 服务器已停止")
    
    def monitor_web_output(self):
        """监控 Web 服务器输出"""
        if not self.web_process:
            return
        
        try:
            for line in iter(self.web_process.stdout.readline, ''):
                if not line:
                    break
                line = line.strip()
                if line:
                    # 显示重要信息
                    if 'Running on' in line or '访问地址' in line:
                        self.log(f"📱 {line}")
        except:
            pass
    
    def monitor_web_errors(self):
        """监控 Web 服务器错误输出"""
        if not self.web_process:
            return
        
        error_lines = []
        try:
            # 读取所有错误输出
            while True:
                line = self.web_process.stderr.readline()
                if not line:
                    # 检查进程是否已退出
                    if self.web_process.poll() is not None:
                        break
                    import time
                    time.sleep(0.1)
                    continue
                
                line = line.strip()
                if line:
                    error_lines.append(line)
                    self.log(f"❌ Web 错误: {line}")
            
            # 如果进程已退出且有错误，显示详细错误信息
            if self.web_process.poll() is not None and error_lines:
                error_text = '\n'.join(error_lines[:10])  # 最多显示10行
                
                # 检查常见错误并给出提示
                error_str = '\n'.join(error_lines)
                if 'ModuleNotFoundError' in error_str or 'No module named' in error_str:
                    if 'flask' in error_str.lower():
                        self.root.after(0, lambda: messagebox.showerror(
                            "Flask 未安装",
                            f"Flask 未安装\n\n错误信息:\n{error_text}\n\n请运行:\npip install flask"
                        ))
                    else:
                        module_name = error_str.split("'")[1] if "'" in error_str else "未知模块"
                        self.root.after(0, lambda m=module_name, e=error_text: messagebox.showerror(
                            f"缺少模块: {m}",
                            f"缺少模块: {m}\n\n错误信息:\n{e}\n\n请运行:\npip install {m}"
                        ))
                elif 'Address already in use' in error_str or 'port' in error_str.lower():
                    self.root.after(0, lambda e=error_text: messagebox.showerror(
                        "端口被占用",
                        f"端口 5001 已被占用\n\n错误信息:\n{e}\n\n解决方案:\n1. 关闭占用端口的程序\n2. 修改 web_app.py 中的端口号"
                    ))
                elif error_lines:
                    # 其他错误，显示前几行
                    self.root.after(0, lambda e=error_text: messagebox.showerror(
                        "Web 服务器启动失败",
                        f"Web 服务器启动失败\n\n错误信息:\n{e}"
                    ))
        except Exception as e:
            self.log(f"❌ 监控 Web 错误时出错: {e}")
    
    def start_ngrok(self):
        """启动 ngrok"""
        if self.ngrok_running or not self.web_running:
            return
        
        self.log("🌐 启动 ngrok...")
        
        try:
            # 检查 ngrok 是否安装
            result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
            if result.returncode != 0:
                messagebox.showerror("错误", "ngrok 未安装\n\n请先安装: brew install ngrok\n然后配置: ngrok config add-authtoken 你的token")
                return
            
            # 检查 ngrok 是否已配置 authtoken
            config_check = subprocess.run(['ngrok', 'config', 'check'], capture_output=True, text=True)
            if config_check.returncode != 0:
                error_msg = config_check.stderr or config_check.stdout
                self.log(f"⚠️ ngrok 配置检查失败: {error_msg}")
                messagebox.showerror(
                    "ngrok 未配置", 
                    f"ngrok 未配置 authtoken\n\n错误信息: {error_msg}\n\n请先配置:\nngrok config add-authtoken 你的token\n\n获取 token: https://dashboard.ngrok.com/get-started/your-authtoken"
                )
                return
            
            # 启动 ngrok
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', '5001'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.ngrok_running = True
            self.ngrok_start_btn.config(state=tk.DISABLED)
            self.ngrok_stop_btn.config(state=tk.NORMAL)
            self.open_ngrok_console_btn.config(state=tk.NORMAL)  # 启用控制台按钮
            
            self.log("✅ ngrok 已启动，正在获取网址...")
            self.log("💡 提示: 如果无法自动获取网址，可点击'控制台'按钮查看")
            
            # 监控 ngrok 输出和错误
            threading.Thread(target=self.monitor_ngrok_output, daemon=True).start()
            threading.Thread(target=self.monitor_ngrok_errors, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ 启动 ngrok 失败: {e}")
            messagebox.showerror("错误", f"启动 ngrok 失败: {e}")
            self.ngrok_running = False
    
    def stop_ngrok(self):
        """停止 ngrok"""
        if not self.ngrok_running and not self.ngrok_process:
            return
        
        self.log("⏹️ 停止 ngrok...")
        
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                try:
                    self.ngrok_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.log("⚠️ ngrok 进程未响应，强制终止...")
                    self.ngrok_process.kill()
                    self.ngrok_process.wait(timeout=2)
            except ProcessLookupError:
                pass
            except Exception as e:
                self.log(f"⚠️ 停止 ngrok 时出错: {e}")
                try:
                    if self.ngrok_process.poll() is None:
                        self.ngrok_process.kill()
                except:
                    pass
            finally:
                self.ngrok_process = None
        
        self.ngrok_running = False
        self.ngrok_start_btn.config(state=tk.NORMAL)
        self.ngrok_stop_btn.config(state=tk.DISABLED)
        
        self.ngrok_url = ""
        self.url_var.set("未启动")
        self.copy_url_btn.config(state=tk.DISABLED)
        self.open_url_btn.config(state=tk.DISABLED)
        self.open_ngrok_console_btn.config(state=tk.DISABLED)
        
        self.log("✅ ngrok 已停止")
    
    def monitor_ngrok_errors(self):
        """监控 ngrok 错误输出"""
        if not self.ngrok_process:
            return
        
        try:
            for line in iter(self.ngrok_process.stderr.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                if line:
                    # 记录错误信息
                    self.log(f"⚠️ ngrok 错误: {line}")
                    
                    # 检查 ERR_NGROK_334 错误（URL已被占用）
                    if 'ERR_NGROK_334' in line:
                        self.root.after(0, lambda: messagebox.showerror(
                            "ngrok 错误 (ERR_NGROK_334)",
                            "ngrok 隧道 URL 已被占用\n\n"
                            "错误说明：\n"
                            "您尝试使用的 ngrok URL 已经被另一个正在运行的隧道占用。\n"
                            "一个 URL 同时只能用于一个隧道会话。\n\n"
                            "解决方案：\n"
                            "1. 停止当前正在运行的 ngrok 隧道\n"
                            "   - 在 ngrok 控制台 (http://127.0.0.1:4040) 中停止现有隧道\n"
                            "   - 或使用命令: pkill ngrok\n"
                            "2. 等待几秒后重新启动\n"
                            "3. 或者使用不同的 URL/hostname\n\n"
                            "提示：\n"
                            "可以在 ngrok Dashboard 查看当前活动的隧道状态\n"
                            "https://dashboard.ngrok.com/\n\n"
                            f"错误详情:\n{line}"
                        ))
                    # 检查认证错误
                    elif 'authtoken' in line.lower() or 'authentication' in line.lower():
                        self.root.after(0, lambda: messagebox.showerror(
                            "ngrok 配置错误",
                            f"ngrok 认证失败\n\n错误: {line}\n\n请检查 authtoken 是否正确配置:\nngrok config add-authtoken 你的token"
                        ))
                    # 检查端口占用
                    elif 'port' in line.lower() and 'in use' in line.lower():
                        self.root.after(0, lambda: messagebox.showerror(
                            "端口被占用",
                            f"端口被占用\n\n错误: {line}\n\n请检查端口 5001 是否被其他程序占用"
                        ))
        except Exception as e:
            self.log(f"⚠️ 监控 ngrok 错误时出错: {e}")
    
    def monitor_ngrok_output(self):
        """监控 ngrok 输出，提取网址"""
        if not self.ngrok_process:
            return
        
        try:
            import time
            import urllib.request
            import json
            
            # 等待一下让 ngrok 启动
            time.sleep(2)
            
            # 检查进程是否还在运行
            if self.ngrok_process.poll() is not None:
                # 进程已退出，读取错误信息
                try:
                    stderr_output = self.ngrok_process.stderr.read()
                    if stderr_output:
                        error_msg = stderr_output.strip()
                        self.log(f"❌ ngrok 启动失败: {error_msg}")
                        self.root.after(0, lambda: messagebox.showerror(
                            "ngrok 启动失败",
                            f"ngrok 进程已退出\n\n错误信息: {error_msg}\n\n可能的原因:\n1. authtoken 未配置或错误\n2. 网络连接问题\n3. ngrok 服务异常"
                        ))
                        self.root.after(0, self.handle_ngrok_stopped)
                except:
                    pass
                return
            
            # 尝试从 ngrok API 获取网址（优先方法）
            max_retries = 15  # 增加重试次数
            url_found = False
            
            for i in range(max_retries):
                try:
                    # 尝试访问 ngrok 本地 API
                    request = urllib.request.Request('http://127.0.0.1:4040/api/tunnels')
                    response = urllib.request.urlopen(request, timeout=3)
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if data.get('tunnels'):
                        # 优先选择 https 隧道
                        for tunnel in data['tunnels']:
                            if tunnel.get('proto') == 'https':
                                url = tunnel.get('public_url', '')
                                if url:
                                    self.ngrok_url = url
                                    self.root.after(0, self.update_ngrok_url)
                                    self.log(f"✅ 在线网址: {url}")
                                    url_found = True
                                    return
                        
                        # 如果没有 https，使用 http
                        for tunnel in data['tunnels']:
                            if tunnel.get('proto') == 'http':
                                url = tunnel.get('public_url', '')
                                if url:
                                    self.ngrok_url = url
                                    self.root.after(0, self.update_ngrok_url)
                                    self.log(f"✅ 在线网址: {url}")
                                    url_found = True
                                    return
                    
                except urllib.error.URLError as e:
                    # API 还未就绪，继续重试
                    if i < max_retries - 1:
                        time.sleep(1)
                    else:
                        self.log(f"⚠️ ngrok API 未响应 (http://127.0.0.1:4040)，尝试其他方法...")
                except Exception as e:
                    self.log(f"⚠️ 获取 ngrok API 数据时出错: {e}")
                    if i < max_retries - 1:
                        time.sleep(1)
            
            # 如果 API 获取失败，尝试从输出中解析
            if not url_found:
                self.log("⚠️ 无法从 API 获取网址，尝试从输出解析...")
                
                # ngrok 的输出格式可能包括:
                # - https://xxx.ngrok-free.app
                # - https://xxx.ngrok.io
                # - Forwarding  https://xxx.ngrok-free.app -> http://localhost:5001
                patterns = [
                    r'https://[a-zA-Z0-9\-]+\.ngrok-free\.app',
                    r'https://[a-zA-Z0-9\-]+\.ngrok\.io',
                    r'https://[a-zA-Z0-9\-]+\.ngrok[^ ]*',
                ]
                
                # 读取一些输出行
                import select
                import sys
                
                if sys.platform != 'win32':
                    # Unix 系统可以使用 select
                    for _ in range(20):  # 最多读取20行
                        if select.select([self.ngrok_process.stdout], [], [], 0.5)[0]:
                            line = self.ngrok_process.stdout.readline()
                            if not line:
                                break
                            
                            line = line.strip()
                            self.log(f"📝 ngrok 输出: {line}")
                            
                            # 尝试匹配各种 URL 格式
                            for pattern in patterns:
                                match = re.search(pattern, line)
                                if match:
                                    url = match.group(0)
                                    self.ngrok_url = url
                                    self.root.after(0, self.update_ngrok_url)
                                    self.log(f"✅ 从输出解析到网址: {url}")
                                    return
                        else:
                            time.sleep(0.5)
                
                # 如果还是没找到，显示提示
                self.log("⚠️ 无法自动获取 ngrok 网址")
                self.root.after(0, lambda: messagebox.showwarning(
                    "无法获取网址",
                    "无法自动获取 ngrok 网址\n\n请手动访问:\nhttp://127.0.0.1:4040\n\n查看 ngrok 控制台获取网址"
                ))
                    
        except Exception as e:
            self.log(f"⚠️ 获取 ngrok 网址时出错: {e}")
            import traceback
            self.log(f"详细错误: {traceback.format_exc()}")
    
    def handle_ngrok_stopped(self):
        """处理 ngrok 停止"""
        self.ngrok_running = False
        self.ngrok_start_btn.config(state=tk.NORMAL)
        self.ngrok_stop_btn.config(state=tk.DISABLED)
        self.ngrok_url = ""
        self.url_var.set("未启动")
        self.copy_url_btn.config(state=tk.DISABLED)
        self.open_url_btn.config(state=tk.DISABLED)
        self.open_ngrok_console_btn.config(state=tk.DISABLED)
    
    def update_ngrok_url(self):
        """更新网址显示（在主线程中执行）"""
        def _update():
            if self.ngrok_url:
                self.url_var.set(self.ngrok_url)
                self.copy_url_btn.config(state=tk.NORMAL)
                self.open_url_btn.config(state=tk.NORMAL)
                self.log(f"🔗 网址已更新到界面: {self.ngrok_url}")
                # 强制刷新界面
                self.root.update_idletasks()
            else:
                self.log("⚠️ ngrok_url 为空，无法更新显示")
        
        # 确保在主线程中执行
        if self.root:
            self.root.after(0, _update)
    
    def copy_url(self):
        """复制网址到剪贴板"""
        if self.ngrok_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.ngrok_url)
            self.root.update()
            messagebox.showinfo("成功", f"网址已复制到剪贴板:\n{self.ngrok_url}")
    
    def open_url(self):
        """在浏览器中打开网址"""
        if self.ngrok_url:
            import webbrowser
            webbrowser.open(self.ngrok_url)
            self.log(f"🔗 已在浏览器中打开: {self.ngrok_url}")
        else:
            messagebox.showwarning("提示", "网址尚未获取，请稍候或查看 ngrok 控制台")
    
    def open_ngrok_console(self):
        """打开 ngrok 控制台"""
        import webbrowser
        webbrowser.open('http://127.0.0.1:4040')
        self.log("📊 已打开 ngrok 控制台: http://127.0.0.1:4040")
    
    def cleanup_processes(self):
        """清理所有子进程"""
        # 清理 Web 服务器进程
        if self.web_process:
            try:
                if self.web_process.poll() is None:
                    self.web_process.terminate()
                    try:
                        self.web_process.wait(timeout=1)
                    except:
                        self.web_process.kill()
            except:
                pass
            self.web_process = None
        
        # 清理 ngrok 进程
        if self.ngrok_process:
            try:
                if self.ngrok_process.poll() is None:
                    self.ngrok_process.terminate()
                    try:
                        self.ngrok_process.wait(timeout=1)
                    except:
                        self.ngrok_process.kill()
            except:
                pass
            self.ngrok_process = None
    
    def check_and_cleanup_port(self, port=5001):
        """检查并清理占用端口的进程"""
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    process_info = lines[1].split()
                    if len(process_info) > 1:
                        pid = process_info[1]
                        cmd = process_info[0] if process_info[0] else '未知'
                        
                        # 检查是否是我们的 web_app.py 进程
                        full_cmd = ' '.join(process_info)
                        if 'web_app.py' in full_cmd or cmd == 'Python':
                            self.log(f"🔍 发现占用端口 {port} 的进程: {cmd} (PID: {pid})")
                            return pid
        except:
            pass
        return None
    
    def cleanup_processes(self):
        """清理所有子进程"""
        # 清理 Web 服务器进程
        if self.web_process:
            try:
                if self.web_process.poll() is None:
                    self.web_process.terminate()
                    try:
                        self.web_process.wait(timeout=1)
                    except:
                        self.web_process.kill()
            except:
                pass
            self.web_process = None
        
        # 清理 ngrok 进程
        if self.ngrok_process:
            try:
                if self.ngrok_process.poll() is None:
                    self.ngrok_process.terminate()
                    try:
                        self.ngrok_process.wait(timeout=1)
                    except:
                        self.ngrok_process.kill()
            except:
                pass
            self.ngrok_process = None
    
    def check_and_cleanup_port(self, port=5001):
        """检查并清理占用端口的进程"""
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    process_info = lines[1].split()
                    if len(process_info) > 1:
                        pid = process_info[1]
                        cmd = process_info[0] if process_info[0] else '未知'
                        
                        # 检查是否是我们的 web_app.py 进程
                        if 'web_app.py' in ' '.join(process_info) or cmd == 'Python':
                            self.log(f"🔍 发现占用端口 {port} 的进程: {cmd} (PID: {pid})")
                            self.log(f"💡 建议: 运行 'kill {pid}' 停止该进程")
                            return pid
        except:
            pass
        return None


def main():
    root = tk.Tk()
    app = MonitorGUI(root)
    
    # 设置窗口关闭时的清理函数
    def on_closing():
        """窗口关闭时的清理"""
        app.log("🔄 正在关闭应用，清理资源...")
        
        # 停止所有服务
        if app.web_running:
            app.stop_web_server()
        if app.ngrok_running:
            app.stop_ngrok()
        if app.monitoring:
            app.stop_monitor()
        
        # 确保所有进程都被终止
        app.cleanup_processes()
        
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

