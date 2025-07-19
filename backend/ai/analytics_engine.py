#!/usr/bin/env python3
"""
AI 기반 분석 엔진
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.ml_models import SalesPredictionModel, AnomalyDetectionModel
from core import get_logger

logger = get_logger(__name__)


class AIAnalyticsEngine:
    """
AI 기반 비즈니스 분석 엔진
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.sales_model = SalesPredictionModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.models_path = "models/"
        
        # 모델 로드 시도
        self._load_models()
    
    def _load_models(self):
        """저장된 모델 로드"""
        try:
            sales_model_path = os.path.join(self.models_path, "sales_prediction.pkl")
            if os.path.exists(sales_model_path):
                self.sales_model.load(sales_model_path)
                logger.info("매출 예측 모델 로드 성공")
                
            anomaly_model_path = os.path.join(self.models_path, "anomaly_detection.pkl")
            if os.path.exists(anomaly_model_path):
                self.anomaly_model.load(anomaly_model_path)
                logger.info("이상 탐지 모델 로드 성공")
        except Exception as e:
            logger.warning(f"모델 로드 실패: {e}")
    
    def get_sales_data(self, days: int = 90) -> pd.DataFrame:
        """판매 데이터 조회"""
        conn = psycopg2.connect(**self.db_config)
        
        query = """
            SELECT 
                DATE(o.created_at) as date,
                p.id as product_id,
                p.name as product_name,
                p.category,
                p.supplier,
                p.price,
                p.stock as stock_level,
                COUNT(DISTINCT o.id) as order_count,
                SUM(oi.quantity) as quantity_sold,
                SUM(oi.quantity * oi.price) as sales
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(o.created_at), p.id, p.name, p.category, p.supplier, p.price, p.stock
            ORDER BY date, product_id
        """
        
        df = pd.read_sql(query, conn, params=(days,))
        conn.close()
        
        return df
    
    def train_models(self) -> Dict[str, Any]:
        """
AI 모델 학습
        """
        logger.info("AI 모델 학습 시작")
        results = {}
        
        # 데이터 준비
        sales_data = self.get_sales_data(days=180)  # 6개월 데이터
        
        if len(sales_data) < 100:
            logger.warning("학습 데이터 부족")
            return {"error": "학습을 위한 충분한 데이터가 없습니다"}
        
        # 1. 매출 예측 모델 학습
        try:
            sales_results = self.sales_model.train(sales_data)
            self.sales_model.save(os.path.join(self.models_path, "sales_prediction.pkl"))
            results['sales_prediction'] = sales_results
        except Exception as e:
            logger.error(f"매출 예측 모델 학습 실패: {e}")
            results['sales_prediction'] = {"error": str(e)}
        
        # 2. 이상 탐지 모델 학습
        try:
            anomaly_results = self.anomaly_model.train(sales_data)
            self.anomaly_model.save(os.path.join(self.models_path, "anomaly_detection.pkl"))
            results['anomaly_detection'] = anomaly_results
        except Exception as e:
            logger.error(f"이상 탐지 모델 학습 실패: {e}")
            results['anomaly_detection'] = {"error": str(e)}
        
        logger.info("AI 모델 학습 완료")
        return results
    
    def predict_sales(self, product_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """매출 예측"""
        if not self.sales_model.is_trained:
            return {"error": "매출 예측 모델이 학습되지 않았습니다"}
        
        # 예측을 위한 미래 날짜 생성
        future_dates = pd.date_range(
            start=datetime.now().date() + timedelta(days=1),
            periods=days,
            freq='D'
        )
        
        # 제품 정보 조회
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if product_id:
            cursor.execute(
                "SELECT * FROM products WHERE id = %s",
                (product_id,)
            )
            products = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT * FROM products WHERE stock > 0 LIMIT 10"
            )
            products = cursor.fetchall()
        
        predictions = []
        
        for product in products:
            # 각 날짜별 예측 데이터 생성
            prediction_data = []
            
            for date in future_dates:
                row = {
                    'date': date,
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'category': product['category'],
                    'supplier': product['supplier'],
                    'price': product['price'],
                    'stock_level': product['stock'],
                    'promotion_active': 0,  # 기본값
                    'avg_sales_last_7days': 0,  # TODO: 실제 계산
                    'avg_sales_last_30days': 0  # TODO: 실제 계산
                }
                prediction_data.append(row)
            
            # 예측 수행
            df = pd.DataFrame(prediction_data)
            predicted_sales = self.sales_model.predict(df)
            
            # 결과 저장
            for i, (date, sales) in enumerate(zip(future_dates, predicted_sales)):
                predictions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'predicted_sales': float(sales),
                    'predicted_revenue': float(sales * product['price'])
                })
        
        conn.close()
        
        # 집계
        total_by_date = {}
        for pred in predictions:
            date = pred['date']
            if date not in total_by_date:
                total_by_date[date] = 0
            total_by_date[date] += pred['predicted_revenue']
        
        return {
            'predictions': predictions,
            'summary': {
                'total_predicted_revenue': sum(total_by_date.values()),
                'daily_average': sum(total_by_date.values()) / len(total_by_date),
                'by_date': total_by_date
            }
        }
    
    def detect_anomalies(self, data_type: str = 'sales') -> Dict[str, Any]:
        """이상치 탐지"""
        if not self.anomaly_model.is_trained:
            return {"error": "이상 탐지 모델이 학습되지 않았습니다"}
        
        # 최근 데이터 조회
        if data_type == 'sales':
            data = self.get_sales_data(days=7)
        else:
            # 다른 데이터 타입 처리
            return {"error": f"지원되지 않는 데이터 타입: {data_type}"}
        
        if len(data) == 0:
            return {"anomalies": [], "message": "분석할 데이터가 없습니다"}
        
        # 이상치 탐지
        predictions, scores = self.anomaly_model.detect(data)
        
        # 이상치 필터링
        anomalies = []
        for idx, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # 이상치
                row = data.iloc[idx]
                anomalies.append({
                    'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else None,
                    'product_id': int(row['product_id']) if pd.notna(row['product_id']) else None,
                    'product_name': row.get('product_name', 'Unknown'),
                    'anomaly_score': float(score),
                    'details': {
                        'sales': float(row.get('sales', 0)),
                        'quantity_sold': int(row.get('quantity_sold', 0)),
                        'order_count': int(row.get('order_count', 0))
                    }
                })
        
        return {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'total_analyzed': len(data),
            'anomaly_rate': len(anomalies) / len(data) if len(data) > 0 else 0
        }
    
    def get_insights(self) -> Dict[str, Any]:
        """비즈니스 인사이트 생성"""
        insights = {
            'generated_at': datetime.now().isoformat(),
            'insights': []
        }
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. 매출 트렌드 분석
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                SUM(total_amount) as daily_revenue
            FROM orders
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        revenue_data = cursor.fetchall()
        if len(revenue_data) > 7:
            # 주간 비교
            last_week = sum(r['daily_revenue'] for r in revenue_data[-7:])
            prev_week = sum(r['daily_revenue'] for r in revenue_data[-14:-7])
            
            if prev_week > 0:
                growth_rate = (last_week - prev_week) / prev_week * 100
                
                if growth_rate > 10:
                    insights['insights'].append({
                        'type': 'revenue_growth',
                        'severity': 'positive',
                        'message': f"지난주 매출이 전주 대비 {growth_rate:.1f}% 증가했습니다",
                        'value': growth_rate
                    })
                elif growth_rate < -10:
                    insights['insights'].append({
                        'type': 'revenue_decline',
                        'severity': 'warning',
                        'message': f"지난주 매출이 전주 대비 {abs(growth_rate):.1f}% 감소했습니다",
                        'value': growth_rate
                    })
        
        # 2. 재고 부족 경고
        cursor.execute("""
            SELECT 
                p.id, p.name, p.stock, p.category,
                COALESCE(AVG(oi.quantity), 0) as avg_daily_sales
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id 
                AND o.created_at >= CURRENT_DATE - INTERVAL '7 days'
            WHERE p.stock > 0
            GROUP BY p.id, p.name, p.stock, p.category
            HAVING p.stock < COALESCE(AVG(oi.quantity), 0) * 7
        """)
        
        low_stock_products = cursor.fetchall()
        if low_stock_products:
            insights['insights'].append({
                'type': 'low_stock_alert',
                'severity': 'warning',
                'message': f"{len(low_stock_products)}개 상품의 재고가 일주일 내 소진될 것으로 예상됩니다",
                'products': [
                    {
                        'id': p['id'],
                        'name': p['name'],
                        'current_stock': p['stock'],
                        'days_remaining': int(p['stock'] / p['avg_daily_sales']) if p['avg_daily_sales'] > 0 else 999
                    }
                    for p in low_stock_products[:5]  # 상위 5개만
                ]
            })
        
        # 3. 베스트셀러 분석
        cursor.execute("""
            SELECT 
                p.id, p.name, p.category,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.quantity * oi.price) as total_revenue
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.id, p.name, p.category
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        
        best_sellers = cursor.fetchall()
        if best_sellers:
            insights['insights'].append({
                'type': 'best_sellers',
                'severity': 'info',
                'message': "지난 30일간 베스트셀러 상품",
                'products': [
                    {
                        'id': p['id'],
                        'name': p['name'],
                        'category': p['category'],
                        'revenue': float(p['total_revenue']),
                        'quantity_sold': int(p['total_quantity'])
                    }
                    for p in best_sellers[:5]
                ]
            })
        
        # 4. 카테고리별 성과
        cursor.execute("""
            SELECT 
                p.category,
                COUNT(DISTINCT p.id) as product_count,
                SUM(oi.quantity * oi.price) as total_revenue,
                AVG(oi.quantity * oi.price) as avg_order_value
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """)
        
        category_performance = cursor.fetchall()
        if category_performance:
            top_category = category_performance[0]
            insights['insights'].append({
                'type': 'top_category',
                'severity': 'info',
                'message': f"최고 매출 카테고리는 '{top_category['category']}'입니다",
                'details': {
                    'category': top_category['category'],
                    'revenue': float(top_category['total_revenue']),
                    'avg_order_value': float(top_category['avg_order_value'])
                }
            })
        
        cursor.close()
        conn.close()
        
        return insights