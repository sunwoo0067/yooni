"""
쿠팡 통계 분석기
판매 데이터 분석 및 인사이트 제공
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict
import statistics

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from market_manager import MarketProduct, MarketOrder

logger = logging.getLogger(__name__)

class CoupangStatsAnalyzer:
    """쿠팡 통계 분석 클래스"""
    
    def __init__(self):
        self.product_manager = MarketProduct()
        self.order_manager = MarketOrder()
    
    def analyze_sales_trend(self, days: int = 30) -> Dict[str, Any]:
        """판매 트렌드 분석"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 일별 판매 데이터 수집
        daily_sales = defaultdict(lambda: {'count': 0, 'amount': 0})
        
        try:
            # DB에서 주문 데이터 조회
            orders = self.order_manager.get_orders(
                market_code='coupang',
                start_date=start_date,
                end_date=end_date
            )
            
            for order in orders:
                order_date = order['order_date'].date()
                daily_sales[order_date]['count'] += 1
                daily_sales[order_date]['amount'] += order['total_price']
            
            # 트렌드 분석
            dates = sorted(daily_sales.keys())
            if len(dates) >= 2:
                # 매출 성장률 계산
                first_week_sales = sum(daily_sales[d]['amount'] for d in dates[:7])
                last_week_sales = sum(daily_sales[d]['amount'] for d in dates[-7:])
                
                growth_rate = 0
                if first_week_sales > 0:
                    growth_rate = ((last_week_sales - first_week_sales) / first_week_sales) * 100
                
                # 일별 평균
                daily_amounts = [daily_sales[d]['amount'] for d in dates]
                daily_counts = [daily_sales[d]['count'] for d in dates]
                
                trend_analysis = {
                    'period': f'{start_date.date()} ~ {end_date.date()}',
                    'total_sales': sum(daily_amounts),
                    'total_orders': sum(daily_counts),
                    'daily_average': {
                        'amount': statistics.mean(daily_amounts) if daily_amounts else 0,
                        'count': statistics.mean(daily_counts) if daily_counts else 0
                    },
                    'growth_rate': growth_rate,
                    'best_day': self._find_best_day(daily_sales),
                    'worst_day': self._find_worst_day(daily_sales),
                    'weekly_pattern': self._analyze_weekly_pattern(daily_sales)
                }
                
                return trend_analysis
            
        except Exception as e:
            logger.error(f"판매 트렌드 분석 실패: {e}")
        
        return {
            'error': '데이터 부족',
            'period': f'{start_date.date()} ~ {end_date.date()}'
        }
    
    def analyze_product_performance(self, days: int = 30) -> Dict[str, Any]:
        """상품별 성과 분석"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        product_stats = defaultdict(lambda: {
            'name': '',
            'orders': 0,
            'quantity': 0,
            'revenue': 0,
            'returns': 0,
            'rating': 0
        })
        
        try:
            # 주문 데이터에서 상품별 집계
            orders = self.order_manager.get_orders(
                market_code='coupang',
                start_date=start_date,
                end_date=end_date
            )
            
            for order in orders:
                for item in order.get('items', []):
                    product_id = item['market_product_id']
                    product_stats[product_id]['name'] = item['product_name']
                    product_stats[product_id]['orders'] += 1
                    product_stats[product_id]['quantity'] += item['quantity']
                    product_stats[product_id]['revenue'] += item['total_price']
                    
                    if item.get('item_status') in ['cancelled', 'returned']:
                        product_stats[product_id]['returns'] += 1
            
            # 상위 10개 상품
            top_products = sorted(
                product_stats.items(),
                key=lambda x: x[1]['revenue'],
                reverse=True
            )[:10]
            
            # 하위 10개 상품
            bottom_products = sorted(
                product_stats.items(),
                key=lambda x: x[1]['revenue']
            )[:10]
            
            # 반품률 높은 상품
            high_return_products = [
                (pid, stats) for pid, stats in product_stats.items()
                if stats['orders'] > 0 and (stats['returns'] / stats['orders']) > 0.1
            ]
            
            return {
                'period': f'{start_date.date()} ~ {end_date.date()}',
                'total_products': len(product_stats),
                'top_products': [
                    {
                        'id': pid,
                        'name': stats['name'],
                        'revenue': stats['revenue'],
                        'orders': stats['orders'],
                        'avg_order_value': stats['revenue'] / stats['orders'] if stats['orders'] > 0 else 0
                    }
                    for pid, stats in top_products
                ],
                'bottom_products': [
                    {
                        'id': pid,
                        'name': stats['name'],
                        'revenue': stats['revenue'],
                        'orders': stats['orders']
                    }
                    for pid, stats in bottom_products
                ],
                'high_return_products': [
                    {
                        'id': pid,
                        'name': stats['name'],
                        'return_rate': (stats['returns'] / stats['orders']) * 100,
                        'returns': stats['returns'],
                        'orders': stats['orders']
                    }
                    for pid, stats in high_return_products
                ]
            }
            
        except Exception as e:
            logger.error(f"상품 성과 분석 실패: {e}")
            return {'error': str(e)}
    
    def analyze_customer_behavior(self, days: int = 30) -> Dict[str, Any]:
        """고객 행동 분석"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        customer_stats = defaultdict(lambda: {
            'orders': 0,
            'total_spent': 0,
            'products': set(),
            'first_order': None,
            'last_order': None
        })
        
        try:
            orders = self.order_manager.get_orders(
                market_code='coupang',
                start_date=start_date,
                end_date=end_date
            )
            
            for order in orders:
                buyer_email = order.get('buyer_email') or order.get('buyer_phone')
                if not buyer_email:
                    continue
                
                customer_stats[buyer_email]['orders'] += 1
                customer_stats[buyer_email]['total_spent'] += order['total_price']
                
                order_date = order['order_date']
                if not customer_stats[buyer_email]['first_order'] or order_date < customer_stats[buyer_email]['first_order']:
                    customer_stats[buyer_email]['first_order'] = order_date
                if not customer_stats[buyer_email]['last_order'] or order_date > customer_stats[buyer_email]['last_order']:
                    customer_stats[buyer_email]['last_order'] = order_date
                
                for item in order.get('items', []):
                    customer_stats[buyer_email]['products'].add(item['market_product_id'])
            
            # 고객 세그먼트 분석
            vip_customers = []  # 3회 이상 구매
            regular_customers = []  # 2회 구매
            new_customers = []  # 1회 구매
            
            for customer, stats in customer_stats.items():
                customer_data = {
                    'customer': customer[:3] + '***',  # 개인정보 보호
                    'orders': stats['orders'],
                    'total_spent': stats['total_spent'],
                    'avg_order_value': stats['total_spent'] / stats['orders'],
                    'unique_products': len(stats['products']),
                    'days_since_first': (end_date - stats['first_order']).days if stats['first_order'] else 0,
                    'days_since_last': (end_date - stats['last_order']).days if stats['last_order'] else 0
                }
                
                if stats['orders'] >= 3:
                    vip_customers.append(customer_data)
                elif stats['orders'] == 2:
                    regular_customers.append(customer_data)
                else:
                    new_customers.append(customer_data)
            
            # VIP 고객 정렬 (구매액 기준)
            vip_customers.sort(key=lambda x: x['total_spent'], reverse=True)
            
            return {
                'period': f'{start_date.date()} ~ {end_date.date()}',
                'total_customers': len(customer_stats),
                'customer_segments': {
                    'vip': {
                        'count': len(vip_customers),
                        'percentage': (len(vip_customers) / len(customer_stats) * 100) if customer_stats else 0,
                        'top_customers': vip_customers[:10]
                    },
                    'regular': {
                        'count': len(regular_customers),
                        'percentage': (len(regular_customers) / len(customer_stats) * 100) if customer_stats else 0
                    },
                    'new': {
                        'count': len(new_customers),
                        'percentage': (len(new_customers) / len(customer_stats) * 100) if customer_stats else 0
                    }
                },
                'average_customer_value': sum(s['total_spent'] for s in customer_stats.values()) / len(customer_stats) if customer_stats else 0,
                'repeat_purchase_rate': (len(vip_customers) + len(regular_customers)) / len(customer_stats) * 100 if customer_stats else 0
            }
            
        except Exception as e:
            logger.error(f"고객 행동 분석 실패: {e}")
            return {'error': str(e)}
    
    def _find_best_day(self, daily_sales: Dict) -> Dict[str, Any]:
        """최고 매출일 찾기"""
        if not daily_sales:
            return {}
        
        best_day = max(daily_sales.items(), key=lambda x: x[1]['amount'])
        return {
            'date': best_day[0].isoformat(),
            'amount': best_day[1]['amount'],
            'orders': best_day[1]['count']
        }
    
    def _find_worst_day(self, daily_sales: Dict) -> Dict[str, Any]:
        """최저 매출일 찾기"""
        if not daily_sales:
            return {}
        
        worst_day = min(daily_sales.items(), key=lambda x: x[1]['amount'])
        return {
            'date': worst_day[0].isoformat(),
            'amount': worst_day[1]['amount'],
            'orders': worst_day[1]['count']
        }
    
    def _analyze_weekly_pattern(self, daily_sales: Dict) -> Dict[str, Any]:
        """요일별 패턴 분석"""
        weekday_stats = defaultdict(lambda: {'total': 0, 'count': 0})
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        
        for date, sales in daily_sales.items():
            weekday = date.weekday()
            weekday_stats[weekday]['total'] += sales['amount']
            weekday_stats[weekday]['count'] += 1
        
        pattern = {}
        for weekday, stats in weekday_stats.items():
            if stats['count'] > 0:
                pattern[weekday_names[weekday]] = {
                    'average': stats['total'] / stats['count'],
                    'days': stats['count']
                }
        
        return pattern
    
    def generate_insights(self) -> List[Dict[str, Any]]:
        """주요 인사이트 생성"""
        insights = []
        
        try:
            # 최근 7일 vs 이전 7일 비교
            recent_trend = self.analyze_sales_trend(days=14)
            if recent_trend and 'growth_rate' in recent_trend:
                if recent_trend['growth_rate'] > 20:
                    insights.append({
                        'type': 'positive',
                        'category': 'sales',
                        'message': f"매출이 지난주 대비 {recent_trend['growth_rate']:.1f}% 증가했습니다!",
                        'action': '성장 요인을 분석하여 지속하세요.'
                    })
                elif recent_trend['growth_rate'] < -20:
                    insights.append({
                        'type': 'negative',
                        'category': 'sales',
                        'message': f"매출이 지난주 대비 {abs(recent_trend['growth_rate']):.1f}% 감소했습니다.",
                        'action': '마케팅 강화나 프로모션을 고려하세요.'
                    })
            
            # 상품 성과 인사이트
            product_performance = self.analyze_product_performance(days=30)
            if product_performance and 'high_return_products' in product_performance:
                high_returns = product_performance['high_return_products']
                if high_returns:
                    insights.append({
                        'type': 'warning',
                        'category': 'product',
                        'message': f"{len(high_returns)}개 상품의 반품률이 10%를 초과합니다.",
                        'action': '상품 품질이나 설명을 개선하세요.',
                        'details': high_returns[:3]  # 상위 3개만
                    })
            
            # 고객 행동 인사이트
            customer_behavior = self.analyze_customer_behavior(days=30)
            if customer_behavior and 'repeat_purchase_rate' in customer_behavior:
                repeat_rate = customer_behavior['repeat_purchase_rate']
                if repeat_rate < 20:
                    insights.append({
                        'type': 'warning',
                        'category': 'customer',
                        'message': f"재구매율이 {repeat_rate:.1f}%로 낮습니다.",
                        'action': '고객 만족도 향상 방안을 마련하세요.'
                    })
                elif repeat_rate > 40:
                    insights.append({
                        'type': 'positive',
                        'category': 'customer',
                        'message': f"재구매율이 {repeat_rate:.1f}%로 우수합니다!",
                        'action': 'VIP 고객 관리 프로그램을 강화하세요.'
                    })
            
        except Exception as e:
            logger.error(f"인사이트 생성 실패: {e}")
        
        return insights
    
    def close(self):
        """리소스 정리"""
        if hasattr(self, 'product_manager'):
            self.product_manager.close()
        if hasattr(self, 'order_manager'):
            self.order_manager.close()