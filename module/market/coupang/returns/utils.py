#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 관련 유틸리티 함수들
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


def handle_api_success(response_data: Dict[str, Any], default_message: str = "API 호출 성공", 
                      **additional_data) -> Dict[str, Any]:
    """
    API 성공 응답 처리
    
    Args:
        response_data: API 응답 데이터
        default_message: 기본 성공 메시지
        **additional_data: 추가 데이터
        
    Returns:
        Dict[str, Any]: 처리된 성공 응답
    """
    result = {
        "success": True,
        "message": default_message,
        "data": response_data.get("data", []),
        "code": response_data.get("code", 200)
    }
    
    # nextToken이 있으면 추가
    if "nextToken" in response_data:
        result["nextToken"] = response_data["nextToken"]
    
    # 추가 데이터 병합
    result.update(additional_data)
    
    return result


def handle_api_error(response_data: Dict[str, Any], custom_message: str = None) -> Dict[str, Any]:
    """
    API 오류 응답 처리
    
    Args:
        response_data: API 응답 데이터
        custom_message: 사용자 정의 오류 메시지
        
    Returns:
        Dict[str, Any]: 처리된 오류 응답
    """
    error_code = response_data.get("code", 500)
    error_message = custom_message or response_data.get("message", "알 수 없는 오류가 발생했습니다")
    
    # 공통 오류 메시지 매핑
    error_mappings = {
        400: "요청 파라미터를 확인해주세요",
        401: "인증에 실패했습니다. API 키를 확인해주세요",
        403: "접근 권한이 없습니다",
        412: "서버 처리 시간이 초과되었습니다. 조회 기간을 줄여서 재시도해주세요",
        500: "서버 오류가 발생했습니다"
    }
    
    if error_code in error_mappings and not custom_message:
        error_message = error_mappings[error_code]
    
    return {
        "success": False,
        "error": error_message,
        "code": error_code,
        "raw_response": response_data
    }


def handle_exception_error(exception: Exception, context: str = "API 호출") -> Dict[str, Any]:
    """
    예외 오류 처리
    
    Args:
        exception: 발생한 예외
        context: 오류 발생 컨텍스트
        
    Returns:
        Dict[str, Any]: 처리된 예외 응답
    """
    error_message = f"{context} 중 오류가 발생했습니다: {str(exception)}"
    
    return {
        "success": False,
        "error": error_message,
        "exception_type": type(exception).__name__,
        "context": context
    }


def print_return_header(title: str):
    """반품/취소 관련 헤더 출력"""
    print("=" * 80)
    print(f"🔄 {title}")
    print("=" * 80)


def print_return_section(title: str):
    """반품/취소 관련 섹션 헤더 출력"""
    print()
    print("=" * 60)
    print(f"📋 {title}")
    print("=" * 60)


def validate_environment_variables(*var_names: str) -> bool:
    """
    환경변수 유효성 검사
    
    Args:
        *var_names: 검사할 환경변수명들
        
    Returns:
        bool: 모든 환경변수가 설정되어 있는지 여부
    """
    missing_vars = []
    for var_name in var_names:
        if not os.getenv(var_name):
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"⚠️  다음 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        return False
    
    return True


def get_env_or_default(env_var: str, default_value: str, description: str = "") -> str:
    """
    환경변수 값을 가져오거나 기본값 반환
    
    Args:
        env_var: 환경변수명
        default_value: 기본값
        description: 설명
        
    Returns:
        str: 환경변수 값 또는 기본값
    """
    value = os.getenv(env_var)
    if not value:
        if description:
            print(f"⚠️  {env_var} 환경변수가 설정되지 않아 기본값 사용: {description}")
        return default_value
    return value


def format_korean_datetime(datetime_str: str) -> str:
    """
    datetime 문자열을 한국어 형식으로 변환
    
    Args:
        datetime_str: datetime 문자열 (yyyy-MM-ddTHH:mm:ss)
        
    Returns:
        str: 한국어 형식의 날짜시간
    """
    if not datetime_str:
        return "정보 없음"
    
    try:
        dt = datetime.fromisoformat(datetime_str.replace('T', ' '))
        return dt.strftime('%Y년 %m월 %d일 %H시 %M분')
    except ValueError:
        return datetime_str


def calculate_days_ago(datetime_str: str) -> int:
    """
    며칠 전인지 계산
    
    Args:
        datetime_str: datetime 문자열
        
    Returns:
        int: 며칠 전 (음수면 미래)
    """
    if not datetime_str:
        return 0
    
    try:
        dt = datetime.fromisoformat(datetime_str.replace('T', ' '))
        now = datetime.now()
        return (now - dt).days
    except ValueError:
        return 0


def format_currency(amount: int) -> str:
    """
    금액을 한국어 통화 형식으로 변환
    
    Args:
        amount: 금액
        
    Returns:
        str: 형식화된 금액
    """
    if amount == 0:
        return "무료"
    elif amount > 0:
        return f"+{amount:,}원 (셀러 부담)"
    else:
        return f"{amount:,}원 (고객 부담)"


def get_return_priority_level(return_request) -> str:
    """
    반품 요청의 우선순위 레벨 반환
    
    Args:
        return_request: ReturnRequest 객체
        
    Returns:
        str: 우선순위 레벨 (HIGH, MEDIUM, LOW)
    """
    # 출고중지 요청이고 미처리인 경우 높음
    if return_request.is_stop_release_required():
        return "HIGH"
    
    # 고객 과실이 아닌 경우 중간
    if return_request.fault_by_type != "CUSTOMER":
        return "MEDIUM"
    
    # 그 외는 낮음
    return "LOW"


def get_priority_emoji(priority: str) -> str:
    """
    우선순위에 따른 이모지 반환
    
    Args:
        priority: 우선순위 (HIGH, MEDIUM, LOW)
        
    Returns:
        str: 이모지
    """
    emoji_map = {
        "HIGH": "🔴",
        "MEDIUM": "🟡", 
        "LOW": "🟢"
    }
    return emoji_map.get(priority, "⚪")


def create_return_summary_report(return_requests: List) -> Dict[str, Any]:
    """
    반품 요청 목록의 요약 보고서 생성
    
    Args:
        return_requests: ReturnRequest 객체 리스트
        
    Returns:
        Dict[str, Any]: 요약 보고서
    """
    if not return_requests:
        return {
            "total_count": 0,
            "summary": "반품/취소 요청이 없습니다"
        }
    
    total_count = len(return_requests)
    
    # 상태별 집계
    status_counts = {}
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    fault_type_counts = {}
    total_cancel_items = 0
    stop_release_required = 0
    
    for request in return_requests:
        # 상태별 집계
        status_text = request.get_receipt_status_text()
        status_counts[status_text] = status_counts.get(status_text, 0) + 1
        
        # 우선순위별 집계
        priority = get_return_priority_level(request)
        priority_counts[priority] += 1
        
        # 귀책 타입별 집계
        fault_text = request.get_fault_by_type_text()
        fault_type_counts[fault_text] = fault_type_counts.get(fault_text, 0) + 1
        
        # 취소 상품 수량 합계
        total_cancel_items += request.cancel_count_sum
        
        # 출고중지 필요 건수
        if request.is_stop_release_required():
            stop_release_required += 1
    
    return {
        "total_count": total_count,
        "total_cancel_items": total_cancel_items,
        "stop_release_required": stop_release_required,
        "status_summary": status_counts,
        "priority_summary": priority_counts,
        "fault_type_summary": fault_type_counts,
        "urgent_action_required": stop_release_required > 0
    }


def print_return_summary_table(summary: Dict[str, Any]):
    """
    반품 요약 정보를 테이블 형식으로 출력
    
    Args:
        summary: 요약 정보 딕셔너리
    """
    if summary["total_count"] == 0:
        print("📭 반품/취소 요청이 없습니다")
        return
    
    print(f"📊 전체 현황: {summary['total_count']}건")
    print(f"📦 총 취소 상품 수량: {summary['total_cancel_items']}개")
    
    if summary["stop_release_required"] > 0:
        print(f"🚨 출고중지 처리 필요: {summary['stop_release_required']}건")
    
    print("\n📈 상태별 현황:")
    for status, count in summary["status_summary"].items():
        percentage = (count / summary["total_count"]) * 100
        print(f"   {status}: {count}건 ({percentage:.1f}%)")
    
    print("\n🎯 우선순위별 현황:")
    for priority, count in summary["priority_summary"].items():
        emoji = get_priority_emoji(priority)
        if count > 0:
            print(f"   {emoji} {priority}: {count}건")
    
    print("\n📋 귀책 타입별 현황:")
    for fault_type, count in summary["fault_type_summary"].items():
        percentage = (count / summary["total_count"]) * 100
        print(f"   {fault_type}: {count}건 ({percentage:.1f}%)")
    
    if summary.get("urgent_action_required"):
        print("\n🚨 긴급 처리 필요!")
        print("   출고중지 요청 건이 있습니다. 즉시 확인하여 처리해주세요.")


def generate_date_range_for_recent_days(days: int = 7) -> tuple:
    """
    최근 N일간의 날짜 범위 생성
    
    Args:
        days: 조회할 일수
        
    Returns:
        tuple: (시작일, 종료일) yyyy-mm-dd 형식
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)  # days-1을 하여 오늘 포함 N일
    
    return (
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )


def generate_timeframe_range_for_recent_hours(hours: int = 24) -> tuple:
    """
    최근 N시간의 timeFrame 날짜 범위 생성
    
    Args:
        hours: 조회할 시간수
        
    Returns:
        tuple: (시작일시, 종료일시) yyyy-MM-ddTHH:mm 형식
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    return (
        start_time.strftime('%Y-%m-%dT%H:%M'),
        end_time.strftime('%Y-%m-%dT%H:%M')
    )