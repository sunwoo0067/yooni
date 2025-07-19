#!/usr/bin/env python3
"""
고급 시계열 예측 모델
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import json

# Prophet
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

# Deep Learning
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

# ARIMA
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

# 기타
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class ProphetModel:
    """
    Facebook Prophet 기반 시계열 예측 모델
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = None
        self.is_trained = False
        self.performance_metrics = {}
        
    def prepare_data(self, df: pd.DataFrame, date_col: str = 'date', 
                    target_col: str = 'value') -> pd.DataFrame:
        """Prophet 형식으로 데이터 변환"""
        prophet_df = df[[date_col, target_col]].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        return prophet_df
    
    def train(self, data: pd.DataFrame, holidays: Optional[pd.DataFrame] = None,
              validate: bool = True) -> Dict[str, Any]:
        """모델 학습"""
        logger.info("Prophet 모델 학습 시작")
        
        # 모델 초기화
        self.model = Prophet(
            yearly_seasonality=self.config.get('yearly_seasonality', True),
            weekly_seasonality=self.config.get('weekly_seasonality', True),
            daily_seasonality=self.config.get('daily_seasonality', False),
            seasonality_mode=self.config.get('seasonality_mode', 'additive'),
            changepoint_prior_scale=self.config.get('changepoint_prior_scale', 0.05),
            interval_width=self.config.get('interval_width', 0.95)
        )
        
        # 휴일 추가
        if holidays is not None:
            self.model.add_country_holidays(country_name='KR')
        
        # 추가 변수 (regressors)
        if 'regressors' in self.config:
            for regressor in self.config['regressors']:
                self.model.add_regressor(regressor)
        
        # 학습
        self.model.fit(data)
        self.is_trained = True
        
        # 검증
        if validate and len(data) > 365:
            self.performance_metrics = self._validate_model(data)
            logger.info(f"모델 성능: MAE={self.performance_metrics['mae']:.2f}")
        
        return {
            'status': 'success',
            'metrics': self.performance_metrics
        }
    
    def predict(self, periods: int, freq: str = 'D', 
                include_history: bool = False) -> pd.DataFrame:
        """예측 수행"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 미래 날짜 생성
        future = self.model.make_future_dataframe(
            periods=periods, 
            freq=freq,
            include_history=include_history
        )
        
        # 예측
        forecast = self.model.predict(future)
        
        # 주요 컬럼 선택
        columns = ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
        if include_history:
            columns.extend(['trend', 'weekly', 'yearly'])
        
        return forecast[columns]
    
    def _validate_model(self, data: pd.DataFrame) -> Dict[str, float]:
        """교차 검증"""
        # 교차 검증 수행
        cv_results = cross_validation(
            self.model, 
            initial='365 days',
            period='90 days',
            horizon='30 days'
        )
        
        # 성능 메트릭 계산
        metrics = performance_metrics(cv_results)
        
        return {
            'mae': metrics['mae'].mean(),
            'mse': metrics['mse'].mean(),
            'rmse': metrics['rmse'].mean(),
            'mape': metrics['mape'].mean()
        }
    
    def get_components(self) -> pd.DataFrame:
        """트렌드, 계절성 컴포넌트 반환"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 컴포넌트 플롯용 데이터
        future = self.model.make_future_dataframe(periods=0)
        forecast = self.model.predict(future)
        
        components = forecast[['ds', 'trend']]
        
        # 계절성 컴포넌트 추가
        for component in ['weekly', 'yearly', 'holidays']:
            if component in forecast.columns:
                components[component] = forecast[component]
        
        return components
    
    def save(self, path: str):
        """모델 저장"""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'config': self.config,
                'metrics': self.performance_metrics
            }, f)
    
    def load(self, path: str):
        """모델 로드"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.config = data['config']
            self.performance_metrics = data['metrics']
            self.is_trained = True


class LSTMModel(nn.Module):
    """
    LSTM 기반 시계열 예측 모델
    """
    
    def __init__(self, input_size: int = 1, hidden_size: int = 50, 
                 num_layers: int = 2, output_size: int = 1, 
                 dropout: float = 0.2):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc = nn.Linear(hidden_size, output_size)
        self.is_trained = False
        self.scaler = MinMaxScaler()
        self.sequence_length = 30
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)
        
    def forward(self, x):
        # LSTM 레이어
        lstm_out, _ = self.lstm(x)
        
        # 마지막 시점의 출력만 사용
        last_output = lstm_out[:, -1, :]
        
        # Fully connected 레이어
        output = self.fc(last_output)
        
        return output
    
    def prepare_sequences(self, data: np.ndarray, seq_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """시퀀스 데이터 생성"""
        sequences = []
        targets = []
        
        for i in range(len(data) - seq_length):
            seq = data[i:i + seq_length]
            target = data[i + seq_length]
            sequences.append(seq)
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    def train_model(self, data: pd.DataFrame, epochs: int = 100, 
                   batch_size: int = 32, learning_rate: float = 0.001,
                   validation_split: float = 0.2) -> Dict[str, Any]:
        """모델 학습"""
        logger.info("LSTM 모델 학습 시작")
        
        # 데이터 준비
        values = data.values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(values)
        
        # 시퀀스 생성
        X, y = self.prepare_sequences(scaled_data, self.sequence_length)
        
        # 학습/검증 분할
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # 텐서 변환
        X_train = torch.FloatTensor(X_train).to(self.device)
        y_train = torch.FloatTensor(y_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        y_val = torch.FloatTensor(y_val).to(self.device)
        
        # 데이터로더
        train_dataset = TensorDataset(X_train, y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        # 옵티마이저와 손실 함수
        optimizer = torch.optim.Adam(self.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # 학습
        train_losses = []
        val_losses = []
        
        for epoch in range(epochs):
            # Training
            self.train()
            epoch_train_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_train_loss += loss.item()
            
            # Validation
            self.eval()
            with torch.no_grad():
                val_outputs = self(X_val)
                val_loss = criterion(val_outputs, y_val)
            
            avg_train_loss = epoch_train_loss / len(train_loader)
            train_losses.append(avg_train_loss)
            val_losses.append(val_loss.item())
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch [{epoch+1}/{epochs}], "
                          f"Train Loss: {avg_train_loss:.4f}, "
                          f"Val Loss: {val_loss.item():.4f}")
        
        self.is_trained = True
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'final_train_loss': train_losses[-1],
            'final_val_loss': val_losses[-1]
        }
    
    def predict(self, data: pd.DataFrame, steps: int = 30) -> np.ndarray:
        """다단계 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        self.eval()
        
        # 초기 시퀀스 준비
        values = data.values.reshape(-1, 1)
        scaled_data = self.scaler.transform(values)
        
        # 마지막 시퀀스 사용
        current_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, 1)
        current_sequence = torch.FloatTensor(current_sequence).to(self.device)
        
        predictions = []
        
        with torch.no_grad():
            for _ in range(steps):
                # 예측
                pred = self(current_sequence)
                predictions.append(pred.cpu().numpy()[0, 0])
                
                # 시퀀스 업데이트
                new_sequence = torch.cat([
                    current_sequence[:, 1:, :],
                    pred.unsqueeze(1)
                ], dim=1)
                current_sequence = new_sequence
        
        # 역변환
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions)
        
        return predictions.flatten()
    
    def save_model(self, path: str):
        """모델 저장"""
        torch.save({
            'model_state_dict': self.state_dict(),
            'scaler': self.scaler,
            'sequence_length': self.sequence_length,
            'config': {
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers
            }
        }, path)
    
    def load_model(self, path: str):
        """모델 로드"""
        checkpoint = torch.load(path, map_location=self.device)
        self.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.sequence_length = checkpoint['sequence_length']
        self.is_trained = True


class ARIMAModel:
    """
    ARIMA/SARIMA 시계열 예측 모델
    """
    
    def __init__(self):
        self.model = None
        self.order = None
        self.seasonal_order = None
        self.is_trained = False
        self.model_type = 'ARIMA'
        
    def test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        """정상성 검정 (ADF Test)"""
        result = adfuller(data.dropna())
        
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05
        }
    
    def auto_select_order(self, data: pd.Series, seasonal: bool = False) -> Tuple:
        """자동 파라미터 선택 (Grid Search)"""
        logger.info("ARIMA 파라미터 자동 선택 시작")
        
        # 파라미터 범위
        p_range = range(0, 3)
        d_range = range(0, 2)
        q_range = range(0, 3)
        
        best_aic = np.inf
        best_order = None
        
        for p in p_range:
            for d in d_range:
                for q in q_range:
                    try:
                        if seasonal:
                            # SARIMA
                            model = SARIMAX(
                                data,
                                order=(p, d, q),
                                seasonal_order=(1, 1, 1, 12)
                            )
                        else:
                            # ARIMA
                            model = ARIMA(data, order=(p, d, q))
                        
                        fitted_model = model.fit(disp=False)
                        
                        if fitted_model.aic < best_aic:
                            best_aic = fitted_model.aic
                            best_order = (p, d, q)
                    
                    except:
                        continue
        
        logger.info(f"최적 파라미터: {best_order}, AIC: {best_aic:.2f}")
        return best_order
    
    def train(self, data: pd.Series, order: Optional[Tuple] = None,
              seasonal_order: Optional[Tuple] = None,
              auto_order: bool = True) -> Dict[str, Any]:
        """모델 학습"""
        logger.info("ARIMA 모델 학습 시작")
        
        # 정상성 검정
        stationarity = self.test_stationarity(data)
        if not stationarity['is_stationary']:
            logger.warning("데이터가 정상성을 만족하지 않습니다. 차분이 필요할 수 있습니다.")
        
        # 파라미터 자동 선택
        if auto_order and order is None:
            order = self.auto_select_order(data, seasonal=seasonal_order is not None)
        
        self.order = order
        self.seasonal_order = seasonal_order
        
        # 모델 학습
        if seasonal_order:
            self.model_type = 'SARIMA'
            model = SARIMAX(data, order=order, seasonal_order=seasonal_order)
        else:
            self.model_type = 'ARIMA'
            model = ARIMA(data, order=order)
        
        self.model = model.fit(disp=False)
        self.is_trained = True
        
        # 모델 진단
        diagnostics = {
            'aic': self.model.aic,
            'bic': self.model.bic,
            'llf': self.model.llf,
            'order': order,
            'seasonal_order': seasonal_order
        }
        
        logger.info(f"{self.model_type} 모델 학습 완료: {diagnostics}")
        
        return diagnostics
    
    def predict(self, steps: int, return_conf_int: bool = True) -> pd.DataFrame:
        """예측 수행"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 예측
        forecast = self.model.forecast(steps=steps)
        
        # 신뢰구간
        if return_conf_int:
            forecast_df = pd.DataFrame({
                'forecast': forecast,
                'lower_bound': forecast - 1.96 * np.sqrt(self.model.mse),
                'upper_bound': forecast + 1.96 * np.sqrt(self.model.mse)
            })
        else:
            forecast_df = pd.DataFrame({'forecast': forecast})
        
        return forecast_df
    
    def get_residuals_analysis(self) -> Dict[str, Any]:
        """잔차 분석"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        residuals = self.model.resid
        
        return {
            'mean': residuals.mean(),
            'std': residuals.std(),
            'skewness': residuals.skew(),
            'kurtosis': residuals.kurtosis(),
            'ljung_box': self.model.test_serial_correlation('ljungbox')
        }


class TimeSeriesEnsemble:
    """
    앙상블 시계열 예측 모델
    """
    
    def __init__(self):
        self.models = {
            'prophet': ProphetModel(),
            'lstm': LSTMModel(),
            'arima': ARIMAModel()
        }
        self.weights = {'prophet': 0.4, 'lstm': 0.4, 'arima': 0.2}
        self.predictions = {}
        
    def train_all(self, data: pd.DataFrame, **kwargs):
        """모든 모델 학습"""
        results = {}
        
        # Prophet
        prophet_data = self.models['prophet'].prepare_data(data)
        results['prophet'] = self.models['prophet'].train(prophet_data)
        
        # LSTM
        if 'value' in data.columns:
            results['lstm'] = self.models['lstm'].train_model(data['value'])
        
        # ARIMA
        if 'value' in data.columns:
            results['arima'] = self.models['arima'].train(data['value'])
        
        return results
    
    def predict_ensemble(self, steps: int) -> pd.DataFrame:
        """앙상블 예측"""
        ensemble_predictions = []
        
        # 각 모델 예측
        self.predictions['prophet'] = self.models['prophet'].predict(steps)['yhat'].values
        self.predictions['lstm'] = self.models['lstm'].predict(steps)
        self.predictions['arima'] = self.models['arima'].predict(steps)['forecast'].values
        
        # 가중 평균
        for i in range(steps):
            weighted_pred = (
                self.weights['prophet'] * self.predictions['prophet'][i] +
                self.weights['lstm'] * self.predictions['lstm'][i] +
                self.weights['arima'] * self.predictions['arima'][i]
            )
            ensemble_predictions.append(weighted_pred)
        
        return pd.DataFrame({
            'ensemble_forecast': ensemble_predictions,
            'prophet': self.predictions['prophet'],
            'lstm': self.predictions['lstm'],
            'arima': self.predictions['arima']
        })