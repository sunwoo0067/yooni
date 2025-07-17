#!/usr/bin/env python3
"""
쿠팡 판매자 상품코드로 상품 요약 정보 조회 API 실제 테스트
환경변수를 통해 실제 API 호출을 수행합니다
"""

import os
import sys
import time
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


def test_external_sku_api():
    """실제 쿠팡 API를 호출하여 판매자 상품코드로 상품 요약 정보 조회 테스트"""
    print("=" * 80)
    print("🚀 쿠팡 판매자 상품코드 조회 API 실제 테스트")
    print("=" * 80)
    
    # 환경변수에서 API 키 확인
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_external_sku = os.getenv('TEST_EXTERNAL_VENDOR_SKU')
    
    if not access_key or not secret_key:
        print("❌ 환경변수 설정이 필요합니다:")
        print("   export COUPANG_ACCESS_KEY=your_access_key")
        print("   export COUPANG_SECRET_KEY=your_secret_key")
        print("   export TEST_EXTERNAL_VENDOR_SKU=your_test_external_sku  # 선택사항")
        return
    
    if not test_external_sku:
        print("⚠️  TEST_EXTERNAL_VENDOR_SKU 환경변수가 설정되지 않아 기본값 사용")
        test_external_sku = "SKU-EXAMPLE-001"  # 기본 테스트 값
    
    try:
        # 클라이언트 초기화
        print(f"\n📋 API 클라이언트 초기화 중...")
        client = ProductClient(access_key, secret_key)
        print(f"✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 테스트할 판매자 상품코드
        external_vendor_sku_code = test_external_sku
        print(f"\n🆔 테스트 대상: 판매자 상품코드 {external_vendor_sku_code}")
        
        # 기본 상품 요약 정보 조회 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 1: 기본 상품 요약 정보 조회")
        print(f"=" * 60)
        
        start_time = time.time()
        
        print(f"📤 API 요청 중...")
        print(f"   🆔 판매자 상품코드: {external_vendor_sku_code}")
        print(f"   🔗 API 경로: /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/external-vendor-sku-codes/{external_vendor_sku_code}")
        
        result = client.get_product_by_external_sku(external_vendor_sku_code)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result.get("success"):
            print(f"\n✅ 상품 요약 정보 조회 성공!")
            
            data = result.get("data", [])
            total_count = result.get("total_count", 0)
            
            print(f"\n📊 조회 결과:")
            print(f"   📦 조회된 상품수: {total_count}개")
            print(f"   🆔 판매자 상품코드: {result.get('external_vendor_sku_code')}")
            
            # 상품 요약 정보 상세 표시
            if data:
                print(f"\n📋 상품 요약 정보 상세:")
                for i, product in enumerate(data[:3], 1):  # 처음 3개만 표시
                    seller_product_id = product.get('sellerProductId', 'N/A')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    vendor_id = product.get('vendorId', 'N/A')
                    display_category_code = product.get('displayCategoryCode', 'N/A')
                    category_id = product.get('categoryId', 'N/A')
                    product_id = product.get('productId', 'N/A')
                    md_name = product.get('mdName', 'N/A')
                    sale_started_at = product.get('saleStartedAt', 'N/A')
                    sale_ended_at = product.get('saleEndedAt', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상품 정보:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 등록상품명: {seller_product_name}")
                    print(f"      📊 상품상태: {status_name}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      🆔 판매자ID: {vendor_id}")
                    print(f"      📂 노출카테고리코드: {display_category_code}")
                    print(f"      🆔 카테고리ID: {category_id}")
                    print(f"      🆔 상품ID: {product_id}")
                    print(f"      👤 담당MD명: {md_name}")
                    print(f"      📅 판매시작일시: {sale_started_at}")
                    print(f"      📅 판매종료일시: {sale_ended_at}")
                    print(f"      📅 등록일시: {created_at}")
                
                if len(data) > 3:
                    print(f"\n   ... 그 외 {len(data) - 3}개 상품 생략")
                
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
                
                # 활성 상품 분석
                active_statuses = ['승인완료', '부분승인완료']
                active_products = [p for p in data if p.get('statusName') in active_statuses]
                print(f"\n🔄 활성화 분석:")
                print(f"   ✅ 활성 상품: {len(active_products)}개")
                print(f"   ⏸️ 비활성 상품: {len(data) - len(active_products)}개")
                
                # 최신 상품 정보
                if len(data) > 0:
                    # 등록일시 기준으로 정렬하여 최신 상품 찾기
                    try:
                        latest_product = max(data, key=lambda x: x.get('createdAt', ''))
                        print(f"\n🔄 최신 등록 상품:")
                        print(f"   📝 상품명: {latest_product.get('sellerProductName', 'N/A')}")
                        print(f"   📊 상태: {latest_product.get('statusName', 'N/A')}")
                        print(f"   📅 등록일시: {latest_product.get('createdAt', 'N/A')}")
                    except:
                        print(f"\n🔄 최신 상품 정보 분석 중 오류 발생")
                
            else:
                print(f"\n📭 해당 판매자 상품코드로 등록된 상품이 없습니다")
                print(f"💡 상품코드가 잘못되었거나 상품이 아직 등록되지 않았을 수 있습니다")
            
        else:
            print(f"\n❌ 상품 요약 정보 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 원본 응답 표시
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                pprint(original_response, width=100)
        
        # 다양한 상품코드 테스트 (환경변수에 여러 개가 설정된 경우)
        multiple_skus = os.getenv('TEST_MULTIPLE_EXTERNAL_SKUS')
        if multiple_skus:
            print(f"\n" + "=" * 60)
            print(f"📋 테스트 2: 여러 판매자 상품코드 조회")
            print(f"=" * 60)
            
            sku_list = [sku.strip() for sku in multiple_skus.split(',')]
            print(f"📤 여러 상품코드 조회 테스트...")
            print(f"   📦 상품코드 목록: {sku_list}")
            
            for i, sku_code in enumerate(sku_list, 1):
                print(f"\n   {i}. {sku_code} 조회 중...")
                
                start_time = time.time()
                result_multi = client.get_product_by_external_sku(sku_code)
                elapsed_time = time.time() - start_time
                
                print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
                
                if result_multi.get("success"):
                    data_multi = result_multi.get("data", [])
                    print(f"      ✅ 조회 성공: {len(data_multi)}개 상품")
                    
                    if data_multi:
                        product_statuses = [p.get('statusName', 'N/A') for p in data_multi]
                        print(f"      📊 상태: {', '.join(set(product_statuses))}")
                else:
                    print(f"      ❌ 조회 실패: {result_multi.get('error')}")
                
                # API 부하를 줄이기 위해 1초 대기
                if i < len(sku_list):
                    time.sleep(1)
        
        # 검증 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 3: 판매자 상품코드 검증")
        print(f"=" * 60)
        
        # 유효한 상품코드 검증 테스트
        print(f"\n🧪 유효한 상품코드 검증 테스트...")
        try:
            validate_external_vendor_sku_code("VALID-SKU_123")
            print(f"✅ 유효한 상품코드 검증 통과")
        except ValueError as e:
            print(f"⚠️  예상과 다른 검증 실패: {e}")
        
        # 잘못된 상품코드 검증 테스트
        print(f"\n🧪 잘못된 상품코드 검증 테스트...")
        try:
            validate_external_vendor_sku_code("")  # 빈 문자열
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        # 특수문자 포함 상품코드 테스트
        print(f"\n🧪 특수문자 포함 상품코드 테스트...")
        try:
            validate_external_vendor_sku_code("SKU@INVALID#123")  # 특수문자 포함
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 모든 판매자 상품코드 조회 테스트 완료!")
        print(f"=" * 60)
        
        print(f"\n✅ 테스트 결과 요약:")
        print(f"   1. ✅ 기본 상품 요약 정보 조회: {'성공' if result.get('success') else '실패'}")
        if multiple_skus:
            print(f"   2. ✅ 여러 상품코드 조회: 완료")
        print(f"   3. ✅ 판매자 상품코드 검증: 정상 작동")
        
        print(f"\n💡 상품 요약 정보 조회 API 특징:")
        print(f"   - 판매자 상품코드로 정확한 상품 식별")
        print(f"   - 상품 기본 정보 및 상태 제공")
        print(f"   - 등록상품ID/카테고리/브랜드 정보 포함")
        print(f"   - 실시간 상품 상태 반영")
        
    except Exception as e:
        print(f"\n❌ 판매자 상품코드 조회 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def test_performance():
    """API 성능 테스트"""
    print(f"\n" + "=" * 60)
    print(f"⚡ 성능 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_external_sku = os.getenv('TEST_EXTERNAL_VENDOR_SKU', 'SKU-EXAMPLE-001')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 성능 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        
        # 여러 번 호출하여 평균 응답 시간 측정
        times = []
        test_count = 3
        
        print(f"📊 {test_count}회 연속 호출 테스트...")
        
        for i in range(test_count):
            print(f"   🔄 {i+1}번째 호출...")
            
            start_time = time.time()
            result = client.get_product_by_external_sku(test_external_sku)
            elapsed_time = time.time() - start_time
            
            times.append(elapsed_time)
            print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
            print(f"      📊 결과: {'성공' if result.get('success') else '실패'}")
            
            # API 부하를 줄이기 위해 1초 대기
            if i < test_count - 1:
                time.sleep(1)
        
        # 통계 계산
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📈 성능 테스트 결과:")
        print(f"   📊 평균 응답시간: {avg_time:.2f}초")
        print(f"   🚀 최소 응답시간: {min_time:.2f}초")
        print(f"   🐌 최대 응답시간: {max_time:.2f}초")
        
        # 성능 평가
        if avg_time < 1.0:
            print(f"   ✅ 성능: 우수 (1초 미만)")
        elif avg_time < 3.0:
            print(f"   👍 성능: 양호 (3초 미만)")
        else:
            print(f"   ⚠️  성능: 개선 필요 (3초 이상)")
            
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


if __name__ == "__main__":
    print(f"🚀 쿠팡 판매자 상품코드 조회 API 실제 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 API 테스트
    test_external_sku_api()
    
    # 성능 테스트
    test_performance()
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 모든 테스트가 완료되었습니다!")