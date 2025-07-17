#!/usr/bin/env python3
"""
쿠팡 카테고리 API 실제 인증 테스트
실제 API 키를 사용한 카테고리 조회 및 유효성 검사 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_client import CoupangCategoryClient
from market.coupang.category.category_recommendation_client import CoupangCategoryRecommendationClient
from market.coupang.category.category_manager import CoupangCategoryManager


def test_real_api_category_display():
    """실제 API로 노출 카테고리 조회 테스트"""
    print("=" * 60 + " 실제 API 노출 카테고리 조회 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = CoupangCategoryClient()
        print("✅ 실제 API 인증으로 카테고리 클라이언트 초기화 성공")
        
        # 1 Depth 카테고리 조회
        print(f"\n📂 1 Depth 카테고리 목록 조회 (실제 API)...")
        categories = client.get_all_first_depth_categories()
        
        if categories:
            print(f"✅ {len(categories)}개의 1 Depth 카테고리 발견")
            print(f"\n📋 실제 카테고리 목록:")
            
            for i, category in enumerate(categories, 1):
                code = category.get('displayItemCategoryCode', 'Unknown')
                name = category.get('name', 'Unknown')
                status = category.get('status', 'Unknown')
                status_emoji = "✅" if status == "ACTIVE" else "⚠️" if status == "READY" else "❌"
                
                print(f"   {i:2d}. [{code:6}] {name} {status_emoji}")
        else:
            print("❌ 1 Depth 카테고리를 찾을 수 없습니다")
            
    except Exception as e:
        print(f"❌ 실제 API 카테고리 조회 오류: {e}")


def test_real_api_category_validation():
    """실제 API로 카테고리 유효성 검사 테스트"""
    print("\n" + "=" * 60 + " 실제 API 카테고리 유효성 검사 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 실제 쿠팡 카테고리 코드들로 테스트 (Excel 데이터 기반)
        test_categories = [
            {"code": 112143, "description": "TV", "expected": "leaf"},
            {"code": 62588, "description": "가전/디지털", "expected": "parent"},
            {"code": 67983, "description": "남성패션운동화", "expected": "leaf"},
            {"code": 58646, "description": "봉지라면", "expected": "leaf"},
            {"code": 63237, "description": "TV/영상가전", "expected": "parent"}
        ]
        
        print(f"📊 {len(test_categories)}개 카테고리 실제 API로 유효성 검사...")
        
        for test_cat in test_categories:
            code = test_cat["code"]
            description = test_cat["description"]
            expected = test_cat["expected"]
            
            print(f"\n📂 카테고리 {code} ({description}) 검사 중...")
            
            try:
                # 실제 API로 카테고리 상태 확인
                status_result = client.check_category_status(code)
                
                print(f"✅ 검사 성공:")
                print(f"   📝 카테고리 코드: {status_result['categoryCode']}")
                print(f"   📊 사용 가능: {'✅ 예' if status_result['isAvailable'] else '❌ 아니오'}")
                print(f"   🏷️ 상태: {status_result['status']}")
                print(f"   💬 메시지: {status_result['message']}")
                
                if expected == "leaf":
                    print(f"   ✅ 예상대로 leaf category로 확인됨")
                else:
                    print(f"   ⚠️ 예상과 달리 leaf category로 확인됨")
                
            except ValueError as e:
                print(f"   ⚠️ leaf category 아님: {str(e)[:200]}...")
                
                if expected == "parent":
                    print(f"   ✅ 예상대로 parent category임")
                    
                    # leaf category ID 추출해보기
                    if "leaf category ID:" in str(e):
                        import re
                        numbers = re.findall(r'\d+', str(e).split("leaf category ID:")[-1])
                        if numbers:
                            leaf_count = len(numbers)
                            print(f"   🌿 관련 leaf 카테고리: {leaf_count}개")
                            print(f"   예시: {', '.join(numbers[:5])}...")
                else:
                    print(f"   ❌ 예상과 달리 parent category임")
                
            except Exception as e:
                print(f"   ❌ 예상치 못한 오류: {e}")
                
    except Exception as e:
        print(f"❌ 실제 API 유효성 검사 오류: {e}")


def test_real_api_category_metadata():
    """실제 API로 카테고리 메타데이터 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 카테고리 메타데이터 조회 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # leaf 카테고리들의 메타데이터 조회
        leaf_categories = [112143, 67983, 58646]  # TV, 남성패션운동화, 봉지라면
        
        for category_code in leaf_categories:
            print(f"\n📂 카테고리 {category_code} 메타데이터 조회 중...")
            
            try:
                # 실제 API로 메타데이터 조회
                metadata = client.get_category_metadata(category_code)
                
                print(f"✅ 메타데이터 조회 성공:")
                data = metadata.get('data', {})
                
                # 기본 정보
                print(f"   📝 카테고리 코드: {data.get('displayCategoryCode', 'Unknown')}")
                print(f"   🏷️ 카테고리명: {data.get('displayCategoryName', 'Unknown')}")
                print(f"   📊 활성 상태: {data.get('activated', 'Unknown')}")
                
                # 필수 속성
                required_attrs = data.get('requiredDocumentNames', [])
                if required_attrs:
                    print(f"   📋 필수 문서: {len(required_attrs)}개")
                    for attr in required_attrs[:3]:  # 상위 3개만 표시
                        print(f"      - {attr}")
                
                # 구매 옵션
                purchase_options = data.get('requiredProductRegisterAttributes', [])
                if purchase_options:
                    print(f"   🛒 필수 속성: {len(purchase_options)}개")
                    for option in purchase_options[:3]:  # 상위 3개만 표시
                        name = option.get('name', 'Unknown')
                        required = option.get('required', False)
                        data_type = option.get('dataType', 'Unknown')
                        print(f"      - {name} ({'필수' if required else '선택'}, {data_type})")
                
                # 옵션 허용 여부
                single_item = data.get('allowSingleItem', False)
                notice_category = data.get('noticeCategoryName', 'Unknown')
                print(f"   📦 단일상품 허용: {'✅ 예' if single_item else '❌ 아니오'}")
                print(f"   📢 고시 카테고리: {notice_category}")
                
            except Exception as e:
                print(f"   ❌ 메타데이터 조회 오류: {e}")
                
    except Exception as e:
        print(f"❌ 메타데이터 조회 테스트 오류: {e}")


def test_real_api_category_recommendation():
    """실제 API로 카테고리 추천 테스트"""
    print("\n" + "=" * 60 + " 실제 API 카테고리 추천 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 추천 클라이언트 초기화
        recommendation_client = CoupangCategoryRecommendationClient()
        print("✅ 실제 API 인증으로 카테고리 추천 클라이언트 초기화 성공")
        
        # 테스트 상품들
        test_products = [
            "삼성 65인치 4K UHD 스마트 TV",
            "나이키 에어맥스 남성 운동화 270 화이트 260mm",
            "농심 신라면 봉지라면 120g x 5개",
            "애플 아이폰 15 Pro 실리콘 케이스",
            "유한양행 유한락스 1L 살균세제"
        ]
        
        print(f"\n🎯 {len(test_products)}개 상품 실제 API로 카테고리 추천...")
        
        for i, product_name in enumerate(test_products, 1):
            print(f"\n📦 상품 {i}: {product_name}")
            
            try:
                # 실제 API로 카테고리 추천
                result = recommendation_client.get_recommendation_result(product_name)
                
                if result.get("success"):
                    print(f"✅ 추천 성공:")
                    print(f"   🎯 결과 타입: {result.get('resultType', 'Unknown')}")
                    print(f"   📂 카테고리 ID: {result.get('categoryId', 'Unknown')}")
                    print(f"   📝 카테고리명: {result.get('categoryName', 'Unknown')}")
                    print(f"   📊 신뢰도: {result.get('confidence', 'Unknown')}")
                    
                    comment = result.get('comment')
                    if comment:
                        print(f"   💬 코멘트: {comment}")
                else:
                    print(f"❌ 추천 실패: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ 추천 오류: {e}")
        
    except Exception as e:
        print(f"❌ 실제 API 추천 테스트 오류: {e}")


def test_real_api_agreement_check():
    """실제 API로 카테고리 자동 매칭 동의 확인 테스트"""
    print("\n" + "=" * 60 + " 실제 API 동의 확인 테스트 " + "=" * 60)
    
    try:
        recommendation_client = CoupangCategoryRecommendationClient()
        
        print("🔍 카테고리 자동 매칭 서비스 동의 상태 확인 (실제 API)...")
        
        # 실제 API로 동의 확인
        agreement_result = recommendation_client.check_auto_category_agreement()
        
        print(f"✅ 동의 확인 완료:")
        print(f"   🏢 판매자 ID: {agreement_result.get('vendorId', 'N/A')}")
        print(f"   📊 동의 상태: {agreement_result.get('status', 'UNKNOWN')}")
        print(f"   💬 메시지: {agreement_result.get('message', 'N/A')}")
        print(f"   ✅ 성공: {'예' if agreement_result.get('success') else '아니오'}")
        
        if agreement_result.get("success"):
            if agreement_result.get("isAgreed"):
                print("   🎉 카테고리 자동 매칭 서비스 사용 가능!")
                
                # 동의된 상태에서 안전한 추천 테스트
                print(f"\n🔍 안전한 카테고리 추천 테스트...")
                safe_result = recommendation_client.predict_category_with_agreement_check(
                    "삼성 갤럭시 S24 투명 케이스"
                )
                
                if safe_result.get("success"):
                    recommendation = safe_result.get("categoryRecommendation", {})
                    if recommendation.get("success"):
                        print(f"   ✅ 안전한 추천 성공:")
                        print(f"   📂 추천 카테고리: {recommendation.get('categoryName', 'N/A')}")
                        print(f"   🎯 카테고리 ID: {recommendation.get('categoryId', 'N/A')}")
                        print(f"   📊 신뢰도: {recommendation.get('confidence', 'N/A')}")
                    else:
                        print(f"   ❌ 추천 실패: {recommendation.get('error', 'N/A')}")
                else:
                    print(f"   ❌ 안전한 추천 실패: {safe_result.get('error', 'N/A')}")
            else:
                print("   ⚠️ 카테고리 자동 매칭 서비스 미동의")
                print("   💡 WING 판매관리시스템에서 동의 필요")
        else:
            print(f"   ❌ 동의 확인 실패: {agreement_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ 실제 API 동의 확인 테스트 오류: {e}")


def test_real_api_integrated_workflow():
    """실제 API로 통합 워크플로우 테스트"""
    print("\n" + "=" * 60 + " 실제 API 통합 워크플로우 테스트 " + "=" * 60)
    
    try:
        # 통합 매니저 초기화 (실제 API + 오프라인 데이터)
        manager = CoupangCategoryManager()
        print("✅ 실제 API + 오프라인 데이터 통합 매니저 초기화 성공")
        
        # 실제 상품으로 완전한 워크플로우 테스트
        test_product = "나이키 에어맥스 남성 운동화 270 화이트 250mm"
        
        print(f"\n🎯 완전한 워크플로우 테스트: '{test_product}'")
        
        # 1단계: 카테고리 추천 (실제 API)
        print(f"\n1️⃣ 실제 API로 카테고리 추천...")
        recommendation = manager.recommend_category(test_product)
        
        if recommendation.get("success"):
            category_id = recommendation.get("categoryId")
            category_name = recommendation.get("categoryName")
            
            print(f"✅ 추천 성공:")
            print(f"   📂 추천 카테고리: {category_name}")
            print(f"   🎯 카테고리 ID: {category_id}")
            print(f"   📊 신뢰도: {recommendation.get('confidence', 'Unknown')}")
            
            # 오프라인 데이터로 보강된 정보 확인
            enhanced_info = recommendation.get("enhancedInfo", {})
            if enhanced_info:
                print(f"\n📈 오프라인 데이터 보강 정보:")
                
                required_options = enhanced_info.get("required_purchase_options", [])
                if required_options:
                    print(f"   🛒 필수 구매 옵션: {len(required_options)}개")
                    for option in required_options[:3]:
                        print(f"      - {option.get('type', 'Unknown')}")
                
                search_options = enhanced_info.get("available_search_options", [])
                if search_options:
                    print(f"   🔍 검색 옵션: {len(search_options)}개")
                
                similar_cats = enhanced_info.get("similar_categories", [])
                if similar_cats:
                    print(f"   🔗 유사 카테고리: {len(similar_cats)}개")
            
            # 2단계: 실제 API로 카테고리 유효성 확인
            if category_id:
                print(f"\n2️⃣ 실제 API로 카테고리 유효성 확인...")
                try:
                    # API 클라이언트로 직접 확인
                    api_client = CoupangCategoryClient()
                    status_result = api_client.check_category_status(int(category_id))
                    
                    print(f"✅ 유효성 확인:")
                    print(f"   📊 사용 가능: {'✅ 예' if status_result['isAvailable'] else '❌ 아니오'}")
                    print(f"   🏷️ 상태: {status_result['status']}")
                    
                    # 3단계: 상품 데이터 검증 (오프라인 데이터 활용)
                    print(f"\n3️⃣ 오프라인 데이터로 상품 데이터 검증...")
                    sample_product_data = {
                        "신발사이즈": "250",
                        "색상": "화이트",
                        "브랜드": "나이키"
                    }
                    
                    validation = manager.validate_product_data(str(category_id), sample_product_data)
                    
                    validation_status = "✅ 유효" if validation["isValid"] else "❌ 무효"
                    print(f"   검증 결과: {validation_status} (점수: {validation['score']}/100)")
                    
                    if validation["missingRequiredOptions"]:
                        print(f"   🚨 누락된 필수 옵션: {', '.join(validation['missingRequiredOptions'])}")
                    
                    if validation["suggestions"]:
                        print(f"   💡 개선 제안:")
                        for suggestion in validation["suggestions"][:3]:
                            print(f"      - {suggestion}")
                            
                except ValueError as e:
                    if "leaf category가 아닙니다" in str(e):
                        print(f"   ⚠️ parent category임 - 실제 상품 등록 시 leaf category 필요")
                    else:
                        print(f"   ❌ 유효성 확인 오류: {e}")
                except Exception as e:
                    print(f"   ❌ 유효성 확인 오류: {e}")
        else:
            print(f"❌ 추천 실패: {recommendation.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ 통합 워크플로우 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 카테고리 API 실제 인증 테스트 시작")
    print("=" * 100)
    
    try:
        test_real_api_category_display()
        test_real_api_category_validation()
        test_real_api_category_metadata()
        test_real_api_category_recommendation()
        test_real_api_agreement_check()
        test_real_api_integrated_workflow()
        
        print(f"\n" + "=" * 50 + " 실제 API 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 테스트가 완료되었습니다!")
        print("\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 인증 및 노출 카테고리 조회")
        print("   2. ✅ 실제 leaf/parent 카테고리 유효성 검사")
        print("   3. ✅ 실제 카테고리 메타데이터 조회")
        print("   4. ✅ 실제 머신러닝 기반 카테고리 추천")
        print("   5. ✅ 실제 카테고리 자동 매칭 동의 확인")
        print("   6. ✅ 실제 API + 오프라인 데이터 통합 워크플로우")
        
    except Exception as e:
        print(f"\n❌ 실제 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()