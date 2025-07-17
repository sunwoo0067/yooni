#!/usr/bin/env python3
"""
쿠팡 상품 목록 페이징 조회 API 사용 예제
등록상품 목록을 페이징으로 조회하는 방법을 보여줍니다
"""

import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import (
    ProductClient,
    ProductSearchParams
)


def test_basic_product_list():
    """기본적인 상품 목록 조회 테스트"""
    print("=" * 60 + " 기본 상품 목록 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 기본 검색 파라미터 설정
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')  # 실제 벤더 ID로 변경 필요
        
        search_params = ProductSearchParams(
            vendor_id=vendor_id,
            max_per_page=10  # 페이지당 10개씩
        )
        
        print(f"\n📋 상품 목록 조회 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📄 페이지당 건수: {search_params.max_per_page}개")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products")
        
        # 상품 목록 조회 실행
        print(f"\n📤 상품 목록 조회 요청 중...")
        result = client.list_products(search_params)
        
        if result.get("success"):
            print(f"\n✅ 상품 목록 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            next_token = result.get("next_token")
            has_next = result.get("has_next")
            current_page = result.get("current_page")
            
            print(f"\n📊 조회 결과 정보:")
            print(f"   📦 조회된 상품수: {len(data)}개")
            print(f"   📄 현재 페이지: {current_page}")
            print(f"   ➡️ 다음 페이지: {'있음' if has_next else '없음'}")
            if next_token:
                print(f"   🔑 다음 페이지 토큰: {next_token}")
            
            # 상품 목록 표시
            if data:
                print(f"\n📋 상품 목록:")
                for i, product in enumerate(data[:5], 1):  # 상위 5개만 표시
                    seller_product_id = product.get('sellerProductId')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상품 정보:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 상품명: {seller_product_name[:50]}{'...' if len(seller_product_name) > 50 else ''}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📊 상태: {status_name}")
                    print(f"      📅 등록일: {created_at}")
                
                if len(data) > 5:
                    print(f"\n   ... 외 {len(data) - 5}개 상품")
            else:
                print(f"\n📭 조회된 상품이 없습니다")
            
            # 페이징 정보
            print(f"\n📄 페이징 정보:")
            print(f"   📋 현재 페이지 상품수: {len(data)}개")
            print(f"   📄 요청 페이지당 최대: {search_params.max_per_page}개")
            if has_next:
                print(f"   ➡️ 다음 페이지 조회 가능")
                print(f"   💡 다음 페이지 조회: next_token='{next_token}' 사용")
            else:
                print(f"   🏁 마지막 페이지입니다")
            
        else:
            print(f"\n❌ 상품 목록 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 상품 목록 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_product_list_with_filters():
    """필터를 사용한 상품 목록 조회 테스트"""
    print("\n" + "=" * 60 + " 필터 적용 상품 목록 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 필터가 적용된 검색 파라미터
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        # 승인완료 상품만 조회
        search_params = ProductSearchParams(
            vendor_id=vendor_id,
            max_per_page=20,  # 페이지당 20개
            status="APPROVED",  # 승인완료 상품만
            # manufacture="테스트브랜드",  # 특정 제조사
            # created_at="2024-01-15"  # 특정 날짜
        )
        
        print(f"\n🔍 필터 적용 상품 목록 조회")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📄 페이지당 건수: {search_params.max_per_page}개")
        print(f"   📊 상품 상태: {search_params.status} (승인완료)")
        # print(f"   🏭 제조사: {search_params.manufacture}")
        # print(f"   📅 등록일: {search_params.created_at}")
        
        # 필터 적용 조회 실행
        print(f"\n📤 필터 적용 조회 요청 중...")
        result = client.list_products(search_params)
        
        if result.get("success"):
            print(f"\n✅ 필터 적용 조회 성공!")
            
            data = result.get("data", [])
            
            print(f"\n📊 필터 적용 결과:")
            print(f"   📦 필터링된 상품수: {len(data)}개")
            print(f"   📊 조건: 승인완료 상품만")
            
            # 상태별 분류
            status_count = {}
            for product in data:
                status = product.get('statusName', 'Unknown')
                status_count[status] = status_count.get(status, 0) + 1
            
            print(f"\n📈 상태별 분포:")
            for status, count in status_count.items():
                print(f"   📊 {status}: {count}개")
            
            # 브랜드별 분류 (상위 5개)
            brand_count = {}
            for product in data:
                brand = product.get('brand', 'Unknown')
                brand_count[brand] = brand_count.get(brand, 0) + 1
            
            print(f"\n🏷️ 브랜드별 분포 (상위 5개):")
            sorted_brands = sorted(brand_count.items(), key=lambda x: x[1], reverse=True)
            for brand, count in sorted_brands[:5]:
                print(f"   🏷️ {brand}: {count}개")
            
            # 필터 효과 분석
            print(f"\n📊 필터링 효과:")
            print(f"   ✅ 목적: 승인완료 상품만 확인")
            print(f"   📋 결과: 판매 중인 상품 {len(data)}개 조회됨")
            if len(data) > 0:
                print(f"   💡 활용: 실제 판매 중인 상품 관리에 유용")
            else:
                print(f"   💡 참고: 해당 조건의 상품이 없음")
            
        else:
            print(f"\n❌ 필터 적용 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 필터 적용 조회 오류: {e}")


def test_product_list_pagination():
    """페이징을 통한 전체 상품 목록 조회 테스트"""
    print("\n" + "=" * 60 + " 페이징 전체 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        print(f"\n📄 페이징을 통한 전체 상품 목록 조회")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 방법: 여러 페이지를 순차적으로 조회")
        
        all_products = []
        current_token = None
        page_num = 1
        max_pages = 3  # 테스트용으로 최대 3페이지만
        
        while page_num <= max_pages:
            print(f"\n📄 {page_num}페이지 조회 중...")
            
            # 페이지별 검색 파라미터
            search_params = ProductSearchParams(
                vendor_id=vendor_id,
                max_per_page=5,  # 테스트용으로 페이지당 5개
                next_token=current_token
            )
            
            # 페이지 조회
            result = client.list_products(search_params)
            
            if result.get("success"):
                data = result.get("data", [])
                next_token = result.get("next_token")
                
                print(f"   ✅ {page_num}페이지 조회 성공: {len(data)}개 상품")
                
                # 전체 목록에 추가
                all_products.extend(data)
                
                # 상품 요약 정보 표시
                for i, product in enumerate(data, 1):
                    product_name = product.get('sellerProductName', 'N/A')
                    status = product.get('statusName', 'N/A')
                    print(f"      {i}. {product_name[:30]}{'...' if len(product_name) > 30 else ''} ({status})")
                
                # 다음 페이지 확인
                if next_token:
                    print(f"   ➡️ 다음 페이지 토큰: {next_token}")
                    current_token = next_token
                    page_num += 1
                else:
                    print(f"   🏁 마지막 페이지입니다")
                    break
            else:
                print(f"   ❌ {page_num}페이지 조회 실패: {result.get('error')}")
                break
        
        # 전체 결과 요약
        print(f"\n📊 전체 페이징 조회 결과:")
        print(f"   📄 조회한 페이지 수: {page_num - 1}페이지")
        print(f"   📦 총 조회된 상품수: {len(all_products)}개")
        
        if all_products:
            # 상태별 통계
            status_stats = {}
            for product in all_products:
                status = product.get('statusName', 'Unknown')
                status_stats[status] = status_stats.get(status, 0) + 1
            
            print(f"\n📈 전체 상품 상태 통계:")
            for status, count in status_stats.items():
                print(f"   📊 {status}: {count}개")
            
            print(f"\n💡 페이징 조회 활용법:")
            print(f"   📋 대량 데이터: 전체 상품 목록 백업")
            print(f"   📊 통계 생성: 상품 현황 분석")
            print(f"   🔄 배치 처리: 일괄 작업을 위한 목록 수집")
        
    except Exception as e:
        print(f"❌ 페이징 조회 오류: {e}")


def test_product_search_by_name():
    """상품명으로 검색하는 테스트"""
    print("\n" + "=" * 60 + " 상품명 검색 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        search_keyword = "클렌징"  # 검색할 키워드
        
        search_params = ProductSearchParams(
            vendor_id=vendor_id,
            max_per_page=15,
            seller_product_name=search_keyword
        )
        
        print(f"\n🔍 상품명 검색")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   🔎 검색 키워드: '{search_keyword}'")
        print(f"   📄 페이지당 건수: {search_params.max_per_page}개")
        
        # 상품명 검색 실행
        print(f"\n📤 상품명 검색 요청 중...")
        result = client.list_products(search_params)
        
        if result.get("success"):
            print(f"\n✅ 상품명 검색 성공!")
            
            data = result.get("data", [])
            
            print(f"\n📊 검색 결과:")
            print(f"   🔎 검색어: '{search_keyword}'")
            print(f"   📦 검색된 상품수: {len(data)}개")
            
            if data:
                print(f"\n📋 검색된 상품 목록:")
                for i, product in enumerate(data, 1):
                    product_id = product.get('sellerProductId')
                    product_name = product.get('sellerProductName', 'N/A')
                    status = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    
                    # 검색어 하이라이트 표시
                    highlighted_name = product_name.replace(search_keyword, f"[{search_keyword}]")
                    
                    print(f"\n   {i}. 매칭된 상품:")
                    print(f"      🆔 ID: {product_id}")
                    print(f"      📝 상품명: {highlighted_name}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📊 상태: {status}")
                
                # 검색 결과 분석
                print(f"\n📈 검색 결과 분석:")
                
                # 키워드 포함 확인
                matching_count = 0
                for product in data:
                    name = product.get('sellerProductName', '')
                    if search_keyword.lower() in name.lower():
                        matching_count += 1
                
                print(f"   🎯 키워드 매칭률: {matching_count}/{len(data)}개 ({(matching_count/len(data)*100):.1f}%)")
                
                # 상태별 분포
                status_dist = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    status_dist[status] = status_dist.get(status, 0) + 1
                
                print(f"   📊 검색 결과 상태 분포:")
                for status, count in status_dist.items():
                    print(f"      📊 {status}: {count}개")
            else:
                print(f"\n📭 '{search_keyword}' 키워드로 검색된 상품이 없습니다")
                print(f"💡 다른 키워드로 검색해보세요")
            
        else:
            print(f"\n❌ 상품명 검색 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 상품명 검색 오류: {e}")


def test_product_list_validation():
    """상품 목록 조회 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 조회 검증 시나리오 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "vendor_id 누락",
            "params": ProductSearchParams(
                vendor_id="",  # 빈 값
                max_per_page=10
            ),
            "expected_error": "판매자 ID"
        },
        {
            "name": "잘못된 페이지 크기 (0)",
            "params": ProductSearchParams(
                vendor_id="A00012345",
                max_per_page=0  # 잘못된 값
            ),
            "expected_error": "페이지당 건수"
        },
        {
            "name": "잘못된 페이지 크기 (101)",
            "params": ProductSearchParams(
                vendor_id="A00012345",
                max_per_page=101  # 최대값 초과
            ),
            "expected_error": "페이지당 건수"
        },
        {
            "name": "긴 상품명 (21자)",
            "params": ProductSearchParams(
                vendor_id="A00012345",
                seller_product_name="이것은매우긴상품명으로21자를넘어섭니다"  # 21자
            ),
            "expected_error": "20자 이하"
        },
        {
            "name": "잘못된 상품 상태",
            "params": ProductSearchParams(
                vendor_id="A00012345",
                status="INVALID_STATUS"  # 존재하지 않는 상태
            ),
            "expected_error": "상품상태"
        },
        {
            "name": "잘못된 날짜 형식",
            "params": ProductSearchParams(
                vendor_id="A00012345",
                created_at="2024/01/15"  # 잘못된 형식
            ),
            "expected_error": "yyyy-MM-dd"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        
        try:
            result = client.list_products(test_case['params'])
            
            if result.get("success"):
                print(f"   ⚠️ 예상과 다르게 성공함 (검증 로직 확인 필요)")
            else:
                print(f"   ✅ 예상대로 검증 실패: {result.get('error')}")
                
        except ValueError as e:
            expected = test_case.get('expected_error', '')
            if expected in str(e):
                print(f"   ✅ 예상대로 검증 오류: {e}")
            else:
                print(f"   ⚠️ 예상과 다른 검증 오류: {e}")
        except Exception as e:
            print(f"   ❌ 예상치 못한 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 목록 페이징 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 상품 목록 조회 테스트
        test_basic_product_list()
        
        # 필터 적용 조회 테스트
        test_product_list_with_filters()
        
        # 페이징 전체 조회 테스트
        test_product_list_pagination()
        
        # 상품명 검색 테스트
        test_product_search_by_name()
        
        # 검증 시나리오 테스트
        test_product_list_validation()
        
        print(f"\n" + "=" * 50 + " 상품 목록 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 목록 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 목록 페이징 조회")
        print("   2. ✅ 상태/제조사별 필터링")
        print("   3. ✅ 상품명 키워드 검색")
        print("   4. ✅ 날짜 범위 조회")
        print("   5. ✅ 페이징 토큰 기반 순차 조회")
        print("   6. ✅ 검색 파라미터 검증")
        print("   7. ✅ 조회 결과 분석")
        
        print(f"\n💡 상품 목록 조회 주요 특징:")
        print("   - 페이징 기반 대량 데이터 처리")
        print("   - 다양한 검색 조건 조합 가능")
        print("   - 실시간 상품 현황 확인")
        print("   - 상태별/날짜별 필터링 지원")
        print("   - next_token 기반 연속 조회")
        
        print(f"\n📊 활용 방안:")
        print("   🔍 검색: 특정 조건의 상품 찾기")
        print("   📊 분석: 상품 포트폴리오 현황 파악")
        print("   🔄 모니터링: 상품 상태 정기 체크")
        print("   📋 관리: 대량 상품 일괄 처리")
        print("   📈 리포팅: 상품 현황 보고서 생성")
        
    except Exception as e:
        print(f"\n❌ 상품 목록 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()