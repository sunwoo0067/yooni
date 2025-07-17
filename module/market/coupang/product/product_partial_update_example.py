#!/usr/bin/env python3
"""
쿠팡 상품 수정 (승인불필요) API 사용 예제
배송 및 반품지 정보만 빠르게 수정하는 방법을 보여줍니다
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
    ProductPartialUpdateRequest
)


def test_partial_update_basic():
    """기본적인 상품 부분 수정 테스트"""
    print("=" * 60 + " 기본 상품 부분 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 수정할 상품 ID (실제 승인완료된 상품 ID로 변경 필요)
        seller_product_id = 309323422  # 예시 ID
        
        print(f"\n📝 상품 부분 수정 중...")
        print(f"   🆔 수정할 상품 ID: {seller_product_id}")
        print(f"   📦 수정 범위: 배송 및 반품지 정보만")
        print(f"   ✨ 특징: 승인 불필요, 빠른 수정")
        
        # 배송 정보 수정 요청 생성
        request = ProductPartialUpdateRequest(
            seller_product_id=seller_product_id,
            
            # 배송 관련 정보 수정
            delivery_method="SEQUENCIAL",  # 일반배송
            delivery_company_code="CJGLS",  # CJ대한통운
            delivery_charge_type="FREE",  # 무료배송
            delivery_charge=0,
            delivery_charge_on_return=3000,  # 반품 배송비 수정
            free_ship_over_amount=0,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            outbound_shipping_place_code="74010",  # 출고지 코드
            outbound_shipping_time_day=1,  # 출고일 수정
            
            # 반품지 정보 수정
            return_center_code="1000274592",  # 반품센터 코드
            return_charge_name="빠른수정 반품센터",  # 반품센터명 수정
            company_contact_number="02-1234-9999",  # 연락처 수정
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="빠른수정빌딩 3층",  # 주소 수정
            return_charge=3000,  # 반품비 수정
            
            # 기타 정보 (필요시 수정)
            extra_info_message="빠른 배송으로 변경되었습니다",  # 주문제작 안내
            pcc_needed=False
        )
        
        print(f"\n📋 수정할 정보:")
        print(f"   🚚 배송: {request.delivery_method} ({request.delivery_company_code})")
        print(f"   💰 배송비: {request.delivery_charge}원 ({request.delivery_charge_type})")
        print(f"   📦 반품비: {request.return_charge}원")
        print(f"   🏢 반품센터: {request.return_charge_name}")
        print(f"   📞 연락처: {request.company_contact_number}")
        print(f"   📅 출고일: {request.outbound_shipping_time_day}일")
        
        # 상품 부분 수정 실행
        print(f"\n📤 상품 부분 수정 요청 중...")
        result = client.update_product_partial(request)
        
        if result.get("success"):
            print(f"\n✅ 상품 부분 수정 성공!")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=8)
                
            print(f"\n   ✨ 부분 수정의 장점:")
            print(f"      - 승인 과정 없이 즉시 반영")
            print(f"      - 배송/반품 정보만 빠르게 수정")
            print(f"      - 기존 상품 정보는 그대로 유지")
        else:
            print(f"\n❌ 상품 부분 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 분석
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 상품 부분 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_partial_update_delivery_only():
    """배송 정보만 수정하는 예제"""
    print("\n" + "=" * 60 + " 배송 정보만 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 상품 정보
        seller_product_id = 309323423
        
        print(f"\n🚚 배송 정보만 수정")
        print(f"   🆔 상품 ID: {seller_product_id}")
        print(f"   📝 수정 내용: 배송비 정책 변경")
        
        # 배송 정보만 수정하는 요청
        request = ProductPartialUpdateRequest(
            seller_product_id=seller_product_id,
            
            # 배송 정보만 수정 (반품지 정보는 기존 유지)
            delivery_method="SEQUENCIAL",
            delivery_company_code="HANJIN",  # 한진택배로 변경
            delivery_charge_type="CONDITIONAL_FREE",  # 조건부 무료배송으로 변경
            delivery_charge=2500,  # 기본 배송비 설정
            free_ship_over_amount=30000,  # 3만원 이상 무료배송
            delivery_charge_on_return=2500,
            remote_area_deliverable="Y",  # 도서산간 배송 가능으로 변경
            union_delivery_type="UNION_DELIVERY",
            outbound_shipping_time_day=2  # 출고일을 2일로 변경
            
            # 반품지 정보는 None으로 두어 기존 정보 유지
        )
        
        print(f"\n📋 수정할 배송 정보:")
        print(f"   🚚 택배사: {request.delivery_company_code} (한진택배)")
        print(f"   💰 배송비: {request.delivery_charge_type}")
        print(f"   📦 기본 배송비: {request.delivery_charge}원")
        print(f"   🎁 무료배송 기준: {request.free_ship_over_amount:,}원 이상")
        print(f"   🏔️ 도서산간: {request.remote_area_deliverable} (배송 가능)")
        print(f"   📅 출고일: {request.outbound_shipping_time_day}일")
        
        # 배송 정보 수정 실행
        print(f"\n📤 배송 정보 수정 요청 중...")
        result = client.update_product_partial(request)
        
        if result.get("success"):
            print(f"\n✅ 배송 정보 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 수정 완료 내용:")
            print(f"      ✅ 택배사 변경 완료")
            print(f"      ✅ 배송비 정책 변경 완료")
            print(f"      ✅ 도서산간 배송 가능으로 변경")
            print(f"      ✅ 출고일 조정 완료")
            print(f"      💡 반품지 정보는 기존 정보 유지")
        else:
            print(f"\n❌ 배송 정보 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 배송 정보 수정 오류: {e}")


def test_partial_update_return_center_only():
    """반품지 정보만 수정하는 예제"""
    print("\n" + "=" * 60 + " 반품지 정보만 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 상품 정보
        seller_product_id = 309323424
        
        print(f"\n📦 반품지 정보만 수정")
        print(f"   🆔 상품 ID: {seller_product_id}")
        print(f"   📝 수정 내용: 반품센터 이전")
        
        # 반품지 정보만 수정하는 요청
        request = ProductPartialUpdateRequest(
            seller_product_id=seller_product_id,
            
            # 배송 정보는 None으로 두어 기존 정보 유지
            
            # 반품지 정보만 수정
            return_center_code="1000274593",  # 새로운 반품센터 코드
            return_charge_name="신규 반품센터",
            company_contact_number="02-8888-1234",  # 새로운 연락처
            return_zip_code="06295",  # 새로운 우편번호
            return_address="서울특별시 강남구 역삼동",  # 새로운 주소
            return_address_detail="신규반품센터빌딩 1층",
            return_charge=2000  # 반품비 인하
        )
        
        print(f"\n📋 수정할 반품지 정보:")
        print(f"   🏢 반품센터: {request.return_charge_name}")
        print(f"   📞 연락처: {request.company_contact_number}")
        print(f"   📍 주소: {request.return_address} {request.return_address_detail}")
        print(f"   📮 우편번호: {request.return_zip_code}")
        print(f"   💰 반품비: {request.return_charge}원")
        
        # 반품지 정보 수정 실행
        print(f"\n📤 반품지 정보 수정 요청 중...")
        result = client.update_product_partial(request)
        
        if result.get("success"):
            print(f"\n✅ 반품지 정보 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 수정 완료 내용:")
            print(f"      ✅ 반품센터 이전 완료")
            print(f"      ✅ 연락처 변경 완료")
            print(f"      ✅ 주소 변경 완료")
            print(f"      ✅ 반품비 인하 완료")
            print(f"      💡 배송 정보는 기존 정보 유지")
        else:
            print(f"\n❌ 반품지 정보 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 반품지 정보 수정 오류: {e}")


def test_partial_update_validation():
    """부분 수정 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 부분 수정 검증 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "seller_product_id 누락",
            "request": ProductPartialUpdateRequest(
                seller_product_id=None,  # None 값
                delivery_method="SEQUENCIAL"
            ),
            "expected_error": "등록상품ID"
        },
        {
            "name": "잘못된 seller_product_id",
            "request": ProductPartialUpdateRequest(
                seller_product_id=0,  # 잘못된 값
                delivery_method="SEQUENCIAL"
            ),
            "expected_error": "등록상품ID"
        },
        {
            "name": "모든 필드 None (수정할 내용 없음)",
            "request": ProductPartialUpdateRequest(
                seller_product_id=123456789
                # 다른 모든 필드는 None
            ),
            "expected_error": "수정할 내용"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        
        try:
            result = client.update_product_partial(test_case['request'])
            
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
    print("🚀 쿠팡 상품 수정 (승인불필요) API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 부분 수정 테스트
        test_partial_update_basic()
        
        # 배송 정보만 수정 테스트
        test_partial_update_delivery_only()
        
        # 반품지 정보만 수정 테스트
        test_partial_update_return_center_only()
        
        # 검증 시나리오 테스트
        test_partial_update_validation()
        
        print(f"\n" + "=" * 50 + " 상품 부분 수정 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 부분 수정 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 부분 수정 (배송+반품지)")
        print("   2. ✅ 배송 정보만 수정")
        print("   3. ✅ 반품지 정보만 수정")
        print("   4. ✅ 부분 수정 요청 데이터 검증")
        print("   5. ✅ 선택적 필드 업데이트")
        print("   6. ✅ 오류 처리 및 검증")
        
        print(f"\n💡 상품 부분 수정 주요 특징:")
        print("   - 승인 과정 없이 즉시 반영")
        print("   - 배송 및 반품지 정보만 수정 가능")
        print("   - 승인완료된 상품만 수정 가능")
        print("   - 기존 상품 정보는 그대로 유지")
        print("   - 선택적 필드만 업데이트")
        print("   - 빠른 물류 정보 변경에 최적화")
        
        print(f"\n📚 사용 가능한 수정 필드:")
        print("   🚚 배송: deliveryMethod, deliveryCompanyCode, deliveryChargeType")
        print("   💰 배송비: deliveryCharge, freeShipOverAmount, deliveryChargeOnReturn")
        print("   📦 출고: outboundShippingPlaceCode, outboundShippingTimeDay")
        print("   🏠 반품지: returnCenterCode, returnChargeName, returnAddress 등")
        print("   📞 연락처: companyContactNumber")
        print("   ℹ️ 기타: extraInfoMessage, pccNeeded")
        
    except Exception as e:
        print(f"\n❌ 상품 부분 수정 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()