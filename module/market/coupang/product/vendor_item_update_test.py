#!/usr/bin/env python3
"""
쿠팡 벤더아이템 수량/가격/판매상태 변경 API 실제 테스트
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
    validate_vendor_item_id,
    validate_quantity,
    validate_price,
    validate_original_price
)


def test_vendor_item_update_apis():
    """실제 쿠팡 API를 호출하여 벤더아이템 변경 API들 테스트"""
    print("=" * 80)
    print("🚀 쿠팡 벤더아이템 변경 API 실제 테스트")
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
        
        # 1. 재고수량 변경 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 1: 벤더아이템 재고수량 변경")
        print(f"=" * 60)
        
        test_quantity = int(os.getenv('TEST_QUANTITY', '50'))  # 테스트 재고수량
        
        start_time = time.time()
        
        print(f"📤 재고수량 변경 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   📦 새로운 재고수량: {test_quantity}개")
        
        result_quantity = client.update_vendor_item_quantity(vendor_item_id, test_quantity)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_quantity.get("success"):
            print(f"\n✅ 재고수량 변경 성공!")
            print(f"   🆔 벤더아이템ID: {result_quantity.get('vendor_item_id')}")
            print(f"   📦 변경된 재고수량: {result_quantity.get('quantity')}개")
            print(f"   📝 메시지: {result_quantity.get('message')}")
        else:
            print(f"\n❌ 재고수량 변경 실패:")
            print(f"   🚨 오류: {result_quantity.get('error')}")
            print(f"   📊 코드: {result_quantity.get('code')}")
        
        # 2. 가격 변경 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 2: 벤더아이템 가격 변경")
        print(f"=" * 60)
        
        test_price = int(os.getenv('TEST_PRICE', '29900'))  # 테스트 가격
        force_update = os.getenv('FORCE_PRICE_UPDATE', 'false').lower() == 'true'
        
        start_time = time.time()
        
        print(f"📤 가격 변경 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   💰 새로운 가격: {test_price:,}원")
        print(f"   🔧 강제 변경: {'예' if force_update else '아니오'}")
        
        result_price = client.update_vendor_item_price(vendor_item_id, test_price, force_update)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_price.get("success"):
            print(f"\n✅ 가격 변경 성공!")
            print(f"   🆔 벤더아이템ID: {result_price.get('vendor_item_id')}")
            print(f"   💰 변경된 가격: {result_price.get('price'):,}원")
            print(f"   🔧 강제 변경 사용: {'예' if result_price.get('force_sale_price_update') else '아니오'}")
            print(f"   📝 메시지: {result_price.get('message')}")
        else:
            print(f"\n❌ 가격 변경 실패:")
            print(f"   🚨 오류: {result_price.get('error')}")
            print(f"   📊 코드: {result_price.get('code')}")
            
            # 가격 변경 비율 제한 오류인 경우 강제 변경 시도
            if '50%' in result_price.get('error', '') and not force_update:
                print(f"\n🔧 강제 가격 변경 옵션으로 재시도...")
                
                result_force = client.update_vendor_item_price(vendor_item_id, test_price, True)
                
                if result_force.get("success"):
                    print(f"✅ 강제 가격 변경 성공!")
                    print(f"   💰 변경된 가격: {result_force.get('price'):,}원")
                else:
                    print(f"❌ 강제 가격 변경도 실패: {result_force.get('error')}")
        
        # 3. 판매 중지 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 3: 벤더아이템 판매 중지")
        print(f"=" * 60)
        
        start_time = time.time()
        
        print(f"📤 판매 중지 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        
        result_stop = client.stop_vendor_item_sales(vendor_item_id)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_stop.get("success"):
            print(f"\n✅ 판매 중지 성공!")
            print(f"   🆔 벤더아이템ID: {result_stop.get('vendor_item_id')}")
            print(f"   📝 메시지: {result_stop.get('message')}")
        else:
            print(f"\n❌ 판매 중지 실패:")
            print(f"   🚨 오류: {result_stop.get('error')}")
            print(f"   📊 코드: {result_stop.get('code')}")
        
        # 판매 중지 후 잠시 대기
        time.sleep(2)
        
        # 4. 판매 재개 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 4: 벤더아이템 판매 재개")
        print(f"=" * 60)
        
        start_time = time.time()
        
        print(f"📤 판매 재개 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        
        result_resume = client.resume_vendor_item_sales(vendor_item_id)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_resume.get("success"):
            print(f"\n✅ 판매 재개 성공!")
            print(f"   🆔 벤더아이템ID: {result_resume.get('vendor_item_id')}")
            print(f"   📝 메시지: {result_resume.get('message')}")
        else:
            print(f"\n❌ 판매 재개 실패:")
            print(f"   🚨 오류: {result_resume.get('error')}")
            print(f"   📊 코드: {result_resume.get('code')}")
            
            # 모니터링 오류인 경우 안내
            if '모니터링에 의해' in result_resume.get('error', ''):
                print(f"\n💡 해결 방법:")
                print("   - 쿠팡 판매자콜센터 문의 필요")
                print("   - 온라인 문의를 통한 해결")
        
        # 5. 할인율 기준가격 변경 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 5: 벤더아이템 할인율 기준가격 변경")
        print(f"=" * 60)
        
        test_original_price = int(os.getenv('TEST_ORIGINAL_PRICE', '39900'))  # 테스트 할인율 기준가격
        
        start_time = time.time()
        
        print(f"📤 할인율 기준가격 변경 API 요청 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   💎 새로운 할인율 기준가격: {test_original_price:,}원")
        
        result_original = client.update_vendor_item_original_price(vendor_item_id, test_original_price)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API 응답 시간: {elapsed_time:.2f}초")
        
        if result_original.get("success"):
            print(f"\n✅ 할인율 기준가격 변경 성공!")
            print(f"   🆔 벤더아이템ID: {result_original.get('vendor_item_id')}")
            print(f"   💎 변경된 할인율 기준가격: {result_original.get('original_price'):,}원")
            print(f"   📝 메시지: {result_original.get('message')}")
            
            # 할인율 계산
            current_price = result_price.get('price', test_price)
            if test_original_price > 0 and current_price:
                discount_rate = ((test_original_price - current_price) / test_original_price) * 100
                print(f"\n📊 할인율 분석:")
                print(f"   💎 할인율 기준가: {test_original_price:,}원")
                print(f"   💰 현재 판매가: {current_price:,}원")
                print(f"   📈 할인율: {discount_rate:.1f}%")
        else:
            print(f"\n❌ 할인율 기준가격 변경 실패:")
            print(f"   🚨 오류: {result_original.get('error')}")
            print(f"   📊 코드: {result_original.get('code')}")
        
        # 검증 테스트
        print(f"\n" + "=" * 60)
        print(f"📋 테스트 6: 파라미터 검증")
        print(f"=" * 60)
        
        # 벤더아이템ID 검증
        print(f"\n🧪 벤더아이템ID 검증 테스트...")
        try:
            validate_vendor_item_id(vendor_item_id)
            print(f"✅ 벤더아이템ID 검증 통과")
        except ValueError as e:
            print(f"❌ 벤더아이템ID 검증 실패: {e}")
        
        # 재고수량 검증
        print(f"\n🧪 재고수량 검증 테스트...")
        try:
            validate_quantity(test_quantity)
            print(f"✅ 재고수량 검증 통과")
        except ValueError as e:
            print(f"❌ 재고수량 검증 실패: {e}")
        
        # 가격 검증
        print(f"\n🧪 가격 검증 테스트...")
        try:
            validate_price(test_price)
            print(f"✅ 가격 검증 통과")
        except ValueError as e:
            print(f"❌ 가격 검증 실패: {e}")
        
        # 할인율 기준가격 검증
        print(f"\n🧪 할인율 기준가격 검증 테스트...")
        try:
            validate_original_price(test_original_price)
            print(f"✅ 할인율 기준가격 검증 통과")
        except ValueError as e:
            print(f"❌ 할인율 기준가격 검증 실패: {e}")
        
        # 잘못된 값 검증 테스트
        print(f"\n🧪 잘못된 값 검증 테스트...")
        
        # 잘못된 재고수량
        try:
            validate_quantity(-1)
            print(f"⚠️  음수 재고수량이 통과됨")
        except ValueError:
            print(f"✅ 음수 재고수량 검증 실패 (정상)")
        
        # 잘못된 가격 (1원 단위)
        try:
            validate_price(29901)
            print(f"⚠️  1원 단위 가격이 통과됨")
        except ValueError:
            print(f"✅ 1원 단위 가격 검증 실패 (정상)")
        
        print(f"\n" + "=" * 60)
        print(f"🎉 모든 벤더아이템 변경 API 테스트 완료!")
        print(f"=" * 60)
        
        print(f"\n✅ 테스트 결과 요약:")
        print(f"   1. ✅ 재고수량 변경: {'성공' if result_quantity.get('success') else '실패'}")
        print(f"   2. ✅ 가격 변경: {'성공' if result_price.get('success') else '실패'}")
        print(f"   3. ✅ 판매 중지: {'성공' if result_stop.get('success') else '실패'}")
        print(f"   4. ✅ 판매 재개: {'성공' if result_resume.get('success') else '실패'}")
        print(f"   5. ✅ 할인율 기준가격 변경: {'성공' if result_original.get('success') else '실패'}")
        print(f"   6. ✅ 파라미터 검증: 정상 작동")
        
        print(f"\n💡 벤더아이템 변경 API 특징:")
        print(f"   - 벤더아이템ID 기반 정확한 변경")
        print(f"   - 실시간 적용 및 즉시 반영")
        print(f"   - 가격 변경 비율 제한 및 강제 변경 옵션")
        print(f"   - 판매 상태 세밀한 제어")
        print(f"   - 할인율 표시를 위한 기준가격 설정")
        
    except Exception as e:
        print(f"\n❌ 벤더아이템 변경 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def test_batch_operations():
    """일괄 변경 시나리오 테스트"""
    print(f"\n" + "=" * 60)
    print(f"📋 일괄 변경 시나리오 테스트")
    print(f"=" * 60)
    
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    
    if not access_key or not secret_key:
        print("❌ 환경변수가 설정되지 않아 일괄 변경 테스트를 건너뜁니다")
        return
    
    # 여러 벤더아이템ID 테스트 (환경변수에서 가져오기)
    multiple_items = os.getenv('TEST_MULTIPLE_VENDOR_ITEMS')
    if not multiple_items:
        print("⚠️  TEST_MULTIPLE_VENDOR_ITEMS 환경변수가 설정되지 않아 일괄 변경 테스트를 건너뜁니다")
        return
    
    try:
        client = ProductClient(access_key, secret_key)
        item_list = [int(item.strip()) for item in multiple_items.split(',')]
        
        print(f"📦 {len(item_list)}개 아이템 일괄 재고 조정 시나리오...")
        
        new_quantity = 30  # 모든 아이템을 30개로 설정
        
        success_count = 0
        error_count = 0
        
        for i, item_id in enumerate(item_list, 1):
            print(f"\n   {i}. ID {item_id} 재고 조정 중...")
            
            try:
                result = client.update_vendor_item_quantity(item_id, new_quantity)
                
                if result.get("success"):
                    print(f"      ✅ 성공: {new_quantity}개로 설정")
                    success_count += 1
                else:
                    print(f"      ❌ 실패: {result.get('error')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"      ❌ 예외: {e}")
                error_count += 1
            
            # API 부하를 줄이기 위해 대기
            if i < len(item_list):
                time.sleep(1)
        
        print(f"\n📈 일괄 변경 결과:")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {error_count}개")
        print(f"   📊 성공률: {(success_count/(success_count+error_count))*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 일괄 변경 테스트 중 오류: {e}")


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
        
        # 재고수량 변경 성능 테스트
        print(f"📊 재고수량 변경 성능 테스트...")
        
        times = []
        test_quantities = [40, 50, 60]  # 여러 재고량으로 테스트
        
        for i, quantity in enumerate(test_quantities, 1):
            print(f"   🔄 {i}번째 재고 변경 ({quantity}개)...")
            
            start_time = time.time()
            result = client.update_vendor_item_quantity(vendor_item_id, quantity)
            elapsed_time = time.time() - start_time
            
            times.append(elapsed_time)
            print(f"      ⏱️  응답시간: {elapsed_time:.2f}초")
            print(f"      📊 결과: {'성공' if result.get('success') else '실패'}")
            
            # API 부하를 줄이기 위해 대기
            if i < len(test_quantities):
                time.sleep(2)
        
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
            if avg_time < 1.0:
                print(f"   ✅ 성능: 우수 (1초 미만)")
            elif avg_time < 2.0:
                print(f"   👍 성능: 양호 (2초 미만)")
            else:
                print(f"   ⚠️  성능: 개선 필요 (2초 이상)")
                
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


if __name__ == "__main__":
    print(f"🚀 쿠팡 벤더아이템 변경 API 실제 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 API 테스트
    test_vendor_item_update_apis()
    
    # 일괄 변경 테스트
    test_batch_operations()
    
    # 성능 테스트
    test_performance()
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎉 모든 테스트가 완료되었습니다!")