#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관련 검증 함수들
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List

from .models import OrderSheetSearchParams
from .constants import (
    ORDER_STATUS, MAX_DATE_RANGE_DAYS, MAX_PER_PAGE,
    DATE_PATTERN, VENDOR_ID_PATTERN, ERROR_MESSAGES, SEARCH_TYPES
)


def validate_vendor_id(vendor_id: str):
    """판매자 ID 검증"""
    if not vendor_id:
        raise ValueError("판매자 ID(vendorId)는 필수입니다")
    
    if not isinstance(vendor_id, str):
        raise ValueError("판매자 ID는 문자열이어야 합니다")
    
    if not re.match(VENDOR_ID_PATTERN, vendor_id):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])


def validate_date_format(date_str: str, field_name: str):
    """날짜 형식 검증"""
    if not date_str:
        raise ValueError(f"{field_name}는 필수입니다")
    
    if not isinstance(date_str, str):
        raise ValueError(f"{field_name}는 문자열이어야 합니다")
    
    if not re.match(DATE_PATTERN, date_str):
        raise ValueError(f"{field_name}: {ERROR_MESSAGES['INVALID_DATE_FORMAT']}")
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name}: 유효하지 않은 날짜입니다")


def validate_date_range(created_at_from: str, created_at_to: str):
    """날짜 범위 검증"""
    # 개별 날짜 형식 검증
    validate_date_format(created_at_from, "검색 시작일시")
    validate_date_format(created_at_to, "검색 종료일시")
    
    # 날짜 파싱
    start_date = datetime.strptime(created_at_from, "%Y-%m-%d")
    end_date = datetime.strptime(created_at_to, "%Y-%m-%d")
    
    # 시작일이 종료일보다 나중인지 확인
    if start_date > end_date:
        raise ValueError("검색 시작일시가 종료일시보다 나중일 수 없습니다")
    
    # 날짜 범위가 31일 이내인지 확인
    date_diff = (end_date - start_date).days
    if date_diff > MAX_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_LONG"])


def validate_order_status(status: str):
    """발주서 상태 검증"""
    if not status:
        raise ValueError("발주서 상태(status)는 필수입니다")
    
    if not isinstance(status, str):
        raise ValueError("발주서 상태는 문자열이어야 합니다")
    
    if status not in ORDER_STATUS:
        valid_statuses = ", ".join(ORDER_STATUS.keys())
        raise ValueError(f"{ERROR_MESSAGES['INVALID_STATUS']} 유효한 값: {valid_statuses}")


def validate_max_per_page(max_per_page: Optional[int]):
    """페이지당 최대 조회 수 검증"""
    if max_per_page is None:
        return  # 선택사항이므로 None은 허용
    
    if not isinstance(max_per_page, int):
        raise ValueError("페이지당 최대 조회 요청 값은 숫자여야 합니다")
    
    if max_per_page < 1 or max_per_page > MAX_PER_PAGE:
        raise ValueError(ERROR_MESSAGES["INVALID_MAX_PER_PAGE"])


def validate_next_token(next_token: Optional[str]):
    """다음 페이지 토큰 검증"""
    if next_token is None:
        return  # 선택사항이므로 None은 허용
    
    if not isinstance(next_token, str):
        raise ValueError("다음 페이지 토큰은 문자열이어야 합니다")
    
    # 빈 문자열은 허용하지 않음
    if next_token.strip() == "":
        raise ValueError("다음 페이지 토큰은 빈 문자열일 수 없습니다")


def validate_search_type(search_type: Optional[str]):
    """검색 타입 검증"""
    if search_type is None:
        return  # 선택사항이므로 None은 허용
    
    if not isinstance(search_type, str):
        raise ValueError("검색 타입은 문자열이어야 합니다")
    
    if search_type not in SEARCH_TYPES:
        valid_types = ", ".join(SEARCH_TYPES.keys())
        raise ValueError(f"올바른 검색 타입을 입력해주세요. 유효한 값: {valid_types}")


def validate_search_params(params: OrderSheetSearchParams):
    """발주서 검색 파라미터 전체 검증"""
    # 필수 필드들 검증
    validate_vendor_id(params.vendor_id)
    validate_date_range(params.created_at_from, params.created_at_to)
    validate_order_status(params.status)
    
    # 선택적 필드들 검증
    validate_max_per_page(params.max_per_page)
    validate_next_token(params.next_token)
    validate_search_type(params.search_type)


def validate_api_response(response: dict):
    """API 응답 검증"""
    if not isinstance(response, dict):
        raise ValueError("API 응답이 유효하지 않습니다")
    
    if "code" not in response:
        raise ValueError("API 응답에 코드가 없습니다")
    
    if response.get("code") != 200:
        error_message = response.get("message", "알 수 없는 오류")
        raise ValueError(f"API 호출 실패: {error_message}")


def is_valid_date_string(date_str: str) -> bool:
    """날짜 문자열 유효성 간단 확인"""
    try:
        validate_date_format(date_str, "날짜")
        return True
    except ValueError:
        return False


def is_valid_vendor_id(vendor_id: str) -> bool:
    """판매자 ID 유효성 간단 확인"""
    try:
        validate_vendor_id(vendor_id)
        return True
    except ValueError:
        return False


def get_max_end_date(start_date: str) -> str:
    """시작 날짜에서 최대 조회 가능한 종료 날짜 계산"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        max_end = start + timedelta(days=MAX_DATE_RANGE_DAYS)
        return max_end.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("시작 날짜 형식이 올바르지 않습니다")


def calculate_date_range_days(start_date: str, end_date: str) -> int:
    """날짜 범위 일수 계산"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days
    except ValueError:
        raise ValueError("날짜 형식이 올바르지 않습니다")


def validate_shipment_box_id(shipment_box_id):
    """배송번호(shipmentBoxId) 검증"""
    if shipment_box_id is None:
        raise ValueError("배송번호(shipmentBoxId)는 필수입니다")
    
    # 숫자 타입인지 확인 (int 또는 문자열로 된 숫자)
    if isinstance(shipment_box_id, str):
        if not shipment_box_id.isdigit():
            raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
        shipment_box_id = int(shipment_box_id)
    elif not isinstance(shipment_box_id, int):
        raise ValueError(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
    
    # 양수인지 확인
    if shipment_box_id <= 0:
        raise ValueError("배송번호(shipmentBoxId)는 양수여야 합니다")
    
    return shipment_box_id


def is_valid_shipment_box_id(shipment_box_id) -> bool:
    """배송번호 유효성 간단 확인"""
    try:
        validate_shipment_box_id(shipment_box_id)
        return True
    except ValueError:
        return False


def validate_order_id(order_id):
    """주문번호(orderId) 검증"""
    if order_id is None:
        raise ValueError("주문번호(orderId)는 필수입니다")
    
    # 숫자 타입인지 확인 (int 또는 문자열로 된 숫자)
    if isinstance(order_id, str):
        if not order_id.isdigit():
            raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])
        order_id = int(order_id)
    elif not isinstance(order_id, int):
        raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])
    
    # 양수인지 확인
    if order_id <= 0:
        raise ValueError("주문번호(orderId)는 양수여야 합니다")
    
    return order_id


def is_valid_order_id(order_id) -> bool:
    """주문번호 유효성 간단 확인"""
    try:
        validate_order_id(order_id)
        return True
    except ValueError:
        return False


def validate_invoice_number(invoice_number: str):
    """송장번호 검증"""
    if not invoice_number:
        raise ValueError("송장번호는 필수입니다")
    
    if not isinstance(invoice_number, str):
        raise ValueError("송장번호는 문자열이어야 합니다")
    
    # 송장번호는 보통 특수문자를 제외한 영숫자
    if len(invoice_number.strip()) == 0:
        raise ValueError("송장번호는 빈 문자열일 수 없습니다")
    
    return invoice_number.strip()


def validate_delivery_company_code(delivery_company_code: str):
    """택배사 코드 검증"""
    if not delivery_company_code:
        raise ValueError("택배사 코드는 필수입니다")
    
    if not isinstance(delivery_company_code, str):
        raise ValueError("택배사 코드는 문자열이어야 합니다")
    
    from .constants import DELIVERY_COMPANY_CODES
    if delivery_company_code not in DELIVERY_COMPANY_CODES:
        valid_codes = ", ".join(DELIVERY_COMPANY_CODES.keys())
        raise ValueError(f"올바른 택배사 코드를 입력해주세요. 유효한 값: {valid_codes}")
    
    return delivery_company_code


def validate_vendor_item_id(vendor_item_id):
    """상품 ID 검증"""
    if vendor_item_id is None:
        raise ValueError("상품 ID(vendorItemId)는 필수입니다")
    
    # 숫자 타입인지 확인 (int 또는 문자열로 된 숫자)
    if isinstance(vendor_item_id, str):
        if not vendor_item_id.isdigit():
            raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ITEM_ID"])
        vendor_item_id = int(vendor_item_id)
    elif not isinstance(vendor_item_id, int):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ITEM_ID"])
    
    # 양수인지 확인
    if vendor_item_id <= 0:
        raise ValueError("상품 ID(vendorItemId)는 양수여야 합니다")
    
    return vendor_item_id


def validate_reason(reason: str):
    """취소/중지 사유 검증"""
    if not reason:
        raise ValueError("사유는 필수입니다")
    
    if not isinstance(reason, str):
        raise ValueError("사유는 문자열이어야 합니다")
    
    if len(reason.strip()) == 0:
        raise ValueError("사유는 빈 문자열일 수 없습니다")
    
    return reason.strip()


def validate_order_status_for_processing(current_status: str, required_status: List[str], operation_name: str):
    """주문 처리 가능 상태 검증"""
    if current_status not in required_status:
        required_statuses = ", ".join(required_status)
        raise ValueError(f"{operation_name}은(는) {required_statuses} 상태에서만 가능합니다. 현재 상태: {current_status}")


def is_valid_invoice_number(invoice_number: str) -> bool:
    """송장번호 유효성 간단 확인"""
    try:
        validate_invoice_number(invoice_number)
        return True
    except ValueError:
        return False


def is_valid_delivery_company_code(delivery_company_code: str) -> bool:
    """택배사 코드 유효성 간단 확인"""
    try:
        validate_delivery_company_code(delivery_company_code)
        return True
    except ValueError:
        return False


def is_valid_vendor_item_id(vendor_item_id) -> bool:
    """상품 ID 유효성 간단 확인"""
    try:
        validate_vendor_item_id(vendor_item_id)
        return True
    except ValueError:
        return False