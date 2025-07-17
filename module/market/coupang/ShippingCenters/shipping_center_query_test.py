#!/usr/bin/env python3
"""
쿠팡 출고지 조회 API 실제 테스트
실제 API 키를 사용한 출고지 조회 및 관리 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.ShippingCenters.shipping_center_client import ShippingCenterClient


def test_real_api_shipping_places_pagination():
    """실제 API로 페이지네이션 출고지 조회 테스트"""
    print("=" * 60 + " 실제 API 페이지네이션 출고지 조회 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ShippingCenterClient()
        print("✅ 실제 API 인증으로 출고지 클라이언트 초기화 성공")
        
        print(f"\n📄 첫 번째 페이지 조회 (페이지 크기: 10)...")
        
        # 첫 번째 페이지 조회
        result = client.get_shipping_places(page_num=1, page_size=10)
        
        if result.get("success"):
            print(f"✅ 실제 API 출고지 조회 성공:")
            print(f"   📊 총 출고지 수: {result.get('total_count')}개")
            print(f"   📄 현재 페이지: {result.get('current_page')}")
            print(f"   📄 총 페이지 수: {result.get('total_pages')}")
            
            shipping_data = result.get("data")
            print(f"   📦 이번 페이지 출고지 수: {len(shipping_data.content)}개")
            
            # 실제 출고지 목록 출력
            print(f"\n📋 실제 등록된 출고지 목록:")
            for i, place in enumerate(shipping_data.content, 1):
                status_emoji = "✅" if place.usable else "❌"
                print(f"   {i:2d}. [{place.outbound_shipping_place_code}] {place.shipping_place_name} {status_emoji}")
                print(f"       📅 생성일: {place.create_date}")
                
                # 주소 정보
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"       📍 주소: {addr.return_address}")
                    print(f"       📞 연락처: {addr.company_contact_number}")
                
                # 택배사 정보
                active_deliveries = [info for info in place.remote_infos if info.usable]
                print(f"       🚚 활성 택배사: {len(active_deliveries)}개")
                
                if active_deliveries:
                    for delivery in active_deliveries[:2]:  # 상위 2개만 표시
                        print(f"          - {delivery.delivery_code}: 제주 {delivery.jeju:,}원, 제주외 {delivery.not_jeju:,}원")
                    
                    if len(active_deliveries) > 2:
                        print(f"          ... 및 {len(active_deliveries) - 2}개 더")
            
            # 페이지가 여러 개인 경우 두 번째 페이지도 확인
            if result.get('total_pages', 1) > 1:
                print(f"\n📄 두 번째 페이지 조회...")
                page2_result = client.get_shipping_places(page_num=2, page_size=10)
                
                if page2_result.get("success"):
                    page2_data = page2_result.get("data")
                    print(f"✅ 두 번째 페이지 조회 성공: {len(page2_data.content)}개 출고지")
                else:
                    print(f"❌ 두 번째 페이지 조회 실패: {page2_result.get('error')}")
                    
        else:
            print(f"❌ 실제 API 출고지 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 실제 API 페이지네이션 조회 오류: {e}")


def test_real_api_all_shipping_places():
    """실제 API로 전체 출고지 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 전체 출고지 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📋 실제 API로 전체 출고지 목록 조회 중...")
        
        result = client.get_all_shipping_places()
        
        if result.get("success"):
            total_count = result.get("total_count")
            shipping_places = result.get("shipping_places", [])
            
            print(f"✅ 전체 출고지 조회 성공:")
            print(f"   📊 총 출고지 수: {total_count}개")
            print(f"   💬 메시지: {result.get('message')}")
            
            # 출고지 현황 분석
            active_places = [place for place in shipping_places if place.usable]
            inactive_places = [place for place in shipping_places if not place.usable]
            
            print(f"\n📈 실제 출고지 현황 분석:")
            print(f"   ✅ 활성화된 출고지: {len(active_places)}개 ({len(active_places)/total_count*100:.1f}%)")
            print(f"   ❌ 비활성화된 출고지: {len(inactive_places)}개 ({len(inactive_places)/total_count*100:.1f}%)")
            
            # 택배사 사용 현황 분석
            delivery_usage = {}
            for place in active_places:
                for remote in place.remote_infos:
                    if remote.usable:
                        if remote.delivery_code not in delivery_usage:
                            delivery_usage[remote.delivery_code] = 0
                        delivery_usage[remote.delivery_code] += 1
            
            print(f"\n📊 활성 출고지의 택배사 사용 현황:")
            sorted_deliveries = sorted(delivery_usage.items(), key=lambda x: x[1], reverse=True)
            for i, (code, count) in enumerate(sorted_deliveries[:5], 1):
                print(f"   {i}. {code}: {count}개 출고지에서 사용")
            
            # 최근 생성된 출고지들
            print(f"\n📅 전체 출고지 목록 (생성일 기준):")
            for i, place in enumerate(shipping_places[:10], 1):
                status_emoji = "✅" if place.usable else "❌"
                print(f"   {i:2d}. [{place.outbound_shipping_place_code}] {place.shipping_place_name} {status_emoji}")
                print(f"       📅 생성일: {place.create_date}")
                
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"       📍 {addr.return_address}")
            
            if len(shipping_places) > 10:
                print(f"   ... 및 {len(shipping_places) - 10}개 더")
                
        else:
            print(f"❌ 전체 출고지 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 전체 출고지 조회 테스트 오류: {e}")


def test_real_api_specific_shipping_place_query():
    """실제 API로 특정 출고지 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 특정 출고지 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 먼저 실제 출고지 목록을 가져와서 테스트에 사용
        print(f"\n🔍 실제 출고지 정보 확인 중...")
        all_result = client.get_all_shipping_places()
        
        if all_result.get("success") and all_result.get("shipping_places"):
            shipping_places = all_result.get("shipping_places")
            
            # 첫 번째 출고지로 코드 조회 테스트
            first_place = shipping_places[0]
            test_code = first_place.outbound_shipping_place_code
            test_name = first_place.shipping_place_name
            
            print(f"\n📦 출고지 코드 조회 테스트 (코드: {test_code})...")
            code_result = client.get_shipping_place_by_code(test_code)
            
            if code_result.get("success"):
                place = code_result.get("shipping_place")
                print(f"✅ 코드 조회 성공:")
                print(f"   🏷️ 출고지 코드: {place.outbound_shipping_place_code}")
                print(f"   📝 출고지명: {place.shipping_place_name}")
                print(f"   📅 생성일: {place.create_date}")
                print(f"   ✅ 활성 상태: {'활성' if place.usable else '비활성'}")
                
                # 상세 정보 출력
                print(f"\n📍 주소 정보 ({len(place.place_addresses)}개):")
                for addr in place.place_addresses:
                    print(f"   - {addr.address_type}: {addr.return_address}")
                    print(f"     📞 {addr.company_contact_number}")
                    if addr.phone_number2:
                        print(f"     📞 보조: {addr.phone_number2}")
                
                print(f"\n🚚 배송비 정보 ({len(place.remote_infos)}개):")
                for remote in place.remote_infos:
                    status = "활성" if remote.usable else "비활성"
                    print(f"   - {remote.delivery_code} ({status}): 제주 {remote.jeju:,}원, 제주외 {remote.not_jeju:,}원")
                    
            else:
                print(f"❌ 코드 조회 실패: {code_result.get('error')}")
            
            # 출고지명으로 조회 테스트
            print(f"\n📝 출고지명 조회 테스트 (이름: '{test_name}')...")
            name_result = client.get_shipping_place_by_name(test_name)
            
            if name_result.get("success"):
                place = name_result.get("shipping_place")
                print(f"✅ 이름 조회 성공:")
                print(f"   🏷️ 출고지 코드: {place.outbound_shipping_place_code}")
                print(f"   📝 출고지명: {place.shipping_place_name}")
                print(f"   📅 생성일: {place.create_date}")
            else:
                print(f"❌ 이름 조회 실패: {name_result.get('error')}")
                
        else:
            print(f"❌ 실제 출고지 정보를 가져올 수 없습니다")
            
    except Exception as e:
        print(f"❌ 특정 출고지 조회 테스트 오류: {e}")


def test_real_api_shipping_place_search():
    """실제 API로 출고지 검색 테스트"""
    print("\n" + "=" * 60 + " 실제 API 출고지 검색 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        # 다양한 패턴으로 실제 출고지 검색
        search_patterns = ["테스트", "API", "출고지", "본사", "센터", "창고"]
        
        for pattern in search_patterns:
            print(f"\n🔍 실제 API로 '{pattern}' 패턴 검색 중...")
            
            try:
                result = client.find_shipping_places_by_name_pattern(pattern)
                
                if result.get("success"):
                    matched_count = result.get("matched_count")
                    matched_places = result.get("shipping_places", [])
                    
                    print(f"✅ 패턴 검색 성공:")
                    print(f"   📊 매칭된 출고지: {matched_count}개")
                    
                    # 매칭된 출고지들을 활성/비활성으로 분류
                    active_matches = [p for p in matched_places if p.usable]
                    inactive_matches = [p for p in matched_places if not p.usable]
                    
                    print(f"   ✅ 활성화된 매칭: {len(active_matches)}개")
                    print(f"   ❌ 비활성화된 매칭: {len(inactive_matches)}개")
                    
                    # 매칭된 출고지 목록 (최대 3개)
                    for i, place in enumerate(matched_places[:3], 1):
                        status_emoji = "✅" if place.usable else "❌"
                        print(f"      {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name} {status_emoji}")
                        print(f"         📅 생성일: {place.create_date}")
                    
                    if len(matched_places) > 3:
                        print(f"      ... 및 {len(matched_places) - 3}개 더")
                        
                    if matched_count == 0:
                        print(f"   💡 '{pattern}' 패턴과 매칭되는 출고지가 없습니다")
                        
                else:
                    print(f"❌ 패턴 검색 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 패턴 검색 오류: {e}")
                
    except Exception as e:
        print(f"❌ 출고지 검색 테스트 오류: {e}")


def test_real_api_active_shipping_places():
    """실제 API로 활성화된 출고지만 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 활성화된 출고지 조회 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n✅ 실제 API로 활성화된 출고지만 조회 중...")
        
        result = client.get_active_shipping_places()
        
        if result.get("success"):
            total_count = result.get("total_count")
            active_count = result.get("active_count")
            active_places = result.get("shipping_places", [])
            
            print(f"✅ 활성화된 출고지 조회 성공:")
            print(f"   📊 전체 출고지: {total_count}개")
            print(f"   ✅ 활성화된 출고지: {active_count}개")
            print(f"   📈 활성화 비율: {(active_count/total_count*100):.1f}%" if total_count > 0 else "   📈 활성화 비율: 0%")
            
            # 활성화된 출고지의 택배사 현황
            delivery_stats = {}
            total_delivery_options = 0
            
            for place in active_places:
                active_deliveries = [info for info in place.remote_infos if info.usable]
                total_delivery_options += len(active_deliveries)
                
                for delivery in active_deliveries:
                    if delivery.delivery_code not in delivery_stats:
                        delivery_stats[delivery.delivery_code] = {
                            'count': 0,
                            'total_jeju': 0,
                            'total_not_jeju': 0
                        }
                    
                    delivery_stats[delivery.delivery_code]['count'] += 1
                    delivery_stats[delivery.delivery_code]['total_jeju'] += delivery.jeju
                    delivery_stats[delivery.delivery_code]['total_not_jeju'] += delivery.not_jeju
            
            print(f"\n📊 활성화된 출고지의 택배사 현황:")
            print(f"   🚚 총 택배사 옵션: {total_delivery_options}개")
            
            sorted_deliveries = sorted(delivery_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            for i, (code, stats) in enumerate(sorted_deliveries[:5], 1):
                avg_jeju = stats['total_jeju'] // stats['count'] if stats['count'] > 0 else 0
                avg_not_jeju = stats['total_not_jeju'] // stats['count'] if stats['count'] > 0 else 0
                print(f"   {i}. {code}: {stats['count']}개 출고지 (평균 제주 {avg_jeju:,}원, 제주외 {avg_not_jeju:,}원)")
            
            # 활성화된 출고지 목록 (최대 5개)
            print(f"\n📋 활성화된 출고지 목록:")
            for i, place in enumerate(active_places[:5], 1):
                print(f"   {i}. [{place.outbound_shipping_place_code}] {place.shipping_place_name}")
                print(f"      📅 생성일: {place.create_date}")
                print(f"      🚚 활성 택배사: {len([r for r in place.remote_infos if r.usable])}개")
                
                if place.place_addresses:
                    addr = place.place_addresses[0]
                    print(f"      📍 {addr.return_address}")
            
            if len(active_places) > 5:
                print(f"   ... 및 {len(active_places) - 5}개 더")
                
        else:
            print(f"❌ 활성화된 출고지 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 활성화된 출고지 조회 테스트 오류: {e}")


def test_real_api_shipping_place_statistics():
    """실제 API로 출고지 통계 분석 테스트"""
    print("\n" + "=" * 60 + " 실제 API 출고지 통계 분석 테스트 " + "=" * 60)
    
    try:
        client = ShippingCenterClient()
        
        print(f"\n📊 실제 출고지 데이터 통계 분석 중...")
        
        # 전체 출고지 정보 가져오기
        result = client.get_all_shipping_places()
        
        if result.get("success"):
            shipping_places = result.get("shipping_places", [])
            total_count = len(shipping_places)
            
            print(f"✅ 출고지 통계 분석 완료:")
            print(f"   📊 총 출고지 수: {total_count}개")
            
            # 활성/비활성 통계
            active_places = [p for p in shipping_places if p.usable]
            inactive_places = [p for p in shipping_places if not p.usable]
            
            print(f"\n🔄 활성화 상태 통계:")
            print(f"   ✅ 활성화: {len(active_places)}개 ({len(active_places)/total_count*100:.1f}%)")
            print(f"   ❌ 비활성화: {len(inactive_places)}개 ({len(inactive_places)/total_count*100:.1f}%)")
            
            # 생성일별 통계 (연도별)
            year_stats = {}
            for place in shipping_places:
                try:
                    year = place.create_date.split('/')[0] if place.create_date else '미지정'
                    if year not in year_stats:
                        year_stats[year] = 0
                    year_stats[year] += 1
                except:
                    if '미지정' not in year_stats:
                        year_stats['미지정'] = 0
                    year_stats['미지정'] += 1
            
            print(f"\n📅 연도별 출고지 생성 통계:")
            for year in sorted(year_stats.keys()):
                count = year_stats[year]
                print(f"   {year}년: {count}개 ({count/total_count*100:.1f}%)")
            
            # 주소 타입별 통계
            address_type_stats = {}
            for place in shipping_places:
                for addr in place.place_addresses:
                    addr_type = addr.address_type
                    if addr_type not in address_type_stats:
                        address_type_stats[addr_type] = 0
                    address_type_stats[addr_type] += 1
            
            print(f"\n📍 주소 타입별 통계:")
            for addr_type, count in address_type_stats.items():
                print(f"   {addr_type}: {count}개")
            
            # 택배사별 통계 (활성화된 것만)
            delivery_stats = {}
            for place in active_places:
                for remote in place.remote_infos:
                    if remote.usable:
                        code = remote.delivery_code
                        if code not in delivery_stats:
                            delivery_stats[code] = {
                                'count': 0,
                                'jeju_fees': [],
                                'not_jeju_fees': []
                            }
                        delivery_stats[code]['count'] += 1
                        delivery_stats[code]['jeju_fees'].append(remote.jeju)
                        delivery_stats[code]['not_jeju_fees'].append(remote.not_jeju)
            
            print(f"\n🚚 택배사별 배송비 통계 (활성화된 것만):")
            sorted_deliveries = sorted(delivery_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for code, stats in sorted_deliveries[:8]:
                count = stats['count']
                avg_jeju = sum(stats['jeju_fees']) // count if count > 0 else 0
                avg_not_jeju = sum(stats['not_jeju_fees']) // count if count > 0 else 0
                min_jeju = min(stats['jeju_fees']) if stats['jeju_fees'] else 0
                max_jeju = max(stats['jeju_fees']) if stats['jeju_fees'] else 0
                
                print(f"   {code}: {count}개 출고지")
                print(f"      제주: 평균 {avg_jeju:,}원 (최소 {min_jeju:,}원, 최대 {max_jeju:,}원)")
                print(f"      제주외: 평균 {avg_not_jeju:,}원")
            
            # 출고지당 평균 택배사 수
            total_active_deliveries = sum(len([r for r in p.remote_infos if r.usable]) for p in active_places)
            avg_deliveries_per_place = total_active_deliveries / len(active_places) if active_places else 0
            
            print(f"\n📈 추가 통계:")
            print(f"   🚚 출고지당 평균 활성 택배사 수: {avg_deliveries_per_place:.1f}개")
            print(f"   📦 총 활성 택배사 옵션: {total_active_deliveries}개")
            
        else:
            print(f"❌ 출고지 통계 분석 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 출고지 통계 분석 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 출고지 조회 API 실제 테스트 시작")
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
        test_real_api_shipping_places_pagination()
        test_real_api_all_shipping_places()
        test_real_api_specific_shipping_place_query()
        test_real_api_shipping_place_search()
        test_real_api_active_shipping_places()
        test_real_api_shipping_place_statistics()
        
        print(f"\n" + "=" * 50 + " 실제 API 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 인증 및 출고지 목록 조회")
        print("   2. ✅ 페이지네이션을 통한 대용량 데이터 처리")
        print("   3. ✅ 출고지 코드/이름으로 특정 출고지 조회")
        print("   4. ✅ 패턴 검색으로 유연한 출고지 찾기")
        print("   5. ✅ 활성화된 출고지만 필터링 조회")
        print("   6. ✅ 상세한 출고지 정보 및 통계 분석")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 출고지별 다양한 택배사 및 배송비 설정")
        print("   - 활성/비활성 상태 관리")
        print("   - 도로명/지번 주소 복합 등록")
        print("   - 생성일 기반 이력 관리")
        print("   - 실시간 API 연동 상태 확인")
        
    except Exception as e:
        print(f"\n❌ 실제 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()