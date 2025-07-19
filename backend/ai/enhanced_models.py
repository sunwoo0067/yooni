#!/usr/bin/env python3
"""
향상된 AI 모델 - 실제 데이터베이스 연동 및 성능 개선
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class EnhancedSalesPredictionModel:
    """향상된 매출 예측 모델"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boost': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=10,
                random_state=42
            )
        }
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.is_trained = False
        self.performance_metrics = {}
        
    def get_training_data(self, days: int = 180) -> pd.DataFrame:
        """실제 데이터베이스에서 학습 데이터 조회"""
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
                SUM(oi.quantity * oi.price) as revenue,
                EXTRACT(DOW FROM o.created_at) as day_of_week,
                EXTRACT(MONTH FROM o.created_at) as month,
                EXTRACT(QUARTER FROM o.created_at) as quarter
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(o.created_at), p.id, p.name, p.category, p.supplier, p.price, p.stock, 
                     EXTRACT(DOW FROM o.created_at), EXTRACT(MONTH FROM o.created_at), 
                     EXTRACT(QUARTER FROM o.created_at)
            ORDER BY date, product_id
        """
        
        df = pd.read_sql(query, conn, params=(days,))
        conn.close()
        
        # 추가 특성 생성
        df['is_weekend'] = (df['day_of_week'].isin([0, 6])).astype(int)  # 일요일=0, 토요일=6
        df['season'] = ((df['month'] % 12) // 3 + 1)  # 1-봄, 2-여름, 3-가을, 4-겨울
        df['price_tier'] = pd.cut(df['price'], bins=5, labels=['very_low', 'low', 'medium', 'high', 'very_high'])
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """고급 특성 엔지니어링"""
        features = pd.DataFrame()
        
        # 기본 수치형 특성
        numeric_features = ['price', 'stock_level', 'order_count', 'quantity_sold']
        for feature in numeric_features:
            if feature in df.columns:
                features[feature] = df[feature]
        
        # 시간 특성
        time_features = ['day_of_week', 'month', 'quarter', 'is_weekend', 'season']
        for feature in time_features:
            if feature in df.columns:
                features[feature] = df[feature]
        
        # 카테고리 인코딩
        categorical_features = ['category', 'supplier', 'price_tier']
        for feature in categorical_features:
            if feature in df.columns:
                if feature not in self.encoders:
                    self.encoders[feature] = LabelEncoder()
                    features[f'{feature}_encoded'] = self.encoders[feature].fit_transform(df[feature].fillna('unknown'))
                else:
                    features[f'{feature}_encoded'] = self.encoders[feature].transform(df[feature].fillna('unknown'))
        
        # 통계 특성 (rolling windows)
        if 'quantity_sold' in df.columns and 'product_id' in df.columns:
            df_sorted = df.sort_values(['product_id', 'date'])
            features['avg_sales_7d'] = df_sorted.groupby('product_id')['quantity_sold'].rolling(window=7, min_periods=1).mean().values
            features['avg_sales_30d'] = df_sorted.groupby('product_id')['quantity_sold'].rolling(window=30, min_periods=1).mean().values
            features['sales_trend'] = df_sorted.groupby('product_id')['quantity_sold'].pct_change(periods=7).fillna(0).values
        
        # 교호작용 특성
        if 'price' in features.columns and 'is_weekend' in features.columns:
            features['price_weekend_interaction'] = features['price'] * features['is_weekend']
        
        # 결측값 처리
        features = features.fillna(0)
        
        return features
    
    def train(self, validate: bool = True) -> Dict[str, Any]:
        """향상된 모델 학습"""
        logger.info("향상된 매출 예측 모델 학습 시작")
        
        # 데이터 준비
        df = self.get_training_data(days=180)
        
        if len(df) < 50:
            return {"error": "학습을 위한 충분한 데이터가 없습니다", "data_count": len(df)}
        
        # 특성 엔지니어링
        X = self.engineer_features(df)
        y = df['revenue'].values
        
        self.feature_names = list(X.columns)
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        
        # 스케일링
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        # 다중 모델 학습 및 앙상블
        results = {}
        predictions = {}
        
        for name, model in self.models.items():
            logger.info(f"학습 중: {name}")
            
            # 모델 학습
            model.fit(X_train_scaled, y_train)
            
            # 예측
            train_pred = model.predict(X_train_scaled)
            test_pred = model.predict(X_test_scaled)
            predictions[name] = test_pred
            
            # 평가
            train_score = r2_score(y_train, train_pred)
            test_score = r2_score(y_test, test_pred)
            mae = mean_absolute_error(y_test, test_pred)
            rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            
            # 교차검증
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            
            results[name] = {
                'train_r2': train_score,
                'test_r2': test_score,
                'mae': mae,
                'rmse': rmse,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
        
        # 앙상블 예측 (평균)
        ensemble_pred = np.mean(list(predictions.values()), axis=0)
        ensemble_r2 = r2_score(y_test, ensemble_pred)
        ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
        
        results['ensemble'] = {
            'test_r2': ensemble_r2,
            'mae': ensemble_mae,
            'improvement': ensemble_r2 - max(r['test_r2'] for r in results.values() if 'test_r2' in r)
        }
        
        self.performance_metrics = results
        self.is_trained = True
        
        logger.info(f"모델 학습 완료 - 최고 R2: {max(r['test_r2'] for r in results.values() if 'test_r2' in r):.3f}")
        logger.info(f"앙상블 R2: {ensemble_r2:.3f}, MAE: {ensemble_mae:.0f}")
        
        return {
            'status': 'success',
            'models_trained': len(self.models),
            'data_samples': len(df),
            'features': len(self.feature_names),
            'performance': results
        }
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """앙상블 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 특성 준비
        X = self.engineer_features(data)
        
        # 누락된 특성 처리
        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0
        
        X = X[self.feature_names]
        X_scaled = self.scalers['main'].transform(X)
        
        # 앙상블 예측
        predictions = []
        for model in self.models.values():
            pred = model.predict(X_scaled)
            predictions.append(pred)
        
        ensemble_pred = np.mean(predictions, axis=0)
        return ensemble_pred
    
    def get_feature_importance(self) -> Dict[str, float]:
        """특성 중요도 분석"""
        if not self.is_trained:
            return {}
        
        importance_scores = {}
        for name, model in self.models.items():
            if hasattr(model, 'feature_importances_'):
                for feature, importance in zip(self.feature_names, model.feature_importances_):
                    if feature not in importance_scores:
                        importance_scores[feature] = []
                    importance_scores[feature].append(importance)
        
        # 평균 중요도 계산
        avg_importance = {
            feature: np.mean(scores) 
            for feature, scores in importance_scores.items()
        }
        
        return dict(sorted(avg_importance.items(), key=lambda x: x[1], reverse=True))
    
    def save(self, path: str):
        """모델 저장"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'models': self.models,
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_names': self.feature_names,
            'performance_metrics': self.performance_metrics,
            'is_trained': self.is_trained
        }, path)
        logger.info(f"향상된 모델 저장 완료: {path}")
    
    def load(self, path: str):
        """모델 로드"""
        data = joblib.load(path)
        self.models = data['models']
        self.scalers = data['scalers']
        self.encoders = data['encoders']
        self.feature_names = data['feature_names']
        self.performance_metrics = data['performance_metrics']
        self.is_trained = data['is_trained']
        logger.info(f"향상된 모델 로드 완료: {path}")


class EnhancedAnomalyDetectionModel:
    """향상된 이상 탐지 모델"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.models = {
            'isolation_forest': IsolationForest(
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            ),
            'statistical': None  # 통계적 이상 탐지
        }
        self.scaler = StandardScaler()
        self.is_trained = False
        self.thresholds = {}
    
    def get_anomaly_data(self, days: int = 30) -> pd.DataFrame:
        """이상 탐지용 데이터 조회"""
        conn = psycopg2.connect(**self.db_config)
        
        query = """
            SELECT 
                DATE(o.created_at) as date,
                p.id as product_id,
                p.name as product_name,
                p.category,
                SUM(oi.quantity) as daily_quantity,
                SUM(oi.quantity * oi.price) as daily_revenue,
                COUNT(DISTINCT o.id) as daily_orders,
                AVG(oi.price) as avg_price,
                STDDEV(oi.quantity) as quantity_variance
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(o.created_at), p.id, p.name, p.category
            ORDER BY date, product_id
        """
        
        df = pd.read_sql(query, conn, params=(days,))
        conn.close()
        
        return df
    
    def engineer_anomaly_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """이상 탐지용 특성 엔지니어링"""
        features = pd.DataFrame()
        
        # 기본 수치형 특성
        numeric_cols = ['daily_quantity', 'daily_revenue', 'daily_orders', 'avg_price', 'quantity_variance']
        for col in numeric_cols:
            if col in df.columns:
                features[col] = df[col]
        
        # 비율 특성
        if 'daily_revenue' in df.columns and 'daily_quantity' in df.columns:
            features['revenue_per_unit'] = df['daily_revenue'] / (df['daily_quantity'] + 1)
        
        if 'daily_revenue' in df.columns and 'daily_orders' in df.columns:
            features['revenue_per_order'] = df['daily_revenue'] / (df['daily_orders'] + 1)
        
        # 이동평균 편차
        if 'product_id' in df.columns:
            df_sorted = df.sort_values(['product_id', 'date'])
            
            for col in ['daily_quantity', 'daily_revenue']:
                if col in df.columns:
                    rolling_mean = df_sorted.groupby('product_id')[col].rolling(window=7, min_periods=1).mean()
                    features[f'{col}_deviation'] = (df_sorted[col] - rolling_mean).abs().values
        
        # 결측값 처리
        features = features.fillna(0)
        
        return features
    
    def train(self) -> Dict[str, Any]:
        """이상 탐지 모델 학습"""
        logger.info("향상된 이상 탐지 모델 학습 시작")
        
        # 데이터 준비
        df = self.get_anomaly_data(days=60)
        
        if len(df) < 30:
            return {"error": "학습을 위한 충분한 데이터가 없습니다", "data_count": len(df)}
        
        # 특성 엔지니어링
        X = self.engineer_anomaly_features(df)
        
        # 스케일링
        X_scaled = self.scaler.fit_transform(X)
        
        # Isolation Forest 학습
        self.models['isolation_forest'].fit(X_scaled)
        
        # 통계적 임계값 계산
        anomaly_scores = self.models['isolation_forest'].score_samples(X_scaled)
        self.thresholds = {
            'isolation_forest': np.percentile(anomaly_scores, 10),  # 하위 10%
            'statistical_z': 3,  # Z-score > 3
            'statistical_iqr': 1.5  # IQR * 1.5
        }
        
        # 학습 데이터 이상치 분석
        anomaly_labels = self.models['isolation_forest'].predict(X_scaled)
        anomaly_count = (anomaly_labels == -1).sum()
        
        self.is_trained = True
        
        logger.info(f"이상 탐지 모델 학습 완료 - 이상치: {anomaly_count}/{len(df)} ({anomaly_count/len(df)*100:.1f}%)")
        
        return {
            'status': 'success',
            'data_samples': len(df),
            'features': len(X.columns),
            'anomaly_rate': float(anomaly_count / len(df)),
            'thresholds': self.thresholds
        }
    
    def detect(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """고급 이상치 탐지"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 특성 준비
        X = self.engineer_anomaly_features(data)
        X_scaled = self.scaler.transform(X)
        
        # Isolation Forest 이상치 탐지
        iso_predictions = self.models['isolation_forest'].predict(X_scaled)
        iso_scores = self.models['isolation_forest'].score_samples(X_scaled)
        
        # 통계적 이상치 탐지
        stat_anomalies = np.zeros(len(X))
        
        # Z-score 기반
        for col_idx, col in enumerate(X.columns):
            if X.iloc[:, col_idx].std() > 0:
                z_scores = np.abs((X.iloc[:, col_idx] - X.iloc[:, col_idx].mean()) / X.iloc[:, col_idx].std())
                stat_anomalies += (z_scores > self.thresholds['statistical_z']).astype(int)
        
        # 최종 이상치 판단 (앙상블)
        final_predictions = np.where(
            (iso_predictions == -1) | (stat_anomalies > 0), -1, 1
        )
        
        # 상세 정보
        details = {
            'isolation_forest_anomalies': (iso_predictions == -1).sum(),
            'statistical_anomalies': (stat_anomalies > 0).sum(),
            'total_anomalies': (final_predictions == -1).sum(),
            'anomaly_rate': (final_predictions == -1).mean()
        }
        
        return final_predictions, iso_scores, details
    
    def save(self, path: str):
        """모델 저장"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'models': self.models,
            'scaler': self.scaler,
            'thresholds': self.thresholds,
            'is_trained': self.is_trained
        }, path)
        logger.info(f"향상된 이상 탐지 모델 저장 완료: {path}")
    
    def load(self, path: str):
        """모델 로드"""
        data = joblib.load(path)
        self.models = data['models']
        self.scaler = data['scaler']
        self.thresholds = data['thresholds']
        self.is_trained = data['is_trained']
        logger.info(f"향상된 이상 탐지 모델 로드 완료: {path}")