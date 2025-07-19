#!/usr/bin/env python3
"""
캐싱이 적용된 API 엔드포인트 예제
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from cache import cache, cache_invalidate, CacheManager, get_redis_client
import logging

logger = logging.getLogger(__name__)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres',
    'password': '1234'
}

# 캐시 매니저
cache_manager = CacheManager()


class CachedProductService:
    """캐싱이 적용된 제품 서비스"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    @cache(prefix="products", ttl=3600)
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """제품 상세 조회 (1시간 캐싱)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT p.*, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return product
    
    @cache(prefix="products", ttl=300, key_builder=lambda **kwargs: f"list:{kwargs.get('category', 'all')}:{kwargs.get('page', 1)}")
    def list_products(self, category: Optional[str] = None, page: int = 1, 
                     page_size: int = 20) -> Dict[str, Any]:
        """제품 목록 조회 (5분 캐싱)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        offset = (page - 1) * page_size
        
        # 기본 쿼리
        query = """
            SELECT p.*, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
        """
        params = []
        
        # 카테고리 필터
        if category:
            query += " WHERE p.category = %s"
            params.append(category)
        
        # 전체 개수
        count_query = f"SELECT COUNT(*) as total FROM ({query}) t"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # 페이징
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'products': products,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    @cache_invalidate(prefix="products", key_builder=lambda product_id, **kwargs: f"{product_id}")
    @cache_invalidate(patterns=["products:list:*"])
    def update_product(self, product_id: int, data: Dict[str, Any]) -> bool:
        """제품 업데이트 (관련 캐시 무효화)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # 업데이트 쿼리 생성
        fields = []
        values = []
        for key, value in data.items():
            if key in ['name', 'category', 'price', 'stock', 'description']:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        # 태그 기반 캐시 무효화
        if success and 'category' in data:
            cache_manager.invalidate_by_tag(f"category:{data['category']}")
        
        return success
    
    @cache(prefix="products:bestsellers", ttl=1800)
    def get_bestsellers(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """베스트셀러 조회 (30분 캐싱)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                p.*,
                COUNT(DISTINCT o.id) as order_count,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.quantity * oi.price) as total_revenue
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY p.id
            ORDER BY total_revenue DESC
            LIMIT %s
        """, (days, limit))
        
        bestsellers = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return bestsellers


class CachedOrderService:
    """캐싱이 적용된 주문 서비스"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.redis = get_redis_client()
    
    @cache(prefix="orders", ttl=600, key_builder=lambda order_id: f"detail:{order_id}")
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """주문 상세 조회 (10분 캐싱)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 주문 정보
        cursor.execute("""
            SELECT o.*, 
                   COUNT(oi.id) as item_count,
                   SUM(oi.quantity) as total_quantity
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = %s
            GROUP BY o.id
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if order:
            # 주문 아이템
            cursor.execute("""
                SELECT oi.*, p.name as product_name, p.category
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,))
            
            order['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return order
    
    def get_user_orders(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """사용자 주문 목록 (슬라이딩 캐싱)"""
        cache_key = f"orders:user:{user_id}:{status or 'all'}"
        
        # 슬라이딩 만료로 캐시 조회
        orders = cache_manager.get_with_sliding_expiration(cache_key)
        
        if orders is not None:
            return orders
        
        # DB 조회
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT o.*, 
                   COUNT(oi.id) as item_count,
                   SUM(oi.quantity * oi.price) as total_amount
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.customer_id = %s
        """
        params = [user_id]
        
        if status:
            query += " AND o.status = %s"
            params.append(status)
        
        query += " GROUP BY o.id ORDER BY o.created_at DESC"
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 슬라이딩 만료로 캐시 저장
        cache_manager.set_with_sliding_expiration(cache_key, orders, ttl=900)
        
        return orders
    
    @cache_invalidate(patterns=["orders:user:*", "orders:stats:*"])
    def create_order(self, order_data: Dict[str, Any]) -> int:
        """주문 생성 (관련 캐시 무효화)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # 주문 생성
        cursor.execute("""
            INSERT INTO orders (customer_id, customer_name, status, total_amount, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            order_data['customer_id'],
            order_data['customer_name'],
            'pending',
            order_data['total_amount'],
            order_data['shipping_address']
        ))
        
        order_id = cursor.fetchone()[0]
        
        # 주문 아이템 생성
        for item in order_data['items']:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return order_id


class CachedAnalyticsService:
    """캐싱이 적용된 분석 서비스"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.cache_manager = CacheManager()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 통계 (다단계 캐싱)"""
        return self.cache_manager.get_multi_level(
            key="analytics:dashboard:stats",
            loaders=[
                lambda: self._get_cached_stats(),
                lambda: self._calculate_stats()
            ],
            ttls=[300, 3600]  # 5분, 1시간
        )
    
    def _get_cached_stats(self) -> Optional[Dict[str, Any]]:
        """메모리 캐시에서 통계 조회"""
        # 실제로는 메모리 캐시 구현
        return None
    
    @cache(prefix="analytics", ttl=3600)
    def _calculate_stats(self) -> Dict[str, Any]:
        """통계 계산"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        stats = {}
        
        # 오늘 주문
        cursor.execute("""
            SELECT 
                COUNT(*) as today_orders,
                COALESCE(SUM(total_amount), 0) as today_revenue
            FROM orders
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        stats.update(cursor.fetchone())
        
        # 이번 달 통계
        cursor.execute("""
            SELECT 
                COUNT(*) as month_orders,
                COALESCE(SUM(total_amount), 0) as month_revenue
            FROM orders
            WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
        """)
        stats.update(cursor.fetchone())
        
        # 재고 현황
        cursor.execute("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN stock < 10 THEN 1 END) as low_stock_count,
                SUM(stock * price) as inventory_value
            FROM products
        """)
        stats.update(cursor.fetchone())
        
        # 인기 카테고리
        cursor.execute("""
            SELECT 
                p.category,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.quantity * oi.price) as revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY p.category
            ORDER BY revenue DESC
            LIMIT 5
        """)
        stats['top_categories'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return stats
    
    @cache(prefix="analytics:sales", ttl=timedelta(hours=6),
           condition=lambda start_date, end_date: (end_date - start_date).days >= 7)
    def get_sales_trend(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """매출 트렌드 (조건부 캐싱 - 7일 이상 기간만)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as order_count,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_order_value
            FROM orders
            WHERE created_at BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date))
        
        trend = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return trend


# 캐시 워밍 함수
def warm_critical_caches():
    """중요 캐시 사전 로딩"""
    logger.info("캐시 워밍 시작")
    
    product_service = CachedProductService(DB_CONFIG)
    analytics_service = CachedAnalyticsService(DB_CONFIG)
    
    configs = [
        {
            'key': 'products:bestsellers',
            'loader': lambda: product_service.get_bestsellers(),
            'ttl': 1800
        },
        {
            'key': 'analytics:dashboard:stats',
            'loader': lambda: analytics_service._calculate_stats(),
            'ttl': 3600
        }
    ]
    
    cache_manager = CacheManager()
    warmed = cache_manager.warm_cache(configs)
    
    logger.info(f"캐시 워밍 완료: {warmed}개")
    return warmed