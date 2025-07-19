#!/usr/bin/env python3
"""
비즈니스 인텔리전스 시스템 통합 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bi.profitability_analyzer import ProfitabilityAnalyzer
from bi.competitor_monitor import CompetitorMonitor
from bi.market_trend_analyzer import MarketTrendAnalyzer
import asyncio
import time
from datetime import datetime

def separator(title):
    """구분선 출력"""
    print(f"\n{'='*80}")
    print(f"🎯 {title}")
    print('='*80)

async def test_profitability_analysis():
    """수익성 분석 테스트"""
    separator("수익성 분석 테스트")
    
    analyzer = ProfitabilityAnalyzer()
    
    # 1. 전체 리포트
    print("\n📊 종합 수익성 리포트 생성...")
    report = analyzer.generate_profitability_report()
    
    print(f"\n✅ 리포트 생성 완료:")
    print(f"   - 분석 시간: {report['timestamp']}")
    print(f"   - 카테고리 수: {len(report['category_analysis'])}")
    print(f"   - 공급사 수: {len(report['supplier_analysis'])}")
    print(f"   - 최적화 기회: {len(report['optimization_opportunities'])}개")
    print(f"   - 리스크: {len(report['risk_analysis'])}개")
    
    # 2. 상위 수익 카테고리
    print("\n💰 수익성 상위 카테고리:")
    for cat in report['category_analysis'][:3]:
        print(f"   {cat['category']}:")
        print(f"     - 순마진: {cat.get('net_margin', 0):.1f}%")
        print(f"     - ROI: {cat.get('roi', 0):.1f}%")
        print(f"     - 수익성 점수: {cat.get('profitability_score', 0):.1f}점")
    
    # 3. 최적 가격 분석
    print("\n💎 최적 가격 분석 (예시):")
    pricing = analyzer.find_optimal_pricing(
        product_id=1,
        supplier_price=15000,
        market_price_range=(20000, 35000),
        demand_elasticity=-1.3
    )
    
    print(f"   원가: 15,000원")
    print(f"   최적 판매가: {pricing['optimal_price']:,.0f}원")
    print(f"   예상 수익: {pricing['expected_profit']:,.0f}원")
    print(f"   추천: {pricing['recommendation']}")
    
    # 4. 최적화 기회
    if report['optimization_opportunities']:
        print("\n🎯 수익 최적화 기회:")
        for opp in report['optimization_opportunities'][:3]:
            print(f"   [{opp['type']}] 상품 #{opp['product_id']} - {opp['product_name']}")
            print(f"     → {opp['recommendation']}")
            print(f"     → {opp.get('potential_improvement', '개선 가능')}")

async def test_competitor_monitoring():
    """경쟁사 모니터링 테스트"""
    separator("경쟁사 모니터링 테스트")
    
    monitor = CompetitorMonitor()
    
    # 1. 경쟁사 가격 수집 시뮬레이션
    print("\n🔍 경쟁사 가격 수집 시작...")
    
    # 테스트용 상품 데이터
    test_products = [
        {'id': 1, 'name': '무선 이어폰', 'price': 50000, 'category': '가전/디지털'},
        {'id': 2, 'name': '스마트워치', 'price': 200000, 'category': '가전/디지털'},
        {'id': 3, 'name': '블루투스 스피커', 'price': 80000, 'category': '가전/디지털'}
    ]
    
    total_prices = 0
    for product in test_products:
        prices = await monitor.collect_competitor_prices(product)
        monitor.save_competitor_prices(prices)
        total_prices += len(prices)
    
    print(f"✅ 수집 완료: {len(test_products)}개 상품, {total_prices}개 가격 정보")
    
    # 2. 가격 포지션 분석
    print("\n📊 가격 포지션 분석:")
    for product in test_products[:2]:
        position = monitor.analyze_price_position(product['id'], product['price'])
        if position:
            print(f"\n   {product['name']}:")
            print(f"     - 우리 가격: {position.our_price:,.0f}원")
            print(f"     - 시장 평균: {position.market_average:,.0f}원")
            print(f"     - 포지션: {position.our_position}")
            print(f"     - 가격 차이: {position.price_gap:+.1f}%")
            print(f"     - 추천: {position.recommendation}")
    
    # 3. 가격 알림
    print("\n🚨 가격 알림 확인:")
    alerts = monitor.detect_price_alerts()
    print(f"   총 {len(alerts)}개 알림 생성")
    
    for alert in alerts[:3]:
        print(f"\n   [{alert['alert_type']}] {alert['product_name']}")
        print(f"     우리: {alert['our_price']:,.0f}원 vs {alert['competitor_name']}: {alert['competitor_price']:,.0f}원")
        print(f"     → {alert['recommendation']}")
    
    # 4. 시장 트렌드
    print("\n📈 시장 트렌드 분석:")
    market_trends = monitor.analyze_market_trends()
    
    if market_trends['market_trends']:
        for trend in market_trends['market_trends'][:3]:
            print(f"\n   {trend['category']}:")
            print(f"     - 주간 변화: {trend['weekly_change']:+.1f}%")
            print(f"     - 월간 변화: {trend['monthly_change']:+.1f}%")
            print(f"     - 트렌드: {trend['trend']}")
            print(f"     - 변동성: {trend['volatility']:.1f}%")

async def test_market_trends():
    """시장 트렌드 분석 테스트"""
    separator("시장 트렌드 분석 테스트")
    
    analyzer = MarketTrendAnalyzer()
    
    # 1. 전체 시장 분석
    print("\n📊 전체 시장 트렌드 분석...")
    trends = analyzer.analyze_market_trends()
    
    print(f"\n✅ 분석 완료:")
    print(f"   - 카테고리 트렌드: {len(trends['category_trends'])}개")
    print(f"   - 라이프사이클 분석: {len(trends['product_lifecycle'])}개 상품")
    print(f"   - 계절성 패턴: {len(trends['seasonal_patterns'])}개")
    print(f"   - 신규 기회: {len(trends['emerging_opportunities'])}개")
    
    # 2. 급성장 카테고리
    print("\n🚀 급성장 카테고리:")
    rising_categories = [t for t in trends['category_trends'] if t['trend_type'] == 'rising_star']
    for cat in rising_categories[:3]:
        print(f"   {cat['category']}:")
        print(f"     - 성장률: {cat['avg_growth_rate']:.1f}%")
        print(f"     - 트렌드 점수: {cat['trend_score']:.1f}")
        print(f"     - 기회 점수: {cat['opportunity_score']:.1f}")
    
    # 3. 계절성 분석
    print("\n🌸 계절성 패턴 (상위 3개):")
    seasonal = sorted(trends['seasonal_patterns'], 
                     key=lambda x: x['seasonality_strength'], reverse=True)[:3]
    
    for pattern in seasonal:
        print(f"\n   {pattern['category']}:")
        print(f"     - 계절성 강도: {pattern['seasonality_strength']:.1f}")
        print(f"     - 성수기: {pattern['peak_months']}")
        print(f"     - 비수기: {pattern['low_months']}")
        print(f"     - 추천: {pattern['recommendation']}")
    
    # 4. 신규 기회
    print("\n💡 신규 시장 기회:")
    for opp in trends['emerging_opportunities'][:5]:
        print(f"\n   [{opp['type']}] {opp['opportunity']}")
        print(f"     → {opp['recommendation']}")
        
        if opp['type'] == 'emerging_keyword':
            print(f"     키워드: '{opp['keyword']}' (성장률: {opp['growth_rate']:.1f}/일)")
        elif opp['type'] == 'supply_gap':
            print(f"     현재 공급: {opp['current_supply']}개 (수요점수: {opp['demand_score']:.1f})")
        elif opp['type'] == 'price_arbitrage':
            print(f"     가격차: {opp['price_gap']:.1f}% (우리: {opp['our_price']:,.0f}원)")
    
    # 5. 수요 예측
    print("\n🔮 수요 예측 테스트:")
    test_categories = ['가전/디지털/컴퓨터', '패션의류/잡화', '생활용품']
    
    for category in test_categories:
        prediction = analyzer.predict_demand_trend(category, days_ahead=30)
        
        if 'error' not in prediction:
            print(f"\n   {category}:")
            print(f"     - 현재 수요: {prediction['current_demand']:.1f}")
            print(f"     - 예측 수요: {prediction['predicted_demand']:.1f}")
            print(f"     - 트렌드: {prediction['trend']} ({prediction['trend_strength']:.1f}%)")
            print(f"     - 신뢰도: {prediction['confidence']}%")
            print(f"     - 추천: {prediction['recommendation']}")

async def test_integrated_bi():
    """통합 BI 시스템 테스트"""
    separator("통합 비즈니스 인텔리전스 시스템")
    
    print("\n🎯 통합 BI 분석 시작...")
    
    # 각 모듈 초기화
    profit_analyzer = ProfitabilityAnalyzer()
    competitor_monitor = CompetitorMonitor()
    trend_analyzer = MarketTrendAnalyzer()
    
    # 통합 인사이트 생성
    print("\n📊 통합 비즈니스 인사이트:")
    
    # 1. 수익성 X 트렌드 분석
    categories = profit_analyzer.analyze_category_profitability()[:5]
    trends = trend_analyzer._analyze_category_trends()
    
    print("\n1️⃣ 수익성 + 성장성 매트릭스:")
    for cat in categories:
        trend = next((t for t in trends if t['category'] == cat['category']), None)
        if trend:
            print(f"   {cat['category']}:")
            print(f"     수익성: {cat.get('profitability_score', 0):.1f}점 | 성장률: {trend['avg_growth_rate']:.1f}%")
            
            if cat.get('profitability_score', 0) > 70 and trend['avg_growth_rate'] > 10:
                print(f"     → 🌟 스타 카테고리: 높은 수익성 + 높은 성장")
            elif cat.get('profitability_score', 0) > 70 and trend['avg_growth_rate'] < 0:
                print(f"     → 💰 캐시카우: 높은 수익성 + 낮은 성장")
            elif cat.get('profitability_score', 0) < 50 and trend['avg_growth_rate'] > 10:
                print(f"     → ❓ 물음표: 낮은 수익성 + 높은 성장")
            else:
                print(f"     → 🐕 개: 낮은 수익성 + 낮은 성장")
    
    # 2. 종합 추천
    print("\n2️⃣ 종합 전략 추천:")
    print("   📌 즉시 실행:")
    print("      - 경쟁사 대비 5% 이상 비싼 상품 가격 조정")
    print("      - 수익성 70점 이상 카테고리 재고 확대")
    print("      - 급성장 키워드 관련 신상품 소싱")
    
    print("\n   📌 단기 계획 (1개월):")
    print("      - 계절성 상품 재고 조정")
    print("      - 저마진 고수요 상품 가격 최적화")
    print("      - 공급 부족 카테고리 진입")
    
    print("\n   📌 장기 전략 (3개월):")
    print("      - 하락세 카테고리 철수 검토")
    print("      - 신규 시장 기회 본격 진입")
    print("      - 프리미엄 라인 개발")

async def main():
    """메인 테스트 실행"""
    print("🚀 Yooni 비즈니스 인텔리전스 시스템 테스트")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 각 모듈 테스트
    await test_profitability_analysis()
    await test_competitor_monitoring()
    await test_market_trends()
    
    # 통합 테스트
    await test_integrated_bi()
    
    print("\n" + "="*80)
    print("✅ 모든 BI 테스트 완료!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())