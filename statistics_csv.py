#!/usr/bin/env python3
"""
生成 CSV 格式的截图速度统计表
"""

from pathlib import Path
from datetime import datetime
from collections import defaultdict
import yaml
import csv

def load_config():
    """加载配置"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except:
        return {'storage': {'save_dir': './screenshots'}}

def scan_all_screenshots():
    """扫描所有截图文件"""
    config = load_config()
    screenshots_dir = Path(config.get('storage', {}).get('save_dir', './screenshots'))
    
    if not screenshots_dir.exists():
        return []
    
    screenshots = []
    
    for id_folder in screenshots_dir.iterdir():
        if not id_folder.is_dir() or not id_folder.name.startswith('ID_'):
            continue
        
        product_id = id_folder.name.replace('ID_', '')
        
        for date_folder in id_folder.iterdir():
            if not date_folder.is_dir():
                continue
            
            date_str = date_folder.name
            
            for img_file in date_folder.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    mtime = datetime.fromtimestamp(img_file.stat().st_mtime)
                    screenshots.append({
                        'id': product_id,
                        'date': date_str,
                        'filename': img_file.name,
                        'serial_number': img_file.stem,
                        'modified': mtime
                    })
    
    return screenshots

def generate_csv(screenshots):
    """生成 CSV 文件"""
    if not screenshots:
        print("❌ 没有找到截图文件")
        return
    
    # 按每20分钟统计
    twenty_min_stats = defaultdict(lambda: {'count': 0, 'times': []})
    
    for screenshot in screenshots:
        minute = screenshot['modified'].minute
        # 0-19分钟 -> :00, 20-39分钟 -> :20, 40-59分钟 -> :40
        if minute < 20:
            time_slot = 0
        elif minute < 40:
            time_slot = 20
        else:
            time_slot = 40
        time_key = screenshot['modified'].strftime(f'%Y-%m-%d %H:{time_slot:02d}')
        twenty_min_stats[time_key]['count'] += 1
        twenty_min_stats[time_key]['times'].append(screenshot['modified'])
    
    # 生成 CSV
    csv_file = 'screenshot_statistics.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # 写入表头
        writer.writerow(['时间段', '数量(张)', '平均间隔(秒)', '速度(张/20分钟)', '最早时间', '最晚时间'])
        
        # 按时间排序
        sorted_data = sorted(twenty_min_stats.items())
        
        for time_key, info in sorted_data:
            count = info['count']
            times = sorted(info['times'])
            earliest = times[0].strftime('%H:%M:%S')
            latest = times[-1].strftime('%H:%M:%S')
            
            # 计算平均间隔
            if len(times) > 1:
                intervals = []
                for i in range(1, len(times)):
                    interval = (times[i] - times[i-1]).total_seconds()
                    intervals.append(interval)
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
            else:
                avg_interval = 0
            
            # 速度就是该20分钟时间段内的数量（张/20分钟）
            speed_per_20min = count
            
            writer.writerow([
                time_key,
                count,
                f'{avg_interval:.1f}',
                f'{speed_per_20min:.2f}',
                earliest,
                latest
            ])
    
    print(f"✅ CSV 文件已生成: {csv_file}")
    print(f"   总计: {len(screenshots)} 张截图")
    print(f"   时间段: {len(sorted_data)} 个")

if __name__ == '__main__':
    print("🔍 正在扫描截图文件...")
    screenshots = scan_all_screenshots()
    print(f"✅ 找到 {len(screenshots)} 张截图")
    
    print("\n📊 正在生成 CSV 文件...")
    generate_csv(screenshots)

