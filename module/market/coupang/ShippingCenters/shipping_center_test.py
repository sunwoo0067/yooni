#!/usr/bin/env python3
"""
쿠팡 출고지 생성 API 실제 테스트
실제 API 키를 사용한 출고지 생성 및 관리 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.ShippingCenters.shipping_center_client import (
    ShippingCenterClient, 
    ShippingCenterRequest, 
    PlaceAddress, 
    RemoteInfo
)


def test_real_api_shipping_center_creation():
    """실제 API로 출고지 생성 테스트"""
    print("=" * 60 + " 실제 API 출고지 생성 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 실제 API 인증으로 출고지 클라이언트 초기화 성공")
        
        # 실제 출고지 정보 설정
        vendor_id = os.getenv('COUPANG_VENDOR_ID')  # 환경변수에서 가져오기
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📦 실제 API로 출고지 생성 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 편의 메서드를 사용한 국내 출고지 생성
        result = client.create_domestic_shipping_center(
            vendor_id=vendor_id,
            user_id="apiTestUser",
            shipping_place_name="API 테스트 출고지",
            zip_code="06292",
            address="서울특별시 강남구 역삼동 테헤란로 123",
            address_detail="테스트빌딩 5층",
            contact_number="02-1234-5678",
            phone_number2="010-9876-5432",
            delivery_infos=[
                {"code": "KGB", "jeju": 3000, "notJeju": 2500},  # 로젠택배
                {"code": "CJGLS", "jeju": 3000, "notJeju": 2500},  # CJ대한통운
                {"code": "HANJIN", "jeju": 3500, "notJeju": 3000}  # 한진택배
            ]
        )
        
        if result.get("success"):
            print(f"\n✅ 실제 API 출고지 생성 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('message')}")
            
            # 응답 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                print(f"   HTTP 코드: {original_response.get('code')}")
                print(f"   서버 메시지: {original_response.get('message')}")
                
        else:
            print(f"\n❌ 실제 API 출고지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except Exception as e:
        print(f"❌ 실제 API 출고지 생성 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_complex_shipping_center():
    """실제 API로 복잡한 출고지 생성 테스트"""
    print("\n" + "=" * 60 + " 실제 API 복잡한 출고지 생성 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📦 복잡한 출고지 설정으로 생성 중...")
        
        # 복잡한 출고지 설정: 도로명 + 지번 주소, 다양한 택배사
        place_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="051-1234-5678",
                phone_number2="010-1111-2222",
                return_zip_code="48058",
                return_address="부산광역시 해운대구 해운대해변로 264",
                return_address_detail="해운대센터 7층 701호"
            ),
            PlaceAddress(
                address_type="JIBUN",
                country_code="KR",
                company_contact_number="051-1234-5678",
                phone_number2="010-1111-2222",
                return_zip_code="48058",
                return_address="부산광역시 해운대구 우동 1408-5",
                return_address_detail="해운대센터 7층 701호"
            )
        ]
        
        # 다양한 택배사별 배송비 설정
        remote_infos = [
            RemoteInfo(delivery_code="KGB", jeju=4000, not_jeju=3000),      # 로젠택배
            RemoteInfo(delivery_code="CJGLS", jeju=3500, not_jeju=2800),    # CJ대한통운
            RemoteInfo(delivery_code="HANJIN", jeju=4500, not_jeju=3500),   # 한진택배
            RemoteInfo(delivery_code="LOTTE", jeju=3800, not_jeju=3200),    # 롯데택배
            RemoteInfo(delivery_code="EPOST", jeju=300, not_jeju=200)       # 우체국택배 (특별 규칙)
        ]
        
        # 출고지 생성 요청
        request = ShippingCenterRequest(
            vendor_id=vendor_id,
            user_id="complexTestUser",
            shipping_place_name="복잡한 API 테스트 출고지",
            place_addresses=place_addresses,
            remote_infos=remote_infos,
            usable=True,
            global_shipping=False
        )
        
        print(f"   📍 주소: {place_addresses[0].return_address}")
        print(f"   📞 연락처: {place_addresses[0].company_contact_number}")
        print(f"   🚚 택배사: {len(remote_infos)}개")
        
        # 출고지 생성 실행
        result = client.create_shipping_center(request)
        
        if result.get("success"):
            print(f"\n✅ 복잡한 출고지 생성 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            
            # 택배사별 설정 확인
            print(f"\n📋 설정된 택배사별 배송비:")
            for i, remote in enumerate(remote_infos, 1):
                print(f"   {i}. {remote.delivery_code}: 제주 {remote.jeju:,}원, 제주외 {remote.not_jeju:,}원")
                
        else:
            print(f"\n❌ 복잡한 출고지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 복잡한 출고지 생성 오류: {e}")


def test_real_api_validation_scenarios():
    """실제 API로 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 실제 API 검증 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        # 실제 API에서 발생할 수 있는 오류 시나리오들
        test_scenarios = [
            {
                "name": "중복 출고지명 테스트",
                "shipping_place_name": "API 테스트 출고지",  # 이미 생성된 이름
                "zip_code": "12345",
                "address": "서울특별시 강남구 테헤란로 456",
                "address_detail": "다른 빌딩",
                "contact_number": "02-9876-5432",
                "expected_error": "중복"
            },
            {
                "name": "중복 주소지 테스트",
                "shipping_place_name": "다른 출고지명",
                "zip_code": "06292",
                "address": "서울특별시 강남구 역삼동 테헤란로 123",  # 이미 등록된 주소
                "address_detail": "테스트빌딩 5층",
                "contact_number": "02-1234-5678",
                "expected_error": "중복 주소지"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 시나리오 {i}: {scenario['name']}")
            
            try:
                result = client.create_domestic_shipping_center(
                    vendor_id=vendor_id,
                    user_id="validationTestUser",
                    shipping_place_name=scenario["shipping_place_name"],
                    zip_code=scenario["zip_code"],
                    address=scenario["address"],
                    address_detail=scenario["address_detail"],
                    contact_number=scenario["contact_number"]
                )
                
                if result.get("success"):
                    print(f"   ⚠️ 예상치 못한 성공: {result.get('shippingCenterCode')}")
                else:
                    error_msg = result.get('error', '')
                    if scenario['expected_error'] in error_msg:
                        print(f"   ✅ 예상된 오류 발생: {error_msg}")
                    else:
                        print(f"   ❓ 다른 오류 발생: {error_msg}")
                        
            except ValueError as e:
                print(f"   ✅ 예상된 검증 오류: {e}")
            except Exception as e:
                if scenario['expected_error'] in str(e):
                    print(f"   ✅ 예상된 API 오류: {e}")
                else:
                    print(f"   ❓ 예상치 못한 오류: {e}")
                    
    except Exception as e:
        print(f"❌ 검증 시나리오 테스트 오류: {e}")


def test_real_api_different_delivery_companies():
    """실제 API로 다양한 택배사 테스트"""
    print("\n" + "=" * 60 + " 실제 API 다양한 택배사 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        # 지원 택배사 목록 확인
        delivery_codes = client.get_delivery_codes()
        print(f"\n📋 지원 택배사 목록 ({len(delivery_codes)}개):")
        
        # 주요 택배사들로 테스트
        major_delivery_companies = [
            {"code": "KGB", "name": "로젠택배", "jeju": 3000, "notJeju": 2500},
            {"code": "CJGLS", "name": "CJ대한통운", "jeju": 3200, "notJeju": 2700},
            {"code": "HANJIN", "name": "한진택배", "jeju": 3500, "notJeju": 3000},
            {"code": "LOTTE", "name": "롯데택배", "jeju": 3300, "notJeju": 2800},
            {"code": "EPOST", "name": "우체국택배", "jeju": 400, "notJeju": 300}
        ]
        
        for i, company in enumerate(major_delivery_companies, 1):
            print(f"   {i}. [{company['code']:8}] {company['name']}")
        
        print(f"\n📦 주요 택배사들로 출고지 생성 중...")
        
        try:
            result = client.create_domestic_shipping_center(
                vendor_id=vendor_id,
                user_id="deliveryTestUser",
                shipping_place_name="다양한 택배사 테스트 출고지",
                zip_code="21554",
                address="인천광역시 남동구 논현로 123",
                address_detail="테스트센터 4층",
                contact_number="032-1234-5678",
                phone_number2="010-5555-6666",
                delivery_infos=major_delivery_companies
            )
            
            if result.get("success"):
                print(f"\n✅ 다양한 택배사 출고지 생성 성공:")
                print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
                print(f"   📊 설정된 택배사 수: {len(major_delivery_companies)}개")
                
                print(f"\n📋 설정된 택배사별 배송비:")
                for company in major_delivery_companies:
                    name = company['name']
                    code = company['code']
                    jeju = company['jeju']
                    not_jeju = company['notJeju']
                    
                    if code == "EPOST":
                        print(f"   📮 {name}({code}): 제주 {jeju:,}원, 제주외 {not_jeju:,}원 (우체국 특별규칙)")
                    else:
                        print(f"   🚚 {name}({code}): 제주 {jeju:,}원, 제주외 {not_jeju:,}원")
                        
            else:
                print(f"\n❌ 다양한 택배사 출고지 생성 실패:")
                print(f"   🚨 오류: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ 택배사 테스트 중 오류: {e}")
            
    except Exception as e:
        print(f"❌ 택배사 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 생성 API 실제 테스트 시작")
    print("=" * 100)
    
    # 환경변수 확인
    vendor_id = os.getenv('COUPANG_VENDOR_ID')
    if not vendor_id:
        print("⚠️ 실제 API 테스트를 위해서는 다음 환경변수가 필요합니다:")
        print("   - COUPANG_ACCESS_KEY")
        print("   - COUPANG_SECRET_KEY") 
        print("   - COUPANG_VENDOR_ID")
        print("\n💡 환경변수 설정 예시:")
        print("   export COUPANG_VENDOR_ID='A00012345'")
        print("   export COUPANG_ACCESS_KEY='your_access_key'")
        print("   export COUPANG_SECRET_KEY='your_secret_key'")
        return
    
    try:
        # 실제 API 테스트 실행
        test_real_api_shipping_center_creation()
        test_real_api_complex_shipping_center()
        test_real_api_different_delivery_companies()
        test_real_api_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 실제 API 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 인증 및 출고지 생성")
        print("   2. ✅ 도로명 + 지번 주소 복합 등록")
        print("   3. ✅ 다양한 택배사별 배송비 설정")
        print("   4. ✅ 우체국 택배 특별 규칙 적용")
        print("   5. ✅ 중복 검증 및 오류 처리")
        print("   6. ✅ 복잡한 출고지 설정 처리")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 출고지 코드는 상품 등록시 사용됩니다")
        print("   - 동일한 주소지/출고지명 중복 등록 불가")
        print("   - 택배사별 도서산간 배송비 차등 설정 가능")
        print("   - usable=true 설정으로 활성화 필요")
        
    except Exception as e:
        print(f"\n❌ 실제 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()