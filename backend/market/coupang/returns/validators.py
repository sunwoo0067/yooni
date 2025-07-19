#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 파라미터 검증 함수들
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union
from .constants import (
    VENDOR_ID_PATTERN, DATE_PATTERN, DATETIME_PATTERN, 
    MAX_DATE_RANGE_DAYS, MAX_PER_PAGE, RETURN_STATUS, CANCEL_TYPE,
    ERROR_MESSAGES
)


def validate_vendor_id(vendor_id: str) -> str:
    """
    판매자 ID 검증
    
    Args:
        vendor_id: 판매자 ID
        
    Returns:
        str: 검증된 판매자 ID
        
    Raises:
        ValueError: 잘못된 판매자 ID
    """
    if not vendor_id:
        raise ValueError("판매자 ID(vendorId)는 필수입니다")
    
    if not re.match(VENDOR_ID_PATTERN, vendor_id):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])
    
    return vendor_id


def validate_search_type(search_type: str) -> str:
    """
    검색 타입 검증
    
    Args:
        search_type: 검색 타입
        
    Returns:
        str: 검증된 검색 타입
        
    Raises:
        ValueError: 잘못된 검색 타입
    """
    if not search_type:
        raise ValueError("검색 타입(searchType)은 필수입니다")
    
    valid_types = ["timeFrame", "daily"]
    if search_type not in valid_types:
        raise ValueError(f"검색 타입은 {valid_types} 중 하나여야 합니다")
    
    return search_type


def validate_date_format(date_str: str, search_type: str, field_name: str) -> str:
    """
    날짜 형식 검증
    
    Args:
        date_str: 날짜 문자열
        search_type: 검색 타입
        field_name: 필드명 (오류 메시지용)
        
    Returns:
        str: 검증된 날짜 문자열
        
    Raises:
        ValueError: 잘못된 날짜 형식
    """
    if not date_str:
        raise ValueError(f"{field_name}은(는) 필수입니다")
    
    if search_type == "timeFrame":
        # timeFrame일 경우 yyyy-MM-ddTHH:mm 형식
        if not re.match(DATETIME_PATTERN, date_str):
            raise ValueError(ERROR_MESSAGES["TIMEFRAME_DATETIME_FORMAT"])
        
        # 실제 날짜/시간 파싱 검증
        try:
            datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            raise ValueError(f"{field_name} 날짜 형식이 올바르지 않습니다: {date_str}")
    else:
        # 일반적인 경우 yyyy-mm-dd 형식
        if not re.match(DATE_PATTERN, date_str):
            raise ValueError(ERROR_MESSAGES["INVALID_DATE_FORMAT"])
        
        # 실제 날짜 파싱 검증
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"{field_name} 날짜 형식이 올바르지 않습니다: {date_str}")
    
    return date_str


def validate_date_range(created_at_from: str, created_at_to: str, search_type: str) -> tuple:
    """
    날짜 범위 검증
    
    Args:
        created_at_from: 검색 시작일
        created_at_to: 검색 종료일
        search_type: 검색 타입
        
    Returns:
        tuple: (검증된 시작일, 검증된 종료일)
        
    Raises:
        ValueError: 잘못된 날짜 범위
    """
    # 개별 날짜 형식 검증
    from_date = validate_date_format(created_at_from, search_type, "검색 시작일(createdAtFrom)")
    to_date = validate_date_format(created_at_to, search_type, "검색 종료일(createdAtTo)")
    
    # 날짜 범위 검증
    if search_type == "timeFrame":
        from_dt = datetime.strptime(from_date, '%Y-%m-%dT%H:%M')
        to_dt = datetime.strptime(to_date, '%Y-%m-%dT%H:%M')
    else:
        from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    # 시작일이 종료일보다 늦은 경우
    if from_dt > to_dt:
        raise ValueError("검색 시작일이 종료일보다 늦을 수 없습니다")
    
    # 최대 조회 기간 검증 (31일)
    if (to_dt - from_dt).days > MAX_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_LONG"])
    
    return from_date, to_date


def validate_status(status: Optional[str]) -> Optional[str]:
    """
    반품 상태 검증
    
    Args:
        status: 반품 상태
        
    Returns:
        Optional[str]: 검증된 반품 상태
        
    Raises:
        ValueError: 잘못된 반품 상태
    """
    if status is None:
        return None
    
    if status not in RETURN_STATUS:
        valid_statuses = list(RETURN_STATUS.keys())
        raise ValueError(f"반품 상태는 {valid_statuses} 중 하나여야 합니다")
    
    return status


def validate_cancel_type(cancel_type: Optional[str]) -> str:
    """
    취소 유형 검증
    
    Args:
        cancel_type: 취소 유형
        
    Returns:
        str: 검증된 취소 유형 (기본값: RETURN)
        
    Raises:
        ValueError: 잘못된 취소 유형
    """
    if cancel_type is None:
        return "RETURN"
    
    if cancel_type not in CANCEL_TYPE:
        valid_types = list(CANCEL_TYPE.keys())
        raise ValueError(f"취소 유형은 {valid_types} 중 하나여야 합니다")
    
    return cancel_type


def validate_max_per_page(max_per_page: Optional[int]) -> Optional[int]:
    """
    페이지당 최대 조회 수 검증
    
    Args:
        max_per_page: 페이지당 최대 조회 수
        
    Returns:
        Optional[int]: 검증된 페이지당 최대 조회 수
        
    Raises:
        ValueError: 잘못된 페이지당 최대 조회 수
    """
    if max_per_page is None:
        return None
    
    if not isinstance(max_per_page, int) or max_per_page < 1 or max_per_page > MAX_PER_PAGE:
        raise ValueError(ERROR_MESSAGES["INVALID_MAX_PER_PAGE"])
    
    return max_per_page


def validate_order_id(order_id: Optional[Union[int, str]]) -> Optional[int]:
    """
    주문번호 검증
    
    Args:
        order_id: 주문번호
        
    Returns:
        Optional[int]: 검증된 주문번호
        
    Raises:
        ValueError: 잘못된 주문번호
    """
    if order_id is None:
        return None
    
    # 문자열을 정수로 변환 시도
    if isinstance(order_id, str):
        if not order_id.strip():
            return None
        try:
            order_id = int(order_id.strip())
        except ValueError:
            raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])
    
    if not isinstance(order_id, int) or order_id <= 0:
        raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])
    
    return order_id


def validate_search_params(params) -> None:
    """
    반품/취소 검색 파라미터 전체 검증
    
    Args:
        params: ReturnRequestSearchParams 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(params.vendor_id)
    validate_search_type(params.search_type)
    validate_date_range(params.created_at_from, params.created_at_to, params.search_type)
    
    # 선택적 파라미터 검증
    validated_status = validate_status(params.status)
    validated_cancel_type = validate_cancel_type(params.cancel_type)
    validated_max_per_page = validate_max_per_page(params.max_per_page)
    validated_order_id = validate_order_id(params.order_id)
    
    # 파라미터 조합 검증
    _validate_parameter_combinations(
        params.search_type, validated_status, validated_cancel_type,
        params.next_token, validated_max_per_page, validated_order_id
    )
    
    # 검증된 값으로 업데이트
    params.status = validated_status
    params.cancel_type = validated_cancel_type
    params.max_per_page = validated_max_per_page
    params.order_id = validated_order_id


def _validate_parameter_combinations(search_type: str, status: Optional[str], 
                                   cancel_type: str, next_token: Optional[str],
                                   max_per_page: Optional[int], order_id: Optional[int]) -> None:
    """
    파라미터 조합 검증
    
    Args:
        search_type: 검색 타입
        status: 반품 상태
        cancel_type: 취소 유형
        next_token: 다음 페이지 토큰
        max_per_page: 페이지당 최대 조회 수
        order_id: 주문번호
        
    Raises:
        ValueError: 잘못된 파라미터 조합
    """
    # cancelType=CANCEL일 경우 status 파라메터 사용 불가
    if cancel_type == "CANCEL" and status is not None:
        raise ValueError(ERROR_MESSAGES["CANCEL_TYPE_STATUS_CONFLICT"])
    
    # status가 없는 경우 order_id가 필수 (단, timeFrame 검색 제외)
    if search_type != "timeFrame" and status is None and order_id is None and cancel_type == "RETURN":
        # 실제로는 status 없이도 전체 조회가 가능하므로 이 조건을 제거
        pass
    
    # timeFrame 검색 시 페이징 파라메터 사용 불가
    if search_type == "timeFrame":
        if next_token is not None or max_per_page is not None or order_id is not None:
            raise ValueError(ERROR_MESSAGES["TIMEFRAME_PAGINATION_CONFLICT"])


def validate_receipt_id(receipt_id: Union[int, str]) -> int:
    """
    접수번호 검증 (is_valid_receipt_id 통합)
    
    Args:
        receipt_id: 접수번호
        
    Returns:
        int: 검증된 접수번호
        
    Raises:
        ValueError: 잘못된 접수번호
    """
    if receipt_id is None:
        raise ValueError("올바른 접수번호를 입력해주세요. Number 타입이어야 합니다.")
    
    try:
        if isinstance(receipt_id, str):
            receipt_id = receipt_id.strip()
            if not receipt_id:
                raise ValueError("올바른 접수번호를 입력해주세요. Number 타입이어야 합니다.")
            receipt_id = int(receipt_id)
        
        if not isinstance(receipt_id, int) or receipt_id <= 0:
            raise ValueError("올바른 접수번호를 입력해주세요. Number 타입이어야 합니다.")
        
        return receipt_id
    except (ValueError, TypeError):
        raise ValueError("올바른 접수번호를 입력해주세요. Number 타입이어야 합니다.")


def is_valid_receipt_id(receipt_id: Union[int, str]) -> bool:
    """
    접수번호 유효성 검사 (validate_receipt_id를 사용하여 중복 제거)
    
    Args:
        receipt_id: 접수번호
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_receipt_id(receipt_id)
        return True
    except ValueError:
        return False