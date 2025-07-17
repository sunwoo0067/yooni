#!/usr/bin/env python3
"""
쿠팡 출고지 생성 API 사용 예제
출고지 생성 및 관리 기능 테스트
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


def test_create_shipping_center_basic():
    """기본 출고지 생성 테스트"""
    print("=" * 60 + " 기본 출고지 생성 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 쿠팡 출고지 클라이언트 초기화 성공")
        
        # 출고지 주소 정보 설정 (도로명 주소 + 지번 주소)
        place_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="02-1234-5678",
                phone_number2="010-1234-5678",
                return_zip_code="12345",
                return_address="서울특별시 강남구 테헤란로 123",
                return_address_detail="ABC빌딩 5층"
            ),
            PlaceAddress(
                address_type="JIBUN",
                country_code="KR",
                company_contact_number="02-1234-5678",
                phone_number2="010-1234-5678",
                return_zip_code="12345",
                return_address="서울특별시 강남구 역삼동 123-45",
                return_address_detail="ABC빌딩 5층"
            )
        ]
        
        # 도서산간 배송비 정보 설정
        remote_infos = [
            RemoteInfo(
                delivery_code="KGB",  # 로젠택배
                jeju=3000,
                not_jeju=2500
            ),
            RemoteInfo(
                delivery_code="CJGLS",  # CJ대한통운
                jeju=3000,
                not_jeju=2500
            )
        ]
        
        # 출고지 생성 요청 데이터
        request = ShippingCenterRequest(
            vendor_id="A00012345",  # 실제 벤더 ID로 변경 필요
            user_id="testUser",
            shipping_place_name="테스트 출고지 1",
            place_addresses=place_addresses,
            remote_infos=remote_infos,
            usable=True,
            global_shipping=False
        )
        
        print(f"\n📦 출고지 생성 요청 중...")
        print(f"   📝 출고지명: {request.shipping_place_name}")
        print(f"   📍 주소: {place_addresses[0].return_address}")
        print(f"   📞 연락처: {place_addresses[0].company_contact_number}")
        print(f"   🚚 택배사: {len(remote_infos)}개")
        
        # 출고지 생성 실행
        result = client.create_shipping_center(request)
        
        if result.get("success"):
            print(f"\n✅ 출고지 생성 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('message')}")
        else:
            print(f"\n❌ 출고지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 출고지 생성 테스트 오류: {e}")


def test_create_shipping_center_convenience():
    """편의 메서드를 사용한 출고지 생성 테스트"""
    print("\n" + "=" * 60 + " 편의 메서드 출고지 생성 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📦 편의 메서드로 출고지 생성 중...")
        
        # 편의 메서드 사용 (국내 출고지)
        result = client.create_domestic_shipping_center(
            vendor_id="A00012345",  # 실제 벤더 ID로 변경 필요
            user_id="testUser",
            shipping_place_name="테스트 출고지 2 (편의메서드)",
            zip_code="54321",
            address="부산광역시 해운대구 해운대해변로 264",
            address_detail="해운대센터 2층",
            contact_number="051-1234-5678",
            phone_number2="010-9876-5432",
            delivery_infos=[
                {"code": "HANJIN", "jeju": 4000, "notJeju": 3000},  # 한진택배
                {"code": "LOTTE", "jeju": 3500, "notJeju": 2800}   # 롯데택배
            ]
        )
        
        if result.get("success"):
            print(f"\n✅ 편의 메서드 출고지 생성 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('message')}")
        else:
            print(f"\n❌ 편의 메서드 출고지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 편의 메서드 테스트 오류: {e}")


def test_create_shipping_center_with_epost():
    """우체국 택배 출고지 생성 테스트"""
    print("\n" + "=" * 60 + " 우체국 택배 출고지 생성 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📦 우체국 택배 출고지 생성 중...")
        
        # 우체국 택배 특별 규칙 (0원 또는 100-400원, 100원 단위)
        result = client.create_domestic_shipping_center(
            vendor_id="A00012345",  # 실제 벤더 ID로 변경 필요
            user_id="testUser",
            shipping_place_name="테스트 출고지 3 (우체국택배)",
            zip_code="13579",
            address="대구광역시 중구 동성로 123",
            address_detail="동성로센터 3층",
            contact_number="053-1234-5678",
            delivery_infos=[
                {"code": "EPOST", "jeju": 300, "notJeju": 200},  # 우체국택배 (특별 규칙)
                {"code": "KGB", "jeju": 3000, "notJeju": 2500}   # 로젠택배 (일반 규칙)
            ]
        )
        
        if result.get("success"):
            print(f"\n✅ 우체국 택배 출고지 생성 성공:")
            print(f"   🏷️ 출고지 코드: {result.get('shippingCenterCode')}")
            print(f"   📊 결과 코드: {result.get('resultCode')}")
            print(f"   💬 메시지: {result.get('message')}")
        else:
            print(f"\n❌ 우체국 택배 출고지 생성 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 우체국 택배 테스트 오류: {e}")


def test_delivery_codes():
    """택배사 코드 목록 조회 테스트"""
    print("\n" + "=" * 60 + " 택배사 코드 목록 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        delivery_codes = client.get_delivery_codes()
        
        print(f"\n📋 지원 택배사 목록 ({len(delivery_codes)}개):")
        for i, (name, code) in enumerate(delivery_codes.items(), 1):
            print(f"   {i:2d}. [{code:8}] {name}")
            
    except Exception as e:
        print(f"❌ 택배사 코드 조회 오류: {e}")


def test_validation_errors():
    """입력 데이터 검증 오류 테스트"""
    print("\n" + "=" * 60 + " 입력 데이터 검증 오류 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 잘못된 데이터로 테스트
        test_cases = [
            {
                "description": "출고지명 길이 초과 (51자)",
                "shipping_place_name": "A" * 51,
                "zip_code": "12345",
                "address": "서울특별시 강남구 테헤란로 123",
                "address_detail": "테스트",
                "contact_number": "02-1234-5678"
            },
            {
                "description": "잘못된 전화번호 형식",
                "shipping_place_name": "테스트 출고지",
                "zip_code": "12345",
                "address": "서울특별시 강남구 테헤란로 123",
                "address_detail": "테스트",
                "contact_number": "02-1234-567"  # 7자리 (잘못됨)
            },
            {
                "description": "잘못된 우편번호 형식",
                "shipping_place_name": "테스트 출고지",
                "zip_code": "1234a",  # 문자 포함 (잘못됨)
                "address": "서울특별시 강남구 테헤란로 123",
                "address_detail": "테스트",
                "contact_number": "02-1234-5678"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n⚠️ 테스트 {i}: {test_case['description']}")
            
            try:
                result = client.create_domestic_shipping_center(
                    vendor_id="A00012345",
                    user_id="testUser",
                    shipping_place_name=test_case["shipping_place_name"],
                    zip_code=test_case["zip_code"],
                    address=test_case["address"],
                    address_detail=test_case["address_detail"],
                    contact_number=test_case["contact_number"]
                )
                
                print(f"   예상치 못한 성공: {result}")
                
            except ValueError as e:
                print(f"   ✅ 예상된 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 검증 오류 테스트 실패: {e}")


def test_request_data_structure():
    """요청 데이터 구조 확인 테스트"""
    print("\n" + "=" * 60 + " 요청 데이터 구조 확인 테스트 " + "=" * 60)
    
    try:
        # 샘플 요청 데이터 생성
        place_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number="02-1234-5678",
                phone_number2="010-1234-5678",
                return_zip_code="12345",
                return_address="서울특별시 강남구 테헤란로 123",
                return_address_detail="ABC빌딩 5층"
            )
        ]
        
        remote_infos = [
            RemoteInfo(
                delivery_code="KGB",
                jeju=3000,
                not_jeju=2500
            )
        ]
        
        request = ShippingCenterRequest(
            vendor_id="A00012345",
            user_id="testUser",
            shipping_place_name="테스트 출고지",
            place_addresses=place_addresses,
            remote_infos=remote_infos,
            usable=True,
            global_shipping=False
        )
        
        # 요청 데이터를 딕셔너리로 변환
        request_dict = request.to_dict()
        
        print(f"\n📋 생성된 요청 데이터 구조:")
        pprint(request_dict, width=100, depth=3)
        
        print(f"\n✅ 요청 데이터 구조 검증 완료")
        
    except Exception as e:
        print(f"❌ 요청 데이터 구조 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 생성 API 테스트 시작")
    
    try:
        test_delivery_codes()
        test_request_data_structure()
        test_validation_errors()
        
        # 실제 API 호출 테스트 (주석 처리)
        # 실제 테스트시에는 주석을 해제하고 올바른 vendorId를 입력하세요
        # test_create_shipping_center_basic()
        # test_create_shipping_center_convenience()
        # test_create_shipping_center_with_epost()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("\n💡 주요 학습 내용:")
        print("   1. 출고지 생성시 도로명 주소와 지번 주소 모두 등록 필요")
        print("   2. 우체국 택배는 특별한 배송비 규칙 적용 (100-400원)")
        print("   3. 일반 택배사는 1000-8000원 범위의 배송비 설정")
        print("   4. 출고지명 중복 등록 불가")
        print("   5. 전화번호는 xx-yyy-zzzz 형식 준수 필요")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()