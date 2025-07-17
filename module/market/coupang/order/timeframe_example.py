#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 분단위 전체 조회 예제
24시간 이내 분단위 조회 API 사용법 데모
"""

import os
import sys
from datetime import datetime, timedelta

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from order_client import OrderClient
from models import OrderSheetTimeFrameParams
from utils import (
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


def example_timeframe_last_12_hours():
    """최근 12시간 발주서 조회 예제"""
    print_order_section("최근 12시간 발주서 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 현재 시간에서 12시간 전부터 현재까지
    now = datetime.now()
    twelve_hours_ago = now - timedelta(hours=12)
    
    base_datetime = twelve_hours_ago.strftime("%Y-%m-%dT%H:%M")
    
    # 12시간 범위 발주서 조회 파라미터 생성
    timeframe_params = create_timeframe_params_for_hours(
        vendor_id=vendor_id,
        status="DELIVERING",  # 배송중 상태
        base_datetime=base_datetime,
        hours=12
    )
    
    print_api_request_info(
        "최근 12시간 발주서 조회 (분단위 전체)",
        시간범위=f"{timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}",
        상태=timeframe_params.status,
        검색타입="timeFrame"
    )
    
    # API 호출
    result = client.get_order_sheets_by_timeframe(timeframe_params)
    
    # 결과 출력
    print_order_result(
        result,
        success_message="최근 12시간 발주서 조회 완료",
        failure_message="최근 12시간 발주서 조회 실패"
    )
    
    return result


def example_timeframe_custom_period():
    """커스텀 시간대 발주서 조회 예제"""
    print_order_section("커스텀 시간대 발주서 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 어제 점심시간 (12시-14시) 발주서 조회
    yesterday = datetime.now() - timedelta(days=1)
    created_at_from = yesterday.strftime("%Y-%m-%d") + "T12:00"
    created_at_to = yesterday.strftime("%Y-%m-%d") + "T14:00"
    
    try:
        timeframe_params = OrderSheetTimeFrameParams(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status="FINAL_DELIVERY"  # 배송완료 상태
        )
        
        print_api_request_info(
            "어제 점심시간 발주서 조회 (분단위 전체)",
            시간범위=f"{timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}",
            상태=timeframe_params.status,
            검색타입="timeFrame"
        )
        
        # API 호출
        result = client.get_order_sheets_by_timeframe(timeframe_params)
        
        # 결과 출력
        print_order_result(
            result,
            success_message="커스텀 시간대 발주서 조회 완료",
            failure_message="커스텀 시간대 발주서 조회 실패"
        )
        
        return result
        
    except ValueError as e:
        print(f"\n❌ 파라미터 생성 실패: {e}")
        return None


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


def example_timeframe_multiple_statuses():
    """여러 상태별 분단위 전체 조회 예제"""
    print_order_section("여러 상태별 분단위 전체 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 오늘 오전 9시부터 오후 6시까지의 여러 상태 조회
    statuses = ["ACCEPT", "INSTRUCT", "DEPARTURE", "DELIVERING"]
    results = {}
    
    for status in statuses:
        print(f"\n📋 {status} 상태 발주서 조회:")
        
        try:
            timeframe_params = create_timeframe_params_for_today(
                vendor_id=vendor_id,
                status=status,
                start_hour=9,
                end_hour=18
            )
            
            print(f"   🔍 조회 중: {timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}")
            
            result = client.get_order_sheets_by_timeframe(timeframe_params)
            results[status] = result
            
            if result.get("success"):
                data = result.get("data", [])
                print(f"   ✅ 성공: {len(data)}개 발주서 조회됨")
            else:
                print(f"   ❌ 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            results[status] = None
    
    # 전체 요약
    print(f"\n📊 전체 요약:")
    total_orders = 0
    for status, result in results.items():
        if result and result.get("success"):
            count = len(result.get("data", []))
            total_orders += count
            print(f"   📦 {status}: {count}개")
        else:
            print(f"   ❌ {status}: 조회 실패")
    
    print(f"\n🎯 총 조회된 발주서: {total_orders}개")
    
    return results


def run_timeframe_examples():
    """모든 분단위 전체 조회 예제 실행"""
    print_order_header("쿠팡 파트너스 발주서 분단위 전체 조회 예제")
    
    # 환경변수 확인
    if not validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
        print("\n⚠️  환경변수 설정 후 다시 실행해주세요.")
        return
    
    print("\n💡 분단위 전체 조회 API 특징:")
    print("   - 24시간 이내로만 조회 가능")
    print("   - 시간 형식: yyyy-mm-ddTHH:MM")
    print("   - searchType=timeFrame 자동 설정")
    print("   - 페이징 없이 전체 데이터 반환")
    
    try:
        # 1. 오늘 영업시간 조회
        print("\n" + "="*80)
        example_timeframe_today_business_hours()
        
        # 2. 최근 12시간 조회
        print("\n" + "="*80)
        example_timeframe_last_12_hours()
        
        # 3. 커스텀 시간대 조회
        print("\n" + "="*80)
        example_timeframe_custom_period()
        
        # 4. 검증 오류 테스트
        print("\n" + "="*80)
        example_timeframe_validation_errors()
        
        # 5. 여러 상태별 조회
        print("\n" + "="*80)
        example_timeframe_multiple_statuses()
        
        print("\n" + "="*80)
        print("🎉 모든 분단위 전체 조회 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    # 단일 예제 실행 (개발/테스트용)
    print("🔧 개발자 모드: 오늘 영업시간 발주서 조회 예제만 실행")
    example_timeframe_today_business_hours()
    
    # 전체 예제 실행을 원할 경우 아래 주석 해제
    # run_timeframe_examples()