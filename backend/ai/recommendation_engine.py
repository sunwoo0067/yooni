#!/usr/bin/env python3
"""
추천 시스템 엔진
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    상품 추천 엔진
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.product_features = None
        self.similarity_matrix = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english'
        )
    
    def build_product_features(self):
        """상품 특성 행렬 구축"""
        conn = psycopg2.connect(**self.db_config)
        
        # 상품 정보 및 판매 통계 조회
        query = """
            SELECT 
                p.id,
                p.name,
                p.category,
                p.supplier,
                p.price,
                p.stock,
                COALESCE(p.description, '') as description,
                COUNT(DISTINCT oi.order_id) as order_count,
                COALESCE(SUM(oi.quantity), 0) as total_sold,
                COALESCE(AVG(oi.price), p.price) as avg_selling_price
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            GROUP BY p.id, p.name, p.category, p.supplier, p.price, p.stock, p.description
        """
        
        self.product_features = pd.read_sql(query, conn)
        conn.close()
        
        # 텍스트 특성 처리 (name + description)
        text_features = self.product_features['name'] + ' ' + self.product_features['description']
        text_features = text_features.fillna('')
        
        # TF-IDF 벡터화
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
        
        # 카테고리 원핫 인코딩
        category_dummies = pd.get_dummies(self.product_features['category'], prefix='cat')
        supplier_dummies = pd.get_dummies(self.product_features['supplier'], prefix='sup')
        
        # 수치 특성 정규화
        numeric_features = self.product_features[['price', 'stock', 'order_count', 'total_sold']].fillna(0)
        numeric_features = (numeric_features - numeric_features.mean()) / (numeric_features.std() + 1e-8)
        
        # 모든 특성 결합
        combined_features = np.hstack([
            tfidf_matrix.toarray(),
            category_dummies.values,
            supplier_dummies.values,
            numeric_features.values
        ])
        
        # 유사도 행렬 계산
        self.similarity_matrix = cosine_similarity(combined_features)
        
        logger.info(f"상품 특성 행렬 구축 완료: {len(self.product_features)}개 상품")
    
    def get_similar_products(self, product_id: int, n: int = 5) -> List[Dict[str, Any]]:
        """유사 상품 추천"""
        if self.similarity_matrix is None:
            self.build_product_features()
        
        # 상품 인덱스 찾기
        try:
            idx = self.product_features[self.product_features['id'] == product_id].index[0]
        except IndexError:
            logger.warning(f"상품 ID {product_id}를 찾을 수 없습니다")
            return []
        
        # 유사도 점수 가져오기
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # 자기 자신을 제외한 상위 N개
        sim_scores = sim_scores[1:n+1]
        
        # 추천 상품 정보 구성
        recommendations = []
        for i, score in sim_scores:
            product = self.product_features.iloc[i]
            recommendations.append({
                'product_id': int(product['id']),
                'name': product['name'],
                'category': product['category'],
                'price': float(product['price']),
                'similarity_score': float(score),
                'popularity_score': int(product['order_count'])
            })
        
        return recommendations
    
    def get_cross_sell_recommendations(self, product_ids: List[int], n: int = 5) -> List[Dict[str, Any]]:
        """교차 판매 추천 (함께 구매된 상품)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 함께 구매된 상품 찾기
        query = """
            WITH target_orders AS (
                SELECT DISTINCT order_id
                FROM order_items
                WHERE product_id = ANY(%s)
            )
            SELECT 
                p.id,
                p.name,
                p.category,
                p.price,
                COUNT(DISTINCT oi.order_id) as co_purchase_count,
                SUM(oi.quantity) as total_quantity
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id IN (SELECT order_id FROM target_orders)
                AND oi.product_id != ALL(%s)
            GROUP BY p.id, p.name, p.category, p.price
            ORDER BY co_purchase_count DESC
            LIMIT %s
        """
        
        cursor.execute(query, (product_ids, product_ids, n))
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            recommendations.append({
                'product_id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'price': float(row['price']),
                'co_purchase_count': row['co_purchase_count'],
                'confidence': row['co_purchase_count'] / len(product_ids)  # 신뢰도
            })
        
        cursor.close()
        conn.close()
        
        return recommendations
    
    def get_personalized_recommendations(self, customer_id: str, n: int = 10) -> List[Dict[str, Any]]:
        """개인화된 추천"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 고객의 구매 이력 분석
        cursor.execute("""
            SELECT 
                p.category,
                p.supplier,
                AVG(p.price) as avg_price,
                COUNT(DISTINCT p.id) as product_count
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.customer_id = %s
            GROUP BY p.category, p.supplier
            ORDER BY product_count DESC
        """, (customer_id,))
        
        purchase_history = cursor.fetchall()
        
        if not purchase_history:
            # 구매 이력이 없는 경우 인기 상품 추천
            return self.get_trending_products(n)
        
        # 선호 카테고리와 가격대 파악
        preferred_categories = [h['category'] for h in purchase_history[:3]]
        avg_price_range = np.mean([h['avg_price'] for h in purchase_history])
        
        # 추천 상품 조회
        query = """
            SELECT DISTINCT
                p.id,
                p.name,
                p.category,
                p.price,
                p.supplier,
                COALESCE(recent_sales.order_count, 0) as recent_popularity,
                ABS(p.price - %s) as price_distance
            FROM products p
            LEFT JOIN (
                SELECT 
                    product_id,
                    COUNT(DISTINCT order_id) as order_count
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY product_id
            ) recent_sales ON p.id = recent_sales.product_id
            WHERE p.category = ANY(%s)
                AND p.stock > 0
                AND p.id NOT IN (
                    SELECT DISTINCT oi.product_id
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.customer_id = %s
                )
            ORDER BY 
                recent_popularity DESC,
                price_distance ASC
            LIMIT %s
        """
        
        cursor.execute(query, (avg_price_range, preferred_categories, customer_id, n))
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            recommendations.append({
                'product_id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'price': float(row['price']),
                'relevance_score': float(1 / (1 + row['price_distance'] / 1000)),  # 가격 관련성
                'popularity_score': row['recent_popularity']
            })
        
        cursor.close()
        conn.close()
        
        return recommendations
    
    def get_trending_products(self, n: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """트렌딩 상품 추천"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            WITH recent_sales AS (
                SELECT 
                    oi.product_id,
                    COUNT(DISTINCT oi.order_id) as recent_orders,
                    SUM(oi.quantity) as recent_quantity
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY oi.product_id
            ),
            previous_sales AS (
                SELECT 
                    oi.product_id,
                    COUNT(DISTINCT oi.order_id) as prev_orders
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
                    AND o.created_at < CURRENT_DATE - INTERVAL '%s days'
                GROUP BY oi.product_id
            )
            SELECT 
                p.id,
                p.name,
                p.category,
                p.price,
                rs.recent_orders,
                rs.recent_quantity,
                COALESCE(ps.prev_orders, 0) as prev_orders,
                CASE 
                    WHEN COALESCE(ps.prev_orders, 0) = 0 THEN rs.recent_orders * 2
                    ELSE rs.recent_orders::float / ps.prev_orders
                END as growth_rate
            FROM products p
            JOIN recent_sales rs ON p.id = rs.product_id
            LEFT JOIN previous_sales ps ON p.id = ps.product_id
            WHERE p.stock > 0
            ORDER BY growth_rate DESC, recent_orders DESC
            LIMIT %s
        """
        
        cursor.execute(query, (days, days * 2, days, n))
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            recommendations.append({
                'product_id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'price': float(row['price']),
                'recent_orders': row['recent_orders'],
                'growth_rate': float(row['growth_rate']),
                'trend_score': float(row['growth_rate'] * row['recent_orders'])  # 트렌드 점수
            })
        
        cursor.close()
        conn.close()
        
        return recommendations
    
    def get_bundle_recommendations(self, product_id: int, n: int = 3) -> List[Dict[str, Any]]:
        """번들 상품 추천"""
        # 유사 상품 찾기
        similar_products = self.get_similar_products(product_id, n=10)
        
        # 교차 판매 상품 찾기
        cross_sell_products = self.get_cross_sell_recommendations([product_id], n=10)
        
        # 번들 구성
        bundles = []
        
        # 유사 상품 + 교차 판매 조합
        for similar in similar_products[:n]:
            for cross in cross_sell_products[:n]:
                if similar['product_id'] != cross['product_id']:
                    bundles.append({
                        'bundle_products': [
                            product_id,
                            similar['product_id'],
                            cross['product_id']
                        ],
                        'bundle_score': (
                            similar['similarity_score'] * 0.5 + 
                            cross['confidence'] * 0.5
                        ),
                        'products': [similar, cross]
                    })
        
        # 점수순 정렬
        bundles = sorted(bundles, key=lambda x: x['bundle_score'], reverse=True)
        
        return bundles[:n]