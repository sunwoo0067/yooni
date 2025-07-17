#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 관리 예제
발주서 목록 조회 API 사용법 예제
"""

import os
import sys
from datetime import datetime, timedelta

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from .order_client import OrderClient
from .models import OrderSheetSearchParams
from .utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, print_order_sheet_details, print_order_summary,
    validate_environment_variables, get_env_or_default
)


def example_basic_order_sheet_query():
    """기본 발주서 목록 조회 예제"""
    print_order_section("기본 발주서 목록 조회 예제")
    
    # 환경변수에서 판매자 ID 가져오기
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID")
    
    # 클라이언트 초기화
    client = OrderClient()
    
    # 검색 파라미터 설정
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    search_params = OrderSheetSearchParams(
        vendor_id=vendor_id,
        created_at_from=yesterday.strftime("%Y-%m-%d"),
        created_at_to=today.strftime("%Y-%m-%d"),
        status="ACCEPT",
        max_per_page=10
    )
    
    print_api_request_info(
        "발주서 목록 조회",
        vendor_id=search_params.vendor_id,
        created_at_from=search_params.created_at_from,
        created_at_to=search_params.created_at_to,
        status=search_params.status,
        max_per_page=search_params.max_per_page
    )
    
    # API 호출
    result = client.get_order_sheets(search_params)
    
    # 결과 출력
    print_order_result(
        result,
        success_message="발주서 목록 조회 완료",
        failure_message="발주서 목록 조회 실패"
    )
    
    return result


def example_all_pages_query():
    """전체 페이지 발주서 조회 예제"""
    print_order_section("전체 페이지 발주서 조회 예제")
    
    client = OrderClient()
    
    # 최근 7일간 모든 상태의 발주서 조회
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    search_params = OrderSheetSearchParams(
        vendor_id=get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID"),
        created_at_from=week_ago.strftime("%Y-%m-%d"),
        created_at_to=today.strftime("%Y-%m-%d"),
        status="ACCEPT"  # 결제완료 상태만 조회
    )
    
    print_api_request_info(
        "전체 페이지 발주서 조회",
        기간=f"{search_params.created_at_from} ~ {search_params.created_at_to}",
        상태=search_params.status
    )
    
    # 전체 페이지 조회
    result = client.get_order_sheets_all_pages(search_params)
    
    print_order_result(
        result,
        success_message="전체 발주서 조회 완료",
        failure_message="전체 발주서 조회 실패"
    )
    
    # 요약 정보 출력
    if result.get("success") and result.get("summary"):
        print_order_summary(result["summary"])
    
    return result


def example_status_specific_query():
    """특정 상태별 발주서 조회 예제"""
    print_order_section("상태별 발주서 조회 예제")
    
    client = OrderClient()
    
    # 최근 3일간 배송중 상태 발주서만 조회
    today = datetime.now()
    three_days_ago = today - timedelta(days=3)
    
    print_api_request_info(
        "배송중 상태 발주서 조회",
        기간=f"{three_days_ago.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}",
        상태="DELIVERING"
    )
    
    # 편의 메서드 사용
    result = client.get_order_sheets_by_status(
        vendor_id=get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID"),
        created_at_from=three_days_ago.strftime("%Y-%m-%d"),
        created_at_to=today.strftime("%Y-%m-%d"),
        status="DELIVERING",
        max_per_page=20
    )
    
    print_order_result(
        result,
        success_message="배송중 발주서 조회 완료",
        failure_message="배송중 발주서 조회 실패"
    )
    
    return result


def example_timeframe_query():
    """분단위 전체 조회 예제"""
    print_order_section("분단위 전체 조회 예제")
    
    client = OrderClient()
    
    # 오늘 하루 전체 발주서 조회 (분단위)
    today = datetime.now().strftime("%Y-%m-%d")
    
    search_params = OrderSheetSearchParams(
        vendor_id=get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID"),
        created_at_from=today,
        created_at_to=today,
        status="ACCEPT",
        search_type="timeFrame"  # 분단위 전체 조회
    )
    
    print_api_request_info(
        "분단위 전체 발주서 조회",
        날짜=today,
        상태=search_params.status,
        검색타입=search_params.search_type
    )
    
    # 분단위 전체 조회
    result = client.get_order_sheets_timeframe(search_params)
    
    print_order_result(
        result,
        success_message="분단위 전체 발주서 조회 완료",
        failure_message="분단위 전체 발주서 조회 실패"
    )
    
    return result


def example_order_summary():
    """날짜 범위별 발주서 요약 조회 예제"""
    print_order_section("발주서 요약 조회 예제")
    
    client = OrderClient()
    
    # 최근 일주일 요약 정보 조회
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    print_api_request_info(
        "발주서 요약 정보 조회",
        기간=f"{week_ago.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}"
    )
    
    # 요약 정보 조회
    result = client.get_order_summary_by_date_range(
        vendor_id=get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID"),
        created_at_from=week_ago.strftime("%Y-%m-%d"),
        created_at_to=today.strftime("%Y-%m-%d")
    )
    
    if result.get("success"):
        print("\n✅ 발주서 요약 조회 성공!")
        
        summary_data = result.get("data", {})
        total_summary = summary_data.get("total_summary", {})
        
        print(f"\n📊 전체 요약:")
        print(f"   📦 총 발주서 수: {total_summary.get('total_orders', 0)}개")
        print(f"   💰 총 주문 금액: {total_summary.get('total_amount', 0):,}원")
        print(f"   🚚 총 배송비: {total_summary.get('total_shipping_fee', 0):,}원")
        
        # 상태별 요약
        status_summary = total_summary.get("status_summary", {})
        if status_summary:
            print(f"\n   📋 상태별 현황:")
            for status, count in status_summary.items():
                print(f"      - {status}: {count}개")
        
        # 택배사별 요약
        delivery_summary = total_summary.get("delivery_company_summary", {})
        if delivery_summary:
            print(f"\n   🚛 택배사별 현황:")
            for company, count in delivery_summary.items():
                print(f"      - {company}: {count}개")
                
    else:
        print(f"\n❌ 발주서 요약 조회 실패: {result.get('error')}")
    
    return result


def example_detailed_order_info():
    """발주서 상세 정보 출력 예제"""
    print_order_section("발주서 상세 정보 예제")
    
    client = OrderClient()
    
    # 최근 발주서 1개 조회
    today = datetime.now().strftime("%Y-%m-%d")
    
    search_params = OrderSheetSearchParams(
        vendor_id=get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID"),
        created_at_from=today,
        created_at_to=today,
        status="ACCEPT",
        max_per_page=1
    )
    
    result = client.get_order_sheets(search_params)
    
    if result.get("success"):
        order_sheets = result.get("data", [])
        if order_sheets:
            print("\n📦 발주서 상세 정보:")
            for sheet in order_sheets:
                print_order_sheet_details(sheet)
        else:
            print("\n📭 조회된 발주서가 없습니다.")
    else:
        print(f"\n❌ 발주서 조회 실패: {result.get('error')}")
    
    return result


def run_all_examples():
    """모든 예제 실행"""
    print_order_header("쿠팡 파트너스 발주서 API 예제 실행")
    
    # 환경변수 확인
    if not validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
        print("\n⚠️  환경변수 설정 후 다시 실행해주세요.")
        print("   export COUPANG_ACCESS_KEY=your_access_key")
        print("   export COUPANG_SECRET_KEY=your_secret_key")
        print("   export COUPANG_VENDOR_ID=your_vendor_id")
        return
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A00000000", "기본 테스트 벤더 ID")
    print(f"\n🔧 사용 중인 판매자 ID: {vendor_id}")
    
    if vendor_id == "A00000000":
        print("⚠️  주의: 테스트용 기본 판매자 ID를 사용 중입니다.")
        print("   실제 환경에서는 COUPANG_VENDOR_ID 환경변수를 설정해주세요.")
    
    try:
        # 1. 기본 조회
        print("\n" + "="*80)
        example_basic_order_sheet_query()
        
        # 2. 전체 페이지 조회
        print("\n" + "="*80)
        example_all_pages_query()
        
        # 3. 상태별 조회
        print("\n" + "="*80)
        example_status_specific_query()
        
        # 4. 분단위 전체 조회
        print("\n" + "="*80)
        example_timeframe_query()
        
        # 5. 요약 정보 조회
        print("\n" + "="*80)
        example_order_summary()
        
        # 6. 상세 정보 출력
        print("\n" + "="*80)
        example_detailed_order_info()
        
        print("\n" + "="*80)
        print("🎉 모든 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    # 단일 예제 실행 (개발/테스트용)
    print("🔧 개발자 모드: 기본 발주서 조회 예제만 실행")
    example_basic_order_sheet_query()
    
    # 전체 예제 실행을 원할 경우 아래 주석 해제
    # run_all_examples()