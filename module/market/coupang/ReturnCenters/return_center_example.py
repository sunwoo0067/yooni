#!/usr/bin/env python3
"""
쿠팡 반품지 생성 API 사용 예제
반품지 생성 기능 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.ReturnCenters.return_center_client import (
    ReturnCenterClient, 
    ReturnCenterRequest, 
    ReturnPlaceAddress, 
    GoodsflowInfo
)


def test_return_center_creation_basic():
    """기본적인 반품지 생성 테스트"""
    print("=" * 60 + " 기본 반품지 생성 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = ReturnCenterClient()
        print("✅ 쿠팡 반품지 클라이언트 초기화 성공")
        
        # 기본 반품지 정보 설정
        vendor_id = "A00012345"  # 실제 벤더 ID로 변경 필요
        
        print(f"\n📦 반품지 생성 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 편의 메서드를 사용한 국내 반품지 생성
        result = client.create_domestic_return_center(
            vendor_id=vendor_id,
            user_id="returnTestUser",
            shipping_place_name="테스트 반품지",
            zip_code="06292",
            address="서울특별시 강남구 테헤란로 123",
            address_detail="테스트빌딩 5층 반품처리센터",
            contact_number="02-1234-5678",
            phone_number2="010-9876-5432",
            delivery_code="CJGLS",  # CJ대한통운
            contract_number="85500067",  # 예시 계약번호
            vendor_credit_fee=2500,  # 모든 중량 동일
            vendor_cash_fee=2500,
            consumer_cash_fee=2500,
            return_fee=2500
        )
        
        if result.get("success"):
            print(f"\n✅ 반품지 생성 성공:")
            print(f"   🏷️ 반품지 코드: {result.get('returnCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('message')}")
            
            # 응답 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 API 응답 상세:")
                print(f"   HTTP 코드: {original_response.get('code')}")
                print(f"   서버 메시지: {original_response.get('message')}")
                
        else:
            print(f"\n❌ 반품지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 반품지 생성 오류: {e}")


def test_return_center_with_multiple_delivery_services():
    """다양한 택배사로 반품지 생성 테스트"""
    print("\n" + "=" * 60 + " 다양한 택배사 반품지 생성 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        # 지원 택배사 목록 확인
        supported_delivery = client.get_supported_delivery_codes()
        print(f"\n📋 지원 택배사 목록:")
        for code, name in supported_delivery.items():
            print(f"   - {code}: {name}")
        
        # 주요 택배사별 반품지 생성 테스트
        test_scenarios = [
            {
                "name": "CJ대한통운 반품지",
                "delivery_code": "CJGLS",
                "contract_number": "85500067",
                "shipping_place_name": "CJ대한통운 반품처리센터"
            },
            {
                "name": "로젠택배 반품지", 
                "delivery_code": "KGB",
                "contract_number": "12345678",
                "shipping_place_name": "로젠택배 반품처리센터"
            },
            {
                "name": "한진택배 반품지",
                "delivery_code": "HANJIN",
                "contract_number": "87654321",
                "shipping_place_name": "한진택배 반품처리센터"
            },
            {
                "name": "우체국택배 반품지",
                "delivery_code": "EPOST",
                "contract_number": "11223344",
                "contract_customer_number": "999888777",  # 우체국만 필요
                "shipping_place_name": "우체국택배 반품처리센터"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📦 시나리오 {i}: {scenario['name']} 생성")
            
            try:
                result = client.create_domestic_return_center(
                    vendor_id="A00012345",
                    user_id="multiDeliveryTestUser",
                    shipping_place_name=scenario["shipping_place_name"],
                    zip_code="21554",
                    address="인천광역시 남동구 논현로 456",
                    address_detail=f"{scenario['name']} 전용",
                    contact_number="032-1234-5678",
                    phone_number2="010-5555-6666",
                    delivery_code=scenario["delivery_code"],
                    contract_number=scenario["contract_number"],
                    contract_customer_number=scenario.get("contract_customer_number", ""),
                    vendor_credit_fee=3000,  # 택배사별 차등
                    vendor_cash_fee=2800,
                    consumer_cash_fee=2700,
                    return_fee=2600
                )
                
                if result.get("success"):
                    print(f"   ✅ 성공: 반품지 코드 {result.get('returnCenterCode')}")
                else:
                    print(f"   ❌ 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
                
    except Exception as e:
        print(f"❌ 다양한 택배사 반품지 테스트 오류: {e}")


def test_return_center_with_custom_fees():
    """중량별 차등 요금 반품지 생성 테스트"""
    print("\n" + "=" * 60 + " 중량별 차등 요금 반품지 생성 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        print(f"\n📦 중량별 차등 요금 반품지 생성...")
        
        # 반품지 주소 정보
        place_address = ReturnPlaceAddress(
            address_type="ROADNAME",
            company_contact_number="02-9999-8888",
            phone_number2="010-7777-6666",
            return_zip_code="48058",
            return_address="부산광역시 해운대구 해운대해변로 264",
            return_address_detail="차등요금 반품처리센터 3층"
        )
        
        # 중량별 차등 택배사 정보 (5kg < 10kg < 20kg 순으로 요금 증가)
        goodsflow_info = GoodsflowInfo(
            deliver_code="CJGLS",
            deliver_name="CJ대한통운",
            contract_number="85500067",
            contract_customer_number="",
            # 신용요금 (5kg: 2000, 10kg: 2500, 20kg: 3000)
            vendor_credit_fee_05kg=2000,
            vendor_credit_fee_10kg=2500,
            vendor_credit_fee_20kg=3000,
            # 선불요금 (5kg: 1900, 10kg: 2400, 20kg: 2900)
            vendor_cash_fee_05kg=1900,
            vendor_cash_fee_10kg=2400,
            vendor_cash_fee_20kg=2900,
            # 착불요금 (5kg: 2100, 10kg: 2600, 20kg: 3100)
            consumer_cash_fee_05kg=2100,
            consumer_cash_fee_10kg=2600,
            consumer_cash_fee_20kg=3100,
            # 반품비 (5kg: 2200, 10kg: 2700, 20kg: 3200)
            return_fee_05kg=2200,
            return_fee_10kg=2700,
            return_fee_20kg=3200
        )
        
        # 반품지 생성 요청
        request = ReturnCenterRequest(
            vendor_id="A00012345",
            user_id="customFeeTestUser",
            shipping_place_name="중량별 차등 요금 반품지",
            goodsflow_info=goodsflow_info,
            place_addresses=[place_address]
        )
        
        print(f"   📊 중량별 요금 설정:")
        print(f"     5kg  - 신용: {goodsflow_info.vendor_credit_fee_05kg:,}원, 선불: {goodsflow_info.vendor_cash_fee_05kg:,}원, 착불: {goodsflow_info.consumer_cash_fee_05kg:,}원, 반품: {goodsflow_info.return_fee_05kg:,}원")
        print(f"     10kg - 신용: {goodsflow_info.vendor_credit_fee_10kg:,}원, 선불: {goodsflow_info.vendor_cash_fee_10kg:,}원, 착불: {goodsflow_info.consumer_cash_fee_10kg:,}원, 반품: {goodsflow_info.return_fee_10kg:,}원")
        print(f"     20kg - 신용: {goodsflow_info.vendor_credit_fee_20kg:,}원, 선불: {goodsflow_info.vendor_cash_fee_20kg:,}원, 착불: {goodsflow_info.consumer_cash_fee_20kg:,}원, 반품: {goodsflow_info.return_fee_20kg:,}원")
        
        # 반품지 생성 실행
        result = client.create_return_center(request)
        
        if result.get("success"):
            print(f"\n✅ 중량별 차등 요금 반품지 생성 성공:")
            print(f"   🏷️ 반품지 코드: {result.get('returnCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            
            print(f"\n📋 설정된 요금 체계:")
            print(f"   💰 경량 상품(5kg): 더 저렴한 요금")
            print(f"   💰 중량 상품(10kg): 중간 요금")
            print(f"   💰 무거운 상품(20kg): 더 높은 요금")
            
        else:
            print(f"\n❌ 중량별 차등 요금 반품지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 중량별 차등 요금 반품지 테스트 오류: {e}")


def test_validation_scenarios():
    """반품지 생성 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 반품지 생성 검증 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        # 잘못된 파라미터들로 테스트
        test_scenarios = [
            {
                "name": "지원하지 않는 택배사 코드",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "shipping_place_name": "잘못된 택배사 반품지",
                    "zip_code": "12345",
                    "address": "테스트 주소",
                    "address_detail": "테스트 상세주소",
                    "contact_number": "02-1234-5678",
                    "delivery_code": "INVALID",  # 잘못된 택배사 코드
                    "contract_number": "12345678"
                },
                "expected_error": "지원하지 않는 택배사"
            },
            {
                "name": "잘못된 전화번호 형식",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "shipping_place_name": "잘못된 전화번호 반품지",
                    "zip_code": "12345",
                    "address": "테스트 주소",
                    "address_detail": "테스트 상세주소",
                    "contact_number": "1234567890",  # 잘못된 형식 (하이픈 없음)
                    "delivery_code": "CJGLS",
                    "contract_number": "12345678"
                },
                "expected_error": "전화번호 형식"
            },
            {
                "name": "잘못된 우편번호",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "shipping_place_name": "잘못된 우편번호 반품지",
                    "zip_code": "123",  # 너무 짧음
                    "address": "테스트 주소",
                    "address_detail": "테스트 상세주소",
                    "contact_number": "02-1234-5678",
                    "delivery_code": "CJGLS",
                    "contract_number": "12345678"
                },
                "expected_error": "우편번호는 5-6자리"
            },
            {
                "name": "음수 요금",
                "params": {
                    "vendor_id": "A00012345",
                    "user_id": "testUser",
                    "shipping_place_name": "음수 요금 반품지",
                    "zip_code": "12345",
                    "address": "테스트 주소",
                    "address_detail": "테스트 상세주소",
                    "contact_number": "02-1234-5678",
                    "delivery_code": "CJGLS",
                    "contract_number": "12345678",
                    "vendor_credit_fee": -1000  # 음수 요금
                },
                "expected_error": "0 이상이어야 합니다"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n⚠️ 시나리오 {i}: {scenario['name']}")
            
            try:
                result = client.create_domestic_return_center(**scenario["params"])
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


def test_epost_specific_requirements():
    """우체국택배 특별 요구사항 테스트"""
    print("\n" + "=" * 60 + " 우체국택배 특별 요구사항 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        print(f"\n📮 우체국택배 업체코드 필수 검증...")
        
        # 우체국택배인데 업체코드 없는 경우
        print(f"\n⚠️ 우체국택배 + 업체코드 없음 테스트:")
        try:
            result = client.create_domestic_return_center(
                vendor_id="A00012345",
                user_id="epostTestUser",
                shipping_place_name="우체국택배 반품지 (업체코드 없음)",
                zip_code="12345",
                address="테스트 주소",
                address_detail="테스트 상세주소",
                contact_number="02-1234-5678",
                delivery_code="EPOST",
                contract_number="11223344",
                contract_customer_number=""  # 업체코드 없음
            )
            print(f"   ❌ 예상치 못한 성공: {result}")
        except ValueError as e:
            if "업체코드" in str(e):
                print(f"   ✅ 예상된 검증 오류: {e}")
            else:
                print(f"   ❓ 다른 오류: {e}")
        
        # 우체국택배 + 업체코드 있는 경우 (정상)
        print(f"\n✅ 우체국택배 + 업체코드 있음 테스트:")
        try:
            result = client.create_domestic_return_center(
                vendor_id="A00012345",
                user_id="epostValidTestUser",
                shipping_place_name="우체국택배 반품지 (정상)",
                zip_code="12345",
                address="테스트 주소",
                address_detail="테스트 상세주소",
                contact_number="02-1234-5678",
                delivery_code="EPOST",
                contract_number="11223344",
                contract_customer_number="999888777"  # 업체코드 있음
            )
            
            if result.get("success"):
                print(f"   ✅ 우체국택배 반품지 생성 성공: {result.get('returnCenterCode')}")
            else:
                print(f"   ❌ 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            
    except Exception as e:
        print(f"❌ 우체국택배 특별 요구사항 테스트 오류: {e}")


def test_return_center_query():\
    """반품지 조회 테스트"""
    print("\n" + "=" * 60 + " 반품지 조회 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        vendor_id = "A00012345"  # 실제 벤더 ID로 변경 필요
        
        print(f"\n📦 반품지 목록 조회 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 1. 페이징으로 반품지 조회
        print(f"\n1️⃣ 페이징으로 반품지 조회 (1페이지, 5개씩)")
        response = client.get_return_centers(vendor_id, page_num=1, page_size=5)
        
        print(f"   📊 페이징 정보:")
        print(f"      현재 페이지: {response.pagination.current_page}")
        print(f"      전체 페이지: {response.pagination.total_pages}")
        print(f"      전체 데이터: {response.pagination.total_elements}")
        print(f"      페이지당 수: {response.pagination.count_per_page}")
        
        print(f"\n   📋 반품지 목록 ({len(response.content)}개):")
        for i, center in enumerate(response.content, 1):
            print(f"      {i}. [{center.return_center_code}] {center.shipping_place_name}")
            print(f"         📦 택배사: {center.deliver_name} ({center.deliver_code})")
            print(f"         📍 주소: {len(center.place_addresses)}개")
            print(f"         💰 5kg 신용요금: {center.vendor_credit_fee_05kg:,}원")
            print(f"         📅 생성일: {center.get_created_date_str()}")
            print(f"         🔄 사용여부: {'사용' if center.usable else '미사용'}")
            
            if center.place_addresses:
                addr = center.place_addresses[0]
                print(f"         📞 연락처: {addr.company_contact_number}")
                print(f"         🏠 주소: {addr.return_address}")
        
        # 2. 모든 반품지 조회
        print(f"\n2️⃣ 모든 반품지 조회")
        all_centers = client.get_all_return_centers(vendor_id)
        print(f"   📦 총 반품지 수: {len(all_centers)}개")
        
        # 3. 반품지명으로 검색
        if all_centers:
            first_center_name = all_centers[0].shipping_place_name
            print(f"\n3️⃣ 반품지명으로 검색: '{first_center_name}'")
            found_center = client.find_return_center_by_name(vendor_id, first_center_name)
            if found_center:
                print(f"   ✅ 검색 성공: [{found_center.return_center_code}] {found_center.shipping_place_name}")
            else:
                print(f"   ❌ 검색 실패")
        
        # 4. 반품지 코드로 검색
        if all_centers:
            first_center_code = all_centers[0].return_center_code
            print(f"\n4️⃣ 반품지 코드로 검색: '{first_center_code}'")
            found_center = client.find_return_center_by_code(vendor_id, first_center_code)
            if found_center:
                print(f"   ✅ 검색 성공: [{found_center.return_center_code}] {found_center.shipping_place_name}")
            else:
                print(f"   ❌ 검색 실패")
        
        # 5. 사용 가능한 반품지만 조회
        print(f"\n5️⃣ 사용 가능한 반품지만 조회")
        usable_centers = client.get_usable_return_centers(vendor_id)
        print(f"   📦 사용 가능한 반품지: {len(usable_centers)}개")
        for center in usable_centers[:3]:  # 최대 3개만 출력
            print(f"      ✅ [{center.return_center_code}] {center.shipping_place_name}")
        
        # 6. 택배사별 반품지 조회
        print(f"\n6️⃣ 택배사별 반품지 조회")
        delivery_codes = ["CJGLS", "KGB", "HANJIN", "EPOST"]
        for delivery_code in delivery_codes:
            centers = client.get_return_centers_by_delivery_code(vendor_id, delivery_code)
            delivery_name = client.SUPPORTED_DELIVERY_CODES.get(delivery_code, "알 수 없음")
            print(f"      📦 {delivery_name}({delivery_code}): {len(centers)}개")
            
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 반품지 조회 오류: {e}")


def test_return_center_query_validation():\
    """반품지 조회 검증 테스트"""
    print("\n" + "=" * 60 + " 반품지 조회 검증 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        # 잘못된 파라미터 테스트
        test_scenarios = [
            {
                "name": "빈 vendor_id",
                "vendor_id": "",
                "page_num": 1,
                "page_size": 10,
                "expected_error": "vendor_id는 필수"
            },
            {
                "name": "잘못된 page_num (0)",
                "vendor_id": "A00012345",
                "page_num": 0,
                "page_size": 10,
                "expected_error": "page_num은 1 이상"
            },
            {
                "name": "잘못된 page_size (0)",
                "vendor_id": "A00012345",
                "page_num": 1,
                "page_size": 0,
                "expected_error": "page_size는 1-100 사이"
            },
            {
                "name": "잘못된 page_size (101)",
                "vendor_id": "A00012345",
                "page_num": 1,
                "page_size": 101,
                "expected_error": "page_size는 1-100 사이"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n⚠️ 시나리오 {i}: {scenario['name']}")
            
            try:
                response = client.get_return_centers(
                    vendor_id=scenario["vendor_id"],
                    page_num=scenario["page_num"],
                    page_size=scenario["page_size"]
                )
                print(f"   ❌ 예상치 못한 성공: {response}")
                
            except ValueError as e:
                if scenario["expected_error"] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 반품지 조회 검증 테스트 오류: {e}")


def test_return_center_update():
    """반품지 수정 테스트"""
    print("\n" + "=" * 60 + " 반품지 수정 테스트 " + "=" * 60)
    
    try:
        from market.coupang.ReturnCenters.return_center_client import (
            ReturnCenterUpdateRequest,
            ReturnCenterUpdateAddress,
            ReturnCenterUpdateGoodsflowInfo
        )
        
        client = ReturnCenterClient()
        vendor_id = "A00012345"  # 실제 벤더 ID로 변경 필요
        
        print(f"\n📦 반품지 수정 테스트 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 1. 반품지명만 수정
        print(f"\n1️⃣ 반품지명만 수정")
        try:
            result = client.update_return_center_name(
                vendor_id=vendor_id,
                return_center_code="1100044653",  # 실제 반품지 코드로 변경 필요
                user_id="testUpdateUser",
                new_name="수정된 반품지명"
            )
            
            if result.get("success"):
                print(f"   ✅ 반품지명 수정 성공: {result.get('resultMessage')}")
            else:
                print(f"   ❌ 반품지명 수정 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 반품지명 수정 오류: {e}")
        
        # 2. 사용여부만 수정
        print(f"\n2️⃣ 사용여부만 수정")
        try:
            result = client.update_return_center_usable(
                vendor_id=vendor_id,
                return_center_code="1100044653",
                user_id="testUpdateUser",
                usable=False  # 사용안함으로 변경
            )
            
            if result.get("success"):
                print(f"   ✅ 사용여부 수정 성공: {result.get('resultMessage')}")
            else:
                print(f"   ❌ 사용여부 수정 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 사용여부 수정 오류: {e}")
        
        # 3. 주소만 수정
        print(f"\n3️⃣ 주소만 수정")
        try:
            result = client.update_return_center_address(
                vendor_id=vendor_id,
                return_center_code="1100044653",
                user_id="testUpdateUser",
                zip_code="06292",
                address="서울특별시 강남구 테헤란로 456",
                address_detail="수정된 빌딩 7층",
                contact_number="02-9999-8888",
                phone_number2="010-1111-2222",
                address_type="ROADNAME"
            )
            
            if result.get("success"):
                print(f"   ✅ 주소 수정 성공: {result.get('resultMessage')}")
            else:
                print(f"   ❌ 주소 수정 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 주소 수정 오류: {e}")
        
        # 4. 요금만 수정
        print(f"\n4️⃣ 요금만 수정 (모든 중량 동일)")
        try:
            result = client.update_return_center_fees(
                vendor_id=vendor_id,
                return_center_code="1100044653",
                user_id="testUpdateUser",
                vendor_credit_fee=3000,  # 모든 중량 3000원
                vendor_cash_fee=2900,
                consumer_cash_fee=3100,
                return_fee=3200
            )
            
            if result.get("success"):
                print(f"   ✅ 요금 수정 성공: {result.get('resultMessage')}")
            else:
                print(f"   ❌ 요금 수정 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 요금 수정 오류: {e}")
        
        # 5. 복합 수정 (여러 필드 동시)
        print(f"\n5️⃣ 복합 수정 (반품지명 + 사용여부 + 주소)")
        try:
            # 수정 주소 정보
            update_address = ReturnCenterUpdateAddress(
                address_type="JIBUN",
                company_contact_number="02-5555-6666",
                phone_number2="010-7777-8888",
                return_zip_code="12345",
                return_address="서울특별시 종로구 종로 99",
                return_address_detail="복합수정 테스트빌딩 10층"
            )
            
            # 수정 요금 정보 (중량별 차등)
            update_goodsflow = ReturnCenterUpdateGoodsflowInfo(
                vendor_credit_fee_05kg=2200,
                vendor_credit_fee_10kg=2700,
                vendor_credit_fee_20kg=3200,
                vendor_cash_fee_05kg=2100,
                vendor_cash_fee_10kg=2600,
                vendor_cash_fee_20kg=3100
            )
            
            # 복합 수정 요청
            request = ReturnCenterUpdateRequest(
                vendor_id=vendor_id,
                return_center_code="1100044653",
                user_id="testUpdateUser",
                shipping_place_name="복합수정 테스트 반품지",
                usable=True,  # 다시 사용가능으로
                place_addresses=[update_address],
                goodsflow_info=update_goodsflow
            )
            
            result = client.update_return_center(request)
            
            if result.get("success"):
                print(f"   ✅ 복합 수정 성공: {result.get('resultMessage')}")
                print(f"      📝 반품지명: 복합수정 테스트 반품지")
                print(f"      🔄 사용여부: 사용")
                print(f"      📍 주소: 서울특별시 종로구 종로 99")
                print(f"      💰 5kg 신용요금: 2,200원")
            else:
                print(f"   ❌ 복합 수정 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 복합 수정 오류: {e}")
            
    except Exception as e:
        print(f"❌ 반품지 수정 테스트 오류: {e}")


def test_return_center_update_validation():
    """반품지 수정 검증 테스트"""
    print("\n" + "=" * 60 + " 반품지 수정 검증 테스트 " + "=" * 60)
    
    try:
        from market.coupang.ReturnCenters.return_center_client import (
            ReturnCenterUpdateRequest
        )
        
        client = ReturnCenterClient()
        
        # 잘못된 파라미터 테스트
        test_scenarios = [
            {
                "name": "빈 vendor_id",
                "vendor_id": "",
                "return_center_code": "1100044653",
                "user_id": "testUser",
                "expected_error": "vendor_id는 필수"
            },
            {
                "name": "빈 return_center_code",
                "vendor_id": "A00012345",
                "return_center_code": "",
                "user_id": "testUser",
                "expected_error": "return_center_code는 필수"
            },
            {
                "name": "빈 user_id",
                "vendor_id": "A00012345",
                "return_center_code": "1100044653",
                "user_id": "",
                "expected_error": "user_id는 필수"
            },
            {
                "name": "빈 반품지명",
                "vendor_id": "A00012345",
                "return_center_code": "1100044653",
                "user_id": "testUser",
                "shipping_place_name": "",
                "expected_error": "빈 문자열"
            },
            {
                "name": "긴 반품지명 (101자)",
                "vendor_id": "A00012345",
                "return_center_code": "1100044653",
                "user_id": "testUser",
                "shipping_place_name": "a" * 101,
                "expected_error": "100자를 초과"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n⚠️ 시나리오 {i}: {scenario['name']}")
            
            try:
                request = ReturnCenterUpdateRequest(
                    vendor_id=scenario["vendor_id"],
                    return_center_code=scenario["return_center_code"],
                    user_id=scenario["user_id"],
                    shipping_place_name=scenario.get("shipping_place_name")
                )
                
                result = client.update_return_center(request)
                print(f"   ❌ 예상치 못한 성공: {result}")
                
            except ValueError as e:
                if scenario["expected_error"] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 반품지 수정 검증 테스트 오류: {e}")


def test_return_center_detail_query():
    """반품지 단건 조회 테스트"""
    print("\n" + "=" * 60 + " 반품지 단건 조회 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        print(f"\n📦 반품지 센터코드로 상세 정보 조회...")
        
        # 1. 단건 조회
        print(f"\n1️⃣ 단건 반품지 상세 조회")
        try:
            center_code = "1000552675"  # 예시 반품지 코드
            detail = client.get_return_center_detail(center_code)
            
            if detail:
                print(f"   ✅ 반품지 상세 조회 성공:")
                print(f"      🏷️ 코드: {detail.return_center_code}")
                print(f"      📝 이름: {detail.shipping_place_name}")
                print(f"      📦 택배사: {detail.deliver_name} ({detail.deliver_code})")
                print(f"      📅 생성일: {detail.get_created_date_str()}")
                print(f"      🔄 사용여부: {'사용' if detail.usable else '미사용'}")
                print(f"      ⚡ 굿스플로 상태: {detail.goodsflow_status}")
                
                # 요금 정보
                print(f"\n   💰 요금 정보:")
                print(f"      2kg - 신용: {detail.vendor_credit_fee_02kg:,}원, 선불: {detail.vendor_cash_fee_02kg:,}원, 착불: {detail.consumer_cash_fee_02kg:,}원, 반품: {detail.return_fee_02kg:,}원")
                print(f"      5kg - 신용: {detail.vendor_credit_fee_05kg:,}원, 선불: {detail.vendor_cash_fee_05kg:,}원, 착불: {detail.consumer_cash_fee_05kg:,}원, 반품: {detail.return_fee_05kg:,}원")
                print(f"     10kg - 신용: {detail.vendor_credit_fee_10kg:,}원, 선불: {detail.vendor_cash_fee_10kg:,}원, 착불: {detail.consumer_cash_fee_10kg:,}원, 반품: {detail.return_fee_10kg:,}원")
                print(f"     20kg - 신용: {detail.vendor_credit_fee_20kg:,}원, 선불: {detail.vendor_cash_fee_20kg:,}원, 착불: {detail.consumer_cash_fee_20kg:,}원, 반품: {detail.return_fee_20kg:,}원")
                
                # 주소 정보
                if detail.place_addresses:
                    addr = detail.place_addresses[0]
                    print(f"\n   📍 주소 정보:")
                    print(f"      타입: {addr.address_type}")
                    print(f"      국가: {addr.country_code}")
                    print(f"      주소: {addr.return_address}")
                    print(f"      상세: {addr.return_address_detail}")
                    print(f"      우편번호: {addr.return_zip_code}")
                    print(f"      연락처: {addr.company_contact_number}")
                    if addr.phone_number2:
                        print(f"      보조연락처: {addr.phone_number2}")
            else:
                print(f"   ❌ 반품지를 찾을 수 없습니다: {center_code}")
                
        except Exception as e:
            print(f"   ❌ 단건 조회 오류: {e}")
        
        # 2. 다건 조회
        print(f"\n2️⃣ 다건 반품지 상세 조회")
        try:
            center_codes = ["1000552675", "1000006047", "1000558900"]  # 예시 반품지 코드들
            details = client.get_multiple_return_center_details(center_codes)
            
            print(f"   📦 조회된 반품지 수: {len(details)}개")
            for i, detail in enumerate(details, 1):
                print(f"      {i}. [{detail.return_center_code}] {detail.shipping_place_name}")
                print(f"         택배사: {detail.deliver_name}")
                print(f"         상태: {'사용' if detail.usable else '미사용'}")
                print(f"         5kg 신용요금: {detail.vendor_credit_fee_05kg:,}원")
                
        except Exception as e:
            print(f"   ❌ 다건 조회 오류: {e}")
        
        # 3. 문자열 형태로 조회
        print(f"\n3️⃣ 쉼표 구분 문자열로 조회")
        try:
            codes_str = "1000552675,1000006047"
            details = client.get_return_center_details(codes_str)
            
            print(f"   📦 문자열 조회 결과: {len(details)}개")
            for detail in details:
                print(f"      [{detail.return_center_code}] {detail.shipping_place_name}")
                
        except Exception as e:
            print(f"   ❌ 문자열 조회 오류: {e}")
        
        # 4. 청크 단위 대량 조회
        print(f"\n4️⃣ 청크 단위 대량 조회 (시뮬레이션)")
        try:
            # 가상의 대량 코드 목록 (실제로는 존재하는 코드를 사용해야 함)
            large_code_list = [f"100000{i:04d}" for i in range(1, 101)]  # 100개 코드
            print(f"   📦 대량 조회 대상: {len(large_code_list)}개 코드")
            print(f"   📦 청크 크기: 20개씩")
            
            # 실제로는 존재하지 않는 코드들이므로 오류가 발생할 수 있음
            try:
                details = client.get_return_center_details_by_chunks(large_code_list, chunk_size=20)
                print(f"   ✅ 청크 조회 완료: {len(details)}개 조회됨")
            except Exception as chunk_error:
                print(f"   ⚠️ 청크 조회 실패 (예상됨 - 가상 코드): {chunk_error}")
                
        except Exception as e:
            print(f"   ❌ 청크 조회 오류: {e}")
            
    except Exception as e:
        print(f"❌ 반품지 단건 조회 테스트 오류: {e}")


def test_return_center_detail_validation():
    """반품지 단건 조회 검증 테스트"""
    print("\n" + "=" * 60 + " 반품지 단건 조회 검증 테스트 " + "=" * 60)
    
    try:
        client = ReturnCenterClient()
        
        # 잘못된 파라미터 테스트
        test_scenarios = [
            {
                "name": "빈 문자열 코드",
                "codes": "",
                "expected_error": "빈 값"
            },
            {
                "name": "빈 리스트",
                "codes": [],
                "expected_error": "빈 목록"
            },
            {
                "name": "너무 많은 코드 (101개)",
                "codes": [f"code{i}" for i in range(101)],
                "expected_error": "최대 100개"
            },
            {
                "name": "잘못된 타입 (숫자)",
                "codes": 12345,
                "expected_error": "문자열 또는 리스트"
            },
            {
                "name": "리스트 내 빈 값",
                "codes": ["1000000001", "", "1000000003"],
                "expected_error": "빈 값"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n⚠️ 시나리오 {i}: {scenario['name']}")
            
            try:
                details = client.get_return_center_details(scenario["codes"])
                print(f"   ❌ 예상치 못한 성공: {len(details)}개 조회됨")
                
            except ValueError as e:
                if scenario["expected_error"] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 반품지 단건 조회 검증 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 반품지 API 테스트 시작")
    
    try:
        # 반품지 생성 테스트
        test_return_center_creation_basic()
        test_return_center_with_multiple_delivery_services()
        test_return_center_with_custom_fees()
        test_validation_scenarios()
        test_epost_specific_requirements()
        
        # 반품지 조회 테스트
        test_return_center_query()
        test_return_center_query_validation()
        
        # 반품지 수정 테스트
        test_return_center_update()
        test_return_center_update_validation()
        
        # 반품지 단건 조회 테스트 추가
        test_return_center_detail_query()
        test_return_center_detail_validation()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("\n💡 주요 학습 내용:")
        print("   1. 반품지는 택배사 계약 정보가 반드시 필요함")
        print("   2. 중량별(2kg, 5kg, 10kg, 20kg) 차등 요금 설정 가능")
        print("   3. 4가지 요금 유형: 신용, 선불, 착불, 반품비")
        print("   4. 우체국택배는 업체코드(contractCustomerNumber) 필수")
        print("   5. 지원 택배사: 롯데, 로젠, 우체국, 한진, CJ대한통운, 일양")
        print("   6. 전화번호는 xx-yyy-zzzz 형식 필수")
        print("   7. 반품지 조회는 페이징 지원 (pageNum, pageSize)")
        print("   8. 반품지명/코드로 개별 검색 가능")
        print("   9. 사용여부/택배사별 필터링 조회 가능")
        print("  10. 반품지 수정은 반품지 코드 필수")
        print("  11. 부분 수정 가능 (원하는 필드만 수정)")
        print("  12. 편의 메서드로 간단한 수정 지원")
        print("  13. 반품지 센터코드로 단건/다건 상세 조회")
        print("  14. 최대 100개까지 일괄 조회 가능")
        print("  15. 2kg 요금 정보 포함 완전한 상세 정보")
        
        print(f"\n🔧 실제 API 테스트 방법:")
        print("   - return_center_test.py 파일 사용")
        print("   - 환경변수에 실제 API 키 설정 필요")
        print("   - 실제 택배사 계약번호 필요")
        print("   - 실제 반품지 코드 필요 (조회 API로 확인)")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()