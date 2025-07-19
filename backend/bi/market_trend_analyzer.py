#!/usr/bin/env python3
"""
시장 트렌드 분석 엔진
- 실시간 트렌드 감지
- 계절성 분석
- 수요 예측
- 신규 기회 발굴
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketTrendAnalyzer:
    """시장 트렌드 분석 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 트렌드 카테고리
        self.trend_categories = {
            'rising_star': '급성장 상품',
            'steady_seller': '스테디셀러',
            'seasonal': '계절 상품',
            'declining': '하락세 상품',
            'new_opportunity': '신규 기회'
        }
        
        self._create_tables()
    
    def _create_tables(self):
        """트렌드 분석 테이블 생성"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_trends (
                    id SERIAL PRIMARY KEY,
                    trend_date DATE NOT NULL,
                    category VARCHAR(200),
                    trend_type VARCHAR(50),
                    trend_score DECIMAL(5, 2),
                    growth_rate DECIMAL(10, 2),
                    demand_index DECIMAL(10, 2),
                    competitive_index DECIMAL(5, 2),
                    opportunity_score DECIMAL(5, 2),
                    key_insights JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trend_date, category)
                );
                
                CREATE TABLE IF NOT EXISTS product_trends (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES supplier_products(id),
                    trend_type VARCHAR(50),
                    trend_score DECIMAL(5, 2),
                    weekly_growth DECIMAL(10, 2),
                    monthly_growth DECIMAL(10, 2),
                    seasonality_factor DECIMAL(5, 2),
                    lifecycle_stage VARCHAR(50), -- 'introduction', 'growth', 'maturity', 'decline'
                    recommendation TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS emerging_keywords (
                    id SERIAL PRIMARY KEY,
                    keyword VARCHAR(200),
                    category VARCHAR(200),
                    frequency INTEGER,
                    growth_rate DECIMAL(10, 2),
                    first_seen DATE,
                    last_seen DATE,
                    related_products JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(keyword, category)
                );
                
                CREATE INDEX IF NOT EXISTS idx_market_trends_date ON market_trends(trend_date DESC);
                CREATE INDEX IF NOT EXISTS idx_product_trends_type ON product_trends(trend_type, analyzed_at DESC);
                CREATE INDEX IF NOT EXISTS idx_emerging_keywords_growth ON emerging_keywords(growth_rate DESC);
            """)
            self.conn.commit()
    
    def analyze_market_trends(self) -> Dict:
        """전체 시장 트렌드 분석"""
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'category_trends': self._analyze_category_trends(),
            'product_lifecycle': self._analyze_product_lifecycle(),
            'seasonal_patterns': self._detect_seasonal_patterns(),
            'emerging_opportunities': self._find_emerging_opportunities(),
            'market_insights': self._generate_market_insights()
        }
        
        # 트렌드 저장
        self._save_trend_analysis(results)
        
        return results
    
    def _analyze_category_trends(self) -> List[Dict]:
        """카테고리별 트렌드 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 카테고리별 성장률 계산
            cursor.execute("""
                WITH category_stats AS (
                    SELECT 
                        category,
                        DATE_TRUNC('week', collected_at) as week,
                        COUNT(*) as product_count,
                        AVG(price) as avg_price
                    FROM supplier_products
                    WHERE collected_at > NOW() - INTERVAL '90 days'
                    GROUP BY category, DATE_TRUNC('week', collected_at)
                ),
                growth_calc AS (
                    SELECT 
                        category,
                        week,
                        product_count,
                        avg_price,
                        LAG(product_count) OVER (PARTITION BY category ORDER BY week) as prev_count,
                        LAG(avg_price) OVER (PARTITION BY category ORDER BY week) as prev_price
                    FROM category_stats
                )
                SELECT 
                    category,
                    AVG(CASE 
                        WHEN prev_count > 0 
                        THEN (product_count - prev_count)::FLOAT / prev_count * 100 
                        ELSE 0 
                    END) as avg_growth_rate,
                    AVG(product_count) as avg_products,
                    AVG(avg_price) as current_avg_price,
                    STDDEV(product_count) as volatility
                FROM growth_calc
                WHERE prev_count IS NOT NULL
                GROUP BY category
                ORDER BY avg_growth_rate DESC
            """)
            
            category_trends = cursor.fetchall()
            
            # 트렌드 타입 분류
            for trend in category_trends:
                growth = float(trend['avg_growth_rate'])
                volatility = float(trend['volatility']) if trend['volatility'] else 0
                
                if growth > 20:
                    trend['trend_type'] = 'rising_star'
                    trend['trend_score'] = min(100, growth)
                elif growth > 5 and volatility < 10:
                    trend['trend_type'] = 'steady_seller'
                    trend['trend_score'] = 70 + min(30, growth)
                elif growth < -10:
                    trend['trend_type'] = 'declining'
                    trend['trend_score'] = max(0, 50 + growth)
                else:
                    trend['trend_type'] = 'stable'
                    trend['trend_score'] = 50 + growth
                
                # 경쟁 강도 분석
                trend['competitive_index'] = self._calculate_competitive_index(
                    trend['category']
                )
                
                # 기회 점수
                trend['opportunity_score'] = self._calculate_opportunity_score(
                    growth, 
                    trend['competitive_index'],
                    float(trend['avg_products'])
                )
            
            return category_trends
    
    def _analyze_product_lifecycle(self) -> List[Dict]:
        """상품 라이프사이클 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                WITH product_history AS (
                    SELECT 
                        sp.id,
                        sp.name,
                        sp.category,
                        sp.collected_at,
                        EXTRACT(EPOCH FROM (NOW() - sp.collected_at)) / 86400 as days_since_launch,
                        pai.demand_score,
                        ROW_NUMBER() OVER (PARTITION BY sp.id ORDER BY sp.collected_at) as version
                    FROM supplier_products sp
                    LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.collected_at > NOW() - INTERVAL '180 days'
                ),
                lifecycle_analysis AS (
                    SELECT 
                        id,
                        name,
                        category,
                        MIN(days_since_launch) as product_age,
                        MAX(version) as update_count,
                        AVG(demand_score) as avg_demand,
                        MAX(demand_score) as peak_demand,
                        MIN(demand_score) as min_demand
                    FROM product_history
                    GROUP BY id, name, category
                )
                SELECT 
                    *,
                    CASE 
                        WHEN product_age < 30 THEN 'introduction'
                        WHEN product_age < 90 AND avg_demand > 60 THEN 'growth'
                        WHEN product_age >= 90 AND avg_demand > 50 THEN 'maturity'
                        ELSE 'decline'
                    END as lifecycle_stage
                FROM lifecycle_analysis
                WHERE avg_demand IS NOT NULL
                ORDER BY avg_demand DESC
                LIMIT 100
            """)
            
            products = cursor.fetchall()
            
            lifecycle_insights = []
            
            for product in products:
                stage = product['lifecycle_stage']
                demand = float(product['avg_demand'])
                
                # 단계별 추천
                if stage == 'introduction':
                    recommendation = "마케팅 강화 및 인지도 구축 필요"
                    action = "promote"
                elif stage == 'growth':
                    recommendation = "재고 확대 및 가격 최적화"
                    action = "expand"
                elif stage == 'maturity':
                    recommendation = "차별화 전략 및 번들 상품 개발"
                    action = "differentiate"
                else:
                    recommendation = "할인 판매 또는 단종 검토"
                    action = "liquidate"
                
                lifecycle_insights.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'category': product['category'],
                    'lifecycle_stage': stage,
                    'product_age_days': int(product['product_age']),
                    'average_demand': demand,
                    'recommendation': recommendation,
                    'action': action
                })
                
                # DB에 저장
                self._save_product_trend(product['id'], {
                    'lifecycle_stage': stage,
                    'recommendation': recommendation
                })
            
            return lifecycle_insights
    
    def _detect_seasonal_patterns(self) -> List[Dict]:
        """계절성 패턴 감지"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 월별 판매 패턴 분석
            cursor.execute("""
                WITH monthly_sales AS (
                    SELECT 
                        category,
                        EXTRACT(MONTH FROM sp.collected_at) as month,
                        EXTRACT(YEAR FROM sp.collected_at) as year,
                        COUNT(*) as product_count,
                        AVG(COALESCE(CAST(pai.demand_score AS DECIMAL), 0)) as avg_demand
                    FROM supplier_products sp
                    LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.collected_at > NOW() - INTERVAL '2 years'
                    GROUP BY category, EXTRACT(MONTH FROM sp.collected_at), EXTRACT(YEAR FROM sp.collected_at)
                ),
                seasonal_analysis AS (
                    SELECT 
                        category,
                        month,
                        AVG(product_count) as avg_count,
                        AVG(avg_demand) as avg_monthly_demand,
                        STDDEV(product_count) as count_volatility
                    FROM monthly_sales
                    GROUP BY category, month
                )
                SELECT 
                    category,
                    month,
                    avg_monthly_demand,
                    avg_monthly_demand / AVG(avg_monthly_demand) OVER (PARTITION BY category) as seasonality_index
                FROM seasonal_analysis
                ORDER BY category, month
            """)
            
            seasonal_data = cursor.fetchall()
            
            # 카테고리별 계절성 분석
            seasonal_patterns = {}
            
            for row in seasonal_data:
                category = row['category']
                month = int(row['month'])
                index = float(row['seasonality_index'])
                
                if category not in seasonal_patterns:
                    seasonal_patterns[category] = {
                        'category': category,
                        'monthly_indices': {},
                        'peak_months': [],
                        'low_months': [],
                        'seasonality_strength': 0
                    }
                
                seasonal_patterns[category]['monthly_indices'][month] = index
                
                if index > 1.2:  # 20% 이상 높음
                    seasonal_patterns[category]['peak_months'].append(month)
                elif index < 0.8:  # 20% 이상 낮음
                    seasonal_patterns[category]['low_months'].append(month)
            
            # 계절성 강도 계산
            results = []
            current_month = datetime.now().month
            
            for category, pattern in seasonal_patterns.items():
                indices = list(pattern['monthly_indices'].values())
                seasonality_strength = np.std(indices) * 100  # 변동성으로 계절성 측정
                
                pattern['seasonality_strength'] = seasonality_strength
                
                # 현재 시점 추천
                current_index = pattern['monthly_indices'].get(current_month, 1.0)
                next_month = (current_month % 12) + 1
                next_index = pattern['monthly_indices'].get(next_month, 1.0)
                
                if next_index > current_index * 1.1:
                    recommendation = "수요 증가 예상. 재고 확보 필요"
                elif next_index < current_index * 0.9:
                    recommendation = "수요 감소 예상. 재고 조정 필요"
                else:
                    recommendation = "안정적 수요 예상"
                
                results.append({
                    'category': category,
                    'seasonality_strength': seasonality_strength,
                    'peak_months': pattern['peak_months'],
                    'low_months': pattern['low_months'],
                    'current_index': current_index,
                    'next_month_index': next_index,
                    'recommendation': recommendation
                })
            
            return sorted(results, key=lambda x: x['seasonality_strength'], reverse=True)
    
    def _find_emerging_opportunities(self) -> List[Dict]:
        """신규 기회 발굴"""
        
        opportunities = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. 빠르게 성장하는 키워드 찾기
            cursor.execute("""
                WITH keyword_growth AS (
                    SELECT 
                        LOWER(SUBSTRING(name FROM '([가-힣a-zA-Z]+)')) as keyword,
                        category,
                        COUNT(*) as frequency,
                        MIN(collected_at) as first_seen,
                        MAX(collected_at) as last_seen
                    FROM supplier_products
                    WHERE collected_at > NOW() - INTERVAL '90 days'
                    AND name IS NOT NULL
                    GROUP BY LOWER(SUBSTRING(name FROM '([가-힣a-zA-Z]+)')), category
                    HAVING COUNT(*) > 5
                )
                SELECT 
                    keyword,
                    category,
                    frequency,
                    first_seen,
                    last_seen,
                    EXTRACT(EPOCH FROM (last_seen - first_seen)) / 86400 as days_active,
                    frequency / GREATEST(EXTRACT(EPOCH FROM (last_seen - first_seen)) / 86400, 1) as daily_growth
                FROM keyword_growth
                WHERE EXTRACT(EPOCH FROM (last_seen - first_seen)) / 86400 > 7
                ORDER BY daily_growth DESC
                LIMIT 20
            """)
            
            emerging_keywords = cursor.fetchall()
            
            for keyword in emerging_keywords:
                if keyword['keyword'] and len(keyword['keyword']) > 2:
                    opportunities.append({
                        'type': 'emerging_keyword',
                        'keyword': keyword['keyword'],
                        'category': keyword['category'],
                        'frequency': keyword['frequency'],
                        'growth_rate': float(keyword['daily_growth']),
                        'opportunity': f"'{keyword['keyword']}' 키워드가 급성장 중",
                        'recommendation': '관련 상품 소싱 검토'
                    })
            
            # 2. 공급 부족 카테고리 찾기
            cursor.execute("""
                WITH supply_demand AS (
                    SELECT 
                        sp.category,
                        COUNT(DISTINCT sp.id) as supply_count,
                        AVG(CAST(pai.demand_score AS DECIMAL)) as avg_demand,
                        COUNT(DISTINCT sp.supplier_id) as supplier_count
                    FROM supplier_products sp
                    LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.status = 'active'
                    GROUP BY sp.category
                    HAVING AVG(CAST(pai.demand_score AS DECIMAL)) > 70
                )
                SELECT 
                    category,
                    supply_count,
                    avg_demand,
                    supplier_count,
                    avg_demand / supply_count as opportunity_index
                FROM supply_demand
                WHERE supply_count < 50  -- 공급이 적은 카테고리
                ORDER BY opportunity_index DESC
                LIMIT 10
            """)
            
            supply_gaps = cursor.fetchall()
            
            for gap in supply_gaps:
                opportunities.append({
                    'type': 'supply_gap',
                    'category': gap['category'],
                    'current_supply': gap['supply_count'],
                    'demand_score': float(gap['avg_demand']),
                    'opportunity_index': float(gap['opportunity_index']),
                    'opportunity': f"{gap['category']} 카테고리 공급 부족",
                    'recommendation': '해당 카테고리 상품 확대'
                })
            
            # 3. 가격 차익 기회
            cursor.execute("""
                WITH price_gaps AS (
                    SELECT 
                        sp.category,
                        AVG(sp.price) as our_avg_price,
                        AVG(cp.competitor_price) as market_avg_price,
                        COUNT(DISTINCT sp.id) as product_count
                    FROM supplier_products sp
                    JOIN competitor_prices cp ON sp.id = cp.product_id
                    WHERE sp.status = 'active'
                    AND cp.collected_at > NOW() - INTERVAL '7 days'
                    GROUP BY sp.category
                    HAVING COUNT(DISTINCT sp.id) > 10
                )
                SELECT 
                    category,
                    our_avg_price,
                    market_avg_price,
                    (market_avg_price - our_avg_price) / our_avg_price * 100 as price_gap_percent
                FROM price_gaps
                WHERE market_avg_price > our_avg_price * 1.15  -- 15% 이상 차이
                ORDER BY price_gap_percent DESC
                LIMIT 10
            """)
            
            price_opportunities = cursor.fetchall()
            
            for opp in price_opportunities:
                opportunities.append({
                    'type': 'price_arbitrage',
                    'category': opp['category'],
                    'our_price': float(opp['our_avg_price']),
                    'market_price': float(opp['market_avg_price']),
                    'price_gap': float(opp['price_gap_percent']),
                    'opportunity': f"{opp['category']} 가격 차익 기회",
                    'recommendation': '가격 조정으로 수익성 개선 가능'
                })
        
        return opportunities
    
    def predict_demand_trend(self, category: str, days_ahead: int = 30) -> Dict:
        """수요 예측"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 과거 데이터 조회
            cursor.execute("""
                SELECT 
                    DATE(sp.collected_at) as date,
                    COUNT(*) as product_count,
                    AVG(COALESCE(CAST(pai.demand_score AS DECIMAL), 0)) as avg_demand
                FROM supplier_products sp
                LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                WHERE sp.category = %s
                AND sp.collected_at > NOW() - INTERVAL '180 days'
                GROUP BY DATE(sp.collected_at)
                ORDER BY date
            """, (category,))
            
            historical_data = cursor.fetchall()
            
            if len(historical_data) < 30:
                return {'error': '예측을 위한 충분한 데이터가 없습니다'}
            
            # 간단한 이동평균 예측
            demands = [float(d['avg_demand']) for d in historical_data[-30:]]
            
            # 7일, 14일, 30일 이동평균
            ma7 = np.mean(demands[-7:])
            ma14 = np.mean(demands[-14:])
            ma30 = np.mean(demands)
            
            # 트렌드 계산
            trend = (ma7 - ma30) / ma30 * 100
            
            # 예측
            if trend > 5:
                forecast = "상승"
                confidence = min(90, 50 + trend * 2)
            elif trend < -5:
                forecast = "하락"
                confidence = min(90, 50 + abs(trend) * 2)
            else:
                forecast = "보합"
                confidence = 70
            
            # 계절성 반영
            current_month = datetime.now().month
            seasonal_factor = self._get_seasonal_factor(category, current_month)
            
            predicted_demand = ma7 * seasonal_factor
            
            return {
                'category': category,
                'current_demand': ma7,
                'predicted_demand': predicted_demand,
                'trend': forecast,
                'trend_strength': abs(trend),
                'confidence': confidence,
                'seasonal_factor': seasonal_factor,
                'recommendation': self._generate_demand_recommendation(
                    forecast, trend, seasonal_factor
                )
            }
    
    def _calculate_competitive_index(self, category: str) -> float:
        """경쟁 강도 계산"""
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT supplier_id) as supplier_count,
                    COUNT(DISTINCT id) as product_count,
                    STDDEV(price) / AVG(price) as price_variance
                FROM supplier_products
                WHERE category = %s
                AND status = 'active'
            """, (category,))
            
            result = cursor.fetchone()
            
            if result and result[0]:
                suppliers = result[0]
                products = result[1]
                variance = result[2] if result[2] else 0
                
                # 경쟁 지수 계산 (0-100)
                supplier_score = min(suppliers / 10 * 30, 30)  # 공급자 수
                product_score = min(products / 100 * 40, 40)  # 상품 수
                variance_score = min(variance * 100 * 30, 30)  # 가격 분산
                
                return supplier_score + product_score + variance_score
            
            return 0
    
    def _calculate_opportunity_score(self, growth: float, competition: float, 
                                   product_count: float) -> float:
        """기회 점수 계산"""
        
        # 성장률 점수 (40%)
        growth_score = min(max(growth, 0), 50) / 50 * 40
        
        # 경쟁 점수 (30%) - 낮을수록 좋음
        competition_score = (100 - competition) / 100 * 30
        
        # 시장 크기 점수 (30%)
        size_score = min(product_count / 100, 1) * 30
        
        return growth_score + competition_score + size_score
    
    def _get_seasonal_factor(self, category: str, month: int) -> float:
        """계절 요인 조회"""
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT seasonality_factor
                FROM market_trends
                WHERE category = %s
                AND EXTRACT(MONTH FROM trend_date) = %s
                ORDER BY trend_date DESC
                LIMIT 1
            """, (category, month))
            
            result = cursor.fetchone()
            return float(result[0]) if result else 1.0
    
    def _generate_demand_recommendation(self, forecast: str, trend: float, 
                                      seasonal: float) -> str:
        """수요 예측 기반 추천"""
        
        if forecast == "상승":
            if seasonal > 1.2:
                return "계절적 수요와 트렌드 상승이 겹침. 적극적 재고 확보 필요"
            else:
                return "수요 상승 예상. 재고 수준 점진적 증가 권장"
        elif forecast == "하락":
            if seasonal < 0.8:
                return "계절적 비수기와 하락 트렌드. 재고 최소화 필요"
            else:
                return "수요 하락 예상. 프로모션 검토 필요"
        else:
            return "안정적 수요 예상. 현 수준 유지"
    
    def _save_trend_analysis(self, analysis: Dict):
        """트렌드 분석 결과 저장"""
        
        with self.conn.cursor() as cursor:
            # 카테고리 트렌드 저장
            for trend in analysis['category_trends']:
                cursor.execute("""
                    INSERT INTO market_trends 
                    (trend_date, category, trend_type, trend_score, growth_rate,
                     competitive_index, opportunity_score, key_insights)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trend_date, category) 
                    DO UPDATE SET 
                        trend_type = EXCLUDED.trend_type,
                        trend_score = EXCLUDED.trend_score,
                        growth_rate = EXCLUDED.growth_rate
                """, (
                    datetime.now().date(),
                    trend['category'],
                    trend['trend_type'],
                    trend['trend_score'],
                    trend['avg_growth_rate'],
                    trend['competitive_index'],
                    trend['opportunity_score'],
                    Json({'volatility': trend.get('volatility', 0)})
                ))
            
            self.conn.commit()
    
    def _save_product_trend(self, product_id: int, trend_data: Dict):
        """상품 트렌드 저장"""
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO product_trends 
                (product_id, trend_type, lifecycle_stage, recommendation)
                VALUES (%s, %s, %s, %s)
            """, (
                product_id,
                trend_data.get('trend_type', 'stable'),
                trend_data.get('lifecycle_stage', 'maturity'),
                trend_data.get('recommendation', '')
            ))
            self.conn.commit()
    
    def _generate_market_insights(self) -> List[str]:
        """시장 인사이트 생성"""
        
        insights = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 가장 빠르게 성장하는 카테고리
            cursor.execute("""
                SELECT category, trend_score
                FROM market_trends
                WHERE trend_date = CURRENT_DATE
                AND trend_type = 'rising_star'
                ORDER BY trend_score DESC
                LIMIT 3
            """)
            
            rising = cursor.fetchall()
            if rising:
                categories = ', '.join([r['category'] for r in rising])
                insights.append(f"🚀 급성장 카테고리: {categories}")
            
            # 계절적 기회
            current_month = datetime.now().month
            next_month = (current_month % 12) + 1
            
            cursor.execute("""
                SELECT category
                FROM market_trends
                WHERE EXTRACT(MONTH FROM trend_date) = %s
                AND key_insights->>'seasonality_index' > '1.3'
                LIMIT 3
            """, (next_month,))
            
            seasonal = cursor.fetchall()
            if seasonal:
                categories = ', '.join([s['category'] for s in seasonal])
                insights.append(f"📅 다음 달 시즌 상품: {categories}")
            
            # 공급 부족 알림
            cursor.execute("""
                SELECT COUNT(DISTINCT category) as gap_count
                FROM market_trends
                WHERE trend_date = CURRENT_DATE
                AND opportunity_score > 80
            """)
            
            gaps = cursor.fetchone()
            if gaps and gaps['gap_count'] > 0:
                insights.append(f"💡 {gaps['gap_count']}개 카테고리에서 공급 부족 기회 발견")
        
        return insights


def main():
    """테스트 실행"""
    analyzer = MarketTrendAnalyzer()
    
    # 전체 시장 트렌드 분석
    print("📊 시장 트렌드 분석 시작...")
    trends = analyzer.analyze_market_trends()
    
    print("\n🔥 급성장 카테고리:")
    for trend in trends['category_trends'][:5]:
        if trend['trend_type'] == 'rising_star':
            print(f"  {trend['category']}: 성장률 {trend['avg_growth_rate']:.1f}%")
    
    print("\n🎯 신규 기회:")
    for opp in trends['emerging_opportunities'][:5]:
        print(f"  [{opp['type']}] {opp['opportunity']}")
        print(f"    → {opp['recommendation']}")
    
    print("\n📈 시장 인사이트:")
    for insight in trends['market_insights']:
        print(f"  {insight}")
    
    # 특정 카테고리 수요 예측
    print("\n🔮 수요 예측 (가전/디지털/컴퓨터):")
    prediction = analyzer.predict_demand_trend('가전/디지털/컴퓨터')
    if 'error' not in prediction:
        print(f"  현재 수요: {prediction['current_demand']:.1f}")
        print(f"  예측 수요: {prediction['predicted_demand']:.1f}")
        print(f"  트렌드: {prediction['trend']} (신뢰도: {prediction['confidence']}%)")
        print(f"  추천: {prediction['recommendation']}")


if __name__ == "__main__":
    main()