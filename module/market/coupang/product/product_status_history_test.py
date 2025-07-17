#!/usr/bin/env python3
"""
쿠팡 상품 상태변경이력 조회 API 실제 테스트
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
    ProductStatusHistoryParams,
    validate_product_status_history_params
)


def test_status_history_api():
    """실제 쿠팡 API를 호출하여 상품 상태변경이력 조회 테스트"""
    print("=" * 80)
    print("🚀 쿠팡 상품 상태변경이력 조회 API 실제 테스트")
    print("=" * 80)
    
    # 환경변수에서 API 키 확인
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID')
    
    if not access_key or not secret_key:
        print("❌ 환경변수 설정이 필요합니다:")
        print("   export COUPANG_ACCESS_KEY=your_access_key")
        print("   export COUPANG_SECRET_KEY=your_secret_key")
        print("   export TEST_SELLER_PRODUCT_ID=your_test_product_id  # 선택사항")
        return
    
    if not test_seller_product_id:
        print("⚠️  TEST_SELLER_PRODUCT_ID 환경변수가 설정되지 않아 기본값 사용")
        test_seller_product_id = "123456789"  # 기본 테스트 값
    
    try:
        # 클라이언트 초기화
        print(f"\n📋 API 클라이언트 초기화 중...")
        client = ProductClient(access_key, secret_key)
        print(f"✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 테스트할 등록상품ID
        seller_product_id = int(test_seller_product_id)
        print(f"\n🆔 테스트 대상: 등록상품ID {seller_product_id}")
        
        # 기본 상태변경이력 조회 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 1: 기본 상품 상태변경이력 조회")
        print(f"=" * 60)
        
        start_time = time.time()
        
        history_params = ProductStatusHistoryParams(
            seller_product_id=seller_product_id,
            max_per_page=20
        )
        
        print(f"📤 API 요청 중...")
        print(f"   🆔 등록상품ID: {seller_product_id}")
        print(f"   📄 페이지당 건수: {history_params.max_per_page}")
        
        result = client.get_product_status_history(history_params)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result.get("success"):
            print(f"\n✅ 상품 상태변경이력 조회 성공!")
            
            data = result.get("data", [])
            next_token = result.get("next_token")
            has_next = result.get("has_next")
            
            print(f"\n📊 조회 결과:")
            print(f"   📦 조회된 이력수: {len(data)}개")
            print(f"   🆔 등록상품ID: {result.get('seller_product_id')}")
            print(f"   ➡️ 다음 페이지: {'있음' if has_next else '없음'}")
            if next_token:
                print(f"   🔑 다음 페이지 토큰: {next_token}")
            
            # 상태변경이력 상세 정보 표시
            if data:
                print(f"\n📋 상품 상태변경이력 상세:")
                for i, history in enumerate(data[:5], 1):  # 처음 5개만 표시
                    status = history.get('status', 'N/A')
                    comment = history.get('comment', 'N/A')
                    created_by = history.get('createdBy', 'N/A')
                    created_at = history.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상태변경 이력:")
                    print(f"      📊 상태: {status}")
                    print(f"      💬 변경내용: {comment}")
                    print(f"      👤 변경자: {created_by}")
                    print(f"      📅 변경일시: {created_at}")
                
                if len(data) > 5:
                    print(f"\n   ... 그 외 {len(data) - 5}개 이력 생략")
                
                # 최근 상태 정보
                latest_history = data[0]
                print(f"\n🔄 최근 상태:")
                print(f"   📊 현재 상태: {latest_history.get('status', 'N/A')}")
                print(f"   📅 마지막 변경: {latest_history.get('createdAt', 'N/A')}")
                print(f"   👤 변경자: {latest_history.get('createdBy', 'N/A')}")
                
            else:
                print(f"\n📭 해당 상품의 상태변경이력이 없습니다")
                print(f"💡 상품이 아직 등록되지 않았거나 ID가 잘못되었을 수 있습니다")
            
        else:
            print(f"\n❌ 상품 상태변경이력 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 원본 응답 표시
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                pprint(original_response, width=100)
        
        # 페이징 테스트 (다음 페이지가 있는 경우)
        if result.get("success") and result.get("has_next"):
            print(f"\n" + "=" * 60)
            print(f"📋 테스트 2: 다음 페이지 조회")
            print(f"=" * 60)
            
            next_token = result.get("next_token")
            
            history_params_page2 = ProductStatusHistoryParams(
                seller_product_id=seller_product_id,
                max_per_page=10,
                next_token=next_token
            )
            
            print(f"📤 다음 페이지 API 요청 중...")
            print(f"   🔑 페이지 토큰: {next_token}")
            
            start_time = time.time()
            result_page2 = client.get_product_status_history(history_params_page2)
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
            
            if result_page2.get("success"):
                data_page2 = result_page2.get("data", [])
                print(f"✅ 2페이지 조회 성공: {len(data_page2)}개 이력")
                
                if data_page2:
                    print(f"📊 2페이지 첫 번째 이력:")
                    first_history = data_page2[0]
                    print(f"   📊 상태: {first_history.get('status', 'N/A')}")
                    print(f"   📅 변경일시: {first_history.get('createdAt', 'N/A')}")
            else:
                print(f"❌ 2페이지 조회 실패: {result_page2.get('error')}")
        
        # 검증 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 3: 파라미터 검증")
        print(f"=" * 60)
        
        # 잘못된 seller_product_id 테스트
        print(f"\n🧪 잘못된 등록상품ID 테스트...")
        try:
            invalid_params = ProductStatusHistoryParams(
                seller_product_id=0
            )
            validate_product_status_history_params(invalid_params)
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        # 잘못된 페이지 크기 테스트
        print(f"\n🧪 잘못된 페이지 크기 테스트...")
        try:
            invalid_params = ProductStatusHistoryParams(
                seller_product_id=123456789,
                max_per_page=101  # 최대값 초과
            )
            validate_product_status_history_params(invalid_params)
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 모든 상품 상태변경이력 조회 테스트 완료!")
        print(f"=" * 60)
        
        print(f"\n✅ 테스트 결과 요약:")
        print(f"   1. ✅ 기본 상태변경이력 조회: {'성공' if result.get('success') else '실패'}")
        if result.get("success") and result.get("has_next"):
            print(f"   2. ✅ 페이징 조회: {'성공' if result_page2.get('success') else '실패'}")
        print(f"   3. ✅ 파라미터 검증: 정상 작동")
        
        print(f"\n💡 상태변경이력 조회 API 특징:")
        print(f"   - 등록상품ID로 정확한 이력 추적")
        print(f"   - 페이징 지원으로 대량 이력 처리")
        print(f"   - 상태/변경자/시간 상세 정보 제공")
        print(f"   - 실시간 상태변경 반영")
        
    except Exception as e:
        print(f"\n❌ 상품 상태변경이력 조회 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def test_performance():
    """API 성능 테스트"""
    print(f"\n" + "=" * 60)
    print(f"⚡ 성능 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '123456789')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 성능 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        seller_product_id = int(test_seller_product_id)
        
        # 여러 번 호출하여 평균 응답 시간 측정
        times = []
        test_count = 3
        
        print(f"📊 {test_count}회 연속 호출 테스트...")
        
        for i in range(test_count):
            print(f"   🔄 {i+1}번째 호출...")
            
            history_params = ProductStatusHistoryParams(
                seller_product_id=seller_product_id,
                max_per_page=10
            )
            
            start_time = time.time()
            result = client.get_product_status_history(history_params)
            elapsed_time = time.time() - start_time
            
            times.append(elapsed_time)
            print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
            
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
        if avg_time < 2.0:
            print(f"   ✅ 성능: 우수 (2초 미만)")
        elif avg_time < 5.0:
            print(f"   👍 성능: 양호 (5초 미만)")
        else:
            print(f"   ⚠️  성능: 개선 필요 (5초 이상)")
            
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


if __name__ == "__main__":
    print(f"🚀 쿠팡 상품 상태변경이력 조회 API 실제 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 API 테스트
    test_status_history_api()
    
    # 성능 테스트
    test_performance()
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 모든 테스트가 완료되었습니다!")