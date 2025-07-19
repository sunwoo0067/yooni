#!/usr/bin/env python3
"""
AI/ML 모델 관리
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SalesPredictionModel:
    """매출 예측 모델"""
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_names = [
            'day_of_week', 'month', 'quarter', 'is_weekend',
            'is_holiday', 'price', 'stock_level', 'category_encoded',
            'supplier_encoded', 'promotion_active', 'season',
            'avg_sales_last_7days', 'avg_sales_last_30days'
        ]
        self.is_trained = False
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """특성 준비"""
        features = pd.DataFrame()
        
        # 시간 특성
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            features['day_of_week'] = data['date'].dt.dayofweek
            features['month'] = data['date'].dt.month
            features['quarter'] = data['date'].dt.quarter
            features['is_weekend'] = (data['date'].dt.dayofweek >= 5).astype(int)
            
            # 계절 (1: 봄, 2: 여름, 3: 가을, 4: 겨울)
            features['season'] = data['date'].dt.month % 12 // 3 + 1
        
        # 제품 특성
        if 'price' in data.columns:
            features['price'] = data['price']
        
        if 'stock_level' in data.columns:
            features['stock_level'] = data['stock_level']
        
        # 카테고리 인코딩
        if 'category' in data.columns:
            features['category_encoded'] = pd.Categorical(data['category']).codes
        
        # 공급업체 인코딩
        if 'supplier' in data.columns:
            features['supplier_encoded'] = pd.Categorical(data['supplier']).codes
        
        # 프로모션 상태
        if 'promotion_active' in data.columns:
            features['promotion_active'] = data['promotion_active'].astype(int)
        
        # 휴일 여부 (간단한 예시)
        features['is_holiday'] = 0  # 실제로는 휴일 데이터를 사용해야 함
        
        # 과거 판매 통계 (예시 값)
        if 'avg_sales_last_7days' not in data.columns:
            features['avg_sales_last_7days'] = 0
        else:
            features['avg_sales_last_7days'] = data['avg_sales_last_7days']
            
        if 'avg_sales_last_30days' not in data.columns:
            features['avg_sales_last_30days'] = 0
        else:
            features['avg_sales_last_30days'] = data['avg_sales_last_30days']
        
        # 누락된 특성 처리
        for feature in self.feature_names:
            if feature not in features.columns:
                features[feature] = 0
        
        return features[self.feature_names]
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """모델 학습"""
        logger.info("매출 예측 모델 학습 시작")
        
        # 특성 준비
        X = self.prepare_features(training_data)
        y = training_data['sales']
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 모델 학습
        self.model.fit(X_train_scaled, y_train)
        
        # 평가
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        logger.info(f"모델 학습 완료 - Train R2: {train_score:.3f}, Test R2: {test_score:.3f}")
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'feature_importance': dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
        }
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """매출 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        X = self.prepare_features(data)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        return predictions
    
    def save(self, path: str):
        """모델 저장"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }, path)
        logger.info(f"모델 저장 완료: {path}")
    
    def load(self, path: str):
        """모델 로드"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.is_trained = data['is_trained']
        logger.info(f"모델 로드 완료: {path}")


class AnomalyDetectionModel:
    """이상 탐지 모델"""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,  # 예상 이상치 비율
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """특성 준비"""
        features = pd.DataFrame()
        
        # 수치형 특성만 사용
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        features = data[numeric_columns].copy()
        
        # 널 값 처리
        features = features.fillna(features.mean())
        
        return features
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """이상 탐지 모델 학습"""
        logger.info("이상 탐지 모델 학습 시작")
        
        # 특성 준비
        X = self.prepare_features(training_data)
        
        # 스케일링
        X_scaled = self.scaler.fit_transform(X)
        
        # 모델 학습
        self.model.fit(X_scaled)
        
        # 학습 데이터에서 이상치 탐지
        anomaly_labels = self.model.predict(X_scaled)
        anomaly_scores = self.model.score_samples(X_scaled)
        
        self.is_trained = True
        
        anomaly_count = (anomaly_labels == -1).sum()
        logger.info(f"이상 탐지 모델 학습 완료 - 이상치: {anomaly_count}/{len(X)}")
        
        return {
            'total_samples': len(X),
            'anomaly_count': int(anomaly_count),
            'anomaly_ratio': float(anomaly_count / len(X)),
            'threshold': float(np.percentile(anomaly_scores, 10))  # 하위 10%
        }
    
    def detect(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """이상치 탐지"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        X = self.prepare_features(data)
        X_scaled = self.scaler.transform(X)
        
        # -1: 이상치, 1: 정상
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        
        return predictions, scores
    
    def save(self, path: str):
        """모델 저장"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }, path)
        logger.info(f"이상 탐지 모델 저장 완료: {path}")
    
    def load(self, path: str):
        """모델 로드"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']
        logger.info(f"이상 탐지 모델 로드 완료: {path}")