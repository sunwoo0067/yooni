#!/usr/bin/env python3
"""
고객 이탈 예측 모델
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

# ML 모델
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve
)

# XGBoost
import xgboost as xgb

# 불균형 데이터 처리
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline

# Feature Engineering
from sklearn.feature_selection import SelectKBest, chi2, mutual_info_classif

# 해석가능성
import shap

# 시각화
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class CustomerChurnPredictor:
    """
    고객 이탈 예측 시스템
    """
    
    def __init__(self, model_type: str = 'xgboost'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.feature_importance = {}
        self.model_metrics = {}
        
        # SHAP 해석기
        self.explainer = None
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        고객 특성 엔지니어링
        
        Features:
        - RFM (Recency, Frequency, Monetary)
        - 구매 패턴
        - 시즌성
        - 고객 생애 가치 (CLV)
        - 행동 변화율
        """
        features = pd.DataFrame()
        features['customer_id'] = df['customer_id'].unique()
        
        # 현재 날짜 기준
        current_date = df['order_date'].max()
        
        for customer_id in features['customer_id']:
            customer_data = df[df['customer_id'] == customer_id]
            
            # RFM 분석
            features.loc[features['customer_id'] == customer_id, 'recency'] = (
                current_date - customer_data['order_date'].max()
            ).days
            
            features.loc[features['customer_id'] == customer_id, 'frequency'] = len(customer_data)
            
            features.loc[features['customer_id'] == customer_id, 'monetary'] = (
                customer_data['total_amount'].sum()
            )
            
            # 평균 주문 금액
            features.loc[features['customer_id'] == customer_id, 'avg_order_value'] = (
                customer_data['total_amount'].mean()
            )
            
            # 고객 생애 기간
            features.loc[features['customer_id'] == customer_id, 'customer_lifetime'] = (
                customer_data['order_date'].max() - customer_data['order_date'].min()
            ).days
            
            # 주문 간격 통계
            if len(customer_data) > 1:
                order_intervals = customer_data['order_date'].sort_values().diff().dt.days.dropna()
                features.loc[features['customer_id'] == customer_id, 'avg_days_between_orders'] = (
                    order_intervals.mean()
                )
                features.loc[features['customer_id'] == customer_id, 'std_days_between_orders'] = (
                    order_intervals.std()
                )
            else:
                features.loc[features['customer_id'] == customer_id, 'avg_days_between_orders'] = 0
                features.loc[features['customer_id'] == customer_id, 'std_days_between_orders'] = 0
            
            # 최근 행동 변화
            if len(customer_data) >= 3:
                recent_orders = customer_data.nlargest(3, 'order_date')
                old_orders = customer_data.nsmallest(3, 'order_date')
                
                features.loc[features['customer_id'] == customer_id, 'recent_avg_value'] = (
                    recent_orders['total_amount'].mean()
                )
                features.loc[features['customer_id'] == customer_id, 'old_avg_value'] = (
                    old_orders['total_amount'].mean()
                )
                
                # 구매 금액 변화율
                if old_orders['total_amount'].mean() > 0:
                    features.loc[features['customer_id'] == customer_id, 'value_change_rate'] = (
                        (recent_orders['total_amount'].mean() - old_orders['total_amount'].mean()) / 
                        old_orders['total_amount'].mean()
                    )
                else:
                    features.loc[features['customer_id'] == customer_id, 'value_change_rate'] = 0
            
            # 카테고리 다양성
            features.loc[features['customer_id'] == customer_id, 'category_diversity'] = (
                customer_data['category'].nunique()
            )
            
            # 할인 사용률
            if 'discount_amount' in customer_data.columns:
                features.loc[features['customer_id'] == customer_id, 'discount_usage_rate'] = (
                    (customer_data['discount_amount'] > 0).mean()
                )
            
            # 반품/취소율
            if 'order_status' in customer_data.columns:
                features.loc[features['customer_id'] == customer_id, 'cancel_rate'] = (
                    (customer_data['order_status'].isin(['cancelled', 'returned'])).mean()
                )
        
        # 결측값 처리
        features = features.fillna(0)
        
        # RFM 점수 계산
        features['rfm_score'] = (
            features['recency'].rank(ascending=False) +
            features['frequency'].rank(ascending=True) +
            features['monetary'].rank(ascending=True)
        ) / 3
        
        # 이탈 레이블 생성 (예: 90일 이상 구매 없음)
        features['churned'] = (features['recency'] > 90).astype(int)
        
        return features
    
    def train(self, features: pd.DataFrame, target_col: str = 'churned',
              test_size: float = 0.2, handle_imbalance: bool = True) -> Dict[str, Any]:
        """모델 학습"""
        logger.info(f"{self.model_type} 이탈 예측 모델 학습 시작")
        
        # 특성과 타겟 분리
        X = features.drop(['customer_id', target_col], axis=1)
        y = features[target_col]
        
        self.feature_names = X.columns.tolist()
        
        # 학습/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 불균형 처리
        if handle_imbalance and y_train.value_counts().min() / y_train.value_counts().max() < 0.3:
            logger.info("불균형 데이터 처리 중...")
            smote = SMOTE(random_state=42)
            X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
        
        # 모델 생성 및 학습
        if self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='binary:logistic',
                random_state=42
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.model = LogisticRegression(random_state=42)
        
        # 하이퍼파라미터 튜닝
        if self.model_type in ['xgboost', 'random_forest']:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7, 10]
            }
            
            grid_search = GridSearchCV(
                self.model, param_grid, cv=5,
                scoring='roc_auc', n_jobs=-1
            )
            
            grid_search.fit(X_train_scaled, y_train)
            self.model = grid_search.best_estimator_
            logger.info(f"최적 파라미터: {grid_search.best_params_}")
        else:
            self.model.fit(X_train_scaled, y_train)
        
        # 예측
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # 평가
        self.model_metrics = {
            'accuracy': (y_pred == y_test).mean(),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
        
        # Feature Importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
        
        # SHAP 값 계산
        self._calculate_shap_values(X_train_scaled[:100])  # 샘플로 계산
        
        self.is_trained = True
        
        logger.info(f"모델 학습 완료 - ROC AUC: {self.model_metrics['roc_auc']:.3f}")
        
        return self.model_metrics
    
    def predict_churn_probability(self, features: pd.DataFrame) -> pd.DataFrame:
        """이탈 확률 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 고객 ID 보존
        customer_ids = features['customer_id'] if 'customer_id' in features.columns else None
        
        # 특성 준비
        X = features[self.feature_names]
        X_scaled = self.scaler.transform(X)
        
        # 예측
        churn_proba = self.model.predict_proba(X_scaled)[:, 1]
        
        # 결과 데이터프레임
        results = pd.DataFrame({
            'churn_probability': churn_proba,
            'churn_risk': pd.cut(
                churn_proba,
                bins=[0, 0.3, 0.7, 1.0],
                labels=['Low', 'Medium', 'High']
            )
        })
        
        if customer_ids is not None:
            results['customer_id'] = customer_ids
        
        # 주요 이탈 요인 추가
        if self.explainer:
            shap_values = self.explainer.shap_values(X_scaled)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # 이탈 클래스
            
            # 상위 3개 요인
            for i in range(len(results)):
                top_features_idx = np.argsort(np.abs(shap_values[i]))[-3:][::-1]
                top_features = [self.feature_names[idx] for idx in top_features_idx]
                results.loc[i, 'top_churn_factors'] = ', '.join(top_features)
        
        return results
    
    def _calculate_shap_values(self, X_sample: np.ndarray):
        """SHAP 값 계산"""
        try:
            if self.model_type == 'xgboost':
                self.explainer = shap.TreeExplainer(self.model)
            else:
                self.explainer = shap.KernelExplainer(
                    self.model.predict_proba,
                    X_sample[:50]  # 배경 데이터
                )
        except Exception as e:
            logger.warning(f"SHAP 값 계산 실패: {e}")
    
    def get_feature_importance_plot(self) -> plt.Figure:
        """특성 중요도 시각화"""
        if not self.feature_importance:
            return None
        
        # 중요도 정렬
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        features, importances = zip(*sorted_features)
        
        # 플롯
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(features, importances)
        
        # 색상 그라데이션
        colors = plt.cm.RdYlBu_r(np.linspace(0.3, 0.7, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xlabel('Feature Importance')
        ax.set_title('Top 10 Churn Prediction Features')
        plt.tight_layout()
        
        return fig
    
    def get_churn_analysis(self, features: pd.DataFrame) -> Dict[str, Any]:
        """이탈 분석 리포트"""
        predictions = self.predict_churn_probability(features)
        
        analysis = {
            'total_customers': len(predictions),
            'high_risk_count': (predictions['churn_risk'] == 'High').sum(),
            'medium_risk_count': (predictions['churn_risk'] == 'Medium').sum(),
            'low_risk_count': (predictions['churn_risk'] == 'Low').sum(),
            'avg_churn_probability': predictions['churn_probability'].mean(),
            'risk_distribution': predictions['churn_risk'].value_counts().to_dict()
        }
        
        # 고위험 고객 특성
        if 'customer_id' in features.columns:
            high_risk_customers = predictions[predictions['churn_risk'] == 'High']['customer_id']
            high_risk_features = features[features['customer_id'].isin(high_risk_customers)]
            
            analysis['high_risk_profile'] = {
                'avg_recency': high_risk_features['recency'].mean(),
                'avg_frequency': high_risk_features['frequency'].mean(),
                'avg_monetary': high_risk_features['monetary'].mean(),
                'avg_lifetime': high_risk_features['customer_lifetime'].mean()
            }
        
        return analysis
    
    def recommend_retention_actions(self, customer_id: str, 
                                  features: pd.DataFrame) -> List[Dict[str, Any]]:
        """고객별 리텐션 전략 추천"""
        customer_features = features[features['customer_id'] == customer_id]
        
        if customer_features.empty:
            return []
        
        # 이탈 확률 예측
        churn_prob = self.predict_churn_probability(customer_features)['churn_probability'].iloc[0]
        
        recommendations = []
        
        # 이탈 확률에 따른 전략
        if churn_prob > 0.7:
            # 고위험 고객
            recommendations.extend([
                {
                    'action': 'immediate_contact',
                    'description': '즉시 고객 연락 필요',
                    'priority': 'high',
                    'suggested_offer': '30% 할인 쿠폰 또는 VIP 혜택'
                },
                {
                    'action': 'win_back_campaign',
                    'description': '윈백 캠페인 대상 포함',
                    'priority': 'high',
                    'channel': ['email', 'sms', 'push']
                }
            ])
        elif churn_prob > 0.3:
            # 중간 위험 고객
            recommendations.extend([
                {
                    'action': 'engagement_campaign',
                    'description': '참여 유도 캠페인',
                    'priority': 'medium',
                    'suggested_offer': '포인트 2배 적립'
                },
                {
                    'action': 'personalized_recommendation',
                    'description': '개인화 상품 추천',
                    'priority': 'medium'
                }
            ])
        
        # 특성 기반 추천
        customer_data = customer_features.iloc[0]
        
        if customer_data['recency'] > 60:
            recommendations.append({
                'action': 'reactivation_email',
                'description': '재활성화 이메일 발송',
                'priority': 'high',
                'content': '오랜만입니다! 특별 혜택을 준비했습니다.'
            })
        
        if customer_data['avg_order_value'] > customer_data['monetary'] / customer_data['frequency']:
            recommendations.append({
                'action': 'upsell_opportunity',
                'description': '업셀링 기회',
                'priority': 'medium',
                'strategy': '번들 상품 또는 프리미엄 제품 추천'
            })
        
        return recommendations