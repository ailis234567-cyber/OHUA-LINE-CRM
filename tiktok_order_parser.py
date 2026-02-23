#!/usr/bin/env python3
"""
TikTok 订单数据解析模块
从订单信息中提取买家TikTok昵称
"""

import re
import json
from typing import Optional, Dict
from pathlib import Path


class TikTokOrderParser:
    """TikTok订单解析器"""
    
    def __init__(self, config: dict = None):
        """
        初始化解析器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        # TikTok昵称可能出现的字段名
        self.nickname_fields = [
            'buyer_nickname',
            'tiktok_username',
            'customer_name',
            'buyer_name',
            'username',
            'nickname',
            'tiktok_id',
            'buyer_id'
        ]
    
    def extract_nickname_from_order(self, order: Dict) -> Optional[str]:
        """
        从订单数据中提取TikTok昵称
        
        Args:
            order: 订单数据字典
            
        Returns:
            TikTok昵称，如果未找到则返回None
        """
        # 方法1: 直接从订单字段中查找
        for field in self.nickname_fields:
            if field in order and order[field]:
                nickname = str(order[field]).strip()
                if nickname and nickname.lower() not in ['null', 'none', '']:
                    return nickname
        
        # 方法2: 从订单备注或描述中提取
        note = order.get('note', '') or order.get('remark', '') or order.get('description', '')
        if note:
            nickname = self._extract_from_text(note)
            if nickname:
                return nickname
        
        # 方法3: 从买家信息中提取
        buyer_info = order.get('buyer', {}) or order.get('customer', {})
        if isinstance(buyer_info, dict):
            for field in self.nickname_fields:
                if field in buyer_info and buyer_info[field]:
                    nickname = str(buyer_info[field]).strip()
                    if nickname and nickname.lower() not in ['null', 'none', '']:
                        return nickname
        
        # 方法4: 从订单ID或SKU中提取（某些情况下昵称可能编码在订单号中）
        order_id = str(order.get('order_id', '') or order.get('order_number', ''))
        if order_id:
            # 检查订单ID格式，某些平台可能包含昵称信息
            # 这里需要根据实际情况调整
            pass
        
        return None
    
    def _extract_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取可能的昵称
        
        Args:
            text: 文本内容
            
        Returns:
            提取的昵称
        """
        if not text:
            return None
        
        # 匹配常见的昵称格式
        # TikTok昵称通常是: @username 或 username
        patterns = [
            r'@([a-zA-Z0-9_\.]+)',  # @username
            r'tiktok[:\s]+([a-zA-Z0-9_\.]+)',  # tiktok: username
            r'nickname[:\s]+([a-zA-Z0-9_\.]+)',  # nickname: username
            r'username[:\s]+([a-zA-Z0-9_\.]+)',  # username: username
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nickname = match.group(1).strip()
                if len(nickname) >= 2:  # 昵称至少2个字符
                    return nickname
        
        return None
    
    def get_nickname_from_tiktok_api(self, order_id: str, api_config: dict) -> Optional[str]:
        """
        从TikTok API获取买家昵称（如果店小秘订单数据中没有）
        
        注意：这需要TikTok Shop API的访问权限
        
        Args:
            order_id: TikTok订单ID
            api_config: TikTok API配置
            
        Returns:
            TikTok昵称
        """
        # 这里需要实现TikTok Shop API调用
        # 由于TikTok API需要认证和特殊权限，这里只提供框架
        
        try:
            import requests
            
            # TikTok Shop API端点（需要根据实际API文档调整）
            api_url = api_config.get('api_url', 'https://open-api.tiktokglobalshop.com')
            access_token = api_config.get('access_token')
            
            if not access_token:
                return None
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 获取订单详情
            response = requests.get(
                f"{api_url}/api/orders/{order_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # 从响应中提取买家昵称
                buyer_info = data.get('buyer', {})
                return buyer_info.get('nickname') or buyer_info.get('username')
            
        except Exception as e:
            print(f"⚠️ 从TikTok API获取昵称失败: {e}")
        
        return None
    
    def parse_order_file(self, file_path: str) -> Dict:
        """
        从文件解析订单数据（支持CSV、JSON、Excel）
        
        Args:
            file_path: 文件路径
            
        Returns:
            订单数据字典列表
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        elif file_path.suffix.lower() == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")



