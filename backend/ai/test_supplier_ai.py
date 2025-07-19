#!/usr/bin/env python3
"""
공급사 상품 AI 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supplier_product_ai import SupplierProductAI
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_models():
    """AI 모델 테스트"""
    print("🤖 공급사 상품 AI 테스트 시작")
    print("=" * 60)
    
    ai = SupplierProductAI()
    
    # 1. 데이터 확인
    print("\n1️⃣ 학습 데이터 확인")
    df = ai.prepare_training_data()
    
    if df.empty:
        print("❌ 학습 데이터가 없습니다.")
        return False
    
    print(f"✅ {len(df)}개 상품 데이터 로드")
    print(f"   카테고리: {df['category'].nunique()}개")
    print(f"   브랜드: {df['brand'].nunique()}개")
    print(f"   평균 가격: {df['price'].mean():,.0f}원")
    print(f"   평균 마진율: {df['margin'].mean():.1%}")
    
    # 2. 모델 학습
    print("\n2️⃣ AI 모델 학습")
    
    # 가격 예측 모델
    print("\n📈 가격 예측 모델 학습 중...")
    price_success = ai.train_price_prediction_model(df)
    
    # 수요 분석 모델
    print("\n📊 수요 분석 모델 학습 중...")
    demand_success = ai.train_demand_analysis_model(df)
    
    if not (price_success and demand_success):
        print("❌ 모델 학습 실패")
        return False
    
    # 3. 개별 상품 예측 테스트
    print("\n3️⃣ 개별 상품 예측 테스트")
    
    # 테스트 상품 데이터
    test_product = {
        'supplier_product_id': 'TEST_001',
        'product_name': '테스트 상품',
        'category': '가전/디지털/컴퓨터',
        'brand': '삼성',
        'cost_price': 50000,
        'price': 75000,
        'weight': 2.5,
        'stock_quantity': 50,
        'supplier_name': '오너클랜',
        'category_avg_price': 80000,
        'brand_avg_price': 90000,
        'supplier_avg_margin': 0.35
    }
    
    print(f"\n🛍️ 테스트 상품: {test_product['product_name']}")
    print(f"   현재가: {test_product['price']:,}원")
    print(f"   원가: {test_product['cost_price']:,}원")
    
    # 가격 예측
    price_result = ai.predict_price(test_product)
    print(f"\n💰 가격 분석:")
    print(f"   예측 가격: {price_result['predicted_price']:,}원")
    print(f"   권장 마진율: {price_result['suggested_margin']:.1f}%")
    print(f"   가격 경쟁력: {price_result['price_competitiveness']:.2f}")
    print(f"   가격 조정 제안: {price_result['price_adjustment']:+.1f}%")
    
    # 수요 분석
    demand_result = ai.analyze_demand(test_product)
    print(f"\n📊 수요 분석:")
    print(f"   수요 점수: {demand_result['demand_score']:.1f}")
    print(f"   수요 등급: {demand_result['demand_grade']} ({demand_result['demand_level']})")
    print(f"   권장 재고: {demand_result['recommended_stock']}개")
    print(f"   재주문점: {demand_result['reorder_point']}개")
    
    # 4. 배치 분석 테스트
    print("\n4️⃣ 배치 분석 테스트")
    results = ai.batch_analyze_products('오너클랜')
    
    if results:
        print(f"\n✅ {len(results)}개 상품 분석 완료")
        
        # 상위 5개 수요 상품
        sorted_results = sorted(results, 
                              key=lambda x: float(x.get('demand_score', 0)), 
                              reverse=True)
        
        print("\n🔥 수요 TOP 5 상품:")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"{i}. {result['product_name'][:30]}...")
            print(f"   수요점수: {result['demand_score']}, 등급: {result['demand_grade']}")
            print(f"   현재가: {result['current_price']:,}원 → 예측가: {result['predicted_price']:,}원")
        
        # 가격 조정 필요 상품
        price_adjust_needed = [r for r in results 
                             if abs(float(r.get('price_adjustment', 0))) > 10]
        
        if price_adjust_needed:
            print(f"\n⚡ 가격 조정 필요 상품: {len(price_adjust_needed)}개")
            for result in price_adjust_needed[:3]:
                adj = float(result['price_adjustment'])
                print(f"   - {result['product_name'][:30]}... ({adj:+.1f}%)")
    
    # 5. 카테고리별 인사이트
    print("\n5️⃣ 카테고리별 AI 인사이트")
    
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    conn = psycopg2.connect(
        host='localhost',
        port=5434,
        database='yoonni',
        user='postgres',
        password='postgres'
    )
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT * FROM category_ai_insights 
            ORDER BY avg_demand_score DESC 
            LIMIT 5
        """)
        
        insights = cursor.fetchall()
        
        if insights:
            print("\n📈 수요 높은 카테고리:")
            for insight in insights:
                print(f"   - {insight['category']}")
                print(f"     평균 수요점수: {insight['avg_demand_score']:.1f}")
                print(f"     고수요 상품: {insight['high_demand_count']}개")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ AI 모델 테스트 완료!")
    
    return True

if __name__ == "__main__":
    test_ai_models()