#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 모듈 검증 함수
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from .constants import (
    VENDOR_ID_PATTERN, DATE_PATTERN, TOKEN_PATTERN,
    MAX_DATE_RANGE_DAYS, MIN_DATE_RANGE_DAYS,
    MIN_MAX_PER_PAGE, MAX_MAX_PER_PAGE,
    ERROR_MESSAGES
)
from .models import RevenueSearchParams


def validate_vendor_id(vendor_id: Any) -> str:
    """
    판매자 ID 검증
    
    Args:
        vendor_id: 검증할 판매자 ID
        
    Returns:
        str: 검증된 판매자 ID
        
    Raises:
        ValueError: 유효하지 않은 판매자 ID
    """
    if not vendor_id or not isinstance(vendor_id, str):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])
    
    if not re.match(VENDOR_ID_PATTERN, vendor_id):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])
    
    return vendor_id


def validate_date_format(date_str: Any, field_name: str = "날짜") -> str:
    """
    날짜 형식 검증 (YYYY-MM-DD)
    
    Args:
        date_str: 검증할 날짜 문자열
        field_name: 필드명 (오류 메시지용)
        
    Returns:
        str: 검증된 날짜 문자열
        
    Raises:
        ValueError: 유효하지 않은 날짜 형식
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError(f"{field_name} 형식이 올바르지 않습니다. (YYYY-MM-DD)")
    
    if not re.match(DATE_PATTERN, date_str):
        raise ValueError(f"{field_name} 형식이 올바르지 않습니다. (YYYY-MM-DD)")
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"{field_name}이 유효하지 않습니다. (YYYY-MM-DD)")
    
    return date_str


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    날짜 범위 검증
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        
    Returns:
        tuple[str, str]: 검증된 시작일, 종료일
        
    Raises:
        ValueError: 유효하지 않은 날짜 범위
    """
    validated_start = validate_date_format(start_date, "시작일")
    validated_end = validate_date_format(end_date, "종료일")
    
    start_dt = datetime.strptime(validated_start, '%Y-%m-%d')
    end_dt = datetime.strptime(validated_end, '%Y-%m-%d')
    
    if start_dt > end_dt:
        raise ValueError(ERROR_MESSAGES["INVALID_DATE_RANGE"])
    
    return validated_start, validated_end


def validate_recognition_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    매출 인식일 범위 검증 (최대 31일)
    
    Args:
        start_date: 매출 인식일 시작 (YYYY-MM-DD)
        end_date: 매출 인식일 종료 (YYYY-MM-DD)
        
    Returns:
        tuple[str, str]: 검증된 시작일, 종료일
        
    Raises:
        ValueError: 유효하지 않은 매출 인식일 범위
    """
    validated_start, validated_end = validate_date_range(start_date, end_date)
    
    start_dt = datetime.strptime(validated_start, '%Y-%m-%d')
    end_dt = datetime.strptime(validated_end, '%Y-%m-%d')
    
    date_diff = (end_dt - start_dt).days + 1
    
    if date_diff > MAX_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_LONG"])
    
    if date_diff < MIN_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_SHORT"])
    
    return validated_start, validated_end


def validate_max_per_page(max_per_page: Any) -> int:
    """
    페이지당 최대 개수 검증
    
    Args:
        max_per_page: 검증할 페이지당 최대 개수
        
    Returns:
        int: 검증된 페이지당 최대 개수
        
    Raises:
        ValueError: 유효하지 않은 페이지당 최대 개수
    """
    if max_per_page is None:
        return 20  # 기본값
    
    try:
        max_per_page_int = int(max_per_page)
    except (ValueError, TypeError):
        raise ValueError(ERROR_MESSAGES["INVALID_MAX_PER_PAGE"])
    
    if max_per_page_int < MIN_MAX_PER_PAGE or max_per_page_int > MAX_MAX_PER_PAGE:
        raise ValueError(ERROR_MESSAGES["INVALID_MAX_PER_PAGE"])
    
    return max_per_page_int


def validate_token(token: Any) -> Optional[str]:
    """
    페이지네이션 토큰 검증
    
    Args:
        token: 검증할 토큰
        
    Returns:
        Optional[str]: 검증된 토큰 (None 가능)
        
    Raises:
        ValueError: 유효하지 않은 토큰
    """
    if token is None or token == "":
        return None
    
    if not isinstance(token, str):
        raise ValueError(ERROR_MESSAGES["INVALID_TOKEN"])
    
    # Base64 패턴 검증 (간단한 검증)
    if not re.match(TOKEN_PATTERN, token):
        raise ValueError(ERROR_MESSAGES["INVALID_TOKEN"])
    
    return token


def validate_revenue_search_params(search_params: RevenueSearchParams) -> RevenueSearchParams:
    """
    매출내역 검색 파라미터 종합 검증
    
    Args:
        search_params: 검증할 검색 파라미터
        
    Returns:
        RevenueSearchParams: 검증된 검색 파라미터
        
    Raises:
        ValueError: 유효하지 않은 검색 파라미터
    """
    # 판매자 ID 검증
    validated_vendor_id = validate_vendor_id(search_params.vendor_id)
    
    # 매출 인식일 범위 검증
    validated_start, validated_end = validate_recognition_date_range(
        search_params.recognition_date_from,
        search_params.recognition_date_to
    )
    
    # 페이지당 최대 개수 검증
    validated_max_per_page = validate_max_per_page(search_params.max_per_page)
    
    # 토큰 검증
    validated_token = validate_token(search_params.token)
    
    # 검증된 파라미터로 새 객체 생성
    return RevenueSearchParams(
        vendor_id=validated_vendor_id,
        recognition_date_from=validated_start,
        recognition_date_to=validated_end,
        max_per_page=validated_max_per_page,
        token=validated_token
    )


def is_valid_vendor_id(vendor_id: Any) -> bool:
    """
    판매자 ID 유효성 검사 (불린 반환)
    
    Args:
        vendor_id: 검사할 판매자 ID
        
    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        validate_vendor_id(vendor_id)
        return True
    except ValueError:
        return False


def is_valid_date_format(date_str: Any) -> bool:
    """
    날짜 형식 유효성 검사 (불린 반환)
    
    Args:
        date_str: 검사할 날짜 문자열
        
    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        validate_date_format(date_str)
        return True
    except ValueError:
        return False


def is_valid_recognition_date_range(start_date: str, end_date: str) -> bool:
    """
    매출 인식일 범위 유효성 검사 (불린 반환)
    
    Args:
        start_date: 시작일
        end_date: 종료일
        
    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        validate_recognition_date_range(start_date, end_date)
        return True
    except ValueError:
        return False


def is_valid_max_per_page(max_per_page: Any) -> bool:
    """
    페이지당 최대 개수 유효성 검사 (불린 반환)
    
    Args:
        max_per_page: 검사할 페이지당 최대 개수
        
    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        validate_max_per_page(max_per_page)
        return True
    except ValueError:
        return False


def validate_recognition_date(recognition_date: str) -> str:
    """
    매출 인식일 검증 (단일 날짜)
    
    Args:
        recognition_date: 매출 인식일 (YYYY-MM-DD)
        
    Returns:
        str: 검증된 매출 인식일
        
    Raises:
        ValueError: 유효하지 않은 매출 인식일
    """
    validated_date = validate_date_format(recognition_date, "매출 인식일")
    
    # 미래 날짜 검증
    recognition_dt = datetime.strptime(validated_date, '%Y-%m-%d')
    today = datetime.now().date()
    
    if recognition_dt.date() > today:
        raise ValueError("매출 인식일은 미래 날짜일 수 없습니다.")
    
    return validated_date


def validate_timeout_settings(max_per_page: int, date_range_days: int) -> Dict[str, Any]:
    """
    타임아웃 설정 검증 및 권장사항 제공
    
    Args:
        max_per_page: 페이지당 최대 개수
        date_range_days: 조회 기간 (일수)
        
    Returns:
        Dict[str, Any]: 타임아웃 설정 정보 및 경고
    """
    warnings = []
    is_risky = False
    
    # 큰 페이지 크기 경고
    if max_per_page >= 50:
        warnings.append(f"페이지 크기가 {max_per_page}개로 큽니다. 응답 시간이 길어질 수 있습니다.")
        is_risky = True
    
    # 긴 조회 기간 경고
    if date_range_days >= 20:
        warnings.append(f"조회 기간이 {date_range_days}일로 깁니다. 타임아웃이 발생할 수 있습니다.")
        is_risky = True
    
    # 복합 위험도 평가
    risk_score = (max_per_page / 100) + (date_range_days / 31)
    if risk_score > 0.8:
        warnings.append("현재 설정으로는 타임아웃 위험이 높습니다. 기간을 줄이거나 페이지 크기를 조정하세요.")
        is_risky = True
    
    # 권장 타임아웃 계산
    base_timeout = 30
    if is_risky:
        recommended_timeout = min(base_timeout + (date_range_days * 2) + (max_per_page // 10), 120)
    else:
        recommended_timeout = base_timeout
    
    return {
        "is_risky": is_risky,
        "warnings": warnings,
        "timeout_seconds": recommended_timeout,
        "risk_score": risk_score,
        "recommendations": [
            "큰 데이터 조회 시 페이지네이션을 활용하세요.",
            "조회 기간을 7일 이내로 제한하면 안정적입니다.",
            "페이지 크기는 20개 이하로 설정하는 것을 권장합니다."
        ] if is_risky else []
    }


def validate_environment_setup() -> Dict[str, Any]:
    """
    환경 설정 검증
    
    Returns:
        Dict[str, Any]: 환경 설정 검증 결과
    """
    try:
        # config 모듈 import
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from common.config import config
        
        validation_result = {
            "is_valid": False,
            "has_access_key": bool(config.coupang_access_key),
            "has_secret_key": bool(config.coupang_secret_key),
            "has_vendor_id": bool(config.coupang_vendor_id),
            "missing_credentials": [],
            "warnings": []
        }
        
        if not config.coupang_access_key:
            validation_result["missing_credentials"].append("COUPANG_ACCESS_KEY")
        
        if not config.coupang_secret_key:
            validation_result["missing_credentials"].append("COUPANG_SECRET_KEY")
        
        if not config.coupang_vendor_id:
            validation_result["missing_credentials"].append("COUPANG_VENDOR_ID")
        
        validation_result["is_valid"] = config.validate_coupang_credentials()
        
        if not validation_result["is_valid"]:
            validation_result["warnings"].append(
                f"누락된 환경변수: {', '.join(validation_result['missing_credentials'])}"
            )
        
        return validation_result
        
    except ImportError as e:
        return {
            "is_valid": False,
            "error": f"설정 모듈을 불러올 수 없습니다: {e}",
            "missing_credentials": ["CONFIG_MODULE"],
            "warnings": ["설정 파일(.env)을 확인해주세요."]
        }


def get_validation_summary(search_params: RevenueSearchParams) -> Dict[str, Any]:
    """
    검색 파라미터 검증 요약
    
    Args:
        search_params: 검증할 검색 파라미터
        
    Returns:
        Dict[str, Any]: 검증 결과 요약
    """
    summary = {
        "vendor_id_valid": is_valid_vendor_id(search_params.vendor_id),
        "date_range_valid": is_valid_recognition_date_range(
            search_params.recognition_date_from,
            search_params.recognition_date_to
        ),
        "max_per_page_valid": is_valid_max_per_page(search_params.max_per_page),
        "overall_valid": False,
        "warnings": []
    }
    
    # 전체 유효성 판단
    summary["overall_valid"] = all([
        summary["vendor_id_valid"],
        summary["date_range_valid"],
        summary["max_per_page_valid"]
    ])
    
    # 타임아웃 설정 검증
    date_range_days = search_params.get_date_range_days()
    timeout_info = validate_timeout_settings(search_params.max_per_page or 20, date_range_days)
    
    if timeout_info["is_risky"]:
        summary["warnings"].extend(timeout_info["warnings"])
    
    # 환경 설정 검증
    env_validation = validate_environment_setup()
    if not env_validation["is_valid"]:
        summary["warnings"].extend(env_validation["warnings"])
    
    return summary