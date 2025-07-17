#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 파라미터 검증 함수들
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union

from .constants import (
    VENDOR_ID_PATTERN, DATETIME_PATTERN, MAX_DATE_RANGE_DAYS,
    MAX_PER_PAGE, EXCHANGE_STATUS, ERROR_MESSAGES, EXCHANGE_REJECT_CODES,
    DELIVERY_COMPANY_CODES
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


def validate_datetime_format(datetime_str: str, field_name: str) -> str:
    """
    날짜시간 형식 검증
    
    Args:
        datetime_str: 날짜시간 문자열
        field_name: 필드명 (오류 메시지용)
        
    Returns:
        str: 검증된 날짜시간 문자열
        
    Raises:
        ValueError: 잘못된 날짜시간 형식
    """
    if not datetime_str:
        raise ValueError(f"{field_name}은(는) 필수입니다")
    
    # yyyy-MM-ddTHH:mm:ss 형식 검증
    if not re.match(DATETIME_PATTERN, datetime_str):
        raise ValueError(ERROR_MESSAGES["INVALID_DATETIME_FORMAT"])
    
    # 실제 날짜/시간 파싱 검증
    try:
        datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        raise ValueError(f"{field_name} 날짜 형식이 올바르지 않습니다: {datetime_str}")
    
    return datetime_str


def validate_date_range(created_at_from: str, created_at_to: str) -> tuple:
    """
    날짜 범위 검증
    
    Args:
        created_at_from: 검색 시작일
        created_at_to: 검색 종료일
        
    Returns:
        tuple: (검증된 시작일, 검증된 종료일)
        
    Raises:
        ValueError: 잘못된 날짜 범위
    """
    # 개별 날짜 형식 검증
    from_date = validate_datetime_format(created_at_from, "검색 시작일(createdAtFrom)")
    to_date = validate_datetime_format(created_at_to, "검색 종료일(createdAtTo)")
    
    # 날짜 범위 검증
    from_dt = datetime.strptime(from_date, '%Y-%m-%dT%H:%M:%S')
    to_dt = datetime.strptime(to_date, '%Y-%m-%dT%H:%M:%S')
    
    # 시작일이 종료일보다 늦은 경우
    if from_dt > to_dt:
        raise ValueError(ERROR_MESSAGES["START_AFTER_END"])
    
    # 최대 조회 기간 검증 (7일)
    if (to_dt - from_dt).days > MAX_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_LONG"])
    
    return from_date, to_date


def validate_exchange_status(status: Optional[str]) -> Optional[str]:
    """
    교환 상태 검증
    
    Args:
        status: 교환 상태
        
    Returns:
        Optional[str]: 검증된 교환 상태
        
    Raises:
        ValueError: 잘못된 교환 상태
    """
    if status is None:
        return None
    
    if status not in EXCHANGE_STATUS:
        valid_statuses = list(EXCHANGE_STATUS.keys())
        raise ValueError(f"교환 상태는 {valid_statuses} 중 하나여야 합니다")
    
    return status


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


def validate_exchange_search_params(params) -> None:
    """
    교환요청 검색 파라미터 전체 검증
    
    Args:
        params: ExchangeRequestSearchParams 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(params.vendor_id)
    validate_date_range(params.created_at_from, params.created_at_to)
    
    # 선택적 파라미터 검증
    validated_status = validate_exchange_status(params.status)
    validated_order_id = validate_order_id(params.order_id)
    validated_max_per_page = validate_max_per_page(params.max_per_page)
    
    # 검증된 값으로 업데이트
    params.status = validated_status
    params.order_id = validated_order_id
    params.max_per_page = validated_max_per_page


def validate_exchange_id(exchange_id: Union[int, str]) -> int:
    """
    교환 ID 검증
    
    Args:
        exchange_id: 교환 ID
        
    Returns:
        int: 검증된 교환 ID
        
    Raises:
        ValueError: 잘못된 교환 ID
    """
    if exchange_id is None:
        raise ValueError("올바른 교환 ID를 입력해주세요. Number 타입이어야 합니다.")
    
    try:
        if isinstance(exchange_id, str):
            exchange_id = exchange_id.strip()
            if not exchange_id:
                raise ValueError("올바른 교환 ID를 입력해주세요. Number 타입이어야 합니다.")
            exchange_id = int(exchange_id)
        
        if not isinstance(exchange_id, int) or exchange_id <= 0:
            raise ValueError("올바른 교환 ID를 입력해주세요. Number 타입이어야 합니다.")
        
        return exchange_id
    except (ValueError, TypeError):
        raise ValueError("올바른 교환 ID를 입력해주세요. Number 타입이어야 합니다.")


def is_valid_exchange_id(exchange_id: Union[int, str]) -> bool:
    """
    교환 ID 유효성 검사
    
    Args:
        exchange_id: 교환 ID
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_exchange_id(exchange_id)
        return True
    except ValueError:
        return False


def validate_exchange_reject_code(reject_code: str) -> str:
    """
    교환 거부 코드 검증
    
    Args:
        reject_code: 교환 거부 코드
        
    Returns:
        str: 검증된 교환 거부 코드
        
    Raises:
        ValueError: 잘못된 교환 거부 코드
    """
    if not reject_code or not isinstance(reject_code, str):
        raise ValueError(ERROR_MESSAGES["INVALID_REJECT_CODE"])
    
    if reject_code not in EXCHANGE_REJECT_CODES:
        raise ValueError(ERROR_MESSAGES["INVALID_REJECT_CODE"])
    
    return reject_code


def validate_delivery_code(delivery_code: str) -> str:
    """
    택배사 코드 검증
    
    Args:
        delivery_code: 택배사 코드
        
    Returns:
        str: 검증된 택배사 코드
        
    Raises:
        ValueError: 잘못된 택배사 코드
    """
    if not delivery_code or not isinstance(delivery_code, str):
        raise ValueError(ERROR_MESSAGES["INVALID_DELIVERY_CODE"])
    
    # 일반적인 택배사 코드 검증 (주요 택배사만 체크)
    if delivery_code not in DELIVERY_COMPANY_CODES:
        # 주요 택배사가 아닌 경우에도 허용하되, 최소한의 형식 검증
        if not re.match(r'^[A-Z0-9]{2,10}$', delivery_code):
            raise ValueError(ERROR_MESSAGES["INVALID_DELIVERY_CODE"])
    
    return delivery_code


def validate_invoice_number(invoice_number: str) -> str:
    """
    운송장번호 검증
    
    Args:
        invoice_number: 운송장번호
        
    Returns:
        str: 검증된 운송장번호
        
    Raises:
        ValueError: 잘못된 운송장번호
    """
    if not invoice_number or not isinstance(invoice_number, str):
        raise ValueError(ERROR_MESSAGES["INVALID_INVOICE_NUMBER"])
    
    # 운송장번호 형식 검증 (숫자 또는 숫자+영문자 조합, 5~20자리)
    invoice_number = invoice_number.strip()
    if not invoice_number or len(invoice_number) < 5 or len(invoice_number) > 20:
        raise ValueError(ERROR_MESSAGES["INVALID_INVOICE_NUMBER"])
    
    # 기본적인 패턴 검증 (숫자, 영문자, 하이픈만 허용)
    if not re.match(r'^[A-Za-z0-9\-]+$', invoice_number):
        raise ValueError(ERROR_MESSAGES["INVALID_INVOICE_NUMBER"])
    
    return invoice_number


def validate_shipment_box_id(shipment_box_id: Union[int, str]) -> int:
    """
    배송번호(배송박스ID) 검증
    
    Args:
        shipment_box_id: 배송번호
        
    Returns:
        int: 검증된 배송번호
        
    Raises:
        ValueError: 잘못된 배송번호
    """
    if shipment_box_id is None:
        raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
    
    try:
        if isinstance(shipment_box_id, str):
            shipment_box_id = shipment_box_id.strip()
            if not shipment_box_id:
                raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
            shipment_box_id = int(shipment_box_id)
        
        if not isinstance(shipment_box_id, int) or shipment_box_id <= 0:
            raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
        
        return shipment_box_id
    except (ValueError, TypeError):
        raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])


def validate_exchange_processing_params(exchange_id: Union[int, str], vendor_id: str) -> tuple:
    """
    교환요청 처리 공통 파라미터 검증
    
    Args:
        exchange_id: 교환 접수번호
        vendor_id: 판매자 ID
        
    Returns:
        tuple: (검증된 교환 ID, 검증된 벤더 ID)
        
    Raises:
        ValueError: 검증 실패
    """
    validated_exchange_id = validate_exchange_id(exchange_id)
    validated_vendor_id = validate_vendor_id(vendor_id)
    
    return validated_exchange_id, validated_vendor_id


def validate_exchange_rejection_params(exchange_id: Union[int, str], vendor_id: str, 
                                     reject_code: str) -> tuple:
    """
    교환요청 거부 처리 파라미터 검증
    
    Args:
        exchange_id: 교환 접수번호
        vendor_id: 판매자 ID
        reject_code: 교환 거부 코드
        
    Returns:
        tuple: (검증된 교환 ID, 검증된 벤더 ID, 검증된 거부 코드)
        
    Raises:
        ValueError: 검증 실패
    """
    validated_exchange_id, validated_vendor_id = validate_exchange_processing_params(
        exchange_id, vendor_id
    )
    validated_reject_code = validate_exchange_reject_code(reject_code)
    
    return validated_exchange_id, validated_vendor_id, validated_reject_code


def validate_exchange_invoice_params(exchange_id: Union[int, str], vendor_id: str,
                                   delivery_code: str, invoice_number: str,
                                   shipment_box_id: Union[int, str]) -> tuple:
    """
    교환상품 송장 업로드 파라미터 검증
    
    Args:
        exchange_id: 교환 접수번호
        vendor_id: 판매자 ID
        delivery_code: 택배사 코드
        invoice_number: 운송장번호
        shipment_box_id: 배송번호
        
    Returns:
        tuple: 모든 검증된 파라미터들
        
    Raises:
        ValueError: 검증 실패
    """
    validated_exchange_id, validated_vendor_id = validate_exchange_processing_params(
        exchange_id, vendor_id
    )
    validated_delivery_code = validate_delivery_code(delivery_code)
    validated_invoice_number = validate_invoice_number(invoice_number)
    validated_shipment_box_id = validate_shipment_box_id(shipment_box_id)
    
    return (validated_exchange_id, validated_vendor_id, validated_delivery_code,
            validated_invoice_number, validated_shipment_box_id)