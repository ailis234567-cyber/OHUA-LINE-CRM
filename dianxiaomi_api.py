#!/usr/bin/env python3
"""
店小秘 API 集成模块
用于获取订单、添加备注等功能
"""

import requests
import time
from typing import List, Dict, Optional
from datetime import datetime


class DianXiaoMiAPI:
    """店小秘 API 客户端"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://openapi.dianxiaomi.com"):
        """
        初始化店小秘 API 客户端
        
        Args:
            api_key: API Key
            api_secret: API Secret
            base_url: API 基础URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TikTok-Nickname-Bot/1.0'
        })
    
    def _get_signature(self, params: dict, timestamp: str) -> str:
        """
        生成签名（根据店小秘API文档实现）
        
        注意：店小秘的签名算法可能不同，需要根据实际API文档调整
        """
        # 这里需要根据店小秘的实际签名算法实现
        # 示例：MD5(api_key + api_secret + timestamp + sorted_params)
        import hashlib
        
        # 排序参数
        sorted_params = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_string = f"{self.api_key}{self.api_secret}{timestamp}{sorted_params}"
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法 (GET, POST)
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time()))
        
        # 构建请求参数
        request_params = params or {}
        request_params.update({
            'api_key': self.api_key,
            'timestamp': timestamp
        })
        
        # 生成签名
        signature = self._get_signature(request_params, timestamp)
        request_params['sign'] = signature
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=request_params, timeout=30)
            else:
                response = self.session.post(url, params=request_params, json=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            # 检查API返回的错误码
            if result.get('code') != 0 and result.get('code') != 200:
                error_msg = result.get('message', '未知错误')
                raise Exception(f"API错误: {error_msg}")
            
            return result.get('data', result)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
    
    def get_orders(self, 
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   order_status: Optional[str] = None,
                   page: int = 1,
                   page_size: int = 100) -> Dict:
        """
        获取订单列表
        
        Args:
            start_time: 开始时间 (格式: YYYY-MM-DD HH:MM:SS)
            end_time: 结束时间 (格式: YYYY-MM-DD HH:MM:SS)
            order_status: 订单状态 (可选)
            page: 页码
            page_size: 每页数量
            
        Returns:
            订单列表数据
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if order_status:
            params['order_status'] = order_status
        
        # 注意：实际的API端点需要根据店小秘文档调整
        return self._request('GET', '/api/orders/list', params=params)
    
    def get_order_detail(self, order_id: str) -> Dict:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单详情数据
        """
        params = {'order_id': order_id}
        return self._request('GET', '/api/orders/detail', params=params)
    
    def add_order_note(self, order_id: str, note: str) -> bool:
        """
        为订单添加备注
        
        Args:
            order_id: 订单ID
            note: 备注内容
            
        Returns:
            是否成功
        """
        data = {
            'order_id': order_id,
            'note': note
        }
        
        try:
            result = self._request('POST', '/api/orders/add_note', data=data)
            return True
        except Exception as e:
            print(f"❌ 添加备注失败 (订单 {order_id}): {e}")
            return False
    
    def update_order_note(self, order_id: str, note: str) -> bool:
        """
        更新订单备注（追加或替换）
        
        Args:
            order_id: 订单ID
            note: 备注内容
            
        Returns:
            是否成功
        """
        data = {
            'order_id': order_id,
            'note': note,
            'append': True  # 是否追加（True=追加，False=替换）
        }
        
        try:
            result = self._request('POST', '/api/orders/update_note', data=data)
            return True
        except Exception as e:
            print(f"❌ 更新备注失败 (订单 {order_id}): {e}")
            return False
    
    def filter_tiktok_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        筛选出来自TikTok的订单
        
        Args:
            orders: 订单列表
            
        Returns:
            TikTok订单列表
        """
        tiktok_orders = []
        tiktok_keywords = ['tiktok', 'tk', '抖音', 'tiktok shop']
        
        for order in orders:
            # 检查订单来源
            source = str(order.get('platform', '') + ' ' + order.get('channel', '')).lower()
            order_id = str(order.get('order_id', '')).lower()
            
            # 检查是否包含TikTok关键词
            if any(keyword in source or keyword in order_id for keyword in tiktok_keywords):
                tiktok_orders.append(order)
        
        return tiktok_orders






