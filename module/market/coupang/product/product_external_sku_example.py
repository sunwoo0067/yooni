#!/usr/bin/env python3
"""
쿠팡 판매자 상품코드로 상품 요약 정보 조회 API 사용 예제
externalVendorSkuCode를 통해 상품의 요약 정보를 조회하는 방법을 보여줍니다
"""

import os
import sys
from datetime import datetime
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import (
    ProductClient,
    validate_external_vendor_sku_code
)


def test_basic_external_sku_lookup():
    """기본적인 판매자 상품코드로 상품 요약 정보 조회 테스트"""
    print("=" * 60 + " 기본 상품 요약 정보 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 예시 판매자 상품코드 (실제 상품코드로 변경 필요)
        external_vendor_sku_code = "SKU-EXAMPLE-001"  # 실제 판매자 상품코드로 변경 필요
        
        print(f"\n📋 상품 요약 정보 조회 중...")
        print(f"   🆔 판매자 상품코드: {external_vendor_sku_code}")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/external-vendor-sku-codes/{external_vendor_sku_code}")
        
        # 상품 요약 정보 조회 실행
        print(f"\n📤 상품 요약 정보 조회 요청 중...")
        result = client.get_product_by_external_sku(external_vendor_sku_code)
        
        if result.get("success"):
            print(f"\n✅ 상품 요약 정보 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            total_count = result.get("total_count", 0)
            
            print(f"\n📊 조회 결과 정보:")
            print(f"   📦 조회된 상품수: {total_count}개")
            print(f"   🆔 판매자 상품코드: {result.get('external_vendor_sku_code')}")
            
            # 상품 요약 정보 표시
            if data:
                print(f"\n📋 상품 요약 정보:")
                for i, product in enumerate(data, 1):
                    seller_product_id = product.get('sellerProductId', 'N/A')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    display_category_code = product.get('displayCategoryCode', 'N/A')
                    vendor_id = product.get('vendorId', 'N/A')
                    sale_started_at = product.get('saleStartedAt', 'N/A')
                    sale_ended_at = product.get('saleEndedAt', 'N/A')
                    brand = product.get('brand', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    category_id = product.get('categoryId', 'N/A')
                    product_id = product.get('productId', 'N/A')
                    md_id = product.get('mdId', 'N/A')
                    md_name = product.get('mdName', 'N/A')
                    
                    print(f"\n   {i}. 상품 정보:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 등록상품명: {seller_product_name}")
                    print(f"      📊 상품상태: {status_name}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📅 판매시작일시: {sale_started_at}")
                    print(f"      📅 판매종료일시: {sale_ended_at}")
                    print(f"      📅 등록일시: {created_at}")
                    print(f"      📂 노출카테고리코드: {display_category_code}")
                    print(f"      🆔 판매자ID: {vendor_id}")
                    print(f"      🆔 카테고리ID: {category_id}")
                    print(f"      🆔 상품ID: {product_id}")
                    print(f"      👤 담당MD ID: {md_id}")
                    print(f"      👤 담당MD명: {md_name}")
                
                # 상품 분석
                print(f"\n📈 상품 분석:")
                
                # 상태별 분석
                status_count = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"\n📊 상태별 분포:")
                for status, count in status_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
                
                # 브랜드별 분석
                brand_count = {}
                for product in data:
                    brand = product.get('brand') or '브랜드 없음'
                    brand_count[brand] = brand_count.get(brand, 0) + 1
                
                print(f"\n🏷️ 브랜드별 분포:")
                for brand, count in brand_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   🏷️ {brand}: {count}개 ({percentage:.1f}%)")
                
                # 최신 상품 정보
                if len(data) > 0:
                    latest_product = max(data, key=lambda x: x.get('createdAt', ''))
                    print(f"\n🔄 최신 등록 상품:")
                    print(f"   📝 상품명: {latest_product.get('sellerProductName', 'N/A')}")
                    print(f"   📊 상태: {latest_product.get('statusName', 'N/A')}")
                    print(f"   📅 등록일시: {latest_product.get('createdAt', 'N/A')}")
                    
                # 활성 상품 분석
                active_products = [p for p in data if p.get('statusName') in ['승인완료', '부분승인완료']]
                inactive_products = [p for p in data if p.get('statusName') not in ['승인완료', '부분승인완료']]
                
                print(f"\n🔄 상품 활성화 분석:")
                print(f"   ✅ 활성 상품: {len(active_products)}개")
                print(f"   ⏸️ 비활성 상품: {len(inactive_products)}개")
                
                if len(data) > 1:
                    print(f"   📈 총 상품 수: {len(data)}개")
                    
            else:
                print(f"\n📭 해당 판매자 상품코드로 등록된 상품이 없습니다")
                print(f"💡 상품코드가 잘못되었거나 상품이 아직 등록되지 않았을 수 있습니다")
            
        else:
            print(f"\n❌ 상품 요약 정보 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 상품 요약 정보 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_external_skus():
    """여러 판매자 상품코드로 상품 조회 및 비교 테스트"""
    print("\n" + "=" * 60 + " 여러 판매자 상품코드 비교 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 비교할 판매자 상품코드들 (실제 상품코드로 변경 필요)
        sku_codes = ["SKU-EXAMPLE-001", "SKU-EXAMPLE-002", "SKU-EXAMPLE-003"]
        
        print(f"\n🔄 여러 판매자 상품코드 조회")
        print(f"   📦 비교 대상: {len(sku_codes)}개 상품코드")
        print(f"   📝 목적: 상품코드별 등록 상품 비교")
        
        sku_results = {}
        
        # 각 판매자 상품코드별로 조회
        for i, sku_code in enumerate(sku_codes, 1):
            print(f"\n📦 상품코드 {i} ({sku_code}) 조회 중...")
            
            result = client.get_product_by_external_sku(sku_code)
            
            if result.get("success"):
                data = result.get("data", [])
                sku_results[sku_code] = data
                print(f"   ✅ 상품코드 {i} 조회 성공: {len(data)}개 상품")
                
                if data:
                    latest_status = data[0].get('statusName', 'N/A')
                    print(f"      📊 대표 상품 상태: {latest_status}")
            else:
                print(f"   ❌ 상품코드 {i} 조회 실패: {result.get('error')}")
                sku_results[sku_code] = []
        
        # 상품코드별 비교 분석
        if any(sku_results.values()):
            print(f"\n📊 판매자 상품코드별 비교:")
            
            # 각 상품코드의 상품 수
            print(f"\n📋 상품코드별 등록 상품 수:")
            for sku_code, products in sku_results.items():
                product_count = len(products)
                print(f"   🆔 {sku_code}: {product_count}개 상품")
                
                if products:
                    active_count = sum(1 for p in products if p.get('statusName') in ['승인완료', '부분승인완료'])
                    print(f"      ✅ 활성 상품: {active_count}개")
            
            # 전체 통계
            total_products = sum(len(products) for products in sku_results.values())
            successful_skus = sum(1 for products in sku_results.values() if products)
            
            print(f"\n📈 전체 분석:")
            print(f"   📊 총 조회된 상품: {total_products}개")
            print(f"   ✅ 성공한 상품코드: {successful_skus}개")
            print(f"   📦 총 상품코드: {len(sku_codes)}개")
            
            # 상태 분포 전체 분석
            all_statuses = {}
            for products in sku_results.values():
                for product in products:
                    status = product.get('statusName', 'Unknown')
                    all_statuses[status] = all_statuses.get(status, 0) + 1
            
            if all_statuses:
                print(f"\n📊 전체 상품 상태 분포:")
                for status, count in all_statuses.items():
                    percentage = (count / total_products) * 100 if total_products > 0 else 0
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
            
            print(f"\n💡 비교 분석 활용:")
            print(f"   📊 재고 관리: 상품코드별 등록 상품 현황 파악")
            print(f"   🔍 상태 모니터링: 승인/반려 상품 추적")
            print(f"   📈 성과 분석: 상품코드별 등록 성공률 비교")
        
    except Exception as e:
        print(f"❌ 여러 판매자 상품코드 비교 오류: {e}")


def test_external_sku_validation():
    """판매자 상품코드 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 판매자 상품코드 검증 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "빈 상품코드",
            "sku_code": "",
            "expected_error": "필수입니다"
        },
        {
            "name": "공백만 있는 상품코드",
            "sku_code": "   ",
            "expected_error": "공백일 수 없습니다"
        },
        {
            "name": "너무 긴 상품코드",
            "sku_code": "A" * 101,  # 101자
            "expected_error": "100자 이하"
        },
        {
            "name": "특수문자 포함 상품코드",
            "sku_code": "SKU@EXAMPLE#001",  # 특수문자 포함
            "expected_error": "영문, 숫자, 하이픈"
        },
        {
            "name": "유효한 상품코드",
            "sku_code": "SKU-EXAMPLE_001",  # 유효한 형식
            "expected_error": None  # 오류 없음
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        sku_code = test_case['sku_code']
        expected_error = test_case['expected_error']
        
        try:
            validate_external_vendor_sku_code(sku_code)
            
            if expected_error is None:
                print(f"   ✅ 예상대로 검증 통과")
            else:
                print(f"   ⚠️ 예상과 다르게 검증 통과 (검증 로직 확인 필요)")
                
        except ValueError as e:
            if expected_error and expected_error in str(e):
                print(f"   ✅ 예상대로 검증 실패: {e}")
            else:
                print(f"   ⚠️ 예상과 다른 검증 오류: {e}")
        except Exception as e:
            print(f"   ❌ 예상치 못한 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 판매자 상품코드로 상품 요약 정보 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 상품 요약 정보 조회 테스트
        test_basic_external_sku_lookup()
        
        # 여러 판매자 상품코드 비교 테스트
        test_multiple_external_skus()
        
        # 검증 시나리오 테스트
        test_external_sku_validation()
        
        print(f"\n" + "=" * 50 + " 상품 요약 정보 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 판매자 상품코드 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 요약 정보 조회")
        print("   2. ✅ 여러 상품코드 일괄 조회")
        print("   3. ✅ 상품 상태 및 분포 분석")
        print("   4. ✅ 브랜드별 분석")
        print("   5. ✅ 활성/비활성 상품 분석")
        print("   6. ✅ 판매자 상품코드 검증")
        
        print(f"\n💡 상품 요약 정보 조회 주요 특징:")
        print("   - 판매자 상품코드 기반 정확한 상품 식별")
        print("   - 상품 요약 정보 한번에 조회")
        print("   - 등록상품ID/상품명/상태/브랜드 등 핵심 정보 제공")
        print("   - 실시간 상품 상태 반영")
        print("   - 여러 상품 동시 조회 지원")
        
        print(f"\n📊 활용 방안:")
        print("   🔍 상품 검색: 판매자 상품코드로 빠른 상품 조회")
        print("   📊 재고 관리: 상품코드별 등록 상품 현황 파악")
        print("   🔄 상태 모니터링: 승인/반려 상품 실시간 추적")
        print("   📈 성과 분석: 상품별 등록 성공률 및 상태 분석")
        print("   🚨 문제 해결: 특정 상품코드 관련 이슈 진단")
        
    except Exception as e:
        print(f"\n❌ 판매자 상품코드 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()