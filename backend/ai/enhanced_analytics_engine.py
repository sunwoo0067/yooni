#!/usr/bin/env python3
"""
향상된 AI 분석 엔진 - 실시간 모니터링 및 성능 개선
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
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.enhanced_models import EnhancedSalesPredictionModel, EnhancedAnomalyDetectionModel
from core import get_logger

logger = get_logger(__name__)


class EnhancedAIAnalyticsEngine:
    """
    향상된 AI 기반 비즈니스 분석 엔진
    - 실시간 모니터링
    - 캐싱
    - 병렬 처리
    - 자동 재학습
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.sales_model = EnhancedSalesPredictionModel(db_config)
        self.anomaly_model = EnhancedAnomalyDetectionModel(db_config)
        self.models_path = "models/enhanced/"
        
        # 캐시 시스템
        self.cache = {}
        self.cache_ttl = {}
        self.cache_lock = threading.Lock()
        
        # 성능 모니터링
        self.performance_metrics = {
            'prediction_count': 0,
            'total_prediction_time': 0,
            'error_count': 0,
            'last_training_time': None,
            'model_accuracy': {}
        }
        
        # 스레드풀
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 자동 모델 로드
        self._load_models()
        
        # 백그라운드 작업 시작
        self._start_background_tasks()
    
    def _load_models(self):
        """저장된 향상된 모델 로드"""
        try:
            os.makedirs(self.models_path, exist_ok=True)
            
            sales_model_path = os.path.join(self.models_path, "enhanced_sales_prediction.pkl")
            if os.path.exists(sales_model_path):
                self.sales_model.load(sales_model_path)
                logger.info("향상된 매출 예측 모델 로드 성공")
                
            anomaly_model_path = os.path.join(self.models_path, "enhanced_anomaly_detection.pkl")
            if os.path.exists(anomaly_model_path):
                self.anomaly_model.load(anomaly_model_path)
                logger.info("향상된 이상 탐지 모델 로드 성공")
        except Exception as e:
            logger.warning(f"모델 로드 실패: {e}")
    
    def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        # 캐시 정리 스레드
        threading.Thread(target=self._cache_cleanup_worker, daemon=True).start()
        
        # 자동 재학습 스레드
        threading.Thread(target=self._auto_retrain_worker, daemon=True).start()
        
        logger.info("백그라운드 작업 시작됨")
    
    def _cache_cleanup_worker(self):
        """캐시 정리 워커"""
        while True:
            time.sleep(300)  # 5분마다 실행
            current_time = time.time()
            
            with self.cache_lock:
                expired_keys = [
                    key for key, ttl in self.cache_ttl.items()
                    if current_time > ttl
                ]
                
                for key in expired_keys:
                    del self.cache[key]
                    del self.cache_ttl[key]
                
                if expired_keys:
                    logger.info(f"캐시 정리 완료: {len(expired_keys)}개 항목 삭제")
    
    def _auto_retrain_worker(self):
        """자동 재학습 워커"""
        while True:
            time.sleep(86400)  # 24시간마다 실행
            
            try:
                # 데이터 변화량 확인
                data_change = self._check_data_changes()
                
                if data_change > 0.1:  # 10% 이상 변화 시 재학습
                    logger.info(f"데이터 변화 감지 ({data_change:.1%}), 자동 재학습 시작")
                    self.train_models()
                    
            except Exception as e:
                logger.error(f"자동 재학습 오류: {e}")
    
    def _check_data_changes(self) -> float:
        """데이터 변화량 확인"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 최근 7일 vs 이전 7일 주문 수 비교
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as recent_orders,
                    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '14 days' 
                                    AND created_at < CURRENT_DATE - INTERVAL '7 days') as prev_orders
                FROM orders
            """)
            
            result = cursor.fetchone()
            recent_orders, prev_orders = result
            
            if prev_orders > 0:
                change_rate = abs(recent_orders - prev_orders) / prev_orders
            else:
                change_rate = 1.0 if recent_orders > 0 else 0.0
            
            conn.close()
            return change_rate
            
        except Exception as e:
            logger.error(f"데이터 변화량 확인 오류: {e}")
            return 0.0
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """캐시 키 생성"""
        key_parts = [operation]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        return "_".join(key_parts)
    
    def _set_cache(self, key: str, value: Any, ttl_seconds: int = 300):
        """캐시 설정"""
        with self.cache_lock:
            self.cache[key] = value
            self.cache_ttl[key] = time.time() + ttl_seconds
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        with self.cache_lock:
            if key in self.cache and time.time() <= self.cache_ttl[key]:
                return self.cache[key]
            return None
    
    def get_business_summary(self) -> Dict[str, Any]:
        """비즈니스 요약 정보 (캐시 적용)"""
        cache_key = self._get_cache_key("business_summary")
        cached_result = self._get_cache(cache_key)
        
        if cached_result:
            return cached_result
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'period': '30일'
        }
        
        # 전체 통계
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT o.id) as total_orders,
                COUNT(DISTINCT p.id) as total_products,
                SUM(o.total_amount) as total_revenue,
                AVG(o.total_amount) as avg_order_value,
                COUNT(DISTINCT o.customer_id) as unique_customers
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        
        stats = cursor.fetchone()
        summary['overview'] = dict(stats) if stats else {}
        
        # 일별 매출 트렌드
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                SUM(total_amount) as daily_revenue,
                COUNT(*) as daily_orders
            FROM orders
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        daily_stats = cursor.fetchall()
        summary['daily_trends'] = [dict(row) for row in daily_stats]
        
        # 카테고리별 성과
        cursor.execute("""
            SELECT 
                p.category,
                SUM(oi.quantity * oi.price) as revenue,
                SUM(oi.quantity) as quantity_sold,
                COUNT(DISTINCT p.id) as product_count
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.category
            ORDER BY revenue DESC
        """)
        
        category_stats = cursor.fetchall()
        summary['category_performance'] = [dict(row) for row in category_stats]
        
        conn.close()
        
        # 캐시 저장 (5분)
        self._set_cache(cache_key, summary, 300)
        
        return summary
    
    def train_models(self) -> Dict[str, Any]:
        """
        향상된 AI 모델 학습 (병렬 처리)
        """
        logger.info("향상된 AI 모델 학습 시작")
        start_time = time.time()
        
        results = {
            'started_at': datetime.now().isoformat(),
            'models': {}
        }
        
        # 병렬 학습
        def train_sales_model():
            try:
                sales_results = self.sales_model.train()
                self.sales_model.save(os.path.join(self.models_path, "enhanced_sales_prediction.pkl"))
                return ('sales_prediction', sales_results)
            except Exception as e:
                logger.error(f"매출 예측 모델 학습 실패: {e}")
                return ('sales_prediction', {"error": str(e)})
        
        def train_anomaly_model():
            try:
                anomaly_results = self.anomaly_model.train()
                self.anomaly_model.save(os.path.join(self.models_path, "enhanced_anomaly_detection.pkl"))
                return ('anomaly_detection', anomaly_results)
            except Exception as e:
                logger.error(f"이상 탐지 모델 학습 실패: {e}")
                return ('anomaly_detection', {"error": str(e)})
        
        # 병렬 실행
        futures = [
            self.executor.submit(train_sales_model),
            self.executor.submit(train_anomaly_model)
        ]
        
        for future in futures:
            model_name, result = future.result()
            results['models'][model_name] = result
        
        training_time = time.time() - start_time
        results['training_time'] = training_time
        results['completed_at'] = datetime.now().isoformat()
        
        # 성능 메트릭 업데이트
        self.performance_metrics['last_training_time'] = datetime.now().isoformat()
        if 'sales_prediction' in results['models'] and 'performance' in results['models']['sales_prediction']:
            self.performance_metrics['model_accuracy']['sales'] = results['models']['sales_prediction']['performance']
        
        logger.info(f"향상된 AI 모델 학습 완료 ({training_time:.1f}초)")
        return results
    
    def predict_sales_advanced(self, product_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """고급 매출 예측 (캐시 및 성능 모니터링)"""
        start_time = time.time()
        
        # 캐시 확인
        cache_key = self._get_cache_key("sales_prediction", product_id=product_id, days=days)
        cached_result = self._get_cache(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            if not self.sales_model.is_trained:
                return {"error": "향상된 매출 예측 모델이 학습되지 않았습니다"}
            
            # 예측을 위한 미래 데이터 생성
            future_dates = pd.date_range(
                start=datetime.now().date() + timedelta(days=1),
                periods=days,
                freq='D'
            )
            
            # 제품 정보 조회
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if product_id:
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                products = cursor.fetchall()
            else:
                cursor.execute("SELECT * FROM products WHERE stock > 0 ORDER BY id LIMIT 10")
                products = cursor.fetchall()
            
            predictions = []
            confidence_scores = []
            
            for product in products:
                # 과거 판매 데이터 조회
                cursor.execute("""
                    SELECT 
                        AVG(oi.quantity) as avg_quantity,
                        STDDEV(oi.quantity) as std_quantity
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    WHERE oi.product_id = %s 
                    AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
                """, (product['id'],))
                
                sales_stats = cursor.fetchone()
                avg_sales = sales_stats['avg_quantity'] if sales_stats and sales_stats['avg_quantity'] else 0
                
                # 각 날짜별 예측 데이터 생성
                prediction_data = []
                
                for date in future_dates:
                    row = {
                        'date': date,
                        'product_id': product['id'],
                        'category': product['category'],
                        'supplier': product['supplier'],
                        'price': float(product['price']),
                        'stock_level': product['stock'],
                        'avg_sales_7d': avg_sales,
                        'avg_sales_30d': avg_sales,
                        'day_of_week': date.weekday(),
                        'month': date.month,
                        'quarter': (date.month - 1) // 3 + 1,
                        'is_weekend': 1 if date.weekday() >= 5 else 0,
                        'season': ((date.month % 12) // 3 + 1),
                        'price_tier': 'medium'  # 기본값
                    }
                    prediction_data.append(row)
                
                # 예측 수행
                df = pd.DataFrame(prediction_data)
                predicted_revenue = self.sales_model.predict(df)
                
                # 신뢰도 계산
                revenue_std = np.std(predicted_revenue) if len(predicted_revenue) > 1 else 0
                confidence = max(0.5, 1.0 - (revenue_std / np.mean(predicted_revenue)) if np.mean(predicted_revenue) > 0 else 0.5)
                confidence_scores.append(confidence)
                
                # 결과 저장
                for i, (date, revenue) in enumerate(zip(future_dates, predicted_revenue)):
                    predictions.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'product_id': product['id'],
                        'product_name': product['name'],
                        'predicted_revenue': float(max(0, revenue)),
                        'confidence': float(confidence)
                    })
            
            conn.close()
            
            # 집계 및 분석
            total_by_date = {}
            for pred in predictions:
                date = pred['date']
                if date not in total_by_date:
                    total_by_date[date] = 0
                total_by_date[date] += pred['predicted_revenue']
            
            # 특성 중요도
            feature_importance = self.sales_model.get_feature_importance()
            
            result = {
                'predictions': predictions,
                'summary': {
                    'total_predicted_revenue': sum(total_by_date.values()),
                    'daily_average': sum(total_by_date.values()) / len(total_by_date) if total_by_date else 0,
                    'by_date': total_by_date,
                    'avg_confidence': np.mean(confidence_scores) if confidence_scores else 0,
                    'prediction_range': f"{days} days"
                },
                'model_info': {
                    'feature_importance': dict(list(feature_importance.items())[:5]),  # 상위 5개
                    'model_performance': self.sales_model.performance_metrics
                }
            }
            
            # 캐시 저장 (10분)
            self._set_cache(cache_key, result, 600)
            
            # 성능 메트릭 업데이트
            prediction_time = time.time() - start_time
            self.performance_metrics['prediction_count'] += 1
            self.performance_metrics['total_prediction_time'] += prediction_time
            
            return result
            
        except Exception as e:
            self.performance_metrics['error_count'] += 1
            logger.error(f"고급 매출 예측 오류: {e}")
            return {"error": str(e)}
    
    def detect_anomalies_advanced(self, data_type: str = 'sales') -> Dict[str, Any]:
        """고급 이상 탐지 (다중 알고리즘 앙상블)"""
        cache_key = self._get_cache_key("anomaly_detection", data_type=data_type)
        cached_result = self._get_cache(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            if not self.anomaly_model.is_trained:
                return {"error": "향상된 이상 탐지 모델이 학습되지 않았습니다"}
            
            # 최근 데이터 조회
            data = self.anomaly_model.get_anomaly_data(days=14)
            
            if len(data) == 0:
                return {"anomalies": [], "message": "분석할 데이터가 없습니다"}
            
            # 이상치 탐지
            predictions, scores, details = self.anomaly_model.detect(data)
            
            # 이상치 상세 정보
            anomalies = []
            for idx, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1:  # 이상치
                    row = data.iloc[idx]
                    
                    # 심각도 계산
                    severity = 'low'
                    if score < np.percentile(scores, 5):
                        severity = 'critical'
                    elif score < np.percentile(scores, 15):
                        severity = 'high'
                    elif score < np.percentile(scores, 30):
                        severity = 'medium'
                    
                    anomaly = {
                        'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else None,
                        'product_id': int(row['product_id']) if pd.notna(row['product_id']) else None,
                        'product_name': row.get('product_name', 'Unknown'),
                        'category': row.get('category', 'Unknown'),
                        'anomaly_score': float(score),
                        'severity': severity,
                        'details': {
                            'daily_revenue': float(row.get('daily_revenue', 0)),
                            'daily_quantity': int(row.get('daily_quantity', 0)),
                            'daily_orders': int(row.get('daily_orders', 0)),
                            'avg_price': float(row.get('avg_price', 0))
                        },
                        'recommendations': self._generate_anomaly_recommendations(row, severity)
                    }
                    anomalies.append(anomaly)
            
            # 우선순위 정렬
            anomalies.sort(key=lambda x: (
                {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x['severity']],
                -x['anomaly_score']
            ), reverse=True)
            
            result = {
                'anomalies': anomalies[:20],  # 상위 20개만
                'summary': {
                    'total_anomalies': len(anomalies),
                    'total_analyzed': len(data),
                    'anomaly_rate': len(anomalies) / len(data) if len(data) > 0 else 0,
                    'by_severity': {
                        severity: len([a for a in anomalies if a['severity'] == severity])
                        for severity in ['critical', 'high', 'medium', 'low']
                    }
                },
                'detection_details': details,
                'analyzed_period': '14 days'
            }
            
            # 캐시 저장 (5분)
            self._set_cache(cache_key, result, 300)
            
            return result
            
        except Exception as e:
            logger.error(f"고급 이상 탐지 오류: {e}")
            return {"error": str(e)}
    
    def _generate_anomaly_recommendations(self, row: pd.Series, severity: str) -> List[str]:
        """이상치에 대한 권장사항 생성"""
        recommendations = []
        
        revenue = row.get('daily_revenue', 0)
        quantity = row.get('daily_quantity', 0)
        orders = row.get('daily_orders', 0)
        
        if severity in ['critical', 'high']:
            if revenue == 0:
                recommendations.append("매출이 없음 - 재고 상태 및 마케팅 전략 점검 필요")
            elif quantity > orders * 10:  # 비정상적으로 많은 수량
                recommendations.append("대량 주문 발생 - 재고 보충 및 공급망 점검 필요")
            elif revenue > quantity * 100000:  # 비정상적으로 높은 단가
                recommendations.append("고가 상품 판매 - 가격 오류 가능성 확인 필요")
        
        if not recommendations:
            recommendations.append("상세 분석을 통한 원인 파악 권장")
        
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """엔진 성능 메트릭 조회"""
        avg_prediction_time = (
            self.performance_metrics['total_prediction_time'] / 
            self.performance_metrics['prediction_count']
            if self.performance_metrics['prediction_count'] > 0 else 0
        )
        
        return {
            'engine_status': 'operational',
            'models_loaded': {
                'sales_prediction': self.sales_model.is_trained,
                'anomaly_detection': self.anomaly_model.is_trained
            },
            'performance': {
                'total_predictions': self.performance_metrics['prediction_count'],
                'avg_prediction_time': f"{avg_prediction_time:.3f}s",
                'error_rate': (
                    self.performance_metrics['error_count'] / 
                    max(1, self.performance_metrics['prediction_count'])
                ),
                'last_training': self.performance_metrics['last_training_time']
            },
            'cache_stats': {
                'cached_items': len(self.cache),
                'cache_hit_rate': 'N/A'  # TODO: 캐시 히트율 추적
            },
            'model_accuracy': self.performance_metrics['model_accuracy']
        }