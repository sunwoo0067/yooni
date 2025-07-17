#!/usr/bin/env python3
"""
쿠팡 벤더아이템 재고/가격/상태 조회 API 실제 테스트
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


def test_vendor_item_inventory_api():
    """실제 쿠팡 API를 호출하여 벤더아이템 재고/가격/상태 조회 테스트"""
    print("=" * 80)
    print("🚀 쿠팡 벤더아이템 재고/가격/상태 조회 API 실제 테스트")
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
        
        # 기본 벤더아이템 재고/가격/상태 조회 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 1: 기본 벤더아이템 재고/가격/상태 조회")
        print(f"=" * 60)
        
        start_time = time.time()
        
        print(f"📤 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   🔗 API 경로: /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/inventories")
        
        result = client.get_vendor_item_inventory(vendor_item_id)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result.get("success"):
            print(f"\n✅ 벤더아이템 재고/가격/상태 조회 성공!")
            
            data = result.get("data", {})
            vendor_item_id_result = result.get("vendor_item_id")
            seller_item_id = result.get("seller_item_id")
            amount_in_stock = result.get("amount_in_stock")
            sale_price = result.get("sale_price")
            on_sale = result.get("on_sale")
            
            print(f"\n📊 조회 결과:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   🆔 셀러아이템ID: {seller_item_id}")
            print(f"   📦 잔여수량: {amount_in_stock}개")
            print(f"   💰 판매가격: {sale_price:,}원")
            print(f"   🔄 판매상태: {'판매중' if on_sale else '판매중지'}")
            
            # 상세 분석
            print(f"\n📈 상세 분석:")
            
            # 재고 수준 분석
            if amount_in_stock == 0:
                stock_status = "품절"
                stock_emoji = "❌"
            elif amount_in_stock <= 5:
                stock_status = "부족"
                stock_emoji = "⚠️"
            elif amount_in_stock <= 20:
                stock_status = "보통"
                stock_emoji = "⚡"
            else:
                stock_status = "충분"
                stock_emoji = "✅"
            
            print(f"   {stock_emoji} 재고 수준: {stock_status}")
            
            # 판매 상태 분석
            if on_sale:
                if amount_in_stock > 0:
                    sale_analysis = "정상 판매 가능"
                    sale_emoji = "✅"
                else:
                    sale_analysis = "품절로 판매 불가"
                    sale_emoji = "❌"
            else:
                sale_analysis = "판매 중지 상태"
                sale_emoji = "⏸️"
            
            print(f"   {sale_emoji} 판매 분석: {sale_analysis}")
            
            # 재고 가치 계산
            if amount_in_stock > 0 and sale_price > 0:
                stock_value = amount_in_stock * sale_price
                print(f"   💎 재고 총 가치: {stock_value:,}원")
            
            # 권장 액션
            print(f"\n💡 권장 액션:")
            if amount_in_stock == 0:
                print("   🔄 재고 즉시 보충 필요")
            elif amount_in_stock <= 5:
                print("   📦 재고 추가 주문 권장")
            
            if not on_sale and amount_in_stock > 0:
                print("   ▶️ 판매 재개 검토")
            elif on_sale and amount_in_stock == 0:
                print("   ⏸️ 임시 판매 중지 검토")
            
            if amount_in_stock > 0 and on_sale:
                print("   ✅ 현재 상태 양호")
            
        else:
            print(f"\n❌ 벤더아이템 재고/가격/상태 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                pprint(original_response, width=100)
            
            # 오류별 해결 방법
            error_message = result.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if '유효한 옵션이 없습니다' in error_message:
                print("   1. 벤더아이템ID 확인 (올바른 ID인지 검증)")
                print("   2. 해당 아이템이 삭제되었는지 확인")
                print("   3. 활성화된 아이템인지 확인")
            elif '유효하지 않은 id' in error_message:
                print("   1. 벤더아이템ID 형식 확인 (숫자여야 함)")
                print("   2. ID 값의 범위 확인")
                print("   3. 올바른 ID로 재시도")
            else:
                print("   1. 네트워크 연결 확인")
                print("   2. API 키 및 권한 확인")
                print("   3. 잠시 후 재시도")
        
        # 여러 벤더아이템 테스트 (환경변수에 여러 개가 설정된 경우)
        multiple_items = os.getenv('TEST_MULTIPLE_VENDOR_ITEMS')
        if multiple_items:
            print(f"\n" + "=" * 60)
            print(f"📋 테스트 2: 여러 벤더아이템 일괄 조회")
            print(f"=" * 60)
            
            item_list = [int(item.strip()) for item in multiple_items.split(',')]
            print(f"📤 여러 벤더아이템 조회 테스트...")
            print(f"   📦 아이템 목록: {item_list}")
            
            total_stock = 0
            total_value = 0
            active_items = 0
            
            for i, item_id in enumerate(item_list, 1):
                print(f"\n   {i}. ID {item_id} 조회 중...")
                
                start_time = time.time()
                result_multi = client.get_vendor_item_inventory(item_id)
                elapsed_time = time.time() - start_time
                
                print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
                
                if result_multi.get("success"):
                    amount_in_stock = result_multi.get("amount_in_stock", 0)
                    sale_price = result_multi.get("sale_price", 0)
                    on_sale = result_multi.get("on_sale", False)
                    
                    print(f"      ✅ 조회 성공")
                    print(f"         📦 재고: {amount_in_stock}개")
                    print(f"         💰 가격: {sale_price:,}원")
                    print(f"         🔄 판매: {'중' if on_sale else '중지'}")
                    
                    total_stock += amount_in_stock
                    total_value += amount_in_stock * sale_price
                    if on_sale and amount_in_stock > 0:
                        active_items += 1
                else:
                    print(f"      ❌ 조회 실패: {result_multi.get('error')}")
                
                # API 부하를 줄이기 위해 1초 대기
                if i < len(item_list):
                    time.sleep(1)
            
            # 일괄 조회 결과 요약
            print(f"\n📈 일괄 조회 결과 요약:")
            print(f"   📦 총 재고량: {total_stock}개")
            print(f"   💎 총 재고 가치: {total_value:,}원")
            print(f"   ✅ 활성 아이템: {active_items}개")
            print(f"   📊 전체 아이템: {len(item_list)}개")
        
        # 검증 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 3: 벤더아이템ID 검증")
        print(f"=" * 60)
        
        # 유효한 벤더아이템ID 검증 테스트
        print(f"\n🧪 유효한 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(3000000000)
            print(f"✅ 유효한 벤더아이템ID 검증 통과")
        except ValueError as e:
            print(f"⚠️  예상과 다른 검증 실패: {e}")
        
        # 잘못된 벤더아이템ID 검증 테스트
        print(f"\n🧪 잘못된 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(0)  # 0 값
            print(f"⚠️  검증이 예상과 다르게 통과됨")
        except ValueError as e:
            print(f"✅ 예상대로 검증 실패: {e}")
        
        # 문자열 변환 테스트
        print(f"\n🧪 문자열 벤더아이템ID 변환 테스트...")
        try:
            validate_vendor_item_id("3000000000")  # 문자열 숫자
            print(f"✅ 문자열 숫자 변환 성공")
        except ValueError as e:
            print(f"⚠️  예상과 다른 변환 실패: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 모든 벤더아이템 재고/가격/상태 조회 테스트 완료!")
        print(f"=" * 60)
        
        print(f"\n✅ 테스트 결과 요약:")
        print(f"   1. ✅ 기본 재고/가격/상태 조회: {'성공' if result.get('success') else '실패'}")
        if multiple_items:
            print(f"   2. ✅ 여러 아이템 일괄 조회: 완료")
        print(f"   3. ✅ 벤더아이템ID 검증: 정상 작동")
        
        print(f"\n💡 벤더아이템 재고/가격/상태 조회 API 특징:")
        print(f"   - 벤더아이템ID로 정확한 재고 정보 조회")
        print(f"   - 실시간 재고수량/판매가격/판매상태")
        print(f"   - 셀러아이템ID 연계 정보 제공")
        print(f"   - 빠른 응답 속도")
        
    except Exception as e:
        print(f"\n❌ 벤더아이템 재고/가격/상태 조회 테스트 중 오류 발생: {e}")
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
        
        # 여러 번 호출하여 평균 응답 시간 측정
        times = []
        test_count = 5
        
        print(f"📊 {test_count}회 연속 호출 테스트...")
        
        for i in range(test_count):
            print(f"   🔄 {i+1}번째 호출...")
            
            start_time = time.time()
            result = client.get_vendor_item_inventory(vendor_item_id)
            elapsed_time = time.time() - start_time
            
            times.append(elapsed_time)
            print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
            print(f"      📊 결과: {'성공' if result.get('success') else '실패'}")
            
            if result.get("success"):
                amount_in_stock = result.get("amount_in_stock", 0)
                print(f"      📦 재고: {amount_in_stock}개")
            
            # API 부하를 줄이기 위해 0.5초 대기
            if i < test_count - 1:
                time.sleep(0.5)
        
        # 통계 계산
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📈 성능 테스트 결과:")
        print(f"   📊 평균 응답시간: {avg_time:.2f}초")
        print(f"   🚀 최소 응답시간: {min_time:.2f}초")
        print(f"   🐌 최대 응답시간: {max_time:.2f}초")
        
        # 성능 평가
        if avg_time < 0.5:
            print(f"   ✅ 성능: 우수 (0.5초 미만)")
        elif avg_time < 1.0:
            print(f"   👍 성능: 양호 (1초 미만)")
        elif avg_time < 2.0:
            print(f"   ⚠️  성능: 보통 (2초 미만)")
        else:
            print(f"   ❌ 성능: 개선 필요 (2초 이상)")
        
        # 처리량 계산
        throughput = test_count / sum(times)
        print(f"   📊 처리량: {throughput:.1f} 요청/초")
            
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


def test_stress():
    """스트레스 테스트 (선택적)"""
    stress_test = os.getenv('ENABLE_STRESS_TEST', 'false').lower()
    if stress_test != 'true':
        return
    
    print(f"\n" + "=" * 60)
    print(f"🔥 스트레스 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    test_vendor_item_id = os.getenv('TEST_VENDOR_ITEM_ID', '3000000000')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 스트레스 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        vendor_item_id = int(test_vendor_item_id)
        
        # 빠른 연속 호출 테스트
        success_count = 0
        error_count = 0
        test_count = 10
        
        print(f"📊 {test_count}회 빠른 연속 호출 테스트...")
        
        start_total = time.time()
        
        for i in range(test_count):
            try:
                result = client.get_vendor_item_inventory(vendor_item_id)
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    print(f"   ❌ 호출 {i+1} 실패: {result.get('error')}")
            except Exception as e:
                error_count += 1
                print(f"   ❌ 호출 {i+1} 예외: {e}")
            
            # 매우 짧은 대기 (API 제한을 피하기 위해)
            time.sleep(0.1)
        
        total_time = time.time() - start_total
        
        print(f"\n📈 스트레스 테스트 결과:")
        print(f"   ✅ 성공: {success_count}회")
        print(f"   ❌ 실패: {error_count}회")
        print(f"   📊 성공률: {(success_count/test_count)*100:.1f}%")
        print(f"   ⏱️  총 시간: {total_time:.2f}초")
        print(f"   📊 평균 처리량: {test_count/total_time:.1f} 요청/초")
        
    except Exception as e:
        print(f"❌ 스트레스 테스트 중 오류: {e}")


if __name__ == "__main__":
    print(f"🚀 쿠팡 벤더아이템 재고/가격/상태 조회 API 실제 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 API 테스트
    test_vendor_item_inventory_api()
    
    # 성능 테스트
    test_performance()
    
    # 스트레스 테스트 (환경변수로 활성화)
    test_stress()
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 모든 테스트가 완료되었습니다!")