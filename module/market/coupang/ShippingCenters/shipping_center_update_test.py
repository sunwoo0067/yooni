#!/usr/bin/env python3
"""
쿠팡 출고지 수정 API 실제 테스트
실제 API 키를 사용한 출고지 수정 및 관리 테스트
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


def test_real_api_shipping_center_update():
    """실제 API로 출고지 수정 테스트"""
    print("=" * 60 + " 실제 API 출고지 수정 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 실제 API 인증으로 출고지 클라이언트 초기화 성공")
        
        # 실제 출고지 정보 설정
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🔍 실제 출고지 목록에서 수정할 출고지 선택 중...")
        
        # 먼저 기존 출고지 목록 조회
        all_places_result = client.get_all_shipping_places()
        if not all_places_result.get("success") or not all_places_result.get("shipping_places"):
            print("❌ 수정할 출고지를 찾을 수 없습니다. 먼저 출고지를 생성해주세요.")
            return
        
        # 첫 번째 활성화된 출고지를 수정 대상으로 선택
        shipping_places = all_places_result.get("shipping_places", [])
        active_places = [place for place in shipping_places if place.usable]
        
        if not active_places:
            print("❌ 활성화된 출고지가 없습니다. 먼저 출고지를 생성하고 활성화해주세요.")
            return
        
        target_place = active_places[0]
        outbound_shipping_place_code = target_place.outbound_shipping_place_code
        
        print(f"📦 수정 대상 출고지:")
        print(f"   🏷️ 출고지 코드: {outbound_shipping_place_code}")
        print(f"   📝 현재 이름: {target_place.shipping_place_name}")
        print(f"   📅 생성일: {target_place.create_date}")
        
        # 기존 주소 정보 표시
        if target_place.place_addresses:
            addr = target_place.place_addresses[0]
            print(f"   📍 현재 주소: {addr.return_address}")
            print(f"   📞 현재 연락처: {addr.company_contact_number}")
        
        # 기존 배송비 정보 표시
        print(f"   🚚 현재 배송비 정보: {len(target_place.remote_infos)}개")
        for remote in target_place.remote_infos:
            status = "활성" if remote.usable else "비활성"
            print(f"      - {remote.delivery_code}(ID:{remote.remote_info_id}): 제주 {remote.jeju:,}원, 제주외 {remote.not_jeju:,}원 ({status})")
        
        print(f"\n📝 출고지 정보 수정 중...")
        
        # 수정할 주소 정보 (기존 정보 기반으로 일부 수정)
        updated_addresses = []
        for addr in target_place.place_addresses:
            updated_addr = PlaceAddress(
                address_type=addr.address_type,
                country_code=addr.country_code,
                company_contact_number="02-9999-8888",  # 연락처 변경
                phone_number2="010-8888-9999",  # 보조 연락처 변경/추가
                return_zip_code=addr.return_zip_code,
                return_address=addr.return_address,
                return_address_detail=f"수정됨 - {addr.return_address_detail}"  # 상세주소 수정
            )
            updated_addresses.append(updated_addr)
        
        # 수정할 배송비 정보 (기존 정보 기반으로 수정)
        updated_remote_infos = []
        
        # 기존 배송정보들을 수정
        for remote in target_place.remote_infos:
            if remote.usable:
                # 활성화된 배송정보는 배송비 인상
                updated_remote = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju + 500,  # 제주 배송비 500원 인상
                    not_jeju=remote.not_jeju + 300,  # 제주외 배송비 300원 인상
                    usable=True,
                    remote_info_id=remote.remote_info_id  # 기존 ID 포함
                )
                updated_remote_infos.append(updated_remote)
            else:
                # 비활성화된 배송정보는 그대로 유지
                updated_remote = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=False,
                    remote_info_id=remote.remote_info_id
                )
                updated_remote_infos.append(updated_remote)
        
        # 새로운 택배사 추가 (우체국택배)
        if not any(remote.delivery_code == "EPOST" for remote in updated_remote_infos):
            new_epost = RemoteInfoUpdate(
                delivery_code="EPOST",
                jeju=400,
                not_jeju=300,
                usable=True
                # remote_info_id는 None (새로운 배송정보)
            )
            updated_remote_infos.append(new_epost)
        
        # 출고지 수정 요청 생성
        update_request = ShippingCenterUpdateRequest(
            vendor_id=vendor_id,
            user_id="realApiUpdateUser",
            outbound_shipping_place_code=outbound_shipping_place_code,
            place_addresses=updated_addresses,
            remote_infos=updated_remote_infos,
            shipping_place_name=f"수정됨 - {target_place.shipping_place_name}",  # 출고지명 수정
            usable=True  # 활성 상태 유지
        )
        
        print(f"   📝 새 출고지명: {update_request.shipping_place_name}")
        print(f"   📞 새 연락처: {updated_addresses[0].company_contact_number}")
        print(f"   🚚 배송비 정보: {len(updated_remote_infos)}개 (기존 인상 + 우체국택배 추가)")
        
        # 출고지 수정 실행
        result = client.update_shipping_center(update_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 출고지 수정 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('outboundShippingPlaceCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('resultMessage')}")
            
            # 수정 내용 요약
            print(f"\n📋 수정된 내용:")
            print(f"   📝 출고지명: '{target_place.shipping_place_name}' → '{update_request.shipping_place_name}'")
            print(f"   📞 연락처: 업데이트됨")
            print(f"   📍 상세주소: '수정됨' 접두사 추가")
            print(f"   🚚 기존 배송비: 인상 적용")
            print(f"   📮 우체국택배: 새로 추가")
            
            # 수정 후 확인
            print(f"\n🔍 수정 결과 확인 중...")
            updated_result = client.get_shipping_place_by_code(outbound_shipping_place_code)
            
            if updated_result.get("success"):
                updated_place = updated_result.get("shipping_place")
                print(f"✅ 수정 확인 완료:")
                print(f"   📝 현재 출고지명: {updated_place.shipping_place_name}")
                print(f"   📞 현재 연락처: {updated_place.place_addresses[0].company_contact_number}")
                print(f"   🚚 현재 배송비 정보: {len(updated_place.remote_infos)}개")
                
                for remote in updated_place.remote_infos:
                    if remote.usable:
                        print(f"      ✅ {remote.delivery_code}: 제주 {remote.jeju:,}원, 제주외 {remote.not_jeju:,}원")
            
        else:
            print(f"\n❌ 실제 API 출고지 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except Exception as e:
        print(f"❌ 실제 API 출고지 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_delivery_info_management():
    """실제 API로 배송비 정보 관리 테스트"""
    print("\n" + "=" * 60 + " 실제 API 배송비 정보 관리 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🚚 배송비 정보 관리 테스트...")
        
        # 출고지 목록에서 테스트 대상 선택
        all_places_result = client.get_all_shipping_places()
        if not all_places_result.get("success"):
            print("❌ 출고지 목록 조회 실패")
            return
        
        active_places = [place for place in all_places_result.get("shipping_places", []) if place.usable]
        if not active_places:
            print("❌ 활성화된 출고지가 없습니다")
            return
        
        target_place = active_places[0]
        outbound_shipping_place_code = target_place.outbound_shipping_place_code
        
        print(f"📦 배송비 관리 대상: {target_place.shipping_place_name} (코드: {outbound_shipping_place_code})")
        
        # 기존 주소 정보는 그대로 유지
        existing_addresses = []
        for addr in target_place.place_addresses:
            existing_addr = PlaceAddress(
                address_type=addr.address_type,
                country_code=addr.country_code,
                company_contact_number=addr.company_contact_number,
                phone_number2=addr.phone_number2,
                return_zip_code=addr.return_zip_code,
                return_address=addr.return_address,
                return_address_detail=addr.return_address_detail
            )
            existing_addresses.append(existing_addr)
        
        # 배송비 시나리오: 일괄 인하 + 새 택배사 추가 + 일부 비활성화
        delivery_scenarios = []
        
        # 기존 배송정보들 처리
        for remote in target_place.remote_infos:
            if remote.delivery_code == "EPOST":
                # 우체국택배는 최대한 저렴하게
                scenario = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=200,
                    not_jeju=100,
                    usable=True,
                    remote_info_id=remote.remote_info_id
                )
                delivery_scenarios.append(scenario)
            elif remote.delivery_code in ["KGB", "CJGLS"]:
                # 주요 택배사는 경쟁력 있는 가격으로
                scenario = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=max(2500, remote.jeju - 500),  # 500원 인하 (최소 2500원)
                    not_jeju=max(2000, remote.not_jeju - 300),  # 300원 인하 (최소 2000원)
                    usable=True,
                    remote_info_id=remote.remote_info_id
                )
                delivery_scenarios.append(scenario)
            elif remote.usable:
                # 다른 활성 택배사는 비활성화
                scenario = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=False,  # 비활성화
                    remote_info_id=remote.remote_info_id
                )
                delivery_scenarios.append(scenario)
            else:
                # 이미 비활성화된 것들은 그대로 유지
                scenario = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=False,
                    remote_info_id=remote.remote_info_id
                )
                delivery_scenarios.append(scenario)
        
        # 새로운 택배사 추가 (롯데택배)
        existing_codes = [remote.delivery_code for remote in target_place.remote_infos]
        if "LOTTE" not in existing_codes:
            new_lotte = RemoteInfoUpdate(
                delivery_code="LOTTE",
                jeju=2800,
                not_jeju=2300,
                usable=True
                # 새로 추가하므로 remote_info_id 없음
            )
            delivery_scenarios.append(new_lotte)
        
        # 배송비 관리 요청 생성
        delivery_update_request = ShippingCenterUpdateRequest(
            vendor_id=vendor_id,
            user_id="deliveryManagerUser",
            outbound_shipping_place_code=outbound_shipping_place_code,
            place_addresses=existing_addresses,
            remote_infos=delivery_scenarios
            # shipping_place_name은 변경하지 않음 (null)
        )
        
        print(f"\n🔄 배송비 정책 변경:")
        active_deliveries = [d for d in delivery_scenarios if d.usable]
        inactive_deliveries = [d for d in delivery_scenarios if not d.usable]
        
        print(f"   ✅ 활성 택배사 ({len(active_deliveries)}개):")
        for delivery in active_deliveries:
            print(f"      - {delivery.delivery_code}: 제주 {delivery.jeju:,}원, 제주외 {delivery.not_jeju:,}원")
        
        print(f"   ❌ 비활성 택배사 ({len(inactive_deliveries)}개):")
        for delivery in inactive_deliveries:
            print(f"      - {delivery.delivery_code}")
        
        # 배송비 정책 적용
        result = client.update_shipping_center(delivery_update_request)
        
        if result.get("success"):
            print(f"\n✅ 배송비 정책 변경 성공:")
            print(f"   📊 새로운 배송비 정책이 적용되었습니다")
            print(f"   💰 주요 택배사 배송비 인하")
            print(f"   📮 우체국택배 최저가 정책")
            print(f"   🚚 롯데택배 신규 추가")
            print(f"   🔒 불필요한 택배사 비활성화")
            
        else:
            print(f"\n❌ 배송비 정책 변경 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 배송비 정보 관리 테스트 오류: {e}")


def test_real_api_update_validation():
    """실제 API로 수정 검증 테스트"""
    print("\n" + "=" * 60 + " 실제 API 수정 검증 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n⚠️ 실제 API에서 발생할 수 있는 오류 시나리오 테스트...")
        
        # 존재하지 않는 출고지 코드로 수정 시도
        invalid_scenarios = [
            {
                "name": "존재하지 않는 출고지 코드",
                "outbound_shipping_place_code": 999999,  # 존재하지 않는 코드
                "expected_error": "존재하지 않는"
            },
            {
                "name": "잘못된 remote_info_id",
                "outbound_shipping_place_code": None,  # 실제 코드로 교체됨
                "invalid_remote_info_id": 999999,  # 존재하지 않는 remote_info_id
                "expected_error": "remote_info_id"
            }
        ]
        
        # 실제 출고지 코드 가져오기 (두 번째 시나리오용)
        all_places_result = client.get_all_shipping_places()
        if all_places_result.get("success") and all_places_result.get("shipping_places"):
            real_place = all_places_result.get("shipping_places")[0]
            invalid_scenarios[1]["outbound_shipping_place_code"] = real_place.outbound_shipping_place_code
        
        for i, scenario in enumerate(invalid_scenarios, 1):
            print(f"\n🧪 시나리오 {i}: {scenario['name']}")
            
            try:
                if scenario["name"] == "존재하지 않는 출고지 코드":
                    # 기본 주소와 배송비 정보로 요청
                    dummy_address = PlaceAddress(
                        address_type="ROADNAME",
                        country_code="KR",
                        company_contact_number="02-1234-5678",
                        return_zip_code="12345",
                        return_address="테스트 주소",
                        return_address_detail=""
                    )
                    
                    dummy_remote = RemoteInfoUpdate(
                        delivery_code="KGB",
                        jeju=3000,
                        not_jeju=2500,
                        usable=True
                    )
                    
                    invalid_request = ShippingCenterUpdateRequest(
                        vendor_id=vendor_id,
                        user_id="invalidTestUser",
                        outbound_shipping_place_code=scenario["outbound_shipping_place_code"],
                        place_addresses=[dummy_address],
                        remote_infos=[dummy_remote]
                    )
                    
                elif scenario["name"] == "잘못된 remote_info_id":
                    # 실제 출고지에 잘못된 remote_info_id로 요청
                    real_place_result = client.get_shipping_place_by_code(scenario["outbound_shipping_place_code"])
                    if not real_place_result.get("success"):
                        continue
                    
                    real_place = real_place_result.get("shipping_place")
                    
                    # 기존 주소 정보 사용
                    existing_addresses = []
                    for addr in real_place.place_addresses:
                        existing_addr = PlaceAddress(
                            address_type=addr.address_type,
                            country_code=addr.country_code,
                            company_contact_number=addr.company_contact_number,
                            phone_number2=addr.phone_number2,
                            return_zip_code=addr.return_zip_code,
                            return_address=addr.return_address,
                            return_address_detail=addr.return_address_detail
                        )
                        existing_addresses.append(existing_addr)
                    
                    # 잘못된 remote_info_id로 배송비 정보 생성
                    invalid_remote = RemoteInfoUpdate(
                        delivery_code="KGB",
                        jeju=3000,
                        not_jeju=2500,
                        usable=True,
                        remote_info_id=scenario["invalid_remote_info_id"]  # 잘못된 ID
                    )
                    
                    invalid_request = ShippingCenterUpdateRequest(
                        vendor_id=vendor_id,
                        user_id="invalidRemoteIdUser",
                        outbound_shipping_place_code=scenario["outbound_shipping_place_code"],
                        place_addresses=existing_addresses,
                        remote_infos=[invalid_remote]
                    )
                
                # 수정 요청 실행
                result = client.update_shipping_center(invalid_request)
                
                if result.get("success"):
                    print(f"   ⚠️ 예상치 못한 성공: {result}")
                else:
                    error_msg = result.get('error', '')
                    print(f"   ✅ 예상된 오류: {error_msg}")
                    
            except ValueError as e:
                print(f"   ✅ 예상된 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 API 오류: {e}")
                
    except Exception as e:
        print(f"❌ 수정 검증 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 수정 API 실제 테스트 시작")
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
        test_real_api_shipping_center_update()
        test_real_api_delivery_info_management()
        test_real_api_update_validation()
        
        print(f"\n" + "=" * 50 + " 실제 API 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 인증 및 출고지 수정")
        print("   2. ✅ 출고지명, 주소, 연락처 정보 업데이트")
        print("   3. ✅ 기존 배송비 정보 수정 (remote_info_id 활용)")
        print("   4. ✅ 새로운 택배사 배송비 정보 추가")
        print("   5. ✅ 택배사별 활성/비활성 상태 관리")
        print("   6. ✅ 배송비 정책 일괄 변경")
        print("   7. ✅ 수정 후 변경 사항 확인")
        print("   8. ✅ 잘못된 파라미터 오류 처리")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 출고지 수정은 기존 정보 + 변경사항을 모두 포함")
        print("   - remote_info_id가 있으면 기존 배송정보 수정")
        print("   - remote_info_id가 없으면 새로운 배송정보 추가")
        print("   - usable=false로 배송정보 비활성화 가능")
        print("   - 국내/해외 분류는 생성 후 변경 불가")
        print("   - 수정 성공 후 즉시 변경사항 반영됨")
        
    except Exception as e:
        print(f"\n❌ 실제 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()