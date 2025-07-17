#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 사용 예제
실제 운영 환경에서의 반품/취소 요청 관리 시나리오
"""

import os
import sys
from datetime import datetime, timedelta

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

import importlib
return_module = importlib.import_module('return.return_client')
ReturnClient = return_module.ReturnClient

models_module = importlib.import_module('return.models')
ReturnRequestSearchParams = models_module.ReturnRequestSearchParams
ReturnRequest = models_module.ReturnRequest

utils_module = importlib.import_module('return.utils')
print_return_header = utils_module.print_return_header
print_return_section = utils_module.print_return_section
validate_environment_variables = utils_module.validate_environment_variables
format_korean_datetime = utils_module.format_korean_datetime
format_currency = utils_module.format_currency
print_return_summary_table = utils_module.print_return_summary_table
get_priority_emoji = utils_module.get_priority_emoji
get_return_priority_level = utils_module.get_return_priority_level
generate_date_range_for_recent_days = utils_module.generate_date_range_for_recent_days


def example_basic_return_requests():
    """기본 반품 요청 목록 조회 예제"""
    print_return_section("기본 반품 요청 목록 조회")
    
    try:
        # ReturnClient 초기화
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 오늘 날짜 반품 요청 조회
        today = datetime.now().strftime('%Y-%m-%d')
        
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type="daily",
            created_at_from=today,
            created_at_to=today,
            cancel_type="RETURN"  # 반품 요청만 조회
        )
        
        print(f"📅 조회 날짜: {today}")
        print(f"🏪 벤더 ID: {vendor_id}")
        
        result = client.get_return_requests(params)
        
        if result.get("success"):
            data = result.get("data", [])
            print(f"✅ 반품 요청 조회 성공: {len(data)}건")
            
            if data:
                print("\n📋 반품 요청 목록:")
                for i, item in enumerate(data[:5], 1):  # 최대 5건만 출력
                    request = ReturnRequest.from_dict(item)
                    priority = get_return_priority_level(request)
                    priority_emoji = get_priority_emoji(priority)
                    
                    print(f"   {i}. {priority_emoji} 접수번호: {request.receipt_id}")
                    print(f"      주문번호: {request.order_id}")
                    print(f"      상태: {request.get_receipt_status_text()}")
                    print(f"      신청인: {request.requester_name}")
                    print(f"      사유: {request.reason_code_text}")
                    print(f"      접수일: {format_korean_datetime(request.created_at)}")
                    
                    if request.is_stop_release_required():
                        print(f"      🚨 출고중지 처리 필요!")
                    print()
                
                if len(data) > 5:
                    print(f"   ... 외 {len(data) - 5}건")
                
                # 요약 통계 출력
                summary_stats = result.get("summary_stats", {})
                if summary_stats:
                    print_return_summary_table(summary_stats)
                    
            else:
                print("📭 오늘 접수된 반품 요청이 없습니다.")
                
        else:
            print(f"❌ 반품 요청 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")


def example_stop_release_check():
    """출고중지 요청 확인 예제 (상품 발송 전 필수 확인)"""
    print_return_section("출고중지 요청 확인 (발송 전 필수)")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 오늘 출고중지 요청 조회
        today = datetime.now().strftime('%Y-%m-%d')
        
        print("🚨 상품 발송 전 출고중지 요청 확인")
        print(f"📅 확인 날짜: {today}")
        
        result = client.get_stop_release_requests(
            vendor_id=vendor_id,
            created_at_from=today,
            created_at_to=today
        )
        
        if result.get("success"):
            data = result.get("data", [])
            stop_release_count = 0
            
            if data:
                print(f"\n⚠️  출고중지 요청 발견: {len(data)}건")
                
                for i, item in enumerate(data, 1):
                    request = ReturnRequest.from_dict(item)
                    
                    print(f"\n🔴 {i}. 접수번호: {request.receipt_id}")
                    print(f"   주문번호: {request.order_id}")
                    print(f"   신청인: {request.requester_name}")
                    print(f"   처리상태: {request.release_stop_status}")
                    print(f"   접수일시: {format_korean_datetime(request.created_at)}")
                    
                    # 출고중지 필요한 상품 목록
                    stop_items = request.get_stop_release_items()
                    if stop_items:
                        stop_release_count += len(stop_items)
                        print(f"   🛑 출고중지 필요 상품:")
                        for item in stop_items:
                            print(f"      - {item.vendor_item_name} (수량: {item.cancel_count})")
                            print(f"        상품ID: {item.vendor_item_id}")
                            print(f"        출고상태: {item.get_release_status_text()}")
                    
                if stop_release_count > 0:
                    print(f"\n🚨 총 {stop_release_count}개 상품의 출고중지 처리가 필요합니다!")
                    print("   발송 전에 반드시 해당 상품들을 출고중지 처리해주세요.")
                else:
                    print("\n✅ 모든 출고중지 요청이 처리되었습니다.")
                    
            else:
                print("✅ 출고중지 요청이 없습니다. 정상 발송 가능합니다.")
                
        else:
            print(f"❌ 출고중지 요청 확인 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 출고중지 확인 실패: {e}")


def example_weekly_return_summary():
    """주간 반품/취소 요약 리포트 예제"""
    print_return_section("주간 반품/취소 요약 리포트")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 최근 7일간 데이터 조회
        date_from, date_to = generate_date_range_for_recent_days(7)
        
        print(f"📊 주간 반품/취소 요약 리포트")
        print(f"📅 기간: {date_from} ~ {date_to}")
        
        result = client.get_return_summary_by_date_range(
            vendor_id=vendor_id,
            created_at_from=date_from,
            created_at_to=date_to
        )
        
        if result.get("success"):
            total_summary = result.get("total_summary", {})
            
            print(f"\n📈 전체 현황:")
            print(f"   총 반품/취소 요청: {total_summary.get('total_requests', 0)}건")
            print(f"   총 취소 상품 수량: {total_summary.get('total_cancel_items', 0)}개")
            
            # 반품 요청 현황
            return_info = total_summary.get("return_requests", {})
            print(f"\n🔄 반품 요청:")
            print(f"   건수: {return_info.get('count', 0)}건")
            print(f"   상품 수량: {return_info.get('cancel_items', 0)}개")
            print(f"   출고중지 처리 필요: {return_info.get('stop_release_required', 0)}건")
            
            # 상태별 현황
            status_summary = return_info.get("status_summary", {})
            if status_summary:
                print(f"   상태별 현황:")
                for status, count in status_summary.items():
                    print(f"      {status}: {count}건")
            
            # 취소 요청 현황
            cancel_info = total_summary.get("cancel_requests", {})
            print(f"\n❌ 취소 요청:")
            print(f"   건수: {cancel_info.get('count', 0)}건")
            print(f"   상품 수량: {cancel_info.get('cancel_items', 0)}개")
            
            # 긴급 처리 필요 여부
            if total_summary.get("urgent_action_required"):
                print(f"\n🚨 긴급 처리 필요!")
                print(f"   출고중지 요청이 {return_info.get('stop_release_required', 0)}건 있습니다.")
                print(f"   즉시 확인하여 처리해주세요.")
            else:
                print(f"\n✅ 긴급 처리가 필요한 건은 없습니다.")
                
        else:
            print(f"❌ 주간 요약 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 주간 요약 생성 실패: {e}")


def example_cancel_requests():
    """취소 요청 조회 예제 (결제완료 단계 취소)"""
    print_return_section("취소 요청 조회 (결제완료 단계)")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 최근 3일간 취소 요청 조회
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        created_at_from = start_date.strftime('%Y-%m-%d')
        created_at_to = end_date.strftime('%Y-%m-%d')
        
        print(f"📅 조회 기간: {created_at_from} ~ {created_at_to}")
        
        result = client.get_cancel_requests(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to
        )
        
        if result.get("success"):
            data = result.get("data", [])
            print(f"✅ 취소 요청 조회 성공: {len(data)}건")
            
            if data:
                print(f"\n📋 취소 요청 목록:")
                total_cancel_amount = 0
                
                for i, item in enumerate(data[:3], 1):  # 최대 3건만 출력
                    request = ReturnRequest.from_dict(item)
                    
                    print(f"   {i}. 접수번호: {request.receipt_id}")
                    print(f"      주문번호: {request.order_id}")
                    print(f"      취소 사유: {request.reason_code_text}")
                    print(f"      취소 수량: {request.cancel_count_sum}개")
                    print(f"      신청인: {request.requester_name}")
                    print(f"      접수일: {format_korean_datetime(request.created_at)}")
                    print(f"      배송비: {format_currency(request.return_shipping_charge)}")
                    print()
                
                if len(data) > 3:
                    print(f"   ... 외 {len(data) - 3}건")
                
                # 요약 정보
                summary_report = result.get("summary_report", {})
                if summary_report:
                    print(f"📊 취소 요청 요약:")
                    print(f"   전체 건수: {summary_report.get('total_count', 0)}건")
                    print(f"   전체 취소 상품: {summary_report.get('total_cancel_items', 0)}개")
                    
            else:
                print("📭 해당 기간에 취소 요청이 없습니다.")
                
        else:
            print(f"❌ 취소 요청 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 취소 요청 조회 실패: {e}")


def example_timeframe_search():
    """timeFrame 검색 예제 (분단위 조회)"""
    print_return_section("분단위 전체 조회 (timeFrame)")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 오늘 하루 전체를 timeFrame으로 조회
        today = datetime.now()
        start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = today.replace(hour=23, minute=59, second=0, microsecond=0)
        
        created_at_from = start_time.strftime('%Y-%m-%dT%H:%M')
        created_at_to = end_time.strftime('%Y-%m-%dT%H:%M')
        
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type="timeFrame",  # 분단위 전체 조회
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            cancel_type="RETURN"
        )
        
        print(f"⏰ timeFrame 검색 (분단위 전체)")
        print(f"📅 조회 범위: {created_at_from} ~ {created_at_to}")
        
        result = client.get_return_requests(params)
        
        if result.get("success"):
            data = result.get("data", [])
            print(f"✅ timeFrame 조회 성공: {len(data)}건")
            
            if data:
                # 시간대별 분석
                hour_stats = {}
                for item in data:
                    request = ReturnRequest.from_dict(item)
                    created_hour = request.created_at[:13]  # YYYY-MM-DDTHH 부분만
                    hour_stats[created_hour] = hour_stats.get(created_hour, 0) + 1
                
                print(f"\n📊 시간대별 반품 요청 현황:")
                for hour, count in sorted(hour_stats.items()):
                    print(f"   {hour}시: {count}건")
                
                # 최신 요청 몇 건 출력
                print(f"\n📋 최근 요청 (최대 3건):")
                for i, item in enumerate(data[:3], 1):
                    request = ReturnRequest.from_dict(item)
                    print(f"   {i}. 접수번호 {request.receipt_id} - {request.reason_code_text}")
                    print(f"      접수시간: {format_korean_datetime(request.created_at)}")
                    
            else:
                print("📭 해당 시간 범위에 반품 요청이 없습니다.")
                
        else:
            print(f"❌ timeFrame 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ timeFrame 조회 실패: {e}")


def run_return_examples():
    """반품/취소 API 사용 예제 실행"""
    print_return_header("쿠팡 파트너스 반품/취소 요청 API 사용 예제")
    
    print("💡 예제 시나리오:")
    print("   1. 기본 반품 요청 목록 조회")
    print("   2. 출고중지 요청 확인 (발송 전 필수)")
    print("   3. 주간 반품/취소 요약 리포트")
    print("   4. 취소 요청 조회 (결제완료 단계)")
    print("   5. timeFrame 검색 (분단위 조회)")
    
    # 환경변수 확인
    if not validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
        print("\n❌ 환경변수가 설정되지 않아 예제를 실행할 수 없습니다.")
        print("   .env 파일에 다음 변수들을 설정해주세요:")
        print("   - COUPANG_ACCESS_KEY")
        print("   - COUPANG_SECRET_KEY")
        print("   - COUPANG_VENDOR_ID")
        return False
    
    try:
        # 1. 기본 반품 요청 목록 조회
        print("\n" + "="*80)
        example_basic_return_requests()
        
        # 2. 출고중지 요청 확인
        print("\n" + "="*80)
        example_stop_release_check()
        
        # 3. 주간 반품/취소 요약 리포트
        print("\n" + "="*80)
        example_weekly_return_summary()
        
        # 4. 취소 요청 조회
        print("\n" + "="*80)
        example_cancel_requests()
        
        # 5. timeFrame 검색
        print("\n" + "="*80)
        example_timeframe_search()
        
        print("\n" + "="*80)
        print("🎉 모든 예제 실행 완료!")
        print("✅ 반품/취소 요청 API가 정상 작동합니다.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    run_return_examples()