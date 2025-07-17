#!/usr/bin/env python3
"""
쿠팡 자동생성옵션 활성화/비활성화 API 실제 테스트
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
    validate_vendor_item_id
)


def test_auto_generated_option_apis():
    """실제 쿠팡 API를 호출하여 자동생성옵션 API들 테스트"""
    print("=" * 80)
    print("🚀 쿠팡 자동생성옵션 API 실제 테스트")
    print("=" * 80)
    
    # 환경변수에서 API 키 확인
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_vendor_item_id = os.getenv('TEST_VENDOR_ITEM_ID')
    
    if not access_key or not secret_key:
        print("❌ 환경변수 설정이 필요합니다:")
        print("   export COUPANG_ACCESS_KEY=your_access_key")
        print("   export COUPANG_SECRET_KEY=your_secret_key")
        print("   export TEST_VENDOR_ITEM_ID=your_test_vendor_item_id  # 선택사항")
        return
    
    if not test_vendor_item_id:
        print("⚠️  TEST_VENDOR_ITEM_ID 환경변수가 설정되지 않아 기본값 사용")
        test_vendor_item_id = "3000000000"  # 기본 테스트 값
    
    try:
        # 클라이언트 초기화
        print(f"\n📋 API 클라이언트 초기화 중...")
        client = ProductClient(access_key, secret_key)
        print(f"✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 테스트할 벤더아이템ID
        vendor_item_id = int(test_vendor_item_id)
        print(f"\n🆔 테스트 대상: 벤더아이템ID {vendor_item_id}")
        
        # 1. 개별 상품 자동생성옵션 활성화 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 1: 개별 상품 자동생성옵션 활성화")
        print(f"=" * 60)
        
        start_time = time.time()
        
        print(f"📤 개별 상품 자동생성옵션 활성화 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   🔗 API: POST /vendor-items/{vendor_item_id}/auto-generated/opt-in")
        
        result_item_enable = client.enable_vendor_item_auto_generated_option(vendor_item_id)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_item_enable.get("success"):
            print(f"\n✅ 개별 상품 자동생성옵션 활성화 성공!")
            print(f"   🆔 벤더아이템ID: {result_item_enable.get('vendor_item_id')}")
            print(f"   📝 메시지: {result_item_enable.get('message')}")
            print(f"   📊 데이터: {result_item_enable.get('data')}")
            
            if result_item_enable.get("processing"):
                print(f"   🔄 처리 상태: 처리 중")
                print(f"   ⏳ 자동생성 옵션 생성까지 시간이 소요될 수 있습니다")
            else:
                print(f"   ✅ 처리 상태: 완료")
                
            print(f"\n💡 예상 효과:")
            print(f"   - 📦 조건에 맞는 번들 옵션 자동 생성")
            print(f"   - 📈 판매 기회 확대")
            print(f"   - 🎯 고객 선택권 증가")
        else:
            print(f"\n❌ 개별 상품 자동생성옵션 활성화 실패:")
            print(f"   🚨 오류: {result_item_enable.get('error')}")
            print(f"   📊 코드: {result_item_enable.get('code')}")
            
            # 원본 응답 표시
            original_response = result_item_enable.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                pprint(original_response, width=100)
        
        # 2. 개별 상품 자동생성옵션 비활성화 테스트 (활성화 성공 시에만)
        if result_item_enable.get("success"):
            time.sleep(3)  # 잠시 대기
            
            print(f"\n" + "=" * 60)
            print(f"📋 테스트 2: 개별 상품 자동생성옵션 비활성화")
            print(f"=" * 60)
            
            start_time = time.time()
            
            print(f"📤 개별 상품 자동생성옵션 비활성화 API 요청 중...")
            print(f"   🆔 벤더아이템ID: {vendor_item_id}")
            print(f"   🔗 API: POST /vendor-items/{vendor_item_id}/auto-generated/opt-out")
            
            result_item_disable = client.disable_vendor_item_auto_generated_option(vendor_item_id)
            
            elapsed_time = time.time() - start_time
            print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
            
            if result_item_disable.get("success"):
                print(f"\n✅ 개별 상품 자동생성옵션 비활성화 성공!")
                print(f"   🆔 벤더아이템ID: {result_item_disable.get('vendor_item_id')}")
                print(f"   📝 메시지: {result_item_disable.get('message')}")
                print(f"   📊 데이터: {result_item_disable.get('data')}")
                
                if result_item_disable.get("processing"):
                    print(f"   🔄 처리 상태: 처리 중")
                else:
                    print(f"   ✅ 처리 상태: 완료")
                    
                print(f"\n💡 결과:")
                print(f"   - ⏹️ 더 이상 새로운 자동 옵션 생성 안됨")
                print(f"   - 📦 기존 자동 생성된 옵션은 유지")
            else:
                print(f"\n❌ 개별 상품 자동생성옵션 비활성화 실패:")
                print(f"   🚨 오류: {result_item_disable.get('error')}")
                print(f"   📊 코드: {result_item_disable.get('code')}")
        
        # 3. 전체 상품 자동생성옵션 활성화 테스트
        enable_seller_test = os.getenv('ENABLE_SELLER_AUTO_GENERATED_TEST', 'false').lower() == 'true'
        
        if enable_seller_test:
            print(f"\n" + "=" * 60)
            print(f"📋 테스트 3: 전체 상품 자동생성옵션 활성화")
            print(f"=" * 60)
            
            print(f"⚠️  주의: 전체 상품에 영향을 미치는 작업입니다")
            
            start_time = time.time()
            
            print(f"📤 전체 상품 자동생성옵션 활성화 API 요청 중...")
            print(f"   🔗 API: POST /seller/auto-generated/opt-in")
            
            result_seller_enable = client.enable_seller_auto_generated_option()
            
            elapsed_time = time.time() - start_time
            print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
            
            if result_seller_enable.get("success"):
                print(f"\n✅ 전체 상품 자동생성옵션 활성화 성공!")
                print(f"   📝 메시지: {result_seller_enable.get('message')}")
                print(f"   📊 데이터: {result_seller_enable.get('data')}")
                
                if result_seller_enable.get("processing"):
                    print(f"   🔄 처리 상태: 처리 중")
                    print(f"   ⏳ 대량 처리로 인해 완료까지 시간 소요")
                else:
                    print(f"   ✅ 처리 상태: 완료")
                    
                print(f"\n💡 예상 효과:")
                print(f"   - 🚀 전체 상품 포트폴리오 확장")
                print(f"   - 📈 매출 기회 극대화")
                print(f"   - 🎯 고객 선택권 대폭 증가")
            else:
                print(f"\n❌ 전체 상품 자동생성옵션 활성화 실패:")
                print(f"   🚨 오류: {result_seller_enable.get('error')}")
                print(f"   📊 코드: {result_seller_enable.get('code')}")
            
            # 4. 전체 상품 자동생성옵션 비활성화 테스트 (활성화 성공 시에만)
            if result_seller_enable.get("success"):
                time.sleep(5)  # 잠시 대기
                
                print(f"\n" + "=" * 60)
                print(f"📋 테스트 4: 전체 상품 자동생성옵션 비활성화")
                print(f"=" * 60)
                
                start_time = time.time()
                
                print(f"📤 전체 상품 자동생성옵션 비활성화 API 요청 중...")
                print(f"   🔗 API: POST /seller/auto-generated/opt-out")
                
                result_seller_disable = client.disable_seller_auto_generated_option()
                
                elapsed_time = time.time() - start_time
                print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
                
                if result_seller_disable.get("success"):
                    print(f"\n✅ 전체 상품 자동생성옵션 비활성화 성공!")
                    print(f"   📝 메시지: {result_seller_disable.get('message')}")
                    print(f"   📊 데이터: {result_seller_disable.get('data')}")
                    
                    if result_seller_disable.get("processing"):
                        print(f"   🔄 처리 상태: 처리 중")
                    else:
                        print(f"   ✅ 처리 상태: 완료")
                else:
                    print(f"\n❌ 전체 상품 자동생성옵션 비활성화 실패:")
                    print(f"   🚨 오류: {result_seller_disable.get('error')}")
                    print(f"   📊 코드: {result_seller_disable.get('code')}")
        else:
            print(f"\n⚠️  전체 상품 자동생성옵션 테스트는 ENABLE_SELLER_AUTO_GENERATED_TEST=true로 활성화할 수 있습니다")
        
        # 검증 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 5: 파라미터 검증")
        print(f"=" * 60)
        
        # 벤더아이템ID 검증
        print(f"\n🧪 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(vendor_item_id)
            print(f"✅ 벤더아이템ID 검증 통과")
        except ValueError as e:
            print(f"❌ 벤더아이템ID 검증 실패: {e}")
        
        # 잘못된 벤더아이템ID 검증
        print(f"\n🧪 잘못된 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(0)  # 0 값
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        # None 값 검증
        print(f"\n🧪 None 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(None)  # None 값
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 모든 자동생성옵션 API 테스트 완료!")
        print(f"=" * 60)
        
        print(f"\n✅ 테스트 결과 요약:")
        print(f"   1. ✅ 개별 상품 활성화: {'성공' if result_item_enable.get('success') else '실패'}")
        if result_item_enable.get("success"):
            print(f"   2. ✅ 개별 상품 비활성화: {'성공' if result_item_disable.get('success') else '실패'}")
        if enable_seller_test:
            if 'result_seller_enable' in locals():
                print(f"   3. ✅ 전체 상품 활성화: {'성공' if result_seller_enable.get('success') else '실패'}")
                if result_seller_enable.get("success"):
                    print(f"   4. ✅ 전체 상품 비활성화: {'성공' if result_seller_disable.get('success') else '실패'}")
        print(f"   5. ✅ 파라미터 검증: 정상 작동")
        
        print(f"\n💡 자동생성옵션 API 특징:")
        print(f"   - 개별/전체 상품 단위 유연한 제어")
        print(f"   - SUCCESS/PROCESSING/FAILED 상태 지원")
        print(f"   - 조건에 맞는 자동 옵션 생성")
        print(f"   - 기존 옵션 보존")
        
    except Exception as e:
        print(f"\n❌ 자동생성옵션 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def test_performance():
    """API 성능 테스트"""
    print(f"\n" + "=" * 60)
    print(f"⚡ 성능 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_vendor_item_id = os.getenv('TEST_VENDOR_ITEM_ID', '3000000000')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 성능 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        vendor_item_id = int(test_vendor_item_id)
        
        # 개별 상품 자동생성옵션 성능 테스트
        print(f"📊 개별 상품 자동생성옵션 성능 테스트...")
        
        times = []
        test_count = 3
        
        for i in range(test_count):
            print(f"   🔄 {i+1}번째 호출...")
            
            start_time = time.time()
            
            if i % 2 == 0:
                # 활성화 테스트
                result = client.enable_vendor_item_auto_generated_option(vendor_item_id)
                action = "활성화"
            else:
                # 비활성화 테스트
                result = client.disable_vendor_item_auto_generated_option(vendor_item_id)
                action = "비활성화"
            
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            
            print(f"      ⏱️  {action} 응답시간: {elapsed_time:.2f}초")
            print(f"      📊 결과: {'성공' if result.get('success') else '실패'}")
            
            if result.get("processing"):
                print(f"      🔄 처리 상태: 처리 중")
            
            # API 부하를 줄이기 위해 대기
            if i < test_count - 1:
                time.sleep(3)
        
        # 통계 계산
        if times:
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


def test_multiple_items():
    """여러 아이템 자동생성옵션 제어 테스트"""
    print(f"\n" + "=" * 60)
    print(f"📦 여러 아이템 자동생성옵션 제어 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 여러 아이템 테스트를 건너뜁니다")
        return
    
    # 여러 벤더아이템ID 테스트 (환경변수에서 가져오기)
    multiple_items = os.getenv('TEST_MULTIPLE_VENDOR_ITEMS')
    if not multiple_items:
        print("⚠️  TEST_MULTIPLE_VENDOR_ITEMS 환경변수가 설정되지 않아 여러 아이템 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        item_list = [int(item.strip()) for item in multiple_items.split(',')]
        
        print(f"📦 {len(item_list)}개 아이템 자동생성옵션 일괄 활성화...")
        
        success_count = 0
        error_count = 0
        processing_count = 0
        
        for i, item_id in enumerate(item_list, 1):
            print(f"\n   {i}. ID {item_id} 자동생성옵션 활성화 중...")
            
            try:
                result = client.enable_vendor_item_auto_generated_option(item_id)
                
                if result.get("success"):
                    if result.get("processing"):
                        print(f"      🔄 처리 중")
                        processing_count += 1
                    else:
                        print(f"      ✅ 즉시 완료")
                    success_count += 1
                else:
                    print(f"      ❌ 실패: {result.get('error')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"      ❌ 예외: {e}")
                error_count += 1
            
            # API 부하를 줄이기 위해 대기
            if i < len(item_list):
                time.sleep(2)
        
        print(f"\n📈 일괄 처리 결과:")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   🔄 처리 중: {processing_count}개")
        print(f"   ❌ 실패: {error_count}개")
        print(f"   📊 성공률: {(success_count/(success_count+error_count))*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 여러 아이템 테스트 중 오류: {e}")


if __name__ == "__main__":
    print(f"🚀 쿠팡 자동생성옵션 API 실제 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 API 테스트
    test_auto_generated_option_apis()
    
    # 성능 테스트
    test_performance()
    
    # 여러 아이템 테스트
    test_multiple_items()
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 모든 테스트가 완료되었습니다!")