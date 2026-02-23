#!/usr/bin/env python3
"""
店小秘 TikTok 订单自动备注机器人
自动为来自TikTok的订单添加买家TikTok昵称备注
"""

import yaml
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import sys

from dianxiaomi_api import DianXiaoMiAPI
from tiktok_order_parser import TikTokOrderParser


class DianXiaoMiTikTokBot:
    """店小秘TikTok订单备注机器人"""
    
    def __init__(self, config_path: str = "dianxiaomi_config.yaml"):
        """
        初始化机器人
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.api = self._init_api()
        self.parser = TikTokOrderParser(self.config.get('tiktok', {}))
        self.processed_orders = set()  # 已处理的订单ID集合
        
        print("=" * 60)
        print("🤖 店小秘 TikTok 订单自动备注机器人")
        print("=" * 60)
        print(f"✅ API 初始化成功")
        print(f"✅ 订单解析器初始化成功")
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {config_path}")
            print(f"   请创建配置文件，参考 dianxiaomi_config.example.yaml")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            sys.exit(1)
    
    def _init_api(self) -> DianXiaoMiAPI:
        """初始化店小秘API"""
        api_config = self.config.get('dianxiaomi', {})
        api_key = api_config.get('api_key')
        api_secret = api_config.get('api_secret')
        base_url = api_config.get('base_url', 'https://openapi.dianxiaomi.com')
        
        if not api_key or not api_secret:
            raise ValueError("请配置店小秘 API Key 和 API Secret")
        
        return DianXiaoMiAPI(api_key, api_secret, base_url)
    
    def process_orders(self, 
                       start_time: Optional[str] = None,
                       end_time: Optional[str] = None,
                       dry_run: bool = False) -> Dict:
        """
        处理订单，为TikTok订单添加昵称备注
        
        Args:
            start_time: 开始时间 (格式: YYYY-MM-DD HH:MM:SS)
            end_time: 结束时间 (格式: YYYY-MM-DD HH:MM:SS)
            dry_run: 是否仅模拟运行（不实际添加备注）
            
        Returns:
            处理结果统计
        """
        print(f"\n📋 开始获取订单...")
        if start_time:
            print(f"   时间范围: {start_time} ~ {end_time or '现在'}")
        
        # 获取订单列表
        try:
            orders_data = self.api.get_orders(
                start_time=start_time,
                end_time=end_time,
                page_size=100
            )
            
            # 解析订单列表（根据实际API响应结构调整）
            orders = orders_data.get('orders', []) or orders_data.get('data', []) or orders_data.get('list', [])
            
            if not orders:
                print("   ℹ️ 未找到订单")
                return {
                    'total': 0,
                    'tiktok_orders': 0,
                    'processed': 0,
                    'success': 0,
                    'failed': 0,
                    'skipped': 0
                }
            
            print(f"   ✅ 获取到 {len(orders)} 个订单")
            
        except Exception as e:
            print(f"   ❌ 获取订单失败: {e}")
            return {
                'total': 0,
                'tiktok_orders': 0,
                'processed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }
        
        # 筛选TikTok订单
        tiktok_orders = self.api.filter_tiktok_orders(orders)
        print(f"   🎯 筛选出 {len(tiktok_orders)} 个TikTok订单")
        
        if not tiktok_orders:
            print("   ℹ️ 没有TikTok订单需要处理")
            return {
                'total': len(orders),
                'tiktok_orders': 0,
                'processed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }
        
        # 处理每个订单
        stats = {
            'total': len(orders),
            'tiktok_orders': len(tiktok_orders),
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        print(f"\n🔄 开始处理订单...")
        if dry_run:
            print("   ⚠️ 模拟运行模式（不会实际添加备注）")
        
        for order in tiktok_orders:
            order_id = order.get('order_id') or order.get('id')
            if not order_id:
                continue
            
            # 检查是否已处理
            if order_id in self.processed_orders:
                stats['skipped'] += 1
                continue
            
            print(f"\n   📦 订单: {order_id}")
            
            # 提取TikTok昵称
            nickname = self.parser.extract_nickname_from_order(order)
            
            if not nickname:
                # 尝试从TikTok API获取
                tiktok_config = self.config.get('tiktok', {})
                if tiktok_config.get('api_enabled', False):
                    tiktok_order_id = order.get('tiktok_order_id') or order.get('platform_order_id')
                    if tiktok_order_id:
                        nickname = self.parser.get_nickname_from_tiktok_api(
                            tiktok_order_id,
                            tiktok_config
                        )
            
            if nickname:
                print(f"      👤 TikTok昵称: {nickname}")
                
                # 构建备注内容
                note_prefix = self.config.get('note_prefix', 'TikTok昵称: ')
                note = f"{note_prefix}{nickname}"
                
                # 检查订单是否已有备注
                existing_note = order.get('note', '') or order.get('remark', '')
                if existing_note:
                    # 检查是否已包含昵称
                    if nickname in existing_note:
                        print(f"      ✅ 备注已包含昵称，跳过")
                        stats['skipped'] += 1
                        self.processed_orders.add(order_id)
                        continue
                    # 追加备注
                    note = f"{existing_note}\n{note}"
                
                if not dry_run:
                    # 添加备注
                    success = self.api.add_order_note(order_id, note)
                    if success:
                        print(f"      ✅ 备注添加成功")
                        stats['success'] += 1
                    else:
                        print(f"      ❌ 备注添加失败")
                        stats['failed'] += 1
                else:
                    print(f"      [模拟] 将添加备注: {note}")
                    stats['success'] += 1
                
                self.processed_orders.add(order_id)
                stats['processed'] += 1
                
            else:
                print(f"      ⚠️ 未找到TikTok昵称")
                stats['failed'] += 1
            
            # 避免请求过快
            time.sleep(0.5)
        
        return stats
    
    def run_continuous(self, interval: int = 300, dry_run: bool = False):
        """
        持续运行，定期检查新订单
        
        Args:
            interval: 检查间隔（秒）
            dry_run: 是否仅模拟运行
        """
        print(f"\n🔄 开始持续监控模式")
        print(f"   检查间隔: {interval} 秒")
        print(f"   按 Ctrl+C 停止\n")
        
        try:
            while True:
                # 获取最近1小时的订单
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=1)
                
                start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                
                stats = self.process_orders(
                    start_time=start_str,
                    end_time=end_str,
                    dry_run=dry_run
                )
                
                print(f"\n📊 本次处理统计:")
                print(f"   总订单数: {stats['total']}")
                print(f"   TikTok订单: {stats['tiktok_orders']}")
                print(f"   已处理: {stats['processed']}")
                print(f"   成功: {stats['success']}")
                print(f"   失败: {stats['failed']}")
                print(f"   跳过: {stats['skipped']}")
                
                print(f"\n⏳ 等待 {interval} 秒后继续检查...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n👋 已停止监控")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='店小秘 TikTok 订单自动备注机器人')
    parser.add_argument('--config', '-c', default='dianxiaomi_config.yaml',
                       help='配置文件路径 (默认: dianxiaomi_config.yaml)')
    parser.add_argument('--start-time', help='开始时间 (格式: YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-time', help='结束时间 (格式: YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--continuous', action='store_true',
                       help='持续运行模式（定期检查新订单）')
    parser.add_argument('--interval', type=int, default=300,
                       help='持续运行模式的检查间隔（秒，默认300）')
    parser.add_argument('--dry-run', action='store_true',
                       help='模拟运行（不实际添加备注）')
    
    args = parser.parse_args()
    
    try:
        bot = DianXiaoMiTikTokBot(args.config)
        
        if args.continuous:
            bot.run_continuous(interval=args.interval, dry_run=args.dry_run)
        else:
            stats = bot.process_orders(
                start_time=args.start_time,
                end_time=args.end_time,
                dry_run=args.dry_run
            )
            
            print(f"\n📊 处理完成！")
            print(f"   总订单数: {stats['total']}")
            print(f"   TikTok订单: {stats['tiktok_orders']}")
            print(f"   已处理: {stats['processed']}")
            print(f"   成功: {stats['success']}")
            print(f"   失败: {stats['failed']}")
            print(f"   跳过: {stats['skipped']}")
    
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()






