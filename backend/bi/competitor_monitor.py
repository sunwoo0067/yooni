#!/usr/bin/env python3
"""
경쟁사 가격 모니터링 시스템
- 실시간 가격 추적
- 가격 변동 알림
- 경쟁력 분석
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging
import json
from dataclasses import dataclass
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceComparison:
    """가격 비교 데이터"""
    product_id: int
    our_price: float
    competitor_prices: Dict[str, float]
    market_average: float
    our_position: str  # 'lowest', 'below_average', 'average', 'above_average', 'highest'
    price_gap: float  # 시장 평균 대비 차이 (%)
    recommendation: str

class CompetitorMonitor:
    """경쟁사 모니터링 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 경쟁사 마켓플레이스 설정
        self.competitors = {
            '쿠팡': {'platform': 'coupang', 'weight': 1.2},
            '11번가': {'platform': '11st', 'weight': 1.0},
            'G마켓': {'platform': 'gmarket', 'weight': 0.9},
            '옥션': {'platform': 'auction', 'weight': 0.8},
            '네이버': {'platform': 'naver', 'weight': 1.1}
        }
        
        self._create_tables()
    
    def _create_tables(self):
        """경쟁사 모니터링 테이블 생성"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitor_prices (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES supplier_products(id),
                    competitor_name VARCHAR(100),
                    competitor_price DECIMAL(12, 2),
                    competitor_url TEXT,
                    shipping_fee DECIMAL(10, 2),
                    availability VARCHAR(50),
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, competitor_name, collected_at)
                );
                
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES supplier_products(id),
                    alert_type VARCHAR(50), -- 'undercut', 'price_war', 'opportunity'
                    our_price DECIMAL(12, 2),
                    competitor_price DECIMAL(12, 2),
                    competitor_name VARCHAR(100),
                    price_difference DECIMAL(10, 2),
                    recommendation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS market_analysis (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(200),
                    analysis_date DATE,
                    average_price DECIMAL(12, 2),
                    price_range JSONB,
                    competitor_distribution JSONB,
                    trend VARCHAR(20), -- 'increasing', 'stable', 'decreasing'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, analysis_date)
                );
                
                CREATE INDEX IF NOT EXISTS idx_competitor_prices_product ON competitor_prices(product_id, collected_at DESC);
                CREATE INDEX IF NOT EXISTS idx_price_alerts_created ON price_alerts(created_at DESC) WHERE acknowledged = FALSE;
                CREATE INDEX IF NOT EXISTS idx_market_analysis_category ON market_analysis(category, analysis_date DESC);
            """)
            self.conn.commit()
    
    async def collect_competitor_prices(self, product: Dict) -> List[Dict]:
        """경쟁사 가격 수집 (시뮬레이션)"""
        
        # 실제로는 각 마켓플레이스 API나 크롤링을 통해 수집
        # 여기서는 시뮬레이션으로 구현
        
        competitor_prices = []
        base_price = float(product['price'])
        
        for comp_name, comp_info in self.competitors.items():
            # 가격 변동 시뮬레이션 (±20% 범위)
            variation = 0.8 + (0.4 * hash(f"{product['id']}{comp_name}") % 100 / 100)
            comp_price = base_price * variation
            
            # 배송비 (무료배송 또는 2500원)
            shipping = 0 if comp_price > 20000 else 2500
            
            competitor_prices.append({
                'product_id': product['id'],
                'competitor_name': comp_name,
                'competitor_price': comp_price,
                'shipping_fee': shipping,
                'availability': 'in_stock' if hash(f"{product['id']}{comp_name}") % 10 > 2 else 'out_of_stock',
                'competitor_url': f"https://{comp_info['platform']}.com/product/{product['id']}"
            })
        
        return competitor_prices
    
    def save_competitor_prices(self, prices: List[Dict]):
        """경쟁사 가격 저장"""
        
        with self.conn.cursor() as cursor:
            for price in prices:
                cursor.execute("""
                    INSERT INTO competitor_prices 
                    (product_id, competitor_name, competitor_price, competitor_url, 
                     shipping_fee, availability)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_id, competitor_name, collected_at) DO NOTHING
                """, (
                    price['product_id'],
                    price['competitor_name'],
                    price['competitor_price'],
                    price['competitor_url'],
                    price['shipping_fee'],
                    price['availability']
                ))
            
            self.conn.commit()
    
    def analyze_price_position(self, product_id: int, our_price: float) -> PriceComparison:
        """가격 포지션 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 최근 경쟁사 가격 조회
            cursor.execute("""
                SELECT DISTINCT ON (competitor_name)
                    competitor_name,
                    competitor_price,
                    shipping_fee,
                    availability
                FROM competitor_prices
                WHERE product_id = %s
                AND collected_at > NOW() - INTERVAL '24 hours'
                ORDER BY competitor_name, collected_at DESC
            """, (product_id,))
            
            competitor_data = cursor.fetchall()
        
        if not competitor_data:
            return None
        
        # 경쟁사 가격 분석
        competitor_prices = {}
        available_prices = []
        
        for comp in competitor_data:
            total_price = float(comp['competitor_price']) + float(comp['shipping_fee'])
            competitor_prices[comp['competitor_name']] = total_price
            
            if comp['availability'] == 'in_stock':
                available_prices.append(total_price)
        
        if not available_prices:
            available_prices = list(competitor_prices.values())
        
        # 시장 평균 계산
        market_average = statistics.mean(available_prices)
        
        # 우리 가격 포지션 결정
        price_gap = ((our_price - market_average) / market_average) * 100
        
        if our_price == min(available_prices + [our_price]):
            position = 'lowest'
            recommendation = "최저가 유지 중. 마진 확인 필요"
        elif our_price < market_average - market_average * 0.05:
            position = 'below_average'
            recommendation = "경쟁력 있는 가격. 현 수준 유지 권장"
        elif abs(price_gap) <= 5:
            position = 'average'
            recommendation = "시장 평균 수준. 차별화 전략 검토"
        elif our_price < max(available_prices):
            position = 'above_average'
            recommendation = "가격 인하 검토 또는 프리미엄 전략 강화"
        else:
            position = 'highest'
            recommendation = "긴급 가격 조정 필요. 경쟁력 상실 위험"
        
        return PriceComparison(
            product_id=product_id,
            our_price=our_price,
            competitor_prices=competitor_prices,
            market_average=market_average,
            our_position=position,
            price_gap=price_gap,
            recommendation=recommendation
        )
    
    def detect_price_alerts(self) -> List[Dict]:
        """가격 알림 감지"""
        
        alerts = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 우리보다 싼 경쟁사 찾기
            cursor.execute("""
                WITH our_products AS (
                    SELECT id, product_name as name, price, category
                    FROM supplier_products
                    WHERE status = 'active'
                ),
                recent_competitor_prices AS (
                    SELECT DISTINCT ON (product_id, competitor_name)
                        product_id,
                        competitor_name,
                        competitor_price + shipping_fee as total_price,
                        availability
                    FROM competitor_prices
                    WHERE collected_at > NOW() - INTERVAL '6 hours'
                    ORDER BY product_id, competitor_name, collected_at DESC
                )
                SELECT 
                    op.id,
                    op.name,
                    op.price as our_price,
                    op.category,
                    rcp.competitor_name,
                    rcp.total_price as competitor_price
                FROM our_products op
                JOIN recent_competitor_prices rcp ON op.id = rcp.product_id
                WHERE rcp.total_price < op.price * 0.95  -- 5% 이상 저렴
                AND rcp.availability = 'in_stock'
            """)
            
            undercut_products = cursor.fetchall()
            
            for product in undercut_products:
                price_diff = float(product['our_price']) - float(product['competitor_price'])
                diff_percent = (price_diff / float(product['our_price'])) * 100
                
                alert = {
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'alert_type': 'undercut',
                    'our_price': float(product['our_price']),
                    'competitor_price': float(product['competitor_price']),
                    'competitor_name': product['competitor_name'],
                    'price_difference': price_diff,
                    'recommendation': self._generate_alert_recommendation(diff_percent)
                }
                
                alerts.append(alert)
                self._save_alert(alert)
            
            # 가격 전쟁 감지
            cursor.execute("""
                SELECT 
                    product_id,
                    COUNT(DISTINCT competitor_name) as competitors_count,
                    MIN(competitor_price + shipping_fee) as min_price,
                    MAX(competitor_price + shipping_fee) as max_price,
                    AVG(competitor_price + shipping_fee) as avg_price,
                    STDDEV(competitor_price + shipping_fee) as price_stddev
                FROM competitor_prices
                WHERE collected_at > NOW() - INTERVAL '24 hours'
                GROUP BY product_id
                HAVING STDDEV(competitor_price + shipping_fee) / AVG(competitor_price + shipping_fee) > 0.2
            """)
            
            price_wars = cursor.fetchall()
            
            for war in price_wars:
                if war['price_stddev'] and float(war['price_stddev']) > 0:
                    cursor.execute("""
                        SELECT product_name as name, price FROM supplier_products WHERE id = %s
                    """, (war['product_id'],))
                    
                    product = cursor.fetchone()
                    if product:
                        alerts.append({
                            'product_id': war['product_id'],
                            'product_name': product['name'],
                            'alert_type': 'price_war',
                            'our_price': float(product['price']),
                            'competitor_price': float(war['min_price']),
                            'price_difference': float(war['max_price']) - float(war['min_price']),
                            'recommendation': '가격 전쟁 진행 중. 신중한 대응 필요'
                        })
        
        return alerts
    
    def analyze_market_trends(self) -> Dict:
        """시장 트렌드 분석"""
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 카테고리별 가격 트렌드
            cursor.execute("""
                WITH category_prices AS (
                    SELECT 
                        sp.category,
                        DATE(cp.collected_at) as price_date,
                        AVG(cp.competitor_price) as avg_price,
                        MIN(cp.competitor_price) as min_price,
                        MAX(cp.competitor_price) as max_price,
                        COUNT(DISTINCT cp.competitor_name) as competitor_count
                    FROM supplier_products sp
                    JOIN competitor_prices cp ON sp.id = cp.product_id
                    WHERE cp.collected_at > NOW() - INTERVAL '30 days'
                    GROUP BY sp.category, DATE(cp.collected_at)
                )
                SELECT 
                    category,
                    AVG(avg_price) as current_avg_price,
                    -- 7일 전 평균 가격
                    (SELECT AVG(avg_price) FROM category_prices cp2 
                     WHERE cp2.category = cp.category 
                     AND cp2.price_date = CURRENT_DATE - 7) as week_ago_price,
                    -- 30일 전 평균 가격
                    (SELECT AVG(avg_price) FROM category_prices cp3 
                     WHERE cp3.category = cp.category 
                     AND cp3.price_date = CURRENT_DATE - 30) as month_ago_price,
                    MIN(min_price) as period_min,
                    MAX(max_price) as period_max
                FROM category_prices cp
                GROUP BY category
            """)
            
            trends = cursor.fetchall()
            
            market_analysis = []
            
            for trend in trends:
                current = float(trend['current_avg_price'])
                week_ago = float(trend['week_ago_price']) if trend['week_ago_price'] else current
                month_ago = float(trend['month_ago_price']) if trend['month_ago_price'] else current
                
                # 트렌드 판단
                weekly_change = ((current - week_ago) / week_ago) * 100 if week_ago > 0 else 0
                monthly_change = ((current - month_ago) / month_ago) * 100 if month_ago > 0 else 0
                
                if abs(monthly_change) < 2:
                    trend_type = 'stable'
                elif monthly_change > 5:
                    trend_type = 'increasing'
                else:
                    trend_type = 'decreasing'
                
                market_analysis.append({
                    'category': trend['category'],
                    'current_avg_price': current,
                    'weekly_change': weekly_change,
                    'monthly_change': monthly_change,
                    'price_range': {
                        'min': float(trend['period_min']),
                        'max': float(trend['period_max'])
                    },
                    'trend': trend_type,
                    'volatility': (float(trend['period_max']) - float(trend['period_min'])) / current * 100
                })
                
                # 분석 결과 저장
                self._save_market_analysis(trend['category'], {
                    'average_price': current,
                    'price_range': {'min': float(trend['period_min']), 'max': float(trend['period_max'])},
                    'trend': trend_type
                })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'market_trends': market_analysis,
                'summary': self._generate_market_summary(market_analysis)
            }
    
    def get_pricing_recommendations(self, limit: int = 20) -> List[Dict]:
        """가격 조정 추천"""
        
        recommendations = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                WITH product_positions AS (
                    SELECT 
                        sp.id,
                        sp.product_name as name,
                        sp.category,
                        sp.price as our_price,
                        AVG(cp.competitor_price + cp.shipping_fee) as market_avg,
                        MIN(cp.competitor_price + cp.shipping_fee) as market_min,
                        COUNT(DISTINCT cp.competitor_name) as competitor_count,
                        pai.demand_score
                    FROM supplier_products sp
                    JOIN competitor_prices cp ON sp.id = cp.product_id
                    LEFT JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.status = 'active'
                    AND cp.collected_at > NOW() - INTERVAL '24 hours'
                    GROUP BY sp.id, sp.product_name, sp.category, sp.price, pai.demand_score
                )
                SELECT 
                    *,
                    (our_price - market_avg) / market_avg * 100 as price_gap_percent
                FROM product_positions
                WHERE ABS((our_price - market_avg) / market_avg) > 0.1  -- 10% 이상 차이
                ORDER BY ABS(our_price - market_avg) DESC
                LIMIT %s
            """, (limit,))
            
            products = cursor.fetchall()
            
            for product in products:
                price_gap = float(product['price_gap_percent'])
                demand_score = float(product['demand_score']) if product['demand_score'] else 50
                
                if price_gap > 10:
                    # 우리가 비쌈
                    if demand_score > 70:
                        action = 'maintain'
                        reason = '높은 수요로 프리미엄 가격 유지 가능'
                    else:
                        action = 'decrease'
                        suggested_price = float(product['market_avg']) * 1.05
                        reason = '경쟁력 확보를 위한 가격 인하 필요'
                else:
                    # 우리가 저렴
                    if demand_score > 60:
                        action = 'increase'
                        suggested_price = float(product['market_avg']) * 0.98
                        reason = '수요가 충분하여 가격 인상 가능'
                    else:
                        action = 'maintain'
                        reason = '낮은 가격으로 수요 창출 중'
                
                recommendation = {
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'category': product['category'],
                    'current_price': float(product['our_price']),
                    'market_average': float(product['market_avg']),
                    'market_min': float(product['market_min']),
                    'price_gap': price_gap,
                    'demand_score': demand_score,
                    'action': action,
                    'reason': reason
                }
                
                if action in ['increase', 'decrease']:
                    recommendation['suggested_price'] = suggested_price
                    recommendation['expected_impact'] = self._calculate_price_impact(
                        product['id'], suggested_price
                    )
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_alert_recommendation(self, price_diff_percent: float) -> str:
        """가격 알림에 대한 추천 생성"""
        
        if price_diff_percent > 20:
            return "심각한 가격 차이. 즉시 가격 조정 또는 판매 중단 검토"
        elif price_diff_percent > 10:
            return "상당한 가격 차이. 24시간 내 대응 방안 수립 필요"
        elif price_diff_percent > 5:
            return "주의 필요. 시장 동향 모니터링 강화"
        else:
            return "경미한 차이. 현 상태 유지하며 관찰"
    
    def _save_alert(self, alert: Dict):
        """가격 알림 저장"""
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO price_alerts 
                (product_id, alert_type, our_price, competitor_price, 
                 competitor_name, price_difference, recommendation)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                alert['product_id'],
                alert['alert_type'],
                alert['our_price'],
                alert['competitor_price'],
                alert.get('competitor_name', ''),
                alert['price_difference'],
                alert['recommendation']
            ))
            self.conn.commit()
    
    def _save_market_analysis(self, category: str, analysis: Dict):
        """시장 분석 결과 저장"""
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO market_analysis 
                (category, analysis_date, average_price, price_range, trend)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (category, analysis_date) 
                DO UPDATE SET 
                    average_price = EXCLUDED.average_price,
                    price_range = EXCLUDED.price_range,
                    trend = EXCLUDED.trend
            """, (
                category,
                datetime.now().date(),
                analysis['average_price'],
                Json(analysis['price_range']),
                analysis['trend']
            ))
            self.conn.commit()
    
    def _generate_market_summary(self, trends: List[Dict]) -> Dict:
        """시장 요약 생성"""
        
        increasing = len([t for t in trends if t['trend'] == 'increasing'])
        decreasing = len([t for t in trends if t['trend'] == 'decreasing'])
        stable = len([t for t in trends if t['trend'] == 'stable'])
        
        avg_volatility = statistics.mean([t['volatility'] for t in trends]) if trends else 0
        
        return {
            'total_categories': len(trends),
            'trend_distribution': {
                'increasing': increasing,
                'stable': stable,
                'decreasing': decreasing
            },
            'average_volatility': avg_volatility,
            'market_condition': 'volatile' if avg_volatility > 20 else 'stable'
        }
    
    def _calculate_price_impact(self, product_id: int, new_price: float) -> Dict:
        """가격 변경 영향 계산"""
        
        # 간단한 영향 계산 (실제로는 더 복잡한 모델 필요)
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT price, product_data->>'cost' as cost
                FROM supplier_products
                WHERE id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            
            if product and product['cost']:
                old_margin = (float(product['price']) - float(product['cost'])) / float(product['price']) * 100
                new_margin = (new_price - float(product['cost'])) / new_price * 100
                
                return {
                    'margin_change': new_margin - old_margin,
                    'revenue_impact': ((new_price - float(product['price'])) / float(product['price'])) * 100
                }
        
        return {'margin_change': 0, 'revenue_impact': 0}


async def monitor_competitors():
    """경쟁사 모니터링 실행"""
    monitor = CompetitorMonitor()
    
    # 활성 상품 조회
    with monitor.conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, name, price, category
            FROM supplier_products
            WHERE status = 'active'
            LIMIT 100
        """)
        products = cursor.fetchall()
    
    # 경쟁사 가격 수집
    for product in products:
        prices = await monitor.collect_competitor_prices(product)
        monitor.save_competitor_prices(prices)
    
    # 가격 알림 확인
    alerts = monitor.detect_price_alerts()
    
    # 시장 트렌드 분석
    trends = monitor.analyze_market_trends()
    
    return {
        'products_monitored': len(products),
        'alerts_generated': len(alerts),
        'market_trends': trends
    }


def main():
    """테스트 실행"""
    monitor = CompetitorMonitor()
    
    # 비동기 모니터링 실행
    result = asyncio.run(monitor_competitors())
    print(f"\n📊 모니터링 결과:")
    print(f"  모니터링 상품: {result['products_monitored']}개")
    print(f"  생성된 알림: {result['alerts_generated']}개")
    
    # 가격 추천
    print("\n💡 가격 조정 추천:")
    recommendations = monitor.get_pricing_recommendations(5)
    for rec in recommendations:
        print(f"\n{rec['product_name']}:")
        print(f"  현재가: {rec['current_price']:,.0f}원")
        print(f"  시장평균: {rec['market_average']:,.0f}원")
        print(f"  추천: {rec['action']} - {rec['reason']}")


if __name__ == "__main__":
    main()