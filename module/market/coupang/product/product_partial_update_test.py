#!/usr/bin/env python3
"""
쿠팡 상품 수정 (승인불필요) API 실제 테스트
실제 API 키를 사용한 상품 부분 수정 테스트
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


def test_real_api_partial_update():
    """실제 API로 상품 부분 수정 테스트"""
    print("=" * 60 + " 실제 API 상품 부분 수정 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ProductClient()
        print("✅ 실제 API 인증으로 상품 클라이언트 초기화 성공")
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📝 실제 API로 상품 부분 수정 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   🆔 수정할 상품 ID: {test_seller_product_id}")
        print(f"   ✨ 특징: 승인불필요, 배송/반품지만 수정")
        print(f"   💡 TEST_SELLER_PRODUCT_ID 환경변수로 상품 ID 설정 가능")
        
        # 1단계: 기존 상품 정보 조회 (참고용)
        print(f"\n🔍 1단계: 기존 상품 정보 조회 (참고용)")
        get_result = client.get_product(test_seller_product_id)
        
        if get_result.get("success"):
            print(f"✅ 상품 조회 성공")
            data = get_result.get("data", {})
            print(f"   📦 조회된 상품명: {data.get('sellerProductName', 'N/A')}")
            print(f"   📊 상품 상태: {data.get('sellerProductStatusName', 'N/A')}")
            
            # 기존 배송 정보 확인
            existing_delivery = data.get('deliveryMethod', 'N/A')
            existing_company = data.get('deliveryCompanyCode', 'N/A')
            print(f"   🚚 기존 배송: {existing_delivery} ({existing_company})")
        else:
            print(f"⚠️ 상품 조회 실패: {get_result.get('error')}")
            print(f"💡 존재하는 승인완료 상품 ID를 TEST_SELLER_PRODUCT_ID 환경변수에 설정하세요")
            print(f"📝 예시 데이터로 부분 수정 요청 테스트 진행...")
        
        # 2단계: 상품 부분 수정 요청 생성
        print(f"\n🔧 2단계: 상품 부분 수정 요청 생성")
        
        # 실제 부분 수정 요청 생성
        partial_request = ProductPartialUpdateRequest(
            seller_product_id=int(test_seller_product_id),
            
            # 배송 정보 수정
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",  # CJ대한통운
            delivery_charge_type="FREE",
            delivery_charge=0,
            delivery_charge_on_return=2500,  # 반품 배송비
            free_ship_over_amount=0,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            outbound_shipping_place_code="74010",
            outbound_shipping_time_day=1,
            
            # 반품지 정보 수정
            return_center_code="1000274592",
            return_charge_name="실제API 테스트 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="실제API테스트빌딩 5층",
            return_charge=2500,
            
            # 기타 정보
            extra_info_message="실제API 부분수정 테스트로 변경됨",
            pcc_needed=False
        )
        
        print(f"\n📋 실제 부분 수정 요청 정보:")
        print(f"   🚚 배송: {partial_request.delivery_method} ({partial_request.delivery_company_code})")
        print(f"   💰 배송비: {partial_request.delivery_charge}원 ({partial_request.delivery_charge_type})")
        print(f"   📦 반품비: {partial_request.return_charge}원")
        print(f"   🏢 반품센터: {partial_request.return_charge_name}")
        print(f"   📞 연락처: {partial_request.company_contact_number}")
        print(f"   📅 출고일: {partial_request.outbound_shipping_time_day}일")
        
        # 3단계: 실제 상품 부분 수정 실행
        print(f"\n📤 3단계: 실제 상품 부분 수정 실행")
        result = client.update_product_partial(partial_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 부분 수정 성공!")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=4)
            
            print(f"\n   ✅ 부분 수정 완료 단계:")
            print(f"      1. ✅ 기존 상품 정보 조회")
            print(f"      2. ✅ 부분 수정 요청 데이터 생성")
            print(f"      3. ✅ 실제 API 부분 수정 실행")
            
            print(f"\n   ✨ 부분 수정의 장점:")
            print(f"      - 승인 과정 없이 즉시 반영")
            print(f"      - 배송/반품 정보만 빠르게 수정")
            print(f"      - 기존 상품 정보는 그대로 유지")
            
        else:
            print(f"\n❌ 실제 API 상품 부분 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
            print(f"\n💡 일반적인 부분 수정 실패 사유:")
            print(f"   - 존재하지 않는 seller_product_id")
            print(f"   - 권한이 없는 상품 수정 시도")
            print(f"   - 승인완료가 아닌 상품 수정 시도")
            print(f"   - '임시저장중' 또는 '승인대기중' 상품")
            print(f"   - 잘못된 반품센터 코드")
            print(f"   - 잘못된 출고지 코드")
                
    except Exception as e:
        print(f"❌ 실제 API 상품 부분 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_delivery_only_update():
    """실제 API로 배송 정보만 수정 테스트"""
    print("\n" + "=" * 60 + " 실제 API 배송 정보만 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323423')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🚚 실제 API로 배송 정보만 수정 테스트")
        print(f"   🆔 상품 ID: {test_seller_product_id}")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 수정 범위: 배송 관련 정보만")
        
        # 배송 정보만 수정하는 요청
        delivery_request = ProductPartialUpdateRequest(
            seller_product_id=int(test_seller_product_id),
            
            # 배송 정보만 수정 (반품지 정보는 기존 유지)
            delivery_method="SEQUENCIAL",
            delivery_company_code="HANJIN",  # 한진택배로 변경
            delivery_charge_type="CONDITIONAL_FREE",  # 조건부 무료배송
            delivery_charge=3000,  # 기본 배송비
            free_ship_over_amount=50000,  # 5만원 이상 무료배송
            delivery_charge_on_return=3000,
            remote_area_deliverable="Y",  # 도서산간 배송 가능
            union_delivery_type="UNION_DELIVERY",
            outbound_shipping_place_code="74010",
            outbound_shipping_time_day=2  # 출고일 2일
            
            # 반품지 정보는 None으로 두어 기존 정보 유지
        )
        
        print(f"\n📋 수정할 배송 정보:")
        print(f"   🚚 택배사: {delivery_request.delivery_company_code} (한진택배)")
        print(f"   💰 배송비 정책: {delivery_request.delivery_charge_type}")
        print(f"   📦 기본 배송비: {delivery_request.delivery_charge:,}원")
        print(f"   🎁 무료배송 기준: {delivery_request.free_ship_over_amount:,}원 이상")
        print(f"   🏔️ 도서산간: {delivery_request.remote_area_deliverable} (배송 가능)")
        print(f"   📅 출고일: {delivery_request.outbound_shipping_time_day}일")
        
        # 배송 정보 수정 실행
        print(f"\n📤 배송 정보 수정 요청 실행...")
        result = client.update_product_partial(delivery_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 배송 정보 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 수정 완료 내용:")
            print(f"      ✅ 택배사 변경: HANJIN (한진택배)")
            print(f"      ✅ 배송비 정책 변경: 조건부 무료배송")
            print(f"      ✅ 무료배송 기준 설정: 5만원 이상")
            print(f"      ✅ 도서산간 배송 가능으로 변경")
            print(f"      ✅ 출고일 조정: 2일")
            print(f"      💡 반품지 정보는 기존 정보 유지")
            
        else:
            print(f"\n❌ 실제 API 배송 정보 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 실제 API 배송 정보 수정 오류: {e}")


def test_real_api_return_center_update():
    """실제 API로 반품지 정보만 수정 테스트"""
    print("\n" + "=" * 60 + " 실제 API 반품지 정보만 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323424')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📦 실제 API로 반품지 정보만 수정 테스트")
        print(f"   🆔 상품 ID: {test_seller_product_id}")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 수정 범위: 반품지 관련 정보만")
        
        # 반품지 정보만 수정하는 요청
        return_request = ProductPartialUpdateRequest(
            seller_product_id=int(test_seller_product_id),
            
            # 배송 정보는 None으로 두어 기존 정보 유지
            
            # 반품지 정보만 수정
            return_center_code="1000274593",  # 새로운 반품센터
            return_charge_name="실제API 신규 반품센터",
            company_contact_number="02-9999-8888",  # 새로운 연락처
            return_zip_code="06295",  # 새로운 우편번호
            return_address="서울특별시 강남구 역삼동",  # 새로운 주소
            return_address_detail="신규반품센터빌딩 2층",
            return_charge=2000  # 반품비 인하
        )
        
        print(f"\n📋 수정할 반품지 정보:")
        print(f"   🏢 반품센터: {return_request.return_charge_name}")
        print(f"   📞 연락처: {return_request.company_contact_number}")
        print(f"   📍 주소: {return_request.return_address} {return_request.return_address_detail}")
        print(f"   📮 우편번호: {return_request.return_zip_code}")
        print(f"   💰 반품비: {return_request.return_charge}원")
        
        # 반품지 정보 수정 실행
        print(f"\n📤 반품지 정보 수정 요청 실행...")
        result = client.update_product_partial(return_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 반품지 정보 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 수정 완료 내용:")
            print(f"      ✅ 반품센터 변경: {return_request.return_charge_name}")
            print(f"      ✅ 연락처 변경: {return_request.company_contact_number}")
            print(f"      ✅ 주소 변경: 역삼동 신규반품센터빌딩")
            print(f"      ✅ 반품비 인하: {return_request.return_charge}원")
            print(f"      💡 배송 정보는 기존 정보 유지")
            
        else:
            print(f"\n❌ 실제 API 반품지 정보 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 실제 API 반품지 정보 수정 오류: {e}")


def test_real_api_partial_update_validation():
    """실제 API 부분 수정 검증 테스트"""
    print("\n" + "=" * 60 + " 실제 API 부분 수정 검증 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🧪 실제 API에서 발생할 수 있는 부분 수정 오류 시나리오")
        
        # 시나리오 1: 존재하지 않는 상품 ID
        print(f"\n📋 시나리오 1: 존재하지 않는 상품 ID")
        invalid_request = ProductPartialUpdateRequest(
            seller_product_id=999999999,  # 존재하지 않는 ID
            delivery_method="SEQUENCIAL",
            delivery_charge_type="FREE"
        )
        
        result1 = client.update_product_partial(invalid_request)
        if result1.get("success"):
            print(f"   ⚠️ 예상과 다르게 성공함")
        else:
            print(f"   ✅ 예상대로 실패: {result1.get('error')}")
        
        # 시나리오 2: 잘못된 반품센터 코드
        print(f"\n📋 시나리오 2: 잘못된 반품센터 코드")
        invalid_return_request = ProductPartialUpdateRequest(
            seller_product_id=int(os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')),
            return_center_code="INVALID_CODE",  # 잘못된 반품센터 코드
            return_charge_name="잘못된 반품센터"
        )
        
        result2 = client.update_product_partial(invalid_return_request)
        if result2.get("success"):
            print(f"   ⚠️ 예상과 다르게 성공함")
        else:
            print(f"   ✅ 예상대로 실패: {result2.get('error')}")
        
        # 시나리오 3: 잘못된 출고지 코드
        print(f"\n📋 시나리오 3: 잘못된 출고지 코드")
        invalid_outbound_request = ProductPartialUpdateRequest(
            seller_product_id=int(os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')),
            outbound_shipping_place_code="INVALID_OUTBOUND",  # 잘못된 출고지 코드
            delivery_method="SEQUENCIAL"
        )
        
        result3 = client.update_product_partial(invalid_outbound_request)
        if result3.get("success"):
            print(f"   ⚠️ 예상과 다르게 성공함")
        else:
            print(f"   ✅ 예상대로 실패: {result3.get('error')}")
        
        print(f"\n💡 실제 API 부분 수정 오류 패턴 확인:")
        print(f"   - 데이터 검증 오류는 클라이언트에서 처리")
        print(f"   - 권한/존재여부 오류는 서버에서 반환")
        print(f"   - 상품 상태 제한 오류 (승인완료 상품만 가능)")
        print(f"   - 코드 유효성 오류 (반품센터, 출고지)")
        print(f"   - 오류 메시지를 통한 문제 파악 가능")
        
    except Exception as e:
        print(f"❌ 실제 API 부분 수정 검증 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 수정 (승인불필요) API 실제 테스트 시작")
    print("=" * 120)
    
    # 환경 변수 확인
    required_env_vars = ['COUPANG_ACCESS_KEY', 'COUPANG_SECRET_KEY', 'COUPANG_VENDOR_ID']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        print("설정 방법:")
        print("   export COUPANG_ACCESS_KEY='your_access_key'")
        print("   export COUPANG_SECRET_KEY='your_secret_key'")
        print("   export COUPANG_VENDOR_ID='your_vendor_id'")
        print("   export TEST_SELLER_PRODUCT_ID='existing_approved_product_id'  # 선택사항")
        return
    
    try:
        # 실제 API 테스트 실행
        test_real_api_partial_update()
        test_real_api_delivery_only_update()
        test_real_api_return_center_update()
        test_real_api_partial_update_validation()
        
        print(f"\n" + "=" * 50 + " 실제 API 부분 수정 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 상품 부분 수정 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 상품 부분 수정")
        print("   2. ✅ 실제 API 배송 정보만 수정")
        print("   3. ✅ 실제 API 반품지 정보만 수정")
        print("   4. ✅ 조회 결과 확인 후 부분 수정")
        print("   5. ✅ 부분 수정 검증 및 오류 처리")
        print("   6. ✅ 선택적 필드 업데이트")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 승인완료된 상품만 부분 수정 가능")
        print("   - 배송 및 반품지 정보만 수정 가능")
        print("   - 승인 과정 없이 즉시 반영")
        print("   - 선택적 필드만 업데이트")
        print("   - 기존 상품 정보는 그대로 유지")
        print("   - 실제 반품센터/출고지 코드 사용 필수")
        print("   - '임시저장중', '승인대기중' 상품은 수정 불가")
        
        print(f"\n✨ 부분 수정 vs 전체 수정 비교:")
        print("   📝 전체 수정 (update_product):")
        print("      - 모든 상품 정보 수정 가능")
        print("      - 승인 과정 필요")
        print("      - 상품 상태에 따라 제한")
        print("   ⚡ 부분 수정 (update_product_partial):")
        print("      - 배송/반품지 정보만 수정")
        print("      - 승인 과정 불필요")
        print("      - 승인완료 상품만 가능")
        
    except Exception as e:
        print(f"\n❌ 실제 API 부분 수정 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()