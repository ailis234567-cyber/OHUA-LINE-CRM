#!/usr/bin/env python3
"""
直播监控截图 Web 应用
提供图片搜索和查看功能
"""

from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
import json
from datetime import datetime
import threading
import time
import yaml
import os
import sys

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 配置
CONFIG_PATH = "config.yaml"
SCREENSHOTS_DIR = Path("./screenshots")
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def load_config():
    """加载配置"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except:
        return {'storage': {'save_dir': './screenshots'}}


def scan_screenshots():
    """扫描screenshots目录，返回所有图片信息"""
    screenshots = []
    config = load_config()
    screenshots_dir = Path(config.get('storage', {}).get('save_dir', './screenshots'))
    
    if not screenshots_dir.exists():
        return screenshots
    
    # 遍历所有ID文件夹
    for id_folder in screenshots_dir.iterdir():
        if not id_folder.is_dir() or not id_folder.name.startswith('ID_'):
            continue
        
        product_id = id_folder.name.replace('ID_', '')
        
        # 遍历日期文件夹
        for date_folder in id_folder.iterdir():
            if not date_folder.is_dir():
                continue
            
            date_str = date_folder.name
            
            # 遍历图片文件
            for img_file in date_folder.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    screenshots.append({
                        'id': product_id,
                        'date': date_str,
                        'filename': img_file.name,
                        'serial_number': img_file.stem,  # 文件名（不含扩展名）就是编号
                        'path': str(img_file.relative_to(screenshots_dir)),
                        'full_path': str(img_file),
                        'size': img_file.stat().st_size,
                        'modified': datetime.fromtimestamp(img_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    return screenshots


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/search')
def search():
    """搜索API"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'auto').strip()  # 'id', 'serial', 'date', 'auto'
    date_filter = request.args.get('date', '').strip()  # 日期筛选，格式：YYYY-MM-DD
    
    # 如果提供了日期筛选，优先使用日期搜索
    if date_filter:
        search_type = 'date'
        query = date_filter
    
    if not query and not date_filter:
        return jsonify({'error': '请输入搜索关键词或选择日期'}), 400
    
    all_screenshots = scan_screenshots()
    
    # 搜索匹配
    results = []
    query_lower = query.lower()
    
    for screenshot in all_screenshots:
        match = False
        
        if search_type == 'date':
            # 按日期搜索（根据上传时间）
            # 支持格式：YYYY-MM-DD 或 YYYY-MM 或 YYYY
            screenshot_date = screenshot['modified'].split(' ')[0]  # 提取日期部分 YYYY-MM-DD
            
            if date_filter:
                # 使用日期筛选器
                filter_date = date_filter
            else:
                filter_date = query
            
            # 支持多种日期格式匹配
            if len(filter_date) == 10:  # YYYY-MM-DD
                if screenshot_date == filter_date:
                    match = True
            elif len(filter_date) == 7:  # YYYY-MM
                if screenshot_date.startswith(filter_date):
                    match = True
            elif len(filter_date) == 4:  # YYYY
                if screenshot_date.startswith(filter_date):
                    match = True
        elif search_type == 'id':
            # 只搜索ID
            if query_lower in screenshot['id'].lower():
                match = True
        elif search_type == 'serial':
            # 只搜索编号
            if query_lower in screenshot['serial_number'].lower():
                match = True
        else:
            # 默认：自动判断
            # 如果输入是4位数字，优先按编号搜索；否则按ID搜索
            if query.isdigit() and len(query) == 4:
                # 4位数字，按编号搜索
                if query_lower in screenshot['serial_number'].lower():
                    match = True
            else:
                # 其他情况，按ID搜索
                if query_lower in screenshot['id'].lower():
                    match = True
        
        if match:
            results.append(screenshot)
    
    # 按日期倒序排列（最新的在前）
    results.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({
        'query': query,
        'type': search_type,
        'date_filter': date_filter if date_filter else None,
        'count': len(results),
        'results': results
    })


@app.route('/api/stats')
def stats():
    """统计信息API"""
    all_screenshots = scan_screenshots()
    
    # 统计每个ID的图片数量
    id_counts = {}
    total_count = len(all_screenshots)
    
    for screenshot in all_screenshots:
        product_id = screenshot['id']
        id_counts[product_id] = id_counts.get(product_id, 0) + 1
    
    return jsonify({
        'total_images': total_count,
        'total_ids': len(id_counts),
        'id_counts': id_counts
    })


@app.route('/api/analytics')
def analytics():
    """数据分析API - 每20分钟的图片数量统计（按日期分类）"""
    # 获取所有图片数据
    all_screenshots = scan_screenshots()
    
    if not all_screenshots:
        return jsonify({
            'by_date': {},
            'total_count': 0
        })
    
    # 按日期分类，每日期内按每20分钟统计
    from collections import defaultdict
    date_stats = defaultdict(lambda: defaultdict(int))
    
    for screenshot in all_screenshots:
        try:
            # 解析文件修改时间（即上传时间）
            modified_time = datetime.strptime(screenshot['modified'], '%Y-%m-%d %H:%M:%S')
            
            # 获取日期
            date_key = modified_time.strftime('%Y-%m-%d')
            
            # 计算20分钟区间：0-19分钟 -> :00, 20-39分钟 -> :20, 40-59分钟 -> :40
            minute = modified_time.minute
            if minute < 20:
                time_slot = 0
            elif minute < 40:
                time_slot = 20
            else:
                time_slot = 40
            
            # 格式: HH:00, HH:20, 或 HH:40（只保留时间，不包含日期）
            time_key = modified_time.strftime(f'%H:{time_slot:02d}')
            date_stats[date_key][time_key] += 1
        except Exception as e:
            # 如果解析失败，跳过这条记录
            continue
    
    # 转换为按日期分类的数据结构
    by_date_data = {}
    for date_key, time_counts in date_stats.items():
        # 将时间点转换为列表并排序
        time_data = sorted([{'time': k, 'count': v} for k, v in time_counts.items()], 
                          key=lambda x: x['time'])
        by_date_data[date_key] = time_data
    
    # 获取所有日期并排序
    dates_list = sorted(by_date_data.keys())
    
    return jsonify({
        'by_date': by_date_data,
        'dates': dates_list,
        'total_count': len(all_screenshots),
        'dates': sorted(by_date_data.keys())
    })


@app.route('/api/images/<path:image_path>')
def get_image(image_path):
    """获取图片"""
    from flask import send_file
    config = load_config()
    screenshots_dir = Path(config.get('storage', {}).get('save_dir', './screenshots'))
    
    # 安全路径检查
    full_path = screenshots_dir / image_path
    screenshots_resolved = screenshots_dir.resolve()
    
    try:
        full_path_resolved = full_path.resolve()
        # 确保路径在screenshots目录内（防止路径遍历攻击）
        if not str(full_path_resolved).startswith(str(screenshots_resolved)):
            return jsonify({'error': '无效的图片路径'}), 403
        
        if not full_path.exists():
            return jsonify({'error': '图片不存在'}), 404
        
        return send_file(str(full_path), mimetype='image/png' if full_path.suffix == '.png' else 'image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload():
    """上传图片API"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    product_id = request.form.get('id', 'unknown')
    serial_number = request.form.get('serial', 'unknown')
    
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    # 保存到对应的ID文件夹
    config = load_config()
    screenshots_dir = Path(config.get('storage', {}).get('save_dir', './screenshots'))
    today = datetime.now().strftime("%m-%d")
    
    id_folder = screenshots_dir / f"ID_{product_id}" / today
    id_folder.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    filename = f"{serial_number}{Path(file.filename).suffix}"
    filepath = id_folder / filename
    file.save(str(filepath))
    
    return jsonify({
        'success': True,
        'message': '上传成功',
        'path': str(filepath.relative_to(screenshots_dir))
    })


def auto_scan():
    """自动扫描新图片（后台任务）"""
    # 这个功能可以用于实时更新，目前通过API调用即可
    pass


def find_free_port(start_port=5001, max_attempts=10):
    """查找可用端口"""
    import socket
    for i in range(max_attempts):
        port = start_port + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None


if __name__ == '__main__':
    # 默认端口，如果被占用可以修改
    port = 5001
    
    # 可以通过命令行参数指定端口: python web_app.py 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"⚠️ 无效的端口号: {sys.argv[1]}，尝试查找可用端口...")
            port = find_free_port(5001) or 5001
    
    print("=" * 50)
    print("🌐 直播监控截图 Web 应用")
    print("=" * 50)
    print(f"📂 截图目录: {SCREENSHOTS_DIR.absolute()}")
    print("🚀 启动服务器...")
    
    try:
        # 生产环境建议 debug=False
        debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except OSError as e:
        error_msg = str(e)
        if "Address already in use" in error_msg:
            print(f"\n❌ 错误: 端口 {port} 已被占用", file=sys.stderr)
            
            # 尝试查找占用端口的进程
            try:
                import subprocess
                result = subprocess.run(['lsof', '-i', f':{port}'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        process_info = lines[1].split()
                        if len(process_info) > 1:
                            pid = process_info[1]
                            cmd = process_info[0] if process_info[0] else '未知'
                            print(f"   占用进程: {cmd} (PID: {pid})", file=sys.stderr)
                            print(f"   停止命令: kill {pid}", file=sys.stderr)
            except:
                pass
            
            # 尝试自动查找可用端口
            print(f"\n💡 正在查找可用端口...", file=sys.stderr)
            free_port = find_free_port(port + 1)
            if free_port:
                print(f"   找到可用端口: {free_port}", file=sys.stderr)
                print(f"   请使用: python web_app.py {free_port}", file=sys.stderr)
            else:
                print(f"   未找到可用端口，请手动指定: python web_app.py 8080", file=sys.stderr)
            
            print(f"\n💡 其他解决方案:", file=sys.stderr)
            print(f"   1. 使用其他端口: python web_app.py 8080", file=sys.stderr)
            print(f"   2. 关闭占用端口的程序", file=sys.stderr)
            print(f"   3. macOS: 在系统设置中关闭 '隔空播放接收器'", file=sys.stderr)
        else:
            print(f"\n❌ 错误: {error_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 启动失败: {error_msg}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

