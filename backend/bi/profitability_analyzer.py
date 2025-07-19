#!/usr/bin/env python3
"""
수익성 분석 엔진
- 상품별/카테고리별 수익성 계산
- 마진율 분석 및 최적화
- 수익 예측 모델
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from dataclasses import dataclass
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProfitabilityMetrics:
    """수익성 지표"""
    revenue: float
    cost: float
    gross_profit: float
    gross_margin: float
    net_profit: float
    net_margin: float
    roi: float  # Return on Investment
    breakeven_point: int  # 손익분기점 수량

class ProfitabilityAnalyzer:
    """수익성 분석 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 비용 구조 설정 (%)
        self.cost_structure = {
            'marketplace_fee': 0.10,      # 마켓플레이스 수수료 10%
            'payment_fee': 0.025,         # 결제 수수료 2.5%
            'shipping_fee': 0.05,         # 배송비 5%
            'operation_cost': 0.03,       # 운영비 3%
            'marketing_cost': 0.02,       # 마케팅비 2%
            'tax_rate': 0.10             # 세금 10%
        }
    
    def calculate_product_profitability(
        self, 
        product_id: int,
        selling_price: float,
        supplier_price: float,
        expected_quantity: int = 1
    ) -> ProfitabilityMetrics:
        """상품별 수익성 계산"""
        
        # 매출
        revenue = selling_price * expected_quantity
        
        # 원가
        cost_of_goods = supplier_price * expected_quantity
        
        # 판매 관련 비용
        marketplace_fee = revenue * self.cost_structure['marketplace_fee']
        payment_fee = revenue * self.cost_structure['payment_fee']
        shipping_fee = revenue * self.cost_structure['shipping_fee']
        operation_cost = revenue * self.cost_structure['operation_cost']
        marketing_cost = revenue * self.cost_structure['marketing_cost']
        
        # 총 비용
        total_cost = (cost_of_goods + marketplace_fee + payment_fee + 
                     shipping_fee + operation_cost + marketing_cost)
        
        # 매출총이익
        gross_profit = revenue - cost_of_goods
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        # 순이익 (세전)
        profit_before_tax = revenue - total_cost
        tax = profit_before_tax * self.cost_structure['tax_rate'] if profit_before_tax > 0 else 0
        
        # 순이익 (세후)
        net_profit = profit_before_tax - tax
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        
        # ROI
        roi = (net_profit / total_cost * 100) if total_cost > 0 else 0
        
        # 손익분기점
        if selling_price > supplier_price:
            fixed_costs = operation_cost / expected_quantity  # 단위당 고정비
            contribution_margin = selling_price - supplier_price - (
                selling_price * (self.cost_structure['marketplace_fee'] + 
                               self.cost_structure['payment_fee'] + 
                               self.cost_structure['shipping_fee'])
            )
            breakeven_point = int(fixed_costs / contribution_margin) if contribution_margin > 0 else 0
        else:
            breakeven_point = 0
        
        return ProfitabilityMetrics(
            revenue=revenue,
            cost=total_cost,
            gross_profit=gross_profit,
            gross_margin=gross_margin,
            net_profit=net_profit,
            net_margin=net_margin,
            roi=roi,
            breakeven_point=breakeven_point
        )
    
    def analyze_category_profitability(self) -> List[Dict]:
        """카테고리별 수익성 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                WITH category_stats AS (
                    SELECT 
                        sp.category,
                        COUNT(DISTINCT sp.id) as product_count,
                        AVG(sp.price) as avg_selling_price,
                        AVG(sp.cost_price) as avg_cost,
                        SUM(CASE WHEN pai.demand_grade IN ('A', 'B') THEN 1 ELSE 0 END) as high_demand_count,
                        AVG(CAST(pai.demand_score AS DECIMAL)) as avg_demand_score
                    FROM supplier_products sp
                    LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.status = 'active'
                    GROUP BY sp.category
                )
                SELECT 
                    category,
                    product_count,
                    avg_selling_price,
                    avg_cost,
                    high_demand_count,
                    avg_demand_score,
                    (avg_selling_price - avg_cost) / avg_selling_price * 100 as avg_margin
                FROM category_stats
                WHERE avg_cost IS NOT NULL
                ORDER BY avg_margin DESC
            """)
            
            categories = cursor.fetchall()
            
            # 수익성 지표 계산
            for cat in categories:
                if cat['avg_selling_price'] and cat['avg_cost']:
                    metrics = self.calculate_product_profitability(
                        product_id=0,
                        selling_price=float(cat['avg_selling_price']),
                        supplier_price=float(cat['avg_cost']),
                        expected_quantity=100  # 평균 판매량 가정
                    )
                    
                    cat['gross_margin'] = metrics.gross_margin
                    cat['net_margin'] = metrics.net_margin
                    cat['roi'] = metrics.roi
                    cat['profitability_score'] = self._calculate_profitability_score(
                        metrics, float(cat['avg_demand_score'] or 0)
                    )
            
            return categories
    
    def find_optimal_pricing(
        self, 
        product_id: int,
        supplier_price: float,
        market_price_range: Tuple[float, float],
        demand_elasticity: float = -1.5
    ) -> Dict:
        """최적 가격 찾기"""
        
        min_price, max_price = market_price_range
        price_points = np.linspace(min_price, max_price, 20)
        
        best_price = min_price
        best_profit = -float('inf')
        results = []
        
        for price in price_points:
            # 수요 예측 (가격 탄력성 적용)
            price_ratio = price / ((min_price + max_price) / 2)
            demand_factor = price_ratio ** demand_elasticity
            expected_quantity = int(100 * demand_factor)  # 기준 수량 100개
            
            # 수익성 계산
            metrics = self.calculate_product_profitability(
                product_id=product_id,
                selling_price=price,
                supplier_price=supplier_price,
                expected_quantity=expected_quantity
            )
            
            total_profit = metrics.net_profit
            
            results.append({
                'price': price,
                'quantity': expected_quantity,
                'revenue': metrics.revenue,
                'profit': total_profit,
                'margin': metrics.net_margin,
                'roi': metrics.roi
            })
            
            if total_profit > best_profit:
                best_profit = total_profit
                best_price = price
        
        return {
            'optimal_price': best_price,
            'expected_profit': best_profit,
            'price_analysis': results,
            'recommendation': self._generate_pricing_recommendation(
                best_price, supplier_price, market_price_range
            )
        }
    
    def analyze_supplier_profitability(self) -> List[Dict]:
        """공급사별 수익성 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    s.id,
                    s.name,
                    COUNT(sp.id) as total_products,
                    AVG(sp.price) as avg_price,
                    AVG(sp.cost_price) as avg_cost,
                    COUNT(CASE WHEN sp.status = 'active' THEN 1 END) as active_products,
                    AVG(CAST(pai.demand_score AS DECIMAL)) as avg_demand_score,
                    AVG(CAST(pai.predicted_price AS DECIMAL)) as avg_predicted_price
                FROM suppliers s
                JOIN supplier_products sp ON s.id = sp.supplier_id
                LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                WHERE s.is_active = true
                GROUP BY s.id, s.name
            """)
            
            suppliers = cursor.fetchall()
            
            for supplier in suppliers:
                if supplier['avg_price'] and supplier['avg_cost']:
                    # 평균 수익성 계산
                    metrics = self.calculate_product_profitability(
                        product_id=0,
                        selling_price=float(supplier['avg_price']),
                        supplier_price=float(supplier['avg_cost']),
                        expected_quantity=1000  # 공급사별 평균 판매량
                    )
                    
                    supplier['gross_margin'] = metrics.gross_margin
                    supplier['net_margin'] = metrics.net_margin
                    supplier['roi'] = metrics.roi
                    supplier['efficiency_score'] = self._calculate_supplier_efficiency(supplier)
            
            return sorted(suppliers, key=lambda x: x.get('roi', 0), reverse=True)
    
    def generate_profitability_report(self) -> Dict:
        """종합 수익성 리포트 생성"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._get_profitability_summary(),
            'category_analysis': self.analyze_category_profitability(),
            'supplier_analysis': self.analyze_supplier_profitability(),
            'top_profitable_products': self._get_top_profitable_products(),
            'optimization_opportunities': self._find_optimization_opportunities(),
            'risk_analysis': self._analyze_profitability_risks()
        }
        
        return report
    
    def _calculate_profitability_score(self, metrics: ProfitabilityMetrics, demand_score: float) -> float:
        """수익성 점수 계산 (0-100)"""
        
        # 가중치
        weights = {
            'net_margin': 0.3,
            'roi': 0.3,
            'demand': 0.2,
            'gross_margin': 0.2
        }
        
        # 정규화
        margin_score = min(metrics.net_margin / 20 * 100, 100)  # 20% 마진 = 100점
        roi_score = min(metrics.roi / 50 * 100, 100)  # 50% ROI = 100점
        demand_score = demand_score  # 이미 0-100
        gross_margin_score = min(metrics.gross_margin / 30 * 100, 100)  # 30% 매출총이익률 = 100점
        
        # 가중 평균
        score = (
            weights['net_margin'] * margin_score +
            weights['roi'] * roi_score +
            weights['demand'] * demand_score +
            weights['gross_margin'] * gross_margin_score
        )
        
        return round(score, 2)
    
    def _calculate_supplier_efficiency(self, supplier: Dict) -> float:
        """공급사 효율성 점수 계산"""
        
        active_ratio = supplier['active_products'] / supplier['total_products'] if supplier['total_products'] > 0 else 0
        margin = (supplier['avg_price'] - supplier['avg_cost']) / supplier['avg_price'] if supplier['avg_price'] else 0
        demand_score = supplier['avg_demand_score'] or 0
        
        # 효율성 점수 (0-100)
        efficiency = (
            active_ratio * 30 +  # 활성 상품 비율 30%
            min(margin * 200, 40) +  # 마진율 40% (20% 마진 = 40점)
            demand_score * 0.3  # 수요 점수 30%
        )
        
        return round(efficiency, 2)
    
    def _get_profitability_summary(self) -> Dict:
        """전체 수익성 요약"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT sp.id) as total_products,
                    AVG(sp.price - sp.cost_price) as avg_profit,
                    AVG((sp.price - sp.cost_price) / sp.price * 100) as avg_margin,
                    COUNT(CASE WHEN sp.price > sp.cost_price * 1.3 THEN 1 END) as high_margin_products
                FROM supplier_products sp
                WHERE sp.status = 'active'
                AND sp.cost_price IS NOT NULL AND sp.cost_price > 0
            """)
            
            return cursor.fetchone()
    
    def _get_top_profitable_products(self, limit: int = 20) -> List[Dict]:
        """수익성 상위 상품"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    sp.id,
                    sp.name,
                    sp.category,
                    s.name as supplier_name,
                    sp.price as selling_price,
                    sp.cost_price as cost,
                    sp.price - sp.cost_price as profit,
                    (sp.price - sp.cost_price) / sp.price * 100 as margin,
                    pai.demand_score,
                    pai.demand_grade
                FROM supplier_products sp
                JOIN suppliers s ON sp.supplier_id = s.id
                LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                WHERE sp.status = 'active'
                AND sp.cost_price IS NOT NULL AND sp.cost_price > 0
                AND sp.price > sp.cost_price
                ORDER BY (sp.price - sp.cost_price) DESC
                LIMIT %s
            """, (limit,))
            
            products = cursor.fetchall()
            
            # 상세 수익성 지표 추가
            for product in products:
                metrics = self.calculate_product_profitability(
                    product_id=product['id'],
                    selling_price=float(product['selling_price']),
                    supplier_price=float(product['cost']),
                    expected_quantity=10
                )
                
                product['net_margin'] = metrics.net_margin
                product['roi'] = metrics.roi
                product['breakeven_point'] = metrics.breakeven_point
            
            return products
    
    def _find_optimization_opportunities(self) -> List[Dict]:
        """수익성 최적화 기회 찾기"""
        
        opportunities = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. 저마진 고수요 상품
            cursor.execute("""
                SELECT 
                    sp.id,
                    sp.name,
                    sp.category,
                    sp.price,
                    sp.cost_price as cost,
                    (sp.price - sp.cost_price) / sp.price * 100 as margin,
                    pai.demand_score
                FROM supplier_products sp
                JOIN product_ai_insights pai ON sp.id = pai.product_id
                WHERE sp.status = 'active'
                AND sp.cost_price IS NOT NULL AND sp.cost_price > 0
                AND (sp.price - sp.cost_price) / sp.price * 100 < 15
                AND pai.demand_score > 70
                LIMIT 10
            """)
            
            low_margin_high_demand = cursor.fetchall()
            
            for product in low_margin_high_demand:
                opportunities.append({
                    'type': 'price_optimization',
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'current_margin': product['margin'],
                    'demand_score': product['demand_score'],
                    'recommendation': '높은 수요를 활용한 가격 인상 검토',
                    'potential_improvement': '마진율 5-10% 개선 가능'
                })
            
            # 2. 비활성 고마진 상품
            cursor.execute("""
                SELECT 
                    sp.id,
                    sp.name,
                    sp.category,
                    (sp.price - sp.cost_price) / sp.price * 100 as margin
                FROM supplier_products sp
                WHERE sp.status = 'inactive'
                AND sp.cost_price IS NOT NULL AND sp.cost_price > 0
                AND (sp.price - sp.cost_price) / sp.price * 100 > 30
                LIMIT 10
            """)
            
            inactive_high_margin = cursor.fetchall()
            
            for product in inactive_high_margin:
                opportunities.append({
                    'type': 'reactivation',
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'margin': product['margin'],
                    'recommendation': '고마진 상품 재활성화 검토',
                    'potential_improvement': '추가 수익원 확보'
                })
        
        return opportunities
    
    def _analyze_profitability_risks(self) -> List[Dict]:
        """수익성 리스크 분석"""
        
        risks = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. 단일 공급사 의존도
            cursor.execute("""
                WITH supplier_revenue AS (
                    SELECT 
                        s.name,
                        COUNT(sp.id) as product_count,
                        SUM(sp.price - sp.cost_price) as total_profit
                    FROM suppliers s
                    JOIN supplier_products sp ON s.id = sp.supplier_id
                    WHERE sp.status = 'active'
                    AND sp.cost_price IS NOT NULL AND sp.cost_price > 0
                    GROUP BY s.name
                )
                SELECT 
                    name,
                    product_count,
                    total_profit,
                    total_profit / SUM(total_profit) OVER () * 100 as profit_share
                FROM supplier_revenue
                ORDER BY profit_share DESC
            """)
            
            supplier_concentration = cursor.fetchall()
            
            if supplier_concentration and supplier_concentration[0]['profit_share'] > 50:
                risks.append({
                    'type': 'supplier_concentration',
                    'severity': 'high',
                    'description': f"{supplier_concentration[0]['name']} 공급사가 전체 수익의 {supplier_concentration[0]['profit_share']:.1f}%를 차지",
                    'recommendation': '공급사 다변화 필요'
                })
            
            # 2. 저마진 상품 비중
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN (price - cost_price) / price * 100 < 10 THEN 1 END) as low_margin_count,
                    COUNT(*) as total_count
                FROM supplier_products
                WHERE status = 'active'
                AND cost_price IS NOT NULL AND cost_price > 0
            """)
            
            margin_analysis = cursor.fetchone()
            low_margin_ratio = margin_analysis['low_margin_count'] / margin_analysis['total_count'] * 100
            
            if low_margin_ratio > 30:
                risks.append({
                    'type': 'low_margin_products',
                    'severity': 'medium',
                    'description': f"전체 상품의 {low_margin_ratio:.1f}%가 10% 미만의 낮은 마진율",
                    'recommendation': '가격 정책 재검토 및 고마진 상품 확대'
                })
        
        return risks
    
    def _generate_pricing_recommendation(
        self, 
        optimal_price: float, 
        supplier_price: float,
        market_range: Tuple[float, float]
    ) -> str:
        """가격 전략 추천"""
        
        min_price, max_price = market_range
        market_position = (optimal_price - min_price) / (max_price - min_price)
        
        if market_position < 0.3:
            strategy = "저가 전략: 가격 경쟁력을 통한 판매량 극대화"
        elif market_position < 0.7:
            strategy = "중간가 전략: 가격과 품질의 균형"
        else:
            strategy = "프리미엄 전략: 고품질 이미지와 높은 마진 추구"
        
        margin = (optimal_price - supplier_price) / optimal_price * 100
        
        return f"{strategy} (최적가: {optimal_price:,.0f}원, 마진율: {margin:.1f}%)"


def main():
    """테스트 실행"""
    analyzer = ProfitabilityAnalyzer()
    
    # 1. 카테고리별 수익성 분석
    print("\n📊 카테고리별 수익성 분석")
    print("=" * 80)
    categories = analyzer.analyze_category_profitability()
    for cat in categories[:5]:
        print(f"\n{cat['category']}:")
        print(f"  상품 수: {cat['product_count']}개")
        print(f"  평균 마진율: {cat.get('net_margin', 0):.1f}%")
        print(f"  ROI: {cat.get('roi', 0):.1f}%")
        print(f"  수익성 점수: {cat.get('profitability_score', 0):.1f}점")
    
    # 2. 최적 가격 찾기
    print("\n💰 최적 가격 분석 (예시)")
    print("=" * 80)
    pricing = analyzer.find_optimal_pricing(
        product_id=1,
        supplier_price=10000,
        market_price_range=(15000, 25000),
        demand_elasticity=-1.2
    )
    print(f"최적 가격: {pricing['optimal_price']:,.0f}원")
    print(f"예상 수익: {pricing['expected_profit']:,.0f}원")
    print(f"추천: {pricing['recommendation']}")


if __name__ == "__main__":
    main()