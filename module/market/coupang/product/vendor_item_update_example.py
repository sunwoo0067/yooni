#!/usr/bin/env python3
"""
쿠팡 벤더아이템 수량/가격/판매상태 변경 API 사용 예제
벤더아이템의 재고, 가격, 판매상태, 할인율 기준가격을 변경하는 방법을 보여줍니다
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
    validate_vendor_item_id,
    validate_quantity,
    validate_price,
    validate_original_price
)


def test_vendor_item_quantity_update():
    """벤더아이템 재고수량 변경 테스트"""
    print("=" * 60 + " 벤더아이템 재고수량 변경 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 예시 벤더아이템ID와 재고수량 (실제 값으로 변경 필요)
        vendor_item_id = 3000000000  # 실제 벤더아이템ID로 변경 필요
        new_quantity = 100  # 새로운 재고수량
        
        print(f"\n📋 벤더아이템 재고수량 변경 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   📦 새로운 재고수량: {new_quantity}개")
        print(f"   🔗 API: PUT /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/quantities/{new_quantity}")
        
        # 재고수량 변경 실행
        print(f"\n📤 재고수량 변경 요청 중...")
        result = client.update_vendor_item_quantity(vendor_item_id, new_quantity)
        
        if result.get("success"):
            print(f"\n✅ 벤더아이템 재고수량 변경 성공!")
            
            vendor_item_id_result = result.get("vendor_item_id")
            quantity_result = result.get("quantity")
            message = result.get("message", "")
            
            print(f"\n📊 변경 결과:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   📦 변경된 재고수량: {quantity_result}개")
            print(f"   📝 메시지: {message}")
            
            print(f"\n💡 재고수량 변경 후 권장사항:")
            print("   1. 📈 재고 모니터링 시스템에서 변경 내역 확인")
            print("   2. 🔄 주문 처리 시스템에 변경사항 반영 확인")
            print("   3. 📊 판매 현황 대시보드에서 재고 수준 점검")
            
            if new_quantity == 0:
                print("   ⚠️  재고가 0개로 설정되어 자동으로 품절 처리됩니다")
            elif new_quantity <= 10:
                print("   📢 재고가 10개 이하로 설정되어 추가 보충을 권장합니다")
            
        else:
            print(f"\n❌ 벤더아이템 재고수량 변경 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류별 해결 방법
            error_message = result.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if '유효하지 않은 재고수량' in error_message:
                print("   1. 재고수량 값 확인 (0 이상의 정수)")
                print("   2. 최대 허용 재고수량 확인")
            elif '삭제된 상품' in error_message:
                print("   1. 벤더아이템ID가 삭제되었는지 확인")
                print("   2. 활성화된 다른 벤더아이템ID 사용")
            else:
                print("   1. 벤더아이템ID 확인")
                print("   2. 네트워크 연결 상태 확인")
                print("   3. 잠시 후 재시도")
            
    except Exception as e:
        print(f"❌ 벤더아이템 재고수량 변경 오류: {e}")
        import traceback
        traceback.print_exc()


def test_vendor_item_price_update():
    """벤더아이템 가격 변경 테스트"""
    print("\n" + "=" * 60 + " 벤더아이템 가격 변경 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 벤더아이템ID와 가격 (실제 값으로 변경 필요)
        vendor_item_id = 3000000000
        new_price = 29900  # 새로운 가격 (10원 단위)
        force_update = False  # 가격 변경 비율 제한 여부
        
        print(f"\n📋 벤더아이템 가격 변경 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   💰 새로운 가격: {new_price:,}원")
        print(f"   🔧 강제 변경: {'예' if force_update else '아니오'}")
        
        # 가격 변경 실행
        print(f"\n📤 가격 변경 요청 중...")
        result = client.update_vendor_item_price(vendor_item_id, new_price, force_update)
        
        if result.get("success"):
            print(f"\n✅ 벤더아이템 가격 변경 성공!")
            
            vendor_item_id_result = result.get("vendor_item_id")
            price_result = result.get("price")
            force_update_result = result.get("force_sale_price_update")
            message = result.get("message", "")
            
            print(f"\n📊 변경 결과:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   💰 변경된 가격: {price_result:,}원")
            print(f"   🔧 강제 변경 사용: {'예' if force_update_result else '아니오'}")
            print(f"   📝 메시지: {message}")
            
            print(f"\n💡 가격 변경 후 권장사항:")
            print("   1. 💰 경쟁사 가격 대비 경쟁력 확인")
            print("   2. 📈 가격 변경 후 판매량 모니터링")
            print("   3. 💵 수익률 재계산 및 분석")
            print("   4. 🎯 마케팅 전략 재검토")
            
        else:
            print(f"\n❌ 벤더아이템 가격 변경 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류별 해결 방법
            error_message = result.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if '변경이 불가능합니다' in error_message and '50%' in error_message:
                print("   1. forceSalePriceUpdate=true 옵션 사용")
                print("   2. 기존 가격의 50% 인하~100% 인상 범위 내에서 변경")
            elif '10원 단위' in error_message:
                print("   1. 가격을 10원 단위로 설정 (1원 단위 불가)")
                print("   2. 예: 29900원 (가능), 29901원 (불가능)")
            elif '자동생성옵션' in error_message:
                print("   1. 기준 판매자옵션의 가격 변경")
                print("   2. WING에서 직접 변경")
            else:
                print("   1. 벤더아이템ID 확인")
                print("   2. 가격 형식 확인")
                print("   3. 잠시 후 재시도")
        
        # 강제 변경 옵션 테스트
        if not result.get("success") and '50%' in result.get('error', ''):
            print(f"\n🔧 강제 가격 변경 옵션으로 재시도...")
            
            result_force = client.update_vendor_item_price(vendor_item_id, new_price, True)
            
            if result_force.get("success"):
                print(f"✅ 강제 가격 변경 성공!")
                print(f"   💰 변경된 가격: {result_force.get('price'):,}원")
            else:
                print(f"❌ 강제 가격 변경도 실패: {result_force.get('error')}")
            
    except Exception as e:
        print(f"❌ 벤더아이템 가격 변경 오류: {e}")


def test_vendor_item_sales_control():
    """벤더아이템 판매 재개/중지 테스트"""
    print("\n" + "=" * 60 + " 벤더아이템 판매 상태 제어 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 벤더아이템ID (실제 값으로 변경 필요)
        vendor_item_id = 3000000000
        
        # 1. 판매 중지 테스트
        print(f"\n📋 벤더아이템 판매 중지 테스트...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   🔗 API: PUT /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/sales/stop")
        
        print(f"\n📤 판매 중지 요청 중...")
        result_stop = client.stop_vendor_item_sales(vendor_item_id)
        
        if result_stop.get("success"):
            print(f"\n✅ 벤더아이템 판매 중지 성공!")
            print(f"   🆔 벤더아이템ID: {result_stop.get('vendor_item_id')}")
            print(f"   📝 메시지: {result_stop.get('message')}")
            
            print(f"\n💡 판매 중지 후 권장사항:")
            print("   1. 🔍 중지 사유 문서화")
            print("   2. 📊 판매 중지 영향 분석")
            print("   3. 🎯 재개 시점 계획 수립")
            print("   4. 📢 고객 안내 메시지 준비")
            
        else:
            print(f"\n❌ 벤더아이템 판매 중지 실패:")
            print(f"   🚨 오류: {result_stop.get('error')}")
            
        # 2. 판매 재개 테스트
        print(f"\n📋 벤더아이템 판매 재개 테스트...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   🔗 API: PUT /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/sales/resume")
        
        print(f"\n📤 판매 재개 요청 중...")
        result_resume = client.resume_vendor_item_sales(vendor_item_id)
        
        if result_resume.get("success"):
            print(f"\n✅ 벤더아이템 판매 재개 성공!")
            print(f"   🆔 벤더아이템ID: {result_resume.get('vendor_item_id')}")
            print(f"   📝 메시지: {result_resume.get('message')}")
            
            print(f"\n💡 판매 재개 후 권장사항:")
            print("   1. 📦 재고 수량 확인")
            print("   2. 💰 가격 경쟁력 점검")
            print("   3. 📈 판매 성과 모니터링")
            print("   4. 🎯 마케팅 활동 재시작")
            
        else:
            print(f"\n❌ 벤더아이템 판매 재개 실패:")
            print(f"   🚨 오류: {result_resume.get('error')}")
            
            # 오류별 해결 방법
            error_message = result_resume.get('error', '').lower()
            if '모니터링에 의해' in error_message:
                print(f"\n💡 해결 방법:")
                print("   1. 쿠팡 판매자콜센터 문의")
                print("   2. 온라인 문의를 통한 해결")
                print("   3. 모니터링 사유 확인 및 개선")
        
        # 판매 상태 제어 결과 요약
        print(f"\n📊 판매 상태 제어 결과 요약:")
        print(f"   ⏸️  판매 중지: {'성공' if result_stop.get('success') else '실패'}")
        print(f"   ▶️  판매 재개: {'성공' if result_resume.get('success') else '실패'}")
        
    except Exception as e:
        print(f"❌ 벤더아이템 판매 상태 제어 오류: {e}")


def test_vendor_item_original_price_update():
    """벤더아이템 할인율 기준가격 변경 테스트"""
    print("\n" + "=" * 60 + " 벤더아이템 할인율 기준가격 변경 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 벤더아이템ID와 할인율 기준가격 (실제 값으로 변경 필요)
        vendor_item_id = 3000000000
        new_original_price = 39900  # 새로운 할인율 기준가격
        
        print(f"\n📋 벤더아이템 할인율 기준가격 변경 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   💎 새로운 할인율 기준가격: {new_original_price:,}원")
        print(f"   🔗 API: PUT /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/original-prices/{new_original_price}")
        
        # 할인율 기준가격 변경 실행
        print(f"\n📤 할인율 기준가격 변경 요청 중...")
        result = client.update_vendor_item_original_price(vendor_item_id, new_original_price)
        
        if result.get("success"):
            print(f"\n✅ 벤더아이템 할인율 기준가격 변경 성공!")
            
            vendor_item_id_result = result.get("vendor_item_id")
            original_price_result = result.get("original_price")
            message = result.get("message", "")
            
            print(f"\n📊 변경 결과:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   💎 변경된 할인율 기준가격: {original_price_result:,}원")
            print(f"   📝 메시지: {message}")
            
            # 할인율 계산 예시 (가정: 현재 판매가격이 29900원인 경우)
            current_sale_price = 29900  # 예시 현재 판매가격
            if new_original_price > 0:
                discount_rate = ((new_original_price - current_sale_price) / new_original_price) * 100
                print(f"\n📈 할인율 분석 (가정: 현재 판매가 {current_sale_price:,}원):")
                print(f"   💎 할인율 기준가: {new_original_price:,}원")
                print(f"   💰 현재 판매가: {current_sale_price:,}원")
                print(f"   📊 할인율: {discount_rate:.1f}%")
                
                if discount_rate > 0:
                    print(f"   ✅ 할인 혜택 제공 중")
                else:
                    print(f"   📢 할인 없음 (기준가 ≤ 판매가)")
            
            print(f"\n💡 할인율 기준가격 변경 후 권장사항:")
            print("   1. 📊 할인율 표시 확인")
            print("   2. 🎯 마케팅 메시지 업데이트")
            print("   3. 💰 가격 경쟁력 재분석")
            print("   4. 📈 고객 반응 모니터링")
            
        else:
            print(f"\n❌ 벤더아이템 할인율 기준가격 변경 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류별 해결 방법
            error_message = result.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if '10원 단위' in error_message:
                print("   1. 할인율 기준가격을 10원 단위로 설정")
                print("   2. 예: 39900원 (가능), 39901원 (불가능)")
            elif 'invalid vendoritemid' in error_message:
                print("   1. 벤더아이템ID 확인")
                print("   2. 활성화된 아이템인지 확인")
            else:
                print("   1. 기준가격 형식 확인")
                print("   2. 네트워크 연결 상태 확인")
                print("   3. 잠시 후 재시도")
            
    except Exception as e:
        print(f"❌ 벤더아이템 할인율 기준가격 변경 오류: {e}")


def test_validation_scenarios():
    """벤더아이템 변경 API 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 벤더아이템 변경 API 검증 테스트 " + "=" * 60)
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 재고수량 검증 테스트
    print(f"\n📦 재고수량 검증 테스트:")
    
    test_quantities = [
        (-1, "음수 재고"),
        (1000000, "최대값 초과"),
        ("abc", "문자열"),
        (50, "정상값")
    ]
    
    for quantity, description in test_quantities:
        try:
            validate_quantity(quantity)
            print(f"   ✅ {description} ({quantity}): 검증 통과")
        except ValueError as e:
            print(f"   ❌ {description} ({quantity}): {e}")
        except Exception as e:
            print(f"   ⚠️  {description} ({quantity}): 예상치 못한 오류 - {e}")
    
    # 가격 검증 테스트
    print(f"\n💰 가격 검증 테스트:")
    
    test_prices = [
        (29901, "1원 단위"),
        (29900, "10원 단위"),
        (-100, "음수 가격"),
        (200000000, "최대값 초과"),
        (15000, "정상값")
    ]
    
    for price, description in test_prices:
        try:
            validate_price(price)
            print(f"   ✅ {description} ({price:,}원): 검증 통과")
        except ValueError as e:
            print(f"   ❌ {description} ({price:,}원): {e}")
        except Exception as e:
            print(f"   ⚠️  {description} ({price:,}원): 예상치 못한 오류 - {e}")
    
    # 할인율 기준가격 검증 테스트
    print(f"\n💎 할인율 기준가격 검증 테스트:")
    
    test_original_prices = [
        (0, "0원"),
        (9999, "1원 단위"),
        (10000, "10원 단위"),
        (-50, "음수"),
        (25000, "정상값")
    ]
    
    for original_price, description in test_original_prices:
        try:
            validate_original_price(original_price)
            print(f"   ✅ {description} ({original_price:,}원): 검증 통과")
        except ValueError as e:
            print(f"   ❌ {description} ({original_price:,}원): {e}")
        except Exception as e:
            print(f"   ⚠️  {description} ({original_price:,}원): 예상치 못한 오류 - {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 벤더아이템 수량/가격/판매상태 변경 API 예제 시작")
    print("=" * 120)
    
    try:
        # 재고수량 변경 테스트
        test_vendor_item_quantity_update()
        
        # 가격 변경 테스트
        test_vendor_item_price_update()
        
        # 판매 상태 제어 테스트
        test_vendor_item_sales_control()
        
        # 할인율 기준가격 변경 테스트
        test_vendor_item_original_price_update()
        
        # 검증 시나리오 테스트
        test_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 벤더아이템 변경 API 예제 완료 " + "=" * 50)
        print("✅ 모든 벤더아이템 변경 API 예제가 완료되었습니다!")
        
        print(f"\n🎉 구현된 API들:")
        print("   1. ✅ 재고수량 변경 (PUT /quantities/{quantity})")
        print("   2. ✅ 가격 변경 (PUT /prices/{price})")
        print("   3. ✅ 판매 재개 (PUT /sales/resume)")
        print("   4. ✅ 판매 중지 (PUT /sales/stop)")
        print("   5. ✅ 할인율 기준가격 변경 (PUT /original-prices/{originalPrice})")
        
        print(f"\n💡 벤더아이템 변경 API 주요 특징:")
        print("   - 벤더아이템ID 기반 정확한 타겟팅")
        print("   - 실시간 변경 및 즉시 반영")
        print("   - 가격 변경 비율 제한 및 강제 변경 옵션")
        print("   - 판매 상태 세밀한 제어")
        print("   - 할인율 표시를 위한 기준가격 설정")
        
        print(f"\n📊 활용 방안:")
        print("   📦 재고 관리: 실시간 재고 조정")
        print("   💰 가격 관리: 동적 가격 조정")
        print("   🔄 판매 제어: 전략적 판매 시작/중지")
        print("   🎯 프로모션: 할인율 기준가격 활용")
        print("   📈 성과 최적화: 데이터 기반 자동 조정")
        
    except Exception as e:
        print(f"\n❌ 벤더아이템 변경 API 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()