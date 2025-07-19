"""
쿠팡 대시보드 클라이언트
통합 대시보드 정보 제공
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from market.coupang.order import OrderClient
from market.coupang.product import ProductQueryClient
from market.coupang.cs import CSClient
from market.coupang.sales import SalesClient
from market.coupang.settlement import SettlementClient
from market.coupang.returns import ReturnClient
from market_manager import MarketSync
from config import get_config

logger = logging.getLogger(__name__)

class CoupangDashboardClient:
    """쿠팡 대시보드 통합 클라이언트"""
    
    def __init__(self, vendor_id: Optional[str] = None):
        """
        Args:
            vendor_id: 쿠팡 벤더 ID
        """
        self.vendor_id = vendor_id or os.getenv('COUPANG_VENDOR_ID')
        if get_config:
            self.vendor_id = self.vendor_id or get_config('api_keys', 'COUPANG_VENDOR_ID')
        
        # 각 모듈 클라이언트 초기화
        self.order_client = OrderClient(vendor_id=self.vendor_id)
        self.product_client = ProductQueryClient(vendor_id=self.vendor_id)
        self.cs_client = CSClient(vendor_id=self.vendor_id)
        self.sales_client = SalesClient(vendor_id=self.vendor_id)
        self.settlement_client = SettlementClient(vendor_id=self.vendor_id)
        self.return_client = ReturnClient(vendor_id=self.vendor_id)
        self.sync_manager = MarketSync()
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """대시보드 요약 정보 조회"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'vendor_id': self.vendor_id,
            'today': self._get_today_stats(),
            'recent': self._get_recent_stats(),
            'alerts': self._get_alerts(),
            'status': 'active'
        }
        
        return summary
    
    def _get_today_stats(self) -> Dict[str, Any]:
        """오늘의 통계 정보"""
        today = datetime.now().date()
        stats = {
            'date': today.isoformat(),
            'orders': {'total': 0, 'new': 0, 'processing': 0, 'shipped': 0},
            'sales': {'amount': 0, 'count': 0},
            'cs': {'total': 0, 'pending': 0, 'answered': 0},
            'returns': {'requested': 0, 'approved': 0, 'rejected': 0}
        }
        
        try:
            # 주문 통계
            orders = self.order_client.get_orders_by_date(
                search_from=today.isoformat(),
                search_to=today.isoformat()
            )
            if orders and 'data' in orders:
                for order in orders['data']:
                    stats['orders']['total'] += 1
                    status = order.get('status', '')
                    if status == 'ACCEPT':
                        stats['orders']['new'] += 1
                    elif status in ['INSTRUCT', 'DEPARTURE']:
                        stats['orders']['processing'] += 1
                    elif status in ['DELIVERING', 'FINAL_DELIVERY']:
                        stats['orders']['shipped'] += 1
            
            # 매출 통계
            revenue = self.sales_client.get_daily_revenue(today.isoformat())
            if revenue and 'data' in revenue:
                for item in revenue['data']:
                    stats['sales']['amount'] += item.get('salesAmount', 0)
                    stats['sales']['count'] += item.get('orderCount', 0)
            
            # CS 통계
            inquiries = self.cs_client.get_inquiries_by_date(
                created_at_from=today.isoformat(),
                created_at_to=today.isoformat()
            )
            if inquiries and 'data' in inquiries:
                stats['cs']['total'] = len(inquiries['data'])
                for inquiry in inquiries['data']:
                    if inquiry.get('answered'):
                        stats['cs']['answered'] += 1
                    else:
                        stats['cs']['pending'] += 1
            
            # 반품 통계
            returns = self.return_client.get_returns_by_date(
                search_from=today.isoformat(),
                search_to=today.isoformat()
            )
            if returns and 'data' in returns:
                for ret in returns['data']:
                    stats['returns']['requested'] += 1
                    status = ret.get('returnStatus', '')
                    if status == 'APPROVED':
                        stats['returns']['approved'] += 1
                    elif status == 'REJECTED':
                        stats['returns']['rejected'] += 1
                        
        except Exception as e:
            logger.error(f"오늘 통계 조회 실패: {e}")
        
        return stats
    
    def _get_recent_stats(self, days: int = 7) -> Dict[str, Any]:
        """최근 N일간 통계"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        stats = {
            'period': f'{start_date.isoformat()} ~ {end_date.isoformat()}',
            'days': days,
            'orders': {'total': 0, 'daily_avg': 0},
            'sales': {'total_amount': 0, 'daily_avg': 0},
            'products': {'active': 0, 'soldout': 0, 'suspended': 0},
            'settlement': {'pending': 0, 'completed': 0}
        }
        
        try:
            # 주문 통계
            orders = self.order_client.get_orders_by_date(
                search_from=start_date.isoformat(),
                search_to=end_date.isoformat()
            )
            if orders and 'data' in orders:
                stats['orders']['total'] = len(orders['data'])
                stats['orders']['daily_avg'] = stats['orders']['total'] / days
            
            # 매출 통계
            for i in range(days):
                date = start_date + timedelta(days=i)
                revenue = self.sales_client.get_daily_revenue(date.isoformat())
                if revenue and 'data' in revenue:
                    for item in revenue['data']:
                        stats['sales']['total_amount'] += item.get('salesAmount', 0)
            stats['sales']['daily_avg'] = stats['sales']['total_amount'] / days
            
            # 상품 통계
            products = self.product_client.get_products(status='ALL')
            if products and 'data' in products:
                for product in products['data']:
                    status = product.get('statusName', '')
                    if status == 'SALE':
                        stats['products']['active'] += 1
                    elif status == 'SOLDOUT':
                        stats['products']['soldout'] += 1
                    elif status == 'SUSPENDED':
                        stats['products']['suspended'] += 1
            
            # 정산 통계
            current_month = datetime.now().strftime('%Y-%m')
            settlements = self.settlement_client.get_settlement_by_month(current_month)
            if settlements and 'data' in settlements:
                for settlement in settlements['data']:
                    if settlement.get('status') == 'COMPLETED':
                        stats['settlement']['completed'] += 1
                    else:
                        stats['settlement']['pending'] += 1
                        
        except Exception as e:
            logger.error(f"최근 통계 조회 실패: {e}")
        
        return stats
    
    def _get_alerts(self) -> List[Dict[str, Any]]:
        """주요 알림 사항"""
        alerts = []
        
        try:
            # 미답변 CS 문의
            cs_pending = self._get_today_stats()['cs']['pending']
            if cs_pending > 0:
                alerts.append({
                    'type': 'cs',
                    'level': 'warning' if cs_pending > 5 else 'info',
                    'message': f'미답변 고객문의 {cs_pending}건',
                    'action': 'cs_respond'
                })
            
            # 품절 상품
            product_stats = self._get_recent_stats()['products']
            if product_stats['soldout'] > 0:
                alerts.append({
                    'type': 'product',
                    'level': 'warning',
                    'message': f'품절 상품 {product_stats["soldout"]}개',
                    'action': 'product_restock'
                })
            
            # 미처리 반품
            return_stats = self._get_today_stats()['returns']
            pending_returns = return_stats['requested'] - return_stats['approved'] - return_stats['rejected']
            if pending_returns > 0:
                alerts.append({
                    'type': 'return',
                    'level': 'warning',
                    'message': f'처리 대기 반품 {pending_returns}건',
                    'action': 'return_process'
                })
            
            # 신규 주문
            new_orders = self._get_today_stats()['orders']['new']
            if new_orders > 0:
                alerts.append({
                    'type': 'order',
                    'level': 'info',
                    'message': f'신규 주문 {new_orders}건',
                    'action': 'order_confirm'
                })
                
        except Exception as e:
            logger.error(f"알림 조회 실패: {e}")
        
        return alerts
    
    def get_order_statistics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """주문 통계 상세 조회"""
        stats = {
            'period': f'{start_date} ~ {end_date}',
            'by_status': {},
            'by_date': {},
            'by_product': {},
            'shipping_summary': {}
        }
        
        try:
            orders = self.order_client.get_orders_by_date(
                search_from=start_date,
                search_to=end_date
            )
            
            if orders and 'data' in orders:
                for order in orders['data']:
                    # 상태별 집계
                    status = order.get('status', 'UNKNOWN')
                    stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                    
                    # 날짜별 집계
                    order_date = order.get('orderedAt', '')[:10]
                    if order_date:
                        if order_date not in stats['by_date']:
                            stats['by_date'][order_date] = {'count': 0, 'amount': 0}
                        stats['by_date'][order_date]['count'] += 1
                        stats['by_date'][order_date]['amount'] += order.get('totalPrice', 0)
                    
                    # 상품별 집계
                    for item in order.get('orderItems', []):
                        product_id = item.get('sellerProductId')
                        product_name = item.get('sellerProductName', 'Unknown')
                        if product_id:
                            if product_id not in stats['by_product']:
                                stats['by_product'][product_id] = {
                                    'name': product_name,
                                    'count': 0,
                                    'amount': 0
                                }
                            stats['by_product'][product_id]['count'] += item.get('shippingCount', 1)
                            stats['by_product'][product_id]['amount'] += item.get('orderPrice', 0)
                
                # 배송 요약
                stats['shipping_summary'] = {
                    'preparing': stats['by_status'].get('ACCEPT', 0) + stats['by_status'].get('INSTRUCT', 0),
                    'shipping': stats['by_status'].get('DEPARTURE', 0) + stats['by_status'].get('DELIVERING', 0),
                    'completed': stats['by_status'].get('FINAL_DELIVERY', 0),
                    'cancelled': stats['by_status'].get('CANCEL', 0) + stats['by_status'].get('RETURNS', 0)
                }
                
        except Exception as e:
            logger.error(f"주문 통계 조회 실패: {e}")
        
        return stats
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성과 지표 조회"""
        metrics = {
            'conversion_rate': 0,  # 전환율
            'average_order_value': 0,  # 평균 주문 금액
            'customer_satisfaction': 0,  # 고객 만족도
            'fulfillment_rate': 0,  # 주문 처리율
            'return_rate': 0,  # 반품율
            'response_time': 0  # CS 평균 응답 시간
        }
        
        try:
            # 최근 30일 데이터로 계산
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            # 주문 데이터
            orders = self.order_client.get_orders_by_date(
                search_from=start_date.isoformat(),
                search_to=end_date.isoformat()
            )
            
            if orders and 'data' in orders:
                total_orders = len(orders['data'])
                total_amount = sum(order.get('totalPrice', 0) for order in orders['data'])
                completed_orders = sum(1 for order in orders['data'] 
                                     if order.get('status') == 'FINAL_DELIVERY')
                
                if total_orders > 0:
                    metrics['average_order_value'] = total_amount / total_orders
                    metrics['fulfillment_rate'] = (completed_orders / total_orders) * 100
            
            # 반품율 계산
            returns = self.return_client.get_returns_by_date(
                search_from=start_date.isoformat(),
                search_to=end_date.isoformat()
            )
            
            if returns and 'data' in returns and total_orders > 0:
                total_returns = len(returns['data'])
                metrics['return_rate'] = (total_returns / total_orders) * 100
            
            # CS 응답 시간 (예시)
            inquiries = self.cs_client.get_inquiries_by_date(
                created_at_from=start_date.isoformat(),
                created_at_to=end_date.isoformat()
            )
            
            if inquiries and 'data' in inquiries:
                answered_inquiries = [inq for inq in inquiries['data'] if inq.get('answered')]
                if answered_inquiries:
                    # 실제 응답 시간 계산 로직 필요
                    metrics['response_time'] = 24  # 예시: 24시간
                    metrics['customer_satisfaction'] = 85  # 예시: 85%
                    
        except Exception as e:
            logger.error(f"성과 지표 조회 실패: {e}")
        
        return metrics
    
    def close(self):
        """리소스 정리"""
        if hasattr(self, 'sync_manager'):
            self.sync_manager.close()