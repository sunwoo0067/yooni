#!/usr/bin/env python3
"""
쿠팡 출고지 조회 API 사용 예제
등록된 출고지 목록 조회 및 검색 기능 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.ShippingCenters.shipping_center_client import ShippingCenterClient


def test_get_shipping_places_pagination():
    """페이지네이션을 사용한 출고지 목록 조회 테스트"""
    print("=" * 60 + " 페이지네이션 출고지 목록 조회 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 쿠팡 출고지 클라이언트 초기화 성공")
        
        # 페이지별 조회 테스트
        page_sizes = [10, 20, 50]
        
        for page_size in page_sizes:
            print(f"\n📄 페이지 크기 {page_size}로 첫 번째 페이지 조회 중...")
            
            try:
                result = client.get_shipping_places(page_num=1, page_size=page_size)
                
                if result.get("success"):
                    print(f"✅ 조회 성공:")
                    print(f"   📊 총 출고지 수: {result.get('total_count')}개")
                    print(f"   📄 현재 페이지: {result.get('current_page')}")
                    print(f"   📄 총 페이지 수: {result.get('total_pages')}")
                    
                    shipping_data = result.get("data")
                    print(f"   📦 이번 페이지 출고지 수: {len(shipping_data.content)}개")
                    
                    # 출고지 목록 출력 (최대 3개)
                    for i, place in enumerate(shipping_data.content[:3], 1):
                        print(f"      {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name}")
                        print(f"         📍 주소: {place.place_addresses[0].return_address if place.place_addresses else 'N/A'}")
                        print(f"         📅 생성일: {place.create_date}")
                        print(f"         ✅ 활성화: {'예' if place.usable else '아니오'}")
                    
                    if len(shipping_data.content) > 3:
                        print(f"      ... 및 {len(shipping_data.content) - 3}개 더")
                        
                else:
                    print(f"❌ 조회 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 페이지 조회 오류: {e}")
                
    except Exception as e:
        print(f"❌ 페이지네이션 테스트 오류: {e}")


def test_get_all_shipping_places():
    """전체 출고지 목록 조회 테스트"""
    print("\n" + "=" * 60 + " 전체 출고지 목록 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📋 전체 출고지 목록 조회 중...")
        
        result = client.get_all_shipping_places()
        
        if result.get("success"):
            total_count = result.get("total_count")
            shipping_places = result.get("shipping_places", [])
            
            print(f"✅ 전체 조회 성공:")
            print(f"   📊 총 출고지 수: {total_count}개")
            print(f"   💬 메시지: {result.get('message')}")
            
            # 출고지 요약 통계
            active_count = sum(1 for place in shipping_places if place.usable)
            inactive_count = total_count - active_count
            
            print(f"\n📈 출고지 현황:")
            print(f"   ✅ 활성화된 출고지: {active_count}개")
            print(f"   ❌ 비활성화된 출고지: {inactive_count}개")
            
            # 최근 생성된 출고지 목록 (상위 5개)
            print(f"\n📋 전체 출고지 목록 (상위 5개):")
            for i, place in enumerate(shipping_places[:5], 1):
                status_emoji = "✅" if place.usable else "❌"
                print(f"   {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name} {status_emoji}")
                print(f"      📅 생성일: {place.create_date}")
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"      📍 주소: {addr.return_address}")
                    print(f"      📞 연락처: {addr.company_contact_number}")
                print(f"      🚚 택배사: {len(place.remote_infos)}개")
                
        else:
            print(f"❌ 전체 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 전체 조회 테스트 오류: {e}")


def test_get_shipping_place_by_code():
    """출고지 코드로 특정 출고지 조회 테스트"""
    print("\n" + "=" * 60 + " 출고지 코드 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 먼저 전체 목록에서 실제 출고지 코드를 가져오기
        print(f"\n🔍 실제 출고지 코드 확인 중...")
        all_result = client.get_all_shipping_places()
        
        if all_result.get("success") and all_result.get("shipping_places"):
            # 첫 번째 출고지 코드로 테스트
            first_place = all_result.get("shipping_places")[0]
            test_code = first_place.outbound_shipping_place_code
            
            print(f"📦 출고지 코드 {test_code}로 조회 중...")
            
            result = client.get_shipping_place_by_code(test_code)
            
            if result.get("success"):
                place = result.get("shipping_place")
                
                print(f"✅ 출고지 조회 성공:")
                print(f"   🏷️ 출고지 코드: {place.outbound_shipping_place_code}")
                print(f"   📝 출고지명: {place.shipping_place_name}")
                print(f"   📅 생성일: {place.create_date}")
                print(f"   ✅ 활성 상태: {'활성' if place.usable else '비활성'}")
                
                # 주소 정보
                print(f"\n📍 주소 정보:")
                for i, addr in enumerate(place.place_addresses, 1):
                    print(f"   {i}. 타입: {addr.address_type}")
                    print(f"      📍 주소: {addr.return_address}")
                    print(f"      📍 상세: {addr.return_address_detail}")
                    print(f"      📞 연락처: {addr.company_contact_number}")
                    if addr.phone_number2:
                        print(f"      📞 보조연락처: {addr.phone_number2}")
                
                # 배송비 정보
                print(f"\n🚚 배송비 정보:")
                for i, remote in enumerate(place.remote_infos, 1):
                    status = "활성" if remote.usable else "비활성"
                    print(f"   {i}. 택배사: {remote.delivery_code} ({status})")
                    print(f"      제주: {remote.jeju:,}원, 제주외: {remote.not_jeju:,}원")
                    
            else:
                print(f"❌ 출고지 조회 실패: {result.get('error')}")
                
            # 존재하지 않는 코드로 테스트
            print(f"\n🧪 존재하지 않는 코드 (999999)로 테스트...")
            invalid_result = client.get_shipping_place_by_code(999999)
            
            if not invalid_result.get("success"):
                print(f"✅ 예상된 오류: {invalid_result.get('error')}")
            else:
                print(f"⚠️ 예상치 못한 성공: {invalid_result}")
                
        else:
            print(f"❌ 실제 출고지 코드를 가져올 수 없습니다")
            
    except Exception as e:
        print(f"❌ 출고지 코드 조회 테스트 오류: {e}")


def test_get_shipping_place_by_name():
    """출고지명으로 특정 출고지 조회 테스트"""
    print("\n" + "=" * 60 + " 출고지명 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 먼저 전체 목록에서 실제 출고지명을 가져오기
        print(f"\n🔍 실제 출고지명 확인 중...")
        all_result = client.get_all_shipping_places()
        
        if all_result.get("success") and all_result.get("shipping_places"):
            # 첫 번째 출고지명으로 테스트
            first_place = all_result.get("shipping_places")[0]
            test_name = first_place.shipping_place_name
            
            print(f"📦 출고지명 '{test_name}'로 조회 중...")
            
            result = client.get_shipping_place_by_name(test_name)
            
            if result.get("success"):
                place = result.get("shipping_place")
                
                print(f"✅ 출고지 조회 성공:")
                print(f"   🏷️ 출고지 코드: {place.outbound_shipping_place_code}")
                print(f"   📝 출고지명: {place.shipping_place_name}")
                print(f"   📅 생성일: {place.create_date}")
                
                # 간단한 정보만 출력
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"   📍 주소: {addr.return_address}")
                    print(f"   📞 연락처: {addr.company_contact_number}")
                    
                print(f"   🚚 택배사 수: {len(place.remote_infos)}개")
                    
            else:
                print(f"❌ 출고지 조회 실패: {result.get('error')}")
                
            # 존재하지 않는 이름으로 테스트
            print(f"\n🧪 존재하지 않는 이름 ('없는출고지')로 테스트...")
            invalid_result = client.get_shipping_place_by_name("없는출고지")
            
            if not invalid_result.get("success"):
                print(f"✅ 예상된 오류: {invalid_result.get('error')}")
            else:
                print(f"⚠️ 예상치 못한 성공: {invalid_result}")
                
        else:
            print(f"❌ 실제 출고지명을 가져올 수 없습니다")
            
    except Exception as e:
        print(f"❌ 출고지명 조회 테스트 오류: {e}")


def test_find_shipping_places_by_pattern():
    """출고지명 패턴 검색 테스트"""
    print("\n" + "=" * 60 + " 출고지명 패턴 검색 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 다양한 패턴으로 검색 테스트
        search_patterns = ["테스트", "출고지", "API", "센터", "본사"]
        
        for pattern in search_patterns:
            print(f"\n🔍 '{pattern}' 패턴으로 검색 중...")
            
            try:
                result = client.find_shipping_places_by_name_pattern(pattern)
                
                if result.get("success"):
                    matched_count = result.get("matched_count")
                    matched_places = result.get("shipping_places", [])
                    
                    print(f"✅ 패턴 검색 성공:")
                    print(f"   📊 매칭된 출고지: {matched_count}개")
                    print(f"   💬 메시지: {result.get('message')}")
                    
                    # 매칭된 출고지 목록 (최대 3개)
                    for i, place in enumerate(matched_places[:3], 1):
                        status_emoji = "✅" if place.usable else "❌"
                        print(f"      {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name} {status_emoji}")
                    
                    if len(matched_places) > 3:
                        print(f"      ... 및 {len(matched_places) - 3}개 더")
                        
                else:
                    print(f"❌ 패턴 검색 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 패턴 검색 오류: {e}")
                
    except Exception as e:
        print(f"❌ 패턴 검색 테스트 오류: {e}")


def test_get_active_shipping_places():
    """활성화된 출고지만 조회 테스트"""
    print("\n" + "=" * 60 + " 활성화된 출고지 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n✅ 활성화된 출고지만 조회 중...")
        
        result = client.get_active_shipping_places()
        
        if result.get("success"):
            total_count = result.get("total_count")
            active_count = result.get("active_count")
            active_places = result.get("shipping_places", [])
            
            print(f"✅ 활성화된 출고지 조회 성공:")
            print(f"   📊 전체 출고지: {total_count}개")
            print(f"   ✅ 활성화된 출고지: {active_count}개")
            print(f"   📈 활성화 비율: {(active_count/total_count*100):.1f}%" if total_count > 0 else "   📈 활성화 비율: 0%")
            print(f"   💬 메시지: {result.get('message')}")
            
            # 활성화된 출고지 목록 (최대 5개)
            print(f"\n📋 활성화된 출고지 목록:")
            for i, place in enumerate(active_places[:5], 1):
                print(f"   {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name}")
                print(f"      📅 생성일: {place.create_date}")
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"      📍 주소: {addr.return_address}")
            
            if len(active_places) > 5:
                print(f"   ... 및 {len(active_places) - 5}개 더")
                
        else:
            print(f"❌ 활성화된 출고지 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 활성화된 출고지 조회 테스트 오류: {e}")


def test_validation_errors():
    """입력 파라미터 검증 오류 테스트"""
    print("\n" + "=" * 60 + " 입력 파라미터 검증 오류 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 잘못된 파라미터 조합 테스트
        test_cases = [
            {
                "description": "파라미터 없음",
                "params": {},
                "expected_error": "반드시 입력해야 합니다"
            },
            {
                "description": "잘못된 pageNum (0)",
                "params": {"page_num": 0, "page_size": 10},
                "expected_error": "1 이상이어야 합니다"
            },
            {
                "description": "잘못된 pageSize (100)",
                "params": {"page_num": 1, "page_size": 100},
                "expected_error": "50 이하여야 합니다"
            },
            {
                "description": "여러 모드 동시 지정",
                "params": {"page_num": 1, "page_size": 10, "place_codes": [123]},
                "expected_error": "하나만 지정할 수 있습니다"
            },
            {
                "description": "잘못된 place_codes (-1)",
                "params": {"place_codes": [-1]},
                "expected_error": "양의 정수 목록이어야 합니다"
            },
            {
                "description": "빈 place_names",
                "params": {"place_names": [""]},
                "expected_error": "비어있지 않은 문자열 목록이어야 합니다"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n⚠️ 테스트 {i}: {test_case['description']}")
            
            try:
                result = client.get_shipping_places(**test_case["params"])
                print(f"   예상치 못한 성공: {result}")
                
            except ValueError as e:
                if test_case["expected_error"] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 검증 오류 테스트 실패: {e}")


def test_shipping_place_data_structure():
    """출고지 데이터 구조 확인 테스트"""
    print("\n" + "=" * 60 + " 출고지 데이터 구조 확인 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📋 출고지 데이터 구조 확인 중...")
        
        # 첫 번째 페이지에서 1개만 조회
        result = client.get_shipping_places(page_num=1, page_size=1)
        
        if result.get("success"):
            shipping_data = result.get("data")
            
            if shipping_data.content:
                place = shipping_data.content[0]
                
                print(f"✅ 출고지 데이터 구조:")
                print(f"   🏷️ 출고지 코드: {place.outbound_shipping_place_code} (타입: {type(place.outbound_shipping_place_code).__name__})")
                print(f"   📝 출고지명: {place.shipping_place_name} (타입: {type(place.shipping_place_name).__name__})")
                print(f"   📅 생성일: {place.create_date} (타입: {type(place.create_date).__name__})")
                print(f"   ✅ 활성 상태: {place.usable} (타입: {type(place.usable).__name__})")
                
                print(f"\n📍 주소 정보 구조:")
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"   📦 주소 타입: {addr.address_type}")
                    print(f"   🌏 국가 코드: {addr.country_code}")
                    print(f"   📞 연락처: {addr.company_contact_number}")
                    print(f"   📮 우편번호: {addr.return_zip_code}")
                    print(f"   📍 주소: {addr.return_address}")
                    print(f"   📍 상세주소: {addr.return_address_detail}")
                
                print(f"\n🚚 배송비 정보 구조:")
                if place.remote_infos:
                    remote = place.remote_infos[0]
                    print(f"   🆔 배송정보 ID: {remote.remote_info_id}")
                    print(f"   🚚 택배사 코드: {remote.delivery_code}")
                    print(f"   🏝️ 제주 배송비: {remote.jeju}원")
                    print(f"   🌍 제주외 배송비: {remote.not_jeju}원")
                    print(f"   ✅ 활성 상태: {remote.usable}")
                
                print(f"\n📊 페이징 정보:")
                pagination = shipping_data.pagination
                print(f"   📄 현재 페이지: {pagination.current_page}")
                print(f"   📄 전체 페이지: {pagination.total_pages}")
                print(f"   📊 전체 요소 수: {pagination.total_elements}")
                print(f"   📄 페이지당 요소 수: {pagination.count_per_page}")
                
            else:
                print(f"❌ 조회된 출고지가 없습니다")
                
        else:
            print(f"❌ 데이터 구조 확인 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 데이터 구조 확인 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 조회 API 테스트 시작")
    
    try:
        test_shipping_place_data_structure()
        test_get_shipping_places_pagination()
        test_get_all_shipping_places()
        test_get_shipping_place_by_code()
        test_get_shipping_place_by_name()
        test_find_shipping_places_by_pattern()
        test_get_active_shipping_places()
        test_validation_errors()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("\n💡 주요 학습 내용:")
        print("   1. 세 가지 조회 모드: 페이지네이션, 출고지 코드, 출고지명")
        print("   2. 전체 목록 조회는 페이지네이션으로 구현")
        print("   3. 패턴 검색으로 유연한 출고지 찾기 가능")
        print("   4. 활성화된 출고지만 필터링하여 조회 가능")
        print("   5. 구조화된 응답 데이터로 편리한 정보 접근")
        
        print(f"\n🔧 실제 API 테스트 방법:")
        print("   - shipping_center_query_test.py 파일 사용")
        print("   - 환경변수에 실제 API 키 설정 필요")
        print("   - COUPANG_VENDOR_ID, COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()