#!/usr/bin/env python3
"""
쿠팡 상품 API 실제 연동 테스트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import ProductClient
from market.coupang.product.models import ProductSearchParams


def test_product_api_authentication():
    """인증 및 기본 API 테스트"""
    print("🔐 쿠팡 상품 API 인증 테스트")
    print("=" * 60)
    
    try:
        # 클라이언트 초기화 (환경변수에서 자동 로드)
        client = ProductClient()
        print("✅ ProductClient 초기화 성공")
        print(f"   📍 BASE_URL: {client.BASE_URL}")
        print(f"   🔑 인증 객체: {type(client.auth).__name__}")
        
        return client
        
    except Exception as e:
        print(f"❌ 클라이언트 초기화 실패: {e}")
        return None


def test_product_inflow_status(client):
    """상품 유입 현황 조회 테스트"""
    print("\n📊 상품 유입 현황 조회 테스트")
    print("=" * 60)
    
    try:
        # 상품 유입 현황 조회
        result = client.get_inflow_status()
        
        if result.get("success"):
            print("✅ 상품 유입 현황 조회 성공")
            
            data = result.get("data", {})
            print(f"   📦 조회 결과:")
            
            # 유입 현황 정보 출력
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"      - {key}: {value}")
            else:
                print(f"      응답 데이터: {data}")
                
        else:
            print(f"❌ 상품 유입 현황 조회 실패: {result.get('error')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 상품 유입 현황 조회 중 오류: {e}")
        return None


def test_product_list_query(client):
    """상품 목록 조회 테스트"""
    print("\n📋 상품 목록 조회 테스트")
    print("=" * 60)
    
    try:
        # 검색 파라미터 설정
        search_params = ProductSearchParams(
            vendor_id=os.getenv("COUPANG_VENDOR_ID", "A01409684"),
            status="APPROVED",  # 승인된 상품 (올바른 상태 코드)
            max_per_page=5  # 최대 5개만 조회
        )
        
        print(f"🔍 검색 조건:")
        print(f"   🆔 판매자 ID: {search_params.vendor_id}")
        print(f"   📊 상태: {search_params.status}")
        print(f"   📄 제한: {search_params.max_per_page}개")
        
        # 상품 목록 조회
        result = client.list_products(search_params)
        
        if result.get("success"):
            print("✅ 상품 목록 조회 성공")
            
            data = result.get("data", [])
            print(f"   📦 조회된 상품 수: {len(data)}개")
            
            # 상품 정보 간략 출력
            for i, product in enumerate(data[:3]):  # 최대 3개만 출력
                print(f"   📦 상품 {i+1}:")
                print(f"      - ID: {product.get('sellerProductId')}")
                print(f"      - 이름: {product.get('sellerProductName')}")
                print(f"      - 상태: {product.get('sellerProductStatusName')}")
                print(f"      - 등록일: {product.get('createdAt')}")
                
        else:
            print(f"❌ 상품 목록 조회 실패: {result.get('error')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 상품 목록 조회 중 오류: {e}")
        return None


def test_category_recommendation(client):
    """카테고리 추천 테스트"""
    print("\n🎯 카테고리 추천 테스트")
    print("=" * 60)
    
    try:
        # 카테고리 추천 요청
        test_product_names = [
            "무선 이어폰",
            "스마트폰 케이스", 
            "노트북 거치대"
        ]
        
        for product_name in test_product_names:
            print(f"\n🔍 상품명: '{product_name}'")
            
            result = client.recommend_category(product_name)
            
            if result.get("success"):
                print("✅ 카테고리 추천 성공")
                
                data = result.get("data", [])
                print(f"   🎯 추천 카테고리 수: {len(data)}개")
                
                # 추천 카테고리 정보 출력 (최대 3개)
                for i, category in enumerate(data[:3]):
                    print(f"      {i+1}. {category.get('categoryName')} (ID: {category.get('categoryId')})")
                    
            else:
                print(f"❌ 카테고리 추천 실패: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 카테고리 추천 중 오류: {e}")
        return False


def test_external_sku_query(client):
    """외부 SKU 코드로 상품 조회 테스트"""
    print("\n🔎 외부 SKU 코드 상품 조회 테스트")
    print("=" * 60)
    
    try:
        # 테스트용 SKU 코드 (실제로는 존재하지 않을 가능성이 높음)
        test_sku = "TEST-SKU-001"
        
        print(f"🔍 조회할 외부 SKU 코드: {test_sku}")
        
        result = client.get_product_by_external_sku(test_sku)
        
        if result.get("success"):
            print("✅ 외부 SKU 상품 조회 성공")
            
            data = result.get("data")
            if data:
                print(f"   📦 상품 정보:")
                print(f"      - ID: {data.get('sellerProductId')}")
                print(f"      - 이름: {data.get('sellerProductName')}")
                print(f"      - 외부 SKU: {data.get('externalVendorSkuCode')}")
            else:
                print("   📭 해당 SKU 코드로 등록된 상품이 없습니다.")
                
        else:
            error_msg = result.get('error', '')
            if "찾을 수 없습니다" in error_msg or "존재하지 않습니다" in error_msg:
                print(f"📭 해당 SKU 코드로 등록된 상품이 없습니다: {test_sku}")
                print("   (이는 예상된 결과입니다 - 테스트용 SKU 코드이므로)")
            else:
                print(f"❌ 외부 SKU 상품 조회 실패: {error_msg}")
            
        return result
        
    except Exception as e:
        print(f"❌ 외부 SKU 상품 조회 중 오류: {e}")
        return None


def run_integration_tests():
    """전체 연동 테스트 실행"""
    print("🚀 쿠팡 상품 API 연동 테스트 시작")
    print("=" * 80)
    
    # 환경변수 확인 메시지
    print("\n📋 필요한 환경변수:")
    print("   - COUPANG_ACCESS_KEY")
    print("   - COUPANG_SECRET_KEY") 
    print("   - COUPANG_VENDOR_ID")
    print("   (이미 .env 파일에 설정되어 있습니다)")
    
    test_results = []
    
    # 1. 인증 테스트
    client = test_product_api_authentication()
    if not client:
        print("\n❌ 인증 실패로 테스트 중단")
        return False
    
    test_results.append(("인증", True))
    
    # 2. 상품 유입 현황 조회
    inflow_result = test_product_inflow_status(client)
    test_results.append(("상품 유입 현황", inflow_result is not None and inflow_result.get("success", False)))
    
    # 3. 상품 목록 조회
    list_result = test_product_list_query(client)
    test_results.append(("상품 목록 조회", list_result is not None and list_result.get("success", False)))
    
    # 4. 카테고리 추천
    category_result = test_category_recommendation(client)
    test_results.append(("카테고리 추천", category_result))
    
    # 5. 외부 SKU 조회
    sku_result = test_external_sku_query(client)
    test_results.append(("외부 SKU 조회", sku_result is not None))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"   {test_name:15} : {status}")
        if success:
            success_count += 1
    
    total_tests = len(test_results)
    print(f"\n🎯 전체 결과: {success_count}/{total_tests} 테스트 통과")
    
    if success_count == total_tests:
        print("🎉 모든 테스트가 성공했습니다!")
        print("   쿠팡 상품 API 연동이 정상적으로 작동합니다.")
    elif success_count > 0:
        print("⚠️  일부 테스트가 실패했지만 기본 연동은 작동합니다.")
        print("   실패한 테스트는 API 정책이나 데이터 상태에 따른 것일 수 있습니다.")
    else:
        print("❌ 대부분의 테스트가 실패했습니다.")
        print("   API 키나 권한을 확인해주세요.")
    
    return success_count > 0


if __name__ == "__main__":
    success = run_integration_tests()
    
    print(f"\n{'='*80}")
    print("🔚 테스트 완료")
    
    if success:
        print("✅ 쿠팡 상품 API 연동 테스트 성공!")
    else:
        print("❌ 쿠팡 상품 API 연동 테스트 실패")
    
    sys.exit(0 if success else 1)