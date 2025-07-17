#!/usr/bin/env python3
"""
쿠팡 카테고리 추천 API 사용 예제
머신러닝 기반 상품 카테고리 자동 추천 테스트
"""

import os
import sys
import json
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_recommendation_client import CoupangCategoryRecommendationClient


def test_basic_recommendation():
    """기본 카테고리 추천 테스트"""
    
    try:
        # 클라이언트 초기화
        client = CoupangCategoryRecommendationClient()
        print("✅ 쿠팡 카테고리 추천 클라이언트 초기화 성공")
        
        print("\n" + "="*50 + " 기본 추천 테스트 " + "="*50)
        
        # 테스트 상품들 (명세서 예시 기반)
        test_products = [
            "[유한양행] 유한젠 가루세제 1kg 용기(살균표백제)x10개",
            "[유한양행] 유한젠 액체세제 1.8L 리필 (살균표백제)",
            "[유한양행] 유한락스 파워젤 1L (살균/악취제거)x10개",
            "삼성 갤럭시 S24 투명 실리콘 케이스",
            "나이키 에어맥스 남성 운동화 270 화이트 250mm"
        ]
        
        for i, product_name in enumerate(test_products, 1):
            print(f"\n📦 테스트 {i}: {product_name}")
            
            try:
                # 카테고리 추천 요청
                result = client.get_recommendation_result(product_name)
                
                if result["success"]:
                    print(f"✅ 추천 성공")
                    print(f"   🎯 결과 타입: {result['resultType']}")
                    print(f"   📂 카테고리 ID: {result['categoryId']}")
                    print(f"   📝 카테고리명: {result['categoryName']}")
                    print(f"   📊 신뢰도: {result['confidence']}")
                    if result['comment']:
                        print(f"   💬 코멘트: {result['comment']}")
                else:
                    print(f"❌ 추천 실패: {result['error']}")
                    
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
        
    except Exception as e:
        print(f"❌ 클라이언트 초기화 오류: {e}")


def test_detailed_recommendation():
    """상세 정보 포함 추천 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 상세 정보 추천 테스트 " + "="*50)
        
        # 상세 정보가 포함된 테스트 케이스
        detailed_product = {
            "product_name": "코데즈컴바인 여성 양털 싱글코트 베이지 FREE",
            "product_description": "캐주얼하지만 큐티한 디자인이 돋보이는 싱글코트에요. 약간 박시한 핏이라 여유있고 편하게 스타일링하기 좋은 캐주얼 싱글코트입니다.",
            "brand": "코데즈컴바인",
            "attributes": {
                "제품 소재": "모달:53.8 폴리:43.2 레이온:2.4 면:0.6",
                "색상": "베이지,네이비",
                "제조국": "한국",
                "사이즈": "FREE"
            },
            "seller_sku_code": "CODES_COAT_001"
        }
        
        print(f"📦 상품명: {detailed_product['product_name']}")
        print(f"🏷️ 브랜드: {detailed_product['brand']}")
        print(f"📋 속성: {detailed_product['attributes']}")
        
        # 카테고리 추천 (상세 정보 포함)
        result = client.predict_category(
            product_name=detailed_product["product_name"],
            product_description=detailed_product["product_description"],
            brand=detailed_product["brand"],
            attributes=detailed_product["attributes"],
            seller_sku_code=detailed_product["seller_sku_code"]
        )
        
        print(f"\n✅ 상세 추천 결과:")
        data = result.get('data', {})
        print(f"   🎯 결과 타입: {data.get('autoCategorizationPredictionResultType')}")
        print(f"   📂 카테고리 ID: {data.get('predictedCategoryId')}")
        print(f"   📝 카테고리명: {data.get('predictedCategoryName')}")
        
        if data.get('comment'):
            print(f"   💬 코멘트: {data.get('comment')}")
        
    except Exception as e:
        print(f"❌ 상세 추천 테스트 오류: {e}")


def test_bulk_recommendation():
    """일괄 추천 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 일괄 추천 테스트 " + "="*50)
        
        # 여러 상품 정보
        bulk_products = [
            {
                "productName": "애플 아이폰 15 Pro 실리콘 케이스 블랙",
                "brand": "애플",
                "attributes": {"색상": "블랙", "호환기종": "아이폰 15 Pro"}
            },
            {
                "productName": "나이키 드라이핏 남성 반팔 티셔츠 화이트 L",
                "brand": "나이키",
                "attributes": {"색상": "화이트", "사이즈": "L", "성별": "남성"}
            },
            {
                "productName": "동원 참치캔 135g x 10개",
                "brand": "동원",
                "attributes": {"용량": "135g", "수량": "10개"}
            },
            {
                "productName": "잘못된상품명예시",  # 의도적으로 부실한 상품명
            }
        ]
        
        print(f"📦 총 {len(bulk_products)}개 상품 일괄 처리 시작...")
        
        # 일괄 추천 실행
        results = client.bulk_predict_categories(bulk_products)
        
        print(f"\n✅ 일괄 추천 완료")
        print(f"📊 결과 요약:")
        
        success_count = sum(1 for r in results if r.get('success'))
        fail_count = len(results) - success_count
        
        print(f"   성공: {success_count}개")
        print(f"   실패: {fail_count}개")
        
        print(f"\n📋 상세 결과:")
        for result in results:
            idx = result.get('index', 'Unknown')
            product_name = result.get('productName', 'Unknown')
            
            if result.get('success'):
                print(f"   [{idx+1}] ✅ {product_name[:30]}...")
                print(f"       └ {result.get('categoryName', 'N/A')} (ID: {result.get('categoryId', 'N/A')})")
            else:
                print(f"   [{idx+1}] ❌ {product_name[:30]}...")
                print(f"       └ 오류: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ 일괄 추천 테스트 오류: {e}")


def test_product_name_validation():
    """상품명 검증 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 상품명 검증 테스트 " + "="*50)
        
        # 다양한 품질의 상품명 테스트
        test_names = [
            "나이키 에어맥스 남성 운동화 270 화이트 250mm",  # 좋은 예시
            "라운드티셔츠 gn 95 aden 그린 계열",  # 나쁜 예시 (성별 없음)
            "애견 캐리어 애견 장난감 애견 의류 리드줄",  # 나쁜 예시 (여러 상품)
            "티셔츠",  # 너무 짧음
            "[유한양행] 유한젠 가루/액체 (살균표백제)",  # 모호한 키워드
            "",  # 빈 문자열
            "코데즈컴바인 여성 양털 싱글코트 베이지 FREE 사이즈 겨울용 따뜻한"  # 좋은 예시
        ]
        
        for i, name in enumerate(test_names, 1):
            print(f"\n📝 테스트 {i}: '{name}'")
            
            try:
                validation = client.validate_product_name(name)
                
                status = "✅ 유효" if validation["isValid"] else "❌ 무효"
                print(f"   상태: {status} (점수: {validation['score']}/100)")
                
                if validation["issues"]:
                    print("   🚨 문제점:")
                    for issue in validation["issues"]:
                        print(f"     - {issue}")
                
                if validation["suggestions"]:
                    print("   💡 개선 제안:")
                    for suggestion in validation["suggestions"]:
                        print(f"     - {suggestion}")
                
                if validation["examples"]:
                    print("   📖 예시:")
                    for example in validation["examples"]:
                        print(f"     - {example}")
                        
            except Exception as e:
                print(f"   ❌ 검증 오류: {e}")
        
    except Exception as e:
        print(f"❌ 상품명 검증 테스트 오류: {e}")


def test_integration_workflow():
    """통합 워크플로우 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 통합 워크플로우 테스트 " + "="*50)
        
        # 실제 사용 시나리오: 상품명 검증 → 개선 → 카테고리 추천
        original_name = "티셔츠 빨간색"  # 부실한 상품명
        
        print(f"🎯 원본 상품명: '{original_name}'")
        
        # 1단계: 상품명 검증
        print(f"\n1️⃣ 상품명 검증 중...")
        validation = client.validate_product_name(original_name)
        
        if not validation["isValid"]:
            print(f"❌ 상품명 품질 부족 (점수: {validation['score']}/100)")
            print("💡 개선이 필요한 상품명입니다")
            
            # 개선된 상품명 제안
            improved_name = "나이키 드라이핏 남성 반팔 티셔츠 빨간색 L"
            print(f"🔧 개선된 상품명: '{improved_name}'")
            
            # 개선된 상품명 재검증
            validation2 = client.validate_product_name(improved_name)
            print(f"✅ 개선 후 점수: {validation2['score']}/100")
            
            # 2단계: 개선된 상품명으로 카테고리 추천
            print(f"\n2️⃣ 개선된 상품명으로 카테고리 추천 중...")
            result = client.get_recommendation_result(
                improved_name,
                brand="나이키",
                attributes={"색상": "빨간색", "사이즈": "L", "성별": "남성"}
            )
            
            if result["success"]:
                print(f"✅ 추천 성공!")
                print(f"   📂 카테고리: {result['categoryName']}")
                print(f"   🎯 카테고리 ID: {result['categoryId']}")
                print(f"   📊 신뢰도: {result['confidence']}")
            else:
                print(f"❌ 추천 실패: {result['error']}")
        else:
            print(f"✅ 상품명 품질 양호 (점수: {validation['score']}/100)")
            
            # 바로 카테고리 추천
            result = client.get_recommendation_result(original_name)
            if result["success"]:
                print(f"📂 추천 카테고리: {result['categoryName']}")
        
    except Exception as e:
        print(f"❌ 통합 워크플로우 테스트 오류: {e}")


def test_agreement_check():
    """카테고리 자동 매칭 서비스 동의 확인 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 동의 확인 테스트 " + "="*50)
        
        # 1. 동의 확인 테스트
        print("🔍 카테고리 자동 매칭 서비스 동의 상태 확인 중...")
        
        agreement_result = client.check_auto_category_agreement()
        
        print(f"✅ 동의 확인 완료")
        print(f"   🏢 판매자 ID: {agreement_result.get('vendorId', 'N/A')}")
        print(f"   📊 동의 상태: {agreement_result.get('status', 'UNKNOWN')}")
        print(f"   💬 메시지: {agreement_result.get('message', 'N/A')}")
        
        if agreement_result.get("success"):
            if agreement_result.get("isAgreed"):
                print("   ✅ 카테고리 자동 매칭 서비스 사용 가능")
            else:
                print("   ❌ 카테고리 자동 매칭 서비스 미동의")
                print("   💡 WING 판매관리시스템에서 동의 필요")
        else:
            print(f"   ❌ 동의 확인 실패: {agreement_result.get('error', 'Unknown error')}")
        
        # 2. 간편 확인 테스트
        print(f"\n🔍 간편 사용 가능 여부 확인...")
        can_use = client.can_use_auto_category()
        print(f"   사용 가능: {'✅ 예' if can_use else '❌ 아니오'}")
        
        # 3. 안전한 추천 테스트 (동의 확인 포함)
        print(f"\n🔍 안전한 카테고리 추천 테스트...")
        safe_result = client.predict_category_with_agreement_check(
            "삼성 갤럭시 투명 실리콘 케이스"
        )
        
        print(f"📊 안전한 추천 결과:")
        print(f"   성공: {'✅ 예' if safe_result.get('success') else '❌ 아니오'}")
        print(f"   동의 상태: {safe_result.get('agreementStatus', 'UNKNOWN')}")
        
        if safe_result.get("success"):
            recommendation = safe_result.get("categoryRecommendation", {})
            if recommendation.get("success"):
                print(f"   📂 추천 카테고리: {recommendation.get('categoryName', 'N/A')}")
                print(f"   🎯 카테고리 ID: {recommendation.get('categoryId', 'N/A')}")
            else:
                print(f"   ❌ 추천 실패: {recommendation.get('error', 'N/A')}")
        else:
            print(f"   ❌ 오류: {safe_result.get('error', 'N/A')}")
            
            # 동의 가이드 표시
            if safe_result.get("agreementGuide"):
                guide = safe_result["agreementGuide"]
                print(f"\n💡 {guide['description']}")
                for step in guide["steps"]:
                    print(f"   {step}")
        
    except Exception as e:
        print(f"❌ 동의 확인 테스트 오류: {e}")


def test_real_world_scenario():
    """실제 사용 시나리오 통합 테스트"""
    
    try:
        client = CoupangCategoryRecommendationClient()
        
        print("\n" + "="*50 + " 실제 시나리오 테스트 " + "="*50)
        
        # 실제 상품 예시
        products_to_test = [
            "나이키 에어맥스 남성 운동화 270 화이트 250mm",
            "[유한양행] 유한젠 가루세제 1kg 용기(살균표백제)x10개",
            "애플 아이폰 15 Pro 투명 실리콘 케이스"
        ]
        
        print(f"🎯 {len(products_to_test)}개 상품에 대한 완전한 워크플로우 테스트")
        
        for i, product_name in enumerate(products_to_test, 1):
            print(f"\n📦 상품 {i}: {product_name[:50]}...")
            
            try:
                # Step 1: 상품명 검증
                print("   1️⃣ 상품명 품질 검증...")
                validation = client.validate_product_name(product_name)
                quality_status = "✅ 양호" if validation["isValid"] else "⚠️ 개선 필요"
                print(f"      품질: {quality_status} ({validation['score']}/100점)")
                
                # Step 2: 동의 확인 + 카테고리 추천
                print("   2️⃣ 동의 확인 및 카테고리 추천...")
                safe_result = client.predict_category_with_agreement_check(product_name)
                
                if safe_result.get("success"):
                    recommendation = safe_result.get("categoryRecommendation", {})
                    if recommendation.get("success"):
                        print(f"      ✅ 추천 성공: {recommendation.get('categoryName', 'N/A')}")
                        print(f"      🎯 카테고리 ID: {recommendation.get('categoryId', 'N/A')}")
                        print(f"      📊 신뢰도: {recommendation.get('confidence', 'N/A')}")
                    else:
                        print(f"      ❌ 추천 실패: {recommendation.get('error', 'N/A')}")
                else:
                    print(f"      ❌ 처리 실패: {safe_result.get('error', 'N/A')}")
                    
                    # 동의 필요한 경우 가이드 표시
                    if safe_result.get("agreementStatus") == "NOT_AGREED":
                        print("      💡 판매관리시스템(WING)에서 카테고리 자동매칭 서비스 동의 필요")
                
            except Exception as e:
                print(f"      ❌ 상품 처리 오류: {e}")
        
        print(f"\n✅ 실제 시나리오 테스트 완료")
        
    except Exception as e:
        print(f"❌ 실제 시나리오 테스트 오류: {e}")


if __name__ == "__main__":
    print("🚀 쿠팡 카테고리 추천 API 테스트 시작")
    
    test_basic_recommendation()
    test_detailed_recommendation() 
    test_bulk_recommendation()
    test_product_name_validation()
    test_integration_workflow()
    test_agreement_check()  # 새로 추가된 테스트
    test_real_world_scenario()  # 새로 추가된 테스트
    
    print("\n🏁 모든 테스트 완료")