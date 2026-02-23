#!/usr/bin/env python3
"""
统计所有截图时间，生成截图速度表格
"""

from pathlib import Path
from datetime import datetime
from collections import defaultdict
import yaml
import sys

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
        print(f"❌ 截图目录不存在: {screenshots_dir}")
        return []
    
    screenshots = []
    
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
                    mtime = datetime.fromtimestamp(img_file.stat().st_mtime)
                    screenshots.append({
                        'id': product_id,
                        'date': date_str,
                        'filename': img_file.name,
                        'serial_number': img_file.stem,
                        'modified': mtime
                    })
    
    return screenshots

def calculate_statistics(screenshots):
    """计算统计数据"""
    if not screenshots:
        return None
    
    # 按日期统计
    daily_stats = defaultdict(lambda: {'count': 0, 'times': []})
    
    for screenshot in screenshots:
        date_key = screenshot['modified'].strftime('%Y-%m-%d')
        daily_stats[date_key]['count'] += 1
        daily_stats[date_key]['times'].append(screenshot['modified'])
    
    # 计算每小时速度
    hourly_stats = defaultdict(lambda: {'count': 0, 'times': []})
    
    for screenshot in screenshots:
        hour_key = screenshot['modified'].strftime('%Y-%m-%d %H:00')
        hourly_stats[hour_key]['count'] += 1
        hourly_stats[hour_key]['times'].append(screenshot['modified'])
    
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
    
    return {
        'daily': daily_stats,
        'hourly': hourly_stats,
        'twenty_min': twenty_min_stats,
        'total': len(screenshots)
    }

def print_table(stats, stat_type='twenty_min'):
    """打印统计表格"""
    if not stats:
        print("❌ 没有数据")
        return
    
    data = stats[stat_type]
    sorted_data = sorted(data.items())
    
    print("\n" + "=" * 80)
    print(f"📊 截图速度统计表 (每20分钟)")
    print("=" * 80)
    print(f"{'时间段':<25} {'数量':<10} {'平均间隔(秒)':<15} {'速度(张/20分钟)':<15}")
    print("-" * 80)
    
    for time_key, info in sorted_data:
        count = info['count']
        times = sorted(info['times'])
        
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
        
        print(f"{time_key:<25} {count:<10} {avg_interval:>10.1f}秒    {speed_per_20min:>12.2f}张/20分钟")
    
    print("=" * 80)
    print(f"总计: {stats['total']} 张截图")
    print()

def print_daily_summary(stats):
    """打印每日汇总"""
    if not stats:
        return
    
    daily = stats['daily']
    sorted_daily = sorted(daily.items())
    
    print("\n" + "=" * 80)
    print("📅 每日汇总")
    print("=" * 80)
    print(f"{'日期':<15} {'数量':<10} {'最早时间':<20} {'最晚时间':<20}")
    print("-" * 80)
    
    for date_key, info in sorted_daily:
        count = info['count']
        times = sorted(info['times'])
        earliest = times[0].strftime('%H:%M:%S')
        latest = times[-1].strftime('%H:%M:%S')
        
        print(f"{date_key:<15} {count:<10} {earliest:<20} {latest:<20}")
    
    print("=" * 80)
    print()

def main():
    print("🔍 正在扫描截图文件...")
    screenshots = scan_all_screenshots()
    
    if not screenshots:
        print("❌ 没有找到截图文件")
        return
    
    print(f"✅ 找到 {len(screenshots)} 张截图")
    
    print("\n📊 正在计算统计数据...")
    stats = calculate_statistics(screenshots)
    
    if not stats:
        print("❌ 无法计算统计数据")
        return
    
    # 打印每20分钟统计
    print_table(stats, 'twenty_min')
    
    # 打印每日汇总
    print_daily_summary(stats)
    
    # 保存到文件
    output_file = 'screenshot_statistics.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("截图速度统计报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"总截图数: {stats['total']} 张\n")
        f.write(f"统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("\n每20分钟统计:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'时间段':<25} {'数量':<10} {'速度(张/20分钟)':<15}\n")
        f.write("-" * 80 + "\n")
        
        sorted_data = sorted(stats['twenty_min'].items())
        for time_key, info in sorted_data:
            count = info['count']
            # 速度就是该20分钟时间段内的数量（张/20分钟）
            speed_per_20min = count
            
            f.write(f"{time_key:<25} {count:<10} {speed_per_20min:>12.2f}张/20分钟\n")
        
        f.write("\n每日汇总:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'日期':<15} {'数量':<10} {'最早时间':<20} {'最晚时间':<20}\n")
        f.write("-" * 80 + "\n")
        
        sorted_daily = sorted(stats['daily'].items())
        for date_key, info in sorted_daily:
            count = info['count']
            times = sorted(info['times'])
            earliest = times[0].strftime('%H:%M:%S')
            latest = times[-1].strftime('%H:%M:%S')
            f.write(f"{date_key:<15} {count:<10} {earliest:<20} {latest:<20}\n")
    
    print(f"✅ 统计报告已保存到: {output_file}")

if __name__ == '__main__':
    main()

