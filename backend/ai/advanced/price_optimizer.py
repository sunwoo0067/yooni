#!/usr/bin/env python3
"""
동적 가격 최적화 엔진
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

# 최적화
from scipy.optimize import minimize, differential_evolution
import cvxpy as cp

# 머신러닝
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# 강화학습
import gym
from gym import spaces
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

logger = logging.getLogger(__name__)


class DemandPredictor:
    """수요 예측 모델"""
    
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """특성 엔지니어링"""
        features = pd.DataFrame()
        
        # 기본 특성
        features['price'] = data['price']
        features['day_of_week'] = pd.to_datetime(data['date']).dt.dayofweek
        features['month'] = pd.to_datetime(data['date']).dt.month
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # 가격 관련 특성
        features['price_ratio'] = data['price'] / data['original_price']
        features['discount_amount'] = data['original_price'] - data['price']
        features['discount_rate'] = features['discount_amount'] / data['original_price']
        
        # 경쟁사 가격 (있는 경우)
        if 'competitor_price' in data.columns:
            features['price_vs_competitor'] = data['price'] / data['competitor_price']
            features['is_cheaper'] = (data['price'] < data['competitor_price']).astype(int)
        
        # 재고 수준
        if 'stock_level' in data.columns:
            features['stock_level'] = data['stock_level']
            features['is_low_stock'] = (data['stock_level'] < 10).astype(int)
        
        # 계절성
        features['is_holiday'] = 0  # 휴일 정보 추가 필요
        features['season'] = pd.to_datetime(data['date']).dt.month.apply(
            lambda x: 1 if x in [12, 1, 2] else 2 if x in [3, 4, 5] else 3 if x in [6, 7, 8] else 4
        )
        
        return features
    
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """수요 예측 모델 학습"""
        features = self.prepare_features(data)
        target = data['quantity_sold']
        
        # 학습/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42
        )
        
        # 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 학습
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # 평가
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        return {
            'train_r2': train_score,
            'test_r2': test_score
        }
    
    def predict_demand(self, price: float, date: datetime, 
                      context: Dict[str, Any]) -> float:
        """특정 가격에서의 수요 예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")
        
        # 특성 생성
        data = pd.DataFrame([{
            'price': price,
            'date': date,
            'original_price': context.get('original_price', price),
            'competitor_price': context.get('competitor_price', price),
            'stock_level': context.get('stock_level', 100)
        }])
        
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)
        
        # 예측
        demand = self.model.predict(features_scaled)[0]
        return max(0, demand)  # 음수 방지


class PriceOptimizer:
    """가격 최적화 엔진"""
    
    def __init__(self, demand_predictor: DemandPredictor):
        self.demand_predictor = demand_predictor
        self.optimization_history = []
        
    def calculate_profit(self, price: float, demand: float, cost: float) -> float:
        """이익 계산"""
        revenue = price * demand
        total_cost = cost * demand
        return revenue - total_cost
    
    def price_elasticity(self, price: float, base_price: float, 
                        base_demand: float, elasticity: float = -1.5) -> float:
        """가격 탄력성 기반 수요 계산"""
        price_ratio = price / base_price
        demand = base_demand * (price_ratio ** elasticity)
        return max(0, demand)
    
    def optimize_price(self, product_id: str, context: Dict[str, Any],
                      method: str = 'profit_maximization') -> Dict[str, Any]:
        """최적 가격 계산"""
        
        # 제약 조건
        min_price = context.get('min_price', context['cost'] * 1.1)
        max_price = context.get('max_price', context['cost'] * 3.0)
        current_price = context.get('current_price', (min_price + max_price) / 2)
        
        if method == 'profit_maximization':
            result = self._optimize_for_profit(
                product_id, context, min_price, max_price
            )
        elif method == 'revenue_maximization':
            result = self._optimize_for_revenue(
                product_id, context, min_price, max_price
            )
        elif method == 'market_share':
            result = self._optimize_for_market_share(
                product_id, context, min_price, max_price
            )
        elif method == 'dynamic_pricing':
            result = self._dynamic_pricing(
                product_id, context, min_price, max_price
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # 기록 저장
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'product_id': product_id,
            'method': method,
            'result': result
        })
        
        return result
    
    def _optimize_for_profit(self, product_id: str, context: Dict[str, Any],
                           min_price: float, max_price: float) -> Dict[str, Any]:
        """이익 최대화"""
        
        def objective(price):
            # 수요 예측
            demand = self.demand_predictor.predict_demand(
                price[0], datetime.now(), context
            )
            # 이익 계산 (최대화를 위해 음수 반환)
            profit = self.calculate_profit(price[0], demand, context['cost'])
            return -profit
        
        # 최적화
        result = minimize(
            objective,
            x0=[context.get('current_price', (min_price + max_price) / 2)],
            bounds=[(min_price, max_price)],
            method='L-BFGS-B'
        )
        
        optimal_price = result.x[0]
        optimal_demand = self.demand_predictor.predict_demand(
            optimal_price, datetime.now(), context
        )
        optimal_profit = self.calculate_profit(
            optimal_price, optimal_demand, context['cost']
        )
        
        return {
            'optimal_price': optimal_price,
            'expected_demand': optimal_demand,
            'expected_profit': optimal_profit,
            'price_change': (optimal_price - context.get('current_price', optimal_price)) / context.get('current_price', optimal_price),
            'confidence': 0.85  # 신뢰도
        }
    
    def _optimize_for_revenue(self, product_id: str, context: Dict[str, Any],
                            min_price: float, max_price: float) -> Dict[str, Any]:
        """매출 최대화"""
        
        def objective(price):
            demand = self.demand_predictor.predict_demand(
                price[0], datetime.now(), context
            )
            revenue = price[0] * demand
            return -revenue  # 최대화를 위해 음수
        
        result = minimize(
            objective,
            x0=[context.get('current_price', (min_price + max_price) / 2)],
            bounds=[(min_price, max_price)],
            method='L-BFGS-B'
        )
        
        optimal_price = result.x[0]
        optimal_demand = self.demand_predictor.predict_demand(
            optimal_price, datetime.now(), context
        )
        
        return {
            'optimal_price': optimal_price,
            'expected_demand': optimal_demand,
            'expected_revenue': optimal_price * optimal_demand,
            'price_change': (optimal_price - context.get('current_price', optimal_price)) / context.get('current_price', optimal_price),
            'confidence': 0.80
        }
    
    def _optimize_for_market_share(self, product_id: str, context: Dict[str, Any],
                                 min_price: float, max_price: float) -> Dict[str, Any]:
        """시장 점유율 최대화 (경쟁사 대비)"""
        
        competitor_price = context.get('competitor_price', max_price * 0.9)
        
        # 경쟁사보다 약간 낮은 가격 설정
        optimal_price = min(competitor_price * 0.95, max_price)
        optimal_price = max(optimal_price, min_price)
        
        optimal_demand = self.demand_predictor.predict_demand(
            optimal_price, datetime.now(), context
        )
        
        return {
            'optimal_price': optimal_price,
            'expected_demand': optimal_demand,
            'price_vs_competitor': optimal_price / competitor_price,
            'confidence': 0.75
        }
    
    def _dynamic_pricing(self, product_id: str, context: Dict[str, Any],
                       min_price: float, max_price: float) -> Dict[str, Any]:
        """동적 가격 결정 (시간대별, 재고 기반)"""
        
        current_hour = datetime.now().hour
        stock_level = context.get('stock_level', 100)
        days_until_expiry = context.get('days_until_expiry', 30)
        
        # 시간대별 조정
        time_multiplier = 1.0
        if 18 <= current_hour <= 22:  # 피크 시간
            time_multiplier = 1.1
        elif 0 <= current_hour <= 6:  # 새벽
            time_multiplier = 0.9
        
        # 재고 기반 조정
        stock_multiplier = 1.0
        if stock_level < 10:  # 재고 부족
            stock_multiplier = 1.2
        elif stock_level > 200:  # 재고 과다
            stock_multiplier = 0.85
        
        # 유통기한 기반 조정
        expiry_multiplier = 1.0
        if days_until_expiry < 7:
            expiry_multiplier = 0.7 + (days_until_expiry / 30)
        
        # 기본 가격에 조정 계수 적용
        base_price = context.get('current_price', (min_price + max_price) / 2)
        optimal_price = base_price * time_multiplier * stock_multiplier * expiry_multiplier
        
        # 범위 제한
        optimal_price = max(min_price, min(max_price, optimal_price))
        
        optimal_demand = self.demand_predictor.predict_demand(
            optimal_price, datetime.now(), context
        )
        
        return {
            'optimal_price': optimal_price,
            'expected_demand': optimal_demand,
            'adjustments': {
                'time_factor': time_multiplier,
                'stock_factor': stock_multiplier,
                'expiry_factor': expiry_multiplier
            },
            'confidence': 0.90
        }


class RLPricingAgent:
    """강화학습 기반 가격 결정 에이전트"""
    
    def __init__(self, state_size: int = 10, action_size: int = 21):
        self.state_size = state_size
        self.action_size = action_size  # 가격 조정 범위 (-10% ~ +10%, 1% 단위)
        
        # DQN 네트워크
        self.q_network = self._build_network()
        self.target_network = self._build_network()
        self.update_target_network()
        
        # 하이퍼파라미터
        self.memory = deque(maxlen=2000)
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.gamma = 0.95
        self.batch_size = 32
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)
        
    def _build_network(self) -> nn.Module:
        """신경망 구성"""
        return nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_size)
        )
    
    def update_target_network(self):
        """타겟 네트워크 업데이트"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def get_state(self, context: Dict[str, Any]) -> np.ndarray:
        """환경 상태 벡터 생성"""
        state = [
            context.get('current_price', 100),
            context.get('demand', 50),
            context.get('stock_level', 100),
            context.get('competitor_price', 100),
            context.get('hour', 12),
            context.get('day_of_week', 3),
            context.get('season', 2),
            context.get('profit_margin', 0.2),
            context.get('market_share', 0.3),
            context.get('customer_satisfaction', 0.8)
        ]
        return np.array(state, dtype=np.float32)
    
    def act(self, state: np.ndarray) -> int:
        """행동 선택 (epsilon-greedy)"""
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_network(state_tensor)
            return np.argmax(q_values.cpu().numpy())
    
    def remember(self, state, action, reward, next_state, done):
        """경험 저장"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """경험 재생을 통한 학습"""
        if len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.FloatTensor([e[4] for e in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Epsilon 감소
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def get_price_adjustment(self, action: int) -> float:
        """행동을 가격 조정률로 변환"""
        # -10% ~ +10% 범위
        return (action - self.action_size // 2) * 0.01


class MultiObjectivePriceOptimizer:
    """다목적 가격 최적화"""
    
    def __init__(self):
        self.pareto_front = []
        
    def optimize_multi_objective(self, product_id: str, context: Dict[str, Any],
                               objectives: List[str]) -> List[Dict[str, Any]]:
        """파레토 최적해 찾기"""
        
        # 목적 함수 정의
        def multi_objective(x):
            price = x[0]
            demand = context['demand_function'](price)
            cost = context['cost']
            
            results = []
            
            if 'profit' in objectives:
                profit = (price - cost) * demand
                results.append(-profit)  # 최소화 문제로 변환
            
            if 'revenue' in objectives:
                revenue = price * demand
                results.append(-revenue)
            
            if 'market_share' in objectives:
                competitor_price = context.get('competitor_price', price)
                market_share = demand / (demand + context['competitor_demand'])
                results.append(-market_share)
            
            if 'inventory_turnover' in objectives:
                turnover = demand / context.get('stock_level', 100)
                results.append(-turnover)
            
            return results
        
        # 차분 진화 알고리즘으로 파레토 프론트 찾기
        bounds = [(context['min_price'], context['max_price'])]
        
        result = differential_evolution(
            lambda x: sum(multi_objective(x)),  # 단일 목적으로 변환
            bounds,
            seed=42,
            workers=1
        )
        
        # 파레토 프론트 구성
        pareto_solutions = []
        
        # 여러 가중치 조합으로 파레토 해 생성
        for w1 in np.linspace(0, 1, 11):
            w2 = 1 - w1
            
            def weighted_objective(x):
                objs = multi_objective(x)
                if len(objs) >= 2:
                    return w1 * objs[0] + w2 * objs[1]
                return objs[0]
            
            res = minimize(
                weighted_objective,
                x0=[context.get('current_price', 100)],
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            if res.success:
                price = res.x[0]
                demand = context['demand_function'](price)
                
                solution = {
                    'price': price,
                    'objectives': {},
                    'demand': demand
                }
                
                if 'profit' in objectives:
                    solution['objectives']['profit'] = (price - context['cost']) * demand
                if 'revenue' in objectives:
                    solution['objectives']['revenue'] = price * demand
                if 'market_share' in objectives:
                    solution['objectives']['market_share'] = demand / (demand + context.get('competitor_demand', demand))
                
                pareto_solutions.append(solution)
        
        # 중복 제거 및 정렬
        self.pareto_front = self._filter_dominated_solutions(pareto_solutions)
        
        return self.pareto_front
    
    def _filter_dominated_solutions(self, solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """지배되는 해 제거"""
        pareto_front = []
        
        for sol in solutions:
            dominated = False
            
            for other in solutions:
                if sol == other:
                    continue
                
                # 다른 해가 모든 목적에서 더 좋은지 확인
                all_better = True
                for obj in sol['objectives']:
                    if sol['objectives'][obj] > other['objectives'][obj]:
                        all_better = False
                        break
                
                if all_better:
                    dominated = True
                    break
            
            if not dominated:
                pareto_front.append(sol)
        
        return pareto_front