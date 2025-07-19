#!/usr/bin/env python3
"""
재고 자동 발주 AI 시스템
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# 예측 모델
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

# 최적화
from scipy.optimize import minimize, linprog
from scipy.stats import norm
import pulp

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """발주 상태"""
    PENDING = "pending"
    SUGGESTED = "suggested"
    APPROVED = "approved"
    ORDERED = "ordered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class InventoryPolicy:
    """재고 정책"""
    reorder_point: float
    order_quantity: float
    safety_stock: float
    service_level: float = 0.95
    lead_time_days: int = 3
    review_period_days: int = 1


@dataclass
class PurchaseOrder:
    """구매 발주"""
    order_id: str
    product_id: str
    supplier_id: str
    quantity: int
    unit_price: float
    order_date: datetime
    expected_delivery: datetime
    status: OrderStatus
    urgency_score: float
    confidence_score: float


class InventoryAI:
    """재고 자동 발주 AI 시스템"""
    
    def __init__(self):
        self.demand_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.lead_time_model = LinearRegression()
        self.is_trained = False
        self.policies = {}
        self.order_history = []
        
    def calculate_safety_stock(self, demand_std: float, lead_time: int,
                             service_level: float = 0.95) -> float:
        """안전재고 계산"""
        # Z-score for service level
        z_score = norm.ppf(service_level)
        
        # 안전재고 = Z * σ * √LT
        safety_stock = z_score * demand_std * np.sqrt(lead_time)
        
        return safety_stock
    
    def calculate_reorder_point(self, avg_demand: float, lead_time: int,
                               safety_stock: float) -> float:
        """재주문점 계산"""
        reorder_point = (avg_demand * lead_time) + safety_stock
        return reorder_point
    
    def calculate_eoq(self, annual_demand: float, ordering_cost: float,
                     holding_cost: float) -> float:
        """경제적 주문량 (EOQ) 계산"""
        if holding_cost <= 0:
            return 0
        
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        return eoq
    
    def train_demand_model(self, sales_data: pd.DataFrame) -> Dict[str, float]:
        """수요 예측 모델 학습"""
        logger.info("수요 예측 모델 학습 시작")
        
        # 특성 생성
        features = self._create_demand_features(sales_data)
        target = sales_data['quantity_sold']
        
        # 학습
        self.demand_model.fit(features, target)
        
        # 평가
        score = self.demand_model.score(features, target)
        
        logger.info(f"수요 예측 모델 학습 완료 - R²: {score:.3f}")
        return {'r2_score': score}
    
    def _create_demand_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """수요 예측을 위한 특성 생성"""
        features = pd.DataFrame()
        
        # 시간 특성
        features['day_of_week'] = pd.to_datetime(data['date']).dt.dayofweek
        features['month'] = pd.to_datetime(data['date']).dt.month
        features['quarter'] = pd.to_datetime(data['date']).dt.quarter
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # 이동 평균
        if 'quantity_sold' in data.columns:
            features['ma_7'] = data['quantity_sold'].rolling(7, min_periods=1).mean()
            features['ma_30'] = data['quantity_sold'].rolling(30, min_periods=1).mean()
        
        # 가격 특성
        if 'price' in data.columns:
            features['price'] = data['price']
            features['price_change'] = data['price'].pct_change().fillna(0)
        
        # 재고 수준
        if 'stock_level' in data.columns:
            features['stock_level'] = data['stock_level']
            features['stock_ratio'] = data['stock_level'] / data['stock_level'].mean()
        
        # 프로모션
        if 'is_promotion' in data.columns:
            features['is_promotion'] = data['is_promotion'].astype(int)
        
        return features.fillna(0)
    
    def predict_demand(self, product_id: str, days_ahead: int = 7) -> Dict[str, Any]:
        """미래 수요 예측"""
        # 시뮬레이션 데이터 생성 (실제로는 최근 데이터 사용)
        future_dates = pd.date_range(
            start=datetime.now(),
            periods=days_ahead,
            freq='D'
        )
        
        predictions = []
        for date in future_dates:
            # 특성 생성
            features = pd.DataFrame([{
                'day_of_week': date.dayofweek,
                'month': date.month,
                'quarter': date.quarter,
                'is_weekend': date.dayofweek in [5, 6],
                'ma_7': 50,  # 실제로는 최근 평균 사용
                'ma_30': 45,
                'price': 10000,
                'price_change': 0,
                'stock_level': 100,
                'stock_ratio': 1.0,
                'is_promotion': 0
            }])
            
            # 예측
            demand = self.demand_model.predict(features)[0] if hasattr(self, 'demand_model') else 50
            predictions.append({
                'date': date,
                'predicted_demand': demand,
                'confidence_interval': (demand * 0.8, demand * 1.2)
            })
        
        return {
            'product_id': product_id,
            'predictions': predictions,
            'total_demand': sum(p['predicted_demand'] for p in predictions)
        }
    
    def optimize_inventory_policy(self, product_id: str, 
                                historical_data: pd.DataFrame,
                                constraints: Dict[str, Any]) -> InventoryPolicy:
        """재고 정책 최적화"""
        
        # 수요 통계
        daily_demand = historical_data['quantity_sold'].mean()
        demand_std = historical_data['quantity_sold'].std()
        
        # 제약 조건
        service_level = constraints.get('service_level', 0.95)
        lead_time = constraints.get('lead_time_days', 3)
        ordering_cost = constraints.get('ordering_cost', 50000)
        holding_cost_rate = constraints.get('holding_cost_rate', 0.2)
        unit_cost = constraints.get('unit_cost', 10000)
        
        # 연간 수요
        annual_demand = daily_demand * 365
        
        # 보유 비용
        holding_cost = unit_cost * holding_cost_rate
        
        # EOQ 계산
        eoq = self.calculate_eoq(annual_demand, ordering_cost, holding_cost)
        
        # 안전재고 계산
        safety_stock = self.calculate_safety_stock(
            demand_std, lead_time, service_level
        )
        
        # 재주문점 계산
        reorder_point = self.calculate_reorder_point(
            daily_demand, lead_time, safety_stock
        )
        
        # 정책 생성
        policy = InventoryPolicy(
            reorder_point=reorder_point,
            order_quantity=eoq,
            safety_stock=safety_stock,
            service_level=service_level,
            lead_time_days=lead_time
        )
        
        self.policies[product_id] = policy
        
        return policy
    
    def check_reorder_needed(self, product_id: str, current_stock: float,
                           pending_orders: float = 0) -> Tuple[bool, Dict[str, Any]]:
        """재주문 필요 여부 확인"""
        
        if product_id not in self.policies:
            return False, {'reason': 'No policy defined'}
        
        policy = self.policies[product_id]
        
        # 유효 재고 = 현재 재고 + 발주 중인 재고
        effective_inventory = current_stock + pending_orders
        
        # 재주문 필요 여부
        needs_reorder = effective_inventory <= policy.reorder_point
        
        # 긴급도 계산
        if needs_reorder:
            days_of_stock = effective_inventory / (policy.reorder_point / policy.lead_time_days)
            urgency = 1 - (days_of_stock / policy.lead_time_days)
            urgency = max(0, min(1, urgency))
        else:
            urgency = 0
        
        return needs_reorder, {
            'current_stock': current_stock,
            'reorder_point': policy.reorder_point,
            'effective_inventory': effective_inventory,
            'urgency_score': urgency,
            'recommended_quantity': policy.order_quantity if needs_reorder else 0
        }
    
    def create_purchase_order(self, product_id: str, supplier_id: str,
                            current_stock: float, context: Dict[str, Any]) -> PurchaseOrder:
        """구매 발주 생성"""
        
        # 재주문 확인
        needs_reorder, reorder_info = self.check_reorder_needed(
            product_id, current_stock
        )
        
        if not needs_reorder:
            return None
        
        # 발주 수량 결정
        policy = self.policies[product_id]
        order_quantity = reorder_info['recommended_quantity']
        
        # 공급업체별 조정
        supplier_constraints = context.get('supplier_constraints', {})
        min_order = supplier_constraints.get('min_order_quantity', 1)
        order_quantity = max(order_quantity, min_order)
        
        # 가격 정보
        unit_price = context.get('unit_price', 10000)
        
        # 발주 생성
        order = PurchaseOrder(
            order_id=f"PO-{product_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            product_id=product_id,
            supplier_id=supplier_id,
            quantity=int(order_quantity),
            unit_price=unit_price,
            order_date=datetime.now(),
            expected_delivery=datetime.now() + timedelta(days=policy.lead_time_days),
            status=OrderStatus.SUGGESTED,
            urgency_score=reorder_info['urgency_score'],
            confidence_score=0.85
        )
        
        return order
    
    def optimize_multi_product_orders(self, products: List[Dict[str, Any]],
                                    budget: float) -> List[PurchaseOrder]:
        """다중 제품 발주 최적화"""
        
        # 선형 계획 문제 설정
        prob = pulp.LpProblem("Multi_Product_Ordering", pulp.LpMaximize)
        
        # 변수 정의
        order_vars = {}
        for i, product in enumerate(products):
            var_name = f"order_{product['product_id']}"
            order_vars[var_name] = pulp.LpVariable(
                var_name,
                lowBound=0,
                upBound=product.get('max_order', 1000),
                cat='Integer'
            )
        
        # 목적 함수: 서비스 수준 최대화
        objective = 0
        for i, product in enumerate(products):
            var_name = f"order_{product['product_id']}"
            # 긴급도와 수요를 고려한 가중치
            weight = product['urgency'] * product['expected_demand']
            objective += weight * order_vars[var_name]
        
        prob += objective
        
        # 제약 조건
        # 1. 예산 제약
        budget_constraint = 0
        for i, product in enumerate(products):
            var_name = f"order_{product['product_id']}"
            budget_constraint += product['unit_price'] * order_vars[var_name]
        
        prob += budget_constraint <= budget
        
        # 2. 창고 용량 제약
        if 'warehouse_capacity' in products[0]:
            capacity_constraint = 0
            for i, product in enumerate(products):
                var_name = f"order_{product['product_id']}"
                capacity_constraint += product.get('volume', 1) * order_vars[var_name]
            
            total_capacity = sum(p.get('warehouse_capacity', 10000) for p in products)
            prob += capacity_constraint <= total_capacity
        
        # 3. 최소 주문량 제약
        for i, product in enumerate(products):
            var_name = f"order_{product['product_id']}"
            if product.get('needs_reorder', False):
                min_order = product.get('min_order_quantity', 0)
                prob += order_vars[var_name] >= min_order
        
        # 문제 해결
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # 결과 변환
        orders = []
        if prob.status == pulp.LpStatusOptimal:
            for i, product in enumerate(products):
                var_name = f"order_{product['product_id']}"
                quantity = order_vars[var_name].varValue
                
                if quantity > 0:
                    order = PurchaseOrder(
                        order_id=f"PO-{product['product_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        product_id=product['product_id'],
                        supplier_id=product['supplier_id'],
                        quantity=int(quantity),
                        unit_price=product['unit_price'],
                        order_date=datetime.now(),
                        expected_delivery=datetime.now() + timedelta(days=product.get('lead_time', 3)),
                        status=OrderStatus.SUGGESTED,
                        urgency_score=product.get('urgency', 0.5),
                        confidence_score=0.90
                    )
                    orders.append(order)
        
        return orders
    
    def simulate_inventory_scenarios(self, product_id: str,
                                   scenarios: List[Dict[str, Any]],
                                   horizon_days: int = 30) -> Dict[str, Any]:
        """재고 시나리오 시뮬레이션"""
        
        results = []
        
        for scenario in scenarios:
            # 시나리오 파라미터
            initial_stock = scenario.get('initial_stock', 100)
            daily_demand_mean = scenario.get('daily_demand_mean', 10)
            daily_demand_std = scenario.get('daily_demand_std', 3)
            lead_time = scenario.get('lead_time', 3)
            order_quantity = scenario.get('order_quantity', 50)
            reorder_point = scenario.get('reorder_point', 30)
            
            # 시뮬레이션
            stock_levels = [initial_stock]
            stockouts = 0
            orders_placed = 0
            pending_deliveries = []
            
            for day in range(horizon_days):
                current_stock = stock_levels[-1]
                
                # 배송 도착 처리
                arrived_orders = [
                    o for o in pending_deliveries 
                    if o['arrival_day'] == day
                ]
                for order in arrived_orders:
                    current_stock += order['quantity']
                    pending_deliveries.remove(order)
                
                # 수요 발생
                demand = max(0, np.random.normal(daily_demand_mean, daily_demand_std))
                
                # 재고 차감
                if current_stock >= demand:
                    current_stock -= demand
                else:
                    stockouts += 1
                    current_stock = 0
                
                # 재주문 확인
                pending_quantity = sum(o['quantity'] for o in pending_deliveries)
                if current_stock + pending_quantity <= reorder_point:
                    # 발주
                    pending_deliveries.append({
                        'quantity': order_quantity,
                        'arrival_day': day + lead_time
                    })
                    orders_placed += 1
                
                stock_levels.append(current_stock)
            
            # 결과 계산
            avg_stock = np.mean(stock_levels)
            service_level = 1 - (stockouts / horizon_days)
            total_orders = orders_placed
            
            results.append({
                'scenario': scenario,
                'avg_stock_level': avg_stock,
                'service_level': service_level,
                'stockout_days': stockouts,
                'total_orders': total_orders,
                'holding_cost': avg_stock * scenario.get('holding_cost_per_unit', 100),
                'ordering_cost': total_orders * scenario.get('ordering_cost', 50000),
                'stock_levels': stock_levels
            })
        
        # 최적 시나리오 선택
        best_scenario = min(
            results,
            key=lambda x: x['holding_cost'] + x['ordering_cost'] + 
                         (1 - x['service_level']) * 1000000  # 서비스 수준 페널티
        )
        
        return {
            'scenarios': results,
            'best_scenario': best_scenario,
            'recommendation': {
                'reorder_point': best_scenario['scenario']['reorder_point'],
                'order_quantity': best_scenario['scenario']['order_quantity'],
                'expected_cost': best_scenario['holding_cost'] + best_scenario['ordering_cost'],
                'expected_service_level': best_scenario['service_level']
            }
        }
    
    def get_supplier_performance(self, supplier_id: str) -> Dict[str, Any]:
        """공급업체 성과 분석"""
        # 실제로는 주문 이력에서 계산
        return {
            'supplier_id': supplier_id,
            'avg_lead_time': 3.2,
            'lead_time_variability': 0.8,
            'on_time_delivery_rate': 0.92,
            'quality_score': 0.95,
            'price_competitiveness': 0.88,
            'overall_score': 0.91
        }