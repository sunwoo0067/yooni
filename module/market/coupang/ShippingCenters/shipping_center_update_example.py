#!/usr/bin/env python3
"""
쿠팡 출고지 수정 API 사용 예제
기존 출고지 정보 수정 기능 테스트
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
    ShippingCenterUpdateRequest, 
    PlaceAddress, 
    RemoteInfoUpdate
)


def test_shipping_center_update_basic():
    """기본적인 출고지 수정 테스트"""
    print("=" * 60 + " 기본 출고지 수정 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 쿠팡 출고지 클라이언트 초기화 성공")
        
        # 실제 업데이트할 출고지 정보 설정
        vendor_id = "A00012345"  # 실제 벤더 ID로 변경 필요
        outbound_shipping_place_code = 123456  # 실제 출고지 코드로 변경 필요
        
        print(f"\n📦 출고지 수정 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   🏷️ 출고지 코드: {outbound_shipping_place_code}")
        
        # 수정할 주소 정보 (기존 주소 정보 업데이트)
        updated_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="02-9999-8888",  # 변경된 연락처
                phone_number2="010-5555-4444",  # 변경된 보조 연락처
                return_zip_code="06292",
                return_address="서울특별시 강남구 테헤란로 456",  # 변경된 주소
                return_address_detail="업데이트된 테스트빌딩 7층"  # 변경된 상세주소
            )
        ]
        
        # 수정할 배송비 정보 (기존 배송비 정보 업데이트 + 새로운 택배사 추가)
        updated_remote_infos = [
            # 기존 배송정보 수정 (remote_info_id 포함)
            RemoteInfoUpdate(
                delivery_code="KGB",
                jeju=3500,  # 변경된 배송비
                not_jeju=3000,  # 변경된 배송비
                usable=True,
                remote_info_id=789  # 기존 배송정보 ID (실제 ID로 변경 필요)
            ),
            # 새로운 택배사 추가 (remote_info_id 없음)
            RemoteInfoUpdate(
                delivery_code="LOTTE",
                jeju=4000,
                not_jeju=3500,
                usable=True
                # remote_info_id는 None (새로운 배송정보)
            ),
            # 기존 배송정보 비활성화
            RemoteInfoUpdate(
                delivery_code="HANJIN",
                jeju=0,
                not_jeju=0,
                usable=False,  # 비활성화
                remote_info_id=790  # 기존 배송정보 ID (실제 ID로 변경 필요)
            )
        ]
        
        # 출고지 수정 요청 생성
        update_request = ShippingCenterUpdateRequest(
            vendor_id=vendor_id,
            user_id="updateTestUser",
            outbound_shipping_place_code=outbound_shipping_place_code,
            place_addresses=updated_addresses,
            remote_infos=updated_remote_infos,
            shipping_place_name="업데이트된 API 테스트 출고지",  # 변경된 출고지명
            usable=True,  # 활성 상태 유지
            global_shipping=False  # 국내/해외 분류는 변경 불가 (참고용)
        )
        
        print(f"   📝 새 출고지명: {update_request.shipping_place_name}")
        print(f"   📍 새 주소: {updated_addresses[0].return_address}")
        print(f"   📞 새 연락처: {updated_addresses[0].company_contact_number}")
        print(f"   🚚 배송비 정보: {len(updated_remote_infos)}개 (수정/추가/비활성화)")
        
        # 출고지 수정 실행
        result = client.update_shipping_center(update_request)
        
        if result.get("success"):
            print(f"\n✅ 출고지 수정 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('outboundShippingPlaceCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('resultMessage')}")
            
            print(f"\n📋 수정된 내용:")
            print(f"   - 출고지명 변경")
            print(f"   - 주소 및 연락처 정보 업데이트")
            print(f"   - 로젠택배 배송비 수정")
            print(f"   - 롯데택배 새로 추가")
            print(f"   - 한진택배 비활성화")
            
        else:
            print(f"\n❌ 출고지 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 원본 응답 출력 (디버깅용)
            if result.get('originalResponse'):
                print(f"\n📋 원본 응답:")
                pprint(result.get('originalResponse'), width=100)
            
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 출고지 수정 오류: {e}")


def test_shipping_center_partial_update():
    """부분 수정 테스트 (출고지명만 변경)"""
    print("\n" + "=" * 60 + " 부분 수정 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 출고지명만 변경하는 경우
        vendor_id = "A00012345"
        outbound_shipping_place_code = 123456
        
        print(f"\n📝 출고지명만 변경하는 부분 수정...")
        
        # 기존 주소 정보는 그대로 유지 (기존 정보를 다시 입력)
        existing_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="02-1234-5678",
                return_zip_code="06292",
                return_address="서울특별시 강남구 테헤란로 123",
                return_address_detail="기존 테스트빌딩 5층"
            )
        ]
        
        # 기존 배송비 정보도 그대로 유지
        existing_remote_infos = [
            RemoteInfoUpdate(
                delivery_code="KGB",
                jeju=3000,
                not_jeju=2500,
                usable=True,
                remote_info_id=789  # 기존 ID 유지
            )
        ]
        
        # 출고지명만 변경하는 요청
        partial_update_request = ShippingCenterUpdateRequest(
            vendor_id=vendor_id,
            user_id="partialUpdateUser",
            outbound_shipping_place_code=outbound_shipping_place_code,
            place_addresses=existing_addresses,  # 기존 정보 유지
            remote_infos=existing_remote_infos,  # 기존 정보 유지
            shipping_place_name="새로운 출고지명만 변경",  # 이것만 변경
            # usable과 global_shipping은 null로 설정 (변경하지 않음)
        )
        
        print(f"   📝 새 출고지명: {partial_update_request.shipping_place_name}")
        print(f"   💡 다른 정보는 기존 상태 유지")
        
        result = client.update_shipping_center(partial_update_request)
        
        if result.get("success"):
            print(f"\n✅ 부분 수정 성공:")
            print(f"   📝 출고지명만 '{partial_update_request.shipping_place_name}'로 변경됨")
        else:
            print(f"\n❌ 부분 수정 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 부분 수정 테스트 오류: {e}")


def test_shipping_center_delivery_update():
    """배송비 정보만 수정하는 테스트"""
    print("\n" + "=" * 60 + " 배송비 정보 수정 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        vendor_id = "A00012345"
        outbound_shipping_place_code = 123456
        
        print(f"\n🚚 배송비 정보만 수정...")
        
        # 기존 주소 정보 유지
        existing_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="02-1234-5678",
                return_zip_code="06292",
                return_address="서울특별시 강남구 테헤란로 123",
                return_address_detail="테스트빌딩 5층"
            )
        ]
        
        # 배송비만 대폭 수정
        updated_delivery_infos = [
            # 기존 로젠택배 배송비 인상
            RemoteInfoUpdate(
                delivery_code="KGB",
                jeju=5000,  # 3000 → 5000
                not_jeju=4000,  # 2500 → 4000
                usable=True,
                remote_info_id=789
            ),
            # 새로운 우체국택배 추가 (저렴한 옵션)
            RemoteInfoUpdate(
                delivery_code="EPOST",
                jeju=500,
                not_jeju=300,
                usable=True
                # 새로 추가하므로 remote_info_id 없음
            ),
            # 기존 다른 택배사 비활성화
            RemoteInfoUpdate(
                delivery_code="CJGLS",
                jeju=0,
                not_jeju=0,
                usable=False,
                remote_info_id=790
            )
        ]
        
        delivery_update_request = ShippingCenterUpdateRequest(
            vendor_id=vendor_id,
            user_id="deliveryUpdateUser",
            outbound_shipping_place_code=outbound_shipping_place_code,
            place_addresses=existing_addresses,
            remote_infos=updated_delivery_infos
            # shipping_place_name은 null (변경하지 않음)
        )
        
        print(f"   📊 배송비 변경 내용:")
        for info in updated_delivery_infos:
            if info.usable:
                print(f"     ✅ {info.delivery_code}: 제주 {info.jeju:,}원, 제주외 {info.not_jeju:,}원")
            else:
                print(f"     ❌ {info.delivery_code}: 비활성화")
        
        result = client.update_shipping_center(delivery_update_request)
        
        if result.get("success"):
            print(f"\n✅ 배송비 정보 수정 성공")
            print(f"   🚚 새로운 배송비 정책이 적용되었습니다")
        else:
            print(f"\n❌ 배송비 정보 수정 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 배송비 수정 테스트 오류: {e}")


def test_validation_scenarios():
    """검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 검증 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 잘못된 파라미터들로 테스트
        test_scenarios = [
            {
                "name": "출고지 코드 없음",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "outbound_shipping_place_code": 0,  # 잘못된 값
                    "place_addresses": [],
                    "remote_infos": []
                },
                "expected_error": "양의 정수여야 합니다"
            },
            {
                "name": "주소 정보 없음",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "outbound_shipping_place_code": 123456,
                    "place_addresses": [],  # 빈 리스트
                    "remote_infos": [
                        RemoteInfoUpdate(delivery_code="KGB", jeju=3000, not_jeju=2500, usable=True)
                    ]
                },
                "expected_error": "최소 1개 이상의 주소 정보가 필요합니다"
            },
            {
                "name": "배송비 정보 없음",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "outbound_shipping_place_code": 123456,
                    "place_addresses": [
                        PlaceAddress(
                            address_type="ROADNAME",
                            country_code="KR",
                            company_contact_number="02-1234-5678",
                            return_zip_code="12345",
                            return_address="테스트 주소",
                            return_address_detail=""
                        )
                    ],
                    "remote_infos": []  # 빈 리스트
                },
                "expected_error": "최소 1개 이상의 배송비 정보가 필요합니다"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n⚠️ 시나리오 {i}: {scenario['name']}")
            
            try:
                request = ShippingCenterUpdateRequest(**scenario["params"])
                result = client.update_shipping_center(request)
                print(f"   ❌ 예상치 못한 성공: {result}")
                
            except ValueError as e:
                if scenario["expected_error"] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 검증 시나리오 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 수정 API 테스트 시작")
    
    try:
        test_shipping_center_update_basic()
        test_shipping_center_partial_update()
        test_shipping_center_delivery_update()
        test_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("\n💡 주요 학습 내용:")
        print("   1. 출고지 수정은 기존 정보 + 변경할 정보를 모두 포함해야 함")
        print("   2. remote_info_id가 있으면 기존 배송정보 수정, 없으면 새로 추가")
        print("   3. usable=false로 설정하여 배송정보 비활성화 가능")
        print("   4. shipping_place_name을 null로 설정하면 기존 이름 유지")
        print("   5. 국내/해외 분류(global)는 생성 후 변경 불가능")
        
        print(f"\n🔧 실제 API 테스트 방법:")
        print("   - shipping_center_update_test.py 파일 사용")
        print("   - 환경변수에 실제 API 키 설정 필요")
        print("   - 실제 출고지 코드와 remote_info_id 확인 필요")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()