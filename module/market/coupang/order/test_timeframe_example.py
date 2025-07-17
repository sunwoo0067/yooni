#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 분단위 전체 조회 예제 테스트
24시간 이내 분단위 조회 API 사용법 데모
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

from order.order_client import OrderClient
from order.models import OrderSheetTimeFrameParams
from order.utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, print_order_summary, validate_environment_variables,
    create_timeframe_params_for_today, create_timeframe_params_for_hours,
    get_env_or_default
)


def example_timeframe_today_business_hours():
    """오늘 영업시간(9시-18시) 발주서 조회 예제"""
    print_order_section("오늘 영업시간 발주서 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 오늘 9시-18시 발주서 조회 파라미터 생성
    timeframe_params = create_timeframe_params_for_today(
        vendor_id=vendor_id,
        status="ACCEPT",  # 결제완료 상태
        start_hour=9,
        end_hour=18
    )
    
    print_api_request_info(
        "오늘 영업시간 발주서 조회 (분단위 전체)",
        시간범위=f"{timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}",
        상태=timeframe_params.status,
        검색타입="timeFrame"
    )
    
    # API 호출
    result = client.get_order_sheets_by_timeframe(timeframe_params)
    
    # 결과 출력
    print_order_result(
        result,
        success_message="영업시간 발주서 조회 완료",
        failure_message="영업시간 발주서 조회 실패"
    )
    
    return result


def example_timeframe_validation_errors():
    """분단위 전체 조회 검증 오류 예제"""
    print_order_section("분단위 전체 조회 검증 오류 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    print("🔍 24시간 초과 조회 시도 (오류 발생 예상):")
    try:
        # 25시간 범위로 시도 (24시간 초과)
        timeframe_params = OrderSheetTimeFrameParams(
            vendor_id=vendor_id,
            created_at_from="2024-01-01T00:00",
            created_at_to="2024-01-02T01:00",  # 25시간 후
            status="ACCEPT"
        )
        print("❌ 예상과 달리 검증을 통과했습니다 (버그)")
        
    except ValueError as e:
        print(f"✅ 올바른 검증 오류: {e}")
    
    print("\n🔍 잘못된 날짜 형식 시도 (오류 발생 예상):")
    try:
        # 잘못된 날짜 형식
        timeframe_params = OrderSheetTimeFrameParams(
            vendor_id=vendor_id,
            created_at_from="2024-01-01 09:00",  # 잘못된 형식
            created_at_to="2024-01-01T18:00",
            status="ACCEPT"
        )
        print("❌ 예상과 달리 검증을 통과했습니다 (버그)")
        
    except ValueError as e:
        print(f"✅ 올바른 검증 오류: {e}")
    
    print("\n🔍 올바른 파라미터 생성 시도:")
    try:
        # 올바른 파라미터
        timeframe_params = OrderSheetTimeFrameParams(
            vendor_id=vendor_id,
            created_at_from="2024-01-01T09:00",
            created_at_to="2024-01-01T18:00",
            status="ACCEPT"
        )
        print("✅ 올바른 파라미터 생성 성공")
        print(f"   📅 시간 범위: {timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}")
        
    except ValueError as e:
        print(f"❌ 예상과 달리 오류 발생: {e}")


def run_timeframe_test():
    """분단위 전체 조회 기능 테스트 실행"""
    print_order_header("쿠팡 파트너스 발주서 분단위 전체 조회 기능 테스트")
    
    print("\n💡 분단위 전체 조회 API 특징:")
    print("   - 24시간 이내로만 조회 가능")
    print("   - 시간 형식: yyyy-mm-ddTHH:MM")
    print("   - searchType=timeFrame 자동 설정")
    print("   - 페이징 없이 전체 데이터 반환")
    
    try:
        # 1. 검증 오류 테스트
        print("\n" + "="*80)
        example_timeframe_validation_errors()
        
        # 2. 환경변수가 설정되어 있으면 실제 API 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n" + "="*80)
            example_timeframe_today_business_hours()
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략합니다.")
        
        print("\n" + "="*80)
        print("🎉 분단위 전체 조회 기능 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    run_timeframe_test()