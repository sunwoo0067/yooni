#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의 파라미터 검증 함수들
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from .constants import (
    VENDOR_ID_PATTERN, DATE_PATTERN, MAX_DATE_RANGE_DAYS,
    ANSWERED_TYPE, DEFAULT_PAGE_NUM, DEFAULT_PAGE_SIZE,
    MIN_PAGE_SIZE, MAX_PAGE_SIZE, ERROR_MESSAGES,
    PARTNER_COUNSELING_STATUS, CC_MIN_PAGE_SIZE, CC_MAX_PAGE_SIZE
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


def validate_date_format(date_str: str, field_name: str) -> str:
    """
    날짜 형식 검증
    
    Args:
        date_str: 날짜 문자열
        field_name: 필드명 (오류 메시지용)
        
    Returns:
        str: 검증된 날짜 문자열
        
    Raises:
        ValueError: 잘못된 날짜 형식
    """
    if not date_str:
        raise ValueError(f"{field_name}은(는) 필수입니다")
    
    # yyyy-MM-dd 형식 검증
    if not re.match(DATE_PATTERN, date_str):
        raise ValueError(ERROR_MESSAGES["INVALID_DATE_FORMAT"])
    
    # 실제 날짜 파싱 검증
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"{field_name} 날짜 형식이 올바르지 않습니다: {date_str}")
    
    return date_str


def validate_date_range(inquiry_start_at: str, inquiry_end_at: str) -> tuple:
    """
    날짜 범위 검증
    
    Args:
        inquiry_start_at: 조회 시작일
        inquiry_end_at: 조회 종료일
        
    Returns:
        tuple: (검증된 시작일, 검증된 종료일)
        
    Raises:
        ValueError: 잘못된 날짜 범위
    """
    # 개별 날짜 형식 검증
    start_date = validate_date_format(inquiry_start_at, "조회 시작일(inquiryStartAt)")
    end_date = validate_date_format(inquiry_end_at, "조회 종료일(inquiryEndAt)")
    
    # 날짜 범위 검증
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 시작일이 종료일보다 늦은 경우
    if start_dt > end_dt:
        raise ValueError(ERROR_MESSAGES["START_AFTER_END"])
    
    # 최대 조회 기간 검증 (7일)
    if (end_dt - start_dt).days > MAX_DATE_RANGE_DAYS:
        raise ValueError(ERROR_MESSAGES["DATE_RANGE_TOO_LONG"])
    
    return start_date, end_date


def validate_answered_type(answered_type: str) -> str:
    """
    답변 상태 검증
    
    Args:
        answered_type: 답변 상태
        
    Returns:
        str: 검증된 답변 상태
        
    Raises:
        ValueError: 잘못된 답변 상태
    """
    if not answered_type:
        raise ValueError("답변 상태(answeredType)는 필수입니다")
    
    if answered_type not in ANSWERED_TYPE:
        valid_types = list(ANSWERED_TYPE.keys())
        raise ValueError(f"답변 상태는 {valid_types} 중 하나여야 합니다")
    
    return answered_type


def validate_page_num(page_num: Optional[Union[int, str]]) -> Optional[int]:
    """
    페이지 번호 검증
    
    Args:
        page_num: 페이지 번호
        
    Returns:
        Optional[int]: 검증된 페이지 번호
        
    Raises:
        ValueError: 잘못된 페이지 번호
    """
    if page_num is None:
        return DEFAULT_PAGE_NUM
    
    # 문자열을 정수로 변환 시도
    if isinstance(page_num, str):
        if not page_num.strip():
            return DEFAULT_PAGE_NUM
        try:
            page_num = int(page_num.strip())
        except ValueError:
            raise ValueError(ERROR_MESSAGES["INVALID_PAGE_NUM"])
    
    if not isinstance(page_num, int) or page_num < 1:
        raise ValueError(ERROR_MESSAGES["INVALID_PAGE_NUM"])
    
    return page_num


def validate_page_size(page_size: Optional[Union[int, str]]) -> Optional[int]:
    """
    페이지 크기 검증
    
    Args:
        page_size: 페이지 크기
        
    Returns:
        Optional[int]: 검증된 페이지 크기
        
    Raises:
        ValueError: 잘못된 페이지 크기
    """
    if page_size is None:
        return DEFAULT_PAGE_SIZE
    
    # 문자열을 정수로 변환 시도
    if isinstance(page_size, str):
        if not page_size.strip():
            return DEFAULT_PAGE_SIZE
        try:
            page_size = int(page_size.strip())
        except ValueError:
            raise ValueError(ERROR_MESSAGES["INVALID_PAGE_SIZE"])
    
    if not isinstance(page_size, int) or page_size < MIN_PAGE_SIZE or page_size > MAX_PAGE_SIZE:
        raise ValueError(ERROR_MESSAGES["INVALID_PAGE_SIZE"])
    
    return page_size


def validate_inquiry_search_params(params) -> None:
    """
    고객문의 검색 파라미터 전체 검증
    
    Args:
        params: InquirySearchParams 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(params.vendor_id)
    validate_date_range(params.inquiry_start_at, params.inquiry_end_at)
    validate_answered_type(params.answered_type)
    
    # 선택적 파라미터 검증
    validated_page_num = validate_page_num(params.page_num)
    validated_page_size = validate_page_size(params.page_size)
    
    # 검증된 값으로 업데이트
    params.page_num = validated_page_num
    params.page_size = validated_page_size


def validate_inquiry_id(inquiry_id: Union[int, str]) -> int:
    """
    문의 ID 검증
    
    Args:
        inquiry_id: 문의 ID
        
    Returns:
        int: 검증된 문의 ID
        
    Raises:
        ValueError: 잘못된 문의 ID
    """
    if inquiry_id is None:
        raise ValueError(ERROR_MESSAGES["INQUIRY_ID_REQUIRED"])
    
    try:
        if isinstance(inquiry_id, str):
            inquiry_id = inquiry_id.strip()
            if not inquiry_id:
                raise ValueError(ERROR_MESSAGES["INVALID_INQUIRY_ID"])
            inquiry_id = int(inquiry_id)
        
        if not isinstance(inquiry_id, int) or inquiry_id <= 0:
            raise ValueError(ERROR_MESSAGES["INVALID_INQUIRY_ID"])
        
        return inquiry_id
    except (ValueError, TypeError):
        raise ValueError(ERROR_MESSAGES["INVALID_INQUIRY_ID"])


def is_valid_inquiry_id(inquiry_id: Union[int, str]) -> bool:
    """
    문의 ID 유효성 검사
    
    Args:
        inquiry_id: 문의 ID
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_inquiry_id(inquiry_id)
        return True
    except ValueError:
        return False


def validate_timeout_settings(page_size: int, date_range_days: int) -> Dict[str, Any]:
    """
    타임아웃 설정 검증 및 권장사항 제공
    
    Args:
        page_size: 페이지 크기
        date_range_days: 조회 기간 (일수)
        
    Returns:
        Dict[str, Any]: 타임아웃 검증 결과
    """
    result = {
        "is_risky": False,
        "recommended_page_size": page_size,
        "recommended_days": date_range_days,
        "timeout_seconds": 30,
        "warnings": []
    }
    
    # 타임아웃 위험도 평가
    risk_score = 0
    
    # 페이지 크기가 클수록 위험
    if page_size > 30:
        risk_score += 2
        result["warnings"].append(f"페이지 크기가 큽니다 ({page_size}). 10-20 권장")
    elif page_size > 20:
        risk_score += 1
    
    # 조회 기간이 길수록 위험
    if date_range_days > 5:
        risk_score += 2
        result["warnings"].append(f"조회 기간이 깁니다 ({date_range_days}일). 1-3일 권장")
    elif date_range_days > 3:
        risk_score += 1
    
    # 위험도에 따른 권장사항
    if risk_score >= 3:
        result["is_risky"] = True
        result["recommended_page_size"] = 10
        result["recommended_days"] = 1
        result["timeout_seconds"] = 60
        result["warnings"].append("타임아웃 위험이 높습니다. 설정을 조정해주세요.")
    elif risk_score >= 2:
        result["timeout_seconds"] = 45
    
    return result


def validate_reply_content(content: str) -> str:
    """
    답변 내용 검증
    
    Args:
        content: 답변 내용
        
    Returns:
        str: 검증된 답변 내용
        
    Raises:
        ValueError: 잘못된 답변 내용
    """
    if not content:
        raise ValueError(ERROR_MESSAGES["INVALID_REPLY_CONTENT"])
    
    # 공백만 있는 경우
    if not content.strip():
        raise ValueError(ERROR_MESSAGES["INVALID_REPLY_CONTENT"])
    
    # 길이 검증 (최대 1000자로 제한)
    if len(content) > 1000:
        raise ValueError("답변 내용은 1000자를 초과할 수 없습니다")
    
    # JSON 특수문자 검증
    import json
    try:
        # 줄바꿈 문자 정리
        cleaned_content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # JSON 인코딩 테스트
        json.dumps({"content": cleaned_content})
        
        return cleaned_content
    except (TypeError, ValueError) as e:
        raise ValueError(ERROR_MESSAGES["INVALID_JSON_FORMAT"])


def validate_reply_by(reply_by: str) -> str:
    """
    응답자 WING ID 검증
    
    Args:
        reply_by: 응답자 WING ID
        
    Returns:
        str: 검증된 WING ID
        
    Raises:
        ValueError: 잘못된 WING ID
    """
    if not reply_by:
        raise ValueError(ERROR_MESSAGES["INVALID_REPLY_BY"])
    
    # 공백만 있는 경우
    if not reply_by.strip():
        raise ValueError(ERROR_MESSAGES["INVALID_REPLY_BY"])
    
    # 기본적인 형식 검증 (영문자, 숫자, 언더스코어만 허용)
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', reply_by.strip()):
        raise ValueError("WING ID는 영문자, 숫자, 언더스코어만 사용할 수 있습니다")
    
    # 길이 검증 (최대 50자)
    if len(reply_by.strip()) > 50:
        raise ValueError("WING ID는 50자를 초과할 수 없습니다")
    
    return reply_by.strip()


def validate_inquiry_reply_request(reply_request) -> None:
    """
    고객문의 답변 요청 전체 검증
    
    Args:
        reply_request: InquiryReplyRequest 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(reply_request.vendor_id)
    validate_inquiry_id(reply_request.inquiry_id)
    
    # 답변 내용 검증 및 정리
    cleaned_content = validate_reply_content(reply_request.content)
    reply_request.content = cleaned_content
    
    # 응답자 ID 검증 및 정리
    cleaned_reply_by = validate_reply_by(reply_request.reply_by)
    reply_request.reply_by = cleaned_reply_by


def is_valid_reply_content(content: str) -> bool:
    """
    답변 내용 유효성 검사
    
    Args:
        content: 답변 내용
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_reply_content(content)
        return True
    except ValueError:
        return False


def is_valid_reply_by(reply_by: str) -> bool:
    """
    WING ID 유효성 검사
    
    Args:
        reply_by: WING ID
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_reply_by(reply_by)
        return True
    except ValueError:
        return False


def validate_partner_counseling_status(status: str) -> str:
    """
    고객센터 문의 상담 상태 검증
    
    Args:
        status: 상담 상태
        
    Returns:
        str: 검증된 상담 상태
        
    Raises:
        ValueError: 잘못된 상담 상태
    """
    if not status:
        raise ValueError(ERROR_MESSAGES["INVALID_COUNSELING_STATUS"])
    
    if status not in PARTNER_COUNSELING_STATUS:
        valid_statuses = list(PARTNER_COUNSELING_STATUS.keys())
        raise ValueError(f"상담 상태는 {valid_statuses} 중 하나여야 합니다")
    
    return status


def validate_vendor_item_id(vendor_item_id: Optional[str]) -> Optional[str]:
    """
    옵션 ID 검증
    
    Args:
        vendor_item_id: 옵션 ID
        
    Returns:
        Optional[str]: 검증된 옵션 ID
        
    Raises:
        ValueError: 잘못된 옵션 ID
    """
    if vendor_item_id is None:
        return None
    
    if not vendor_item_id.strip():
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ITEM_ID"])
    
    # 숫자 형식 검증
    try:
        int(vendor_item_id.strip())
    except ValueError:
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ITEM_ID"])
    
    return vendor_item_id.strip()


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
    
    try:
        if isinstance(order_id, str):
            order_id = order_id.strip()
            if not order_id:
                return None
            order_id = int(order_id)
        
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])
        
        return order_id
    except (ValueError, TypeError):
        raise ValueError(ERROR_MESSAGES["INVALID_ORDER_ID"])


def validate_cc_page_size(page_size: Optional[Union[int, str]]) -> Optional[int]:
    """
    고객센터 문의 페이지 크기 검증 (1~30)
    
    Args:
        page_size: 페이지 크기
        
    Returns:
        Optional[int]: 검증된 페이지 크기
        
    Raises:
        ValueError: 잘못된 페이지 크기
    """
    if page_size is None:
        return None
    
    # 문자열을 정수로 변환 시도
    if isinstance(page_size, str):
        if not page_size.strip():
            return None
        try:
            page_size = int(page_size.strip())
        except ValueError:
            raise ValueError(ERROR_MESSAGES["INVALID_PAGE_SIZE_CC"])
    
    if not isinstance(page_size, int) or page_size < CC_MIN_PAGE_SIZE or page_size > CC_MAX_PAGE_SIZE:
        raise ValueError(ERROR_MESSAGES["INVALID_PAGE_SIZE_CC"])
    
    return page_size


def validate_cc_inquiry_search_params(params) -> None:
    """
    고객센터 문의 검색 파라미터 전체 검증
    
    Args:
        params: CallCenterInquirySearchParams 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(params.vendor_id)
    validate_partner_counseling_status(params.partner_counseling_status)
    
    # 날짜 범위 검증 (설정된 경우에만)
    if params.inquiry_start_at and params.inquiry_end_at:
        validate_date_range(params.inquiry_start_at, params.inquiry_end_at)
    elif params.inquiry_start_at and not params.inquiry_end_at:
        raise ValueError("조회 시작일을 설정했으면 종료일도 설정해야 합니다")
    elif not params.inquiry_start_at and params.inquiry_end_at:
        raise ValueError("조회 종료일을 설정했으면 시작일도 설정해야 합니다")
    
    # vendorItemId나 날짜 범위 중 하나는 반드시 설정되어야 함
    has_date_range = params.inquiry_start_at and params.inquiry_end_at
    has_vendor_item_id = params.vendor_item_id
    
    if not has_date_range and not has_vendor_item_id:
        raise ValueError("조회 기간 또는 옵션 ID 중 하나는 반드시 설정해야 합니다")
    
    # 선택적 파라미터 검증
    validated_vendor_item_id = validate_vendor_item_id(params.vendor_item_id)
    validated_order_id = validate_order_id(params.order_id)
    validated_page_num = validate_page_num(params.page_num)
    validated_page_size = validate_cc_page_size(params.page_size)
    
    # 검증된 값으로 업데이트
    params.vendor_item_id = validated_vendor_item_id
    params.order_id = validated_order_id
    params.page_num = validated_page_num
    params.page_size = validated_page_size


def validate_cc_reply_content(content: str) -> str:
    """
    고객센터 문의 답변 내용 검증 (2~1000자)
    
    Args:
        content: 답변 내용
        
    Returns:
        str: 검증된 답변 내용
        
    Raises:
        ValueError: 잘못된 답변 내용
    """
    if not content or not content.strip():
        raise ValueError(ERROR_MESSAGES["CONTENT_LENGTH_ERROR"])
    
    cleaned_content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    if not (2 <= len(cleaned_content) <= 1000):
        raise ValueError(ERROR_MESSAGES["CONTENT_LENGTH_ERROR"])
    
    # JSON 인코딩 검증
    import json
    try:
        json.dumps({"content": cleaned_content})
        return cleaned_content
    except (TypeError, ValueError):
        raise ValueError(ERROR_MESSAGES["INVALID_JSON_FORMAT"])


def validate_parent_answer_id(parent_answer_id: Union[int, str]) -> int:
    """
    부모 답변 ID 검증
    
    Args:
        parent_answer_id: 부모 답변 ID
        
    Returns:
        int: 검증된 부모 답변 ID
        
    Raises:
        ValueError: 잘못된 부모 답변 ID
    """
    if parent_answer_id is None:
        raise ValueError(ERROR_MESSAGES["PARENT_ANSWER_ID_REQUIRED"])
    
    try:
        if isinstance(parent_answer_id, str):
            parent_answer_id = parent_answer_id.strip()
            if not parent_answer_id:
                raise ValueError(ERROR_MESSAGES["PARENT_ANSWER_ID_REQUIRED"])
            parent_answer_id = int(parent_answer_id)
        
        if not isinstance(parent_answer_id, int) or parent_answer_id <= 0:
            raise ValueError(ERROR_MESSAGES["PARENT_ANSWER_ID_REQUIRED"])
        
        return parent_answer_id
    except (ValueError, TypeError):
        raise ValueError(ERROR_MESSAGES["PARENT_ANSWER_ID_REQUIRED"])


def validate_cc_reply_request(reply_request) -> None:
    """
    고객센터 문의 답변 요청 전체 검증
    
    Args:
        reply_request: CallCenterInquiryReplyRequest 객체
        
    Raises:
        ValueError: 검증 실패
    """
    # 필수 파라미터 검증
    validate_vendor_id(reply_request.vendor_id)
    validate_inquiry_id(reply_request.inquiry_id)
    validate_parent_answer_id(reply_request.parent_answer_id)
    
    # 답변 내용 검증 및 정리
    cleaned_content = validate_cc_reply_content(reply_request.content)
    reply_request.content = cleaned_content
    
    # 응답자 ID 검증 및 정리
    cleaned_reply_by = validate_reply_by(reply_request.reply_by)
    reply_request.reply_by = cleaned_reply_by


def validate_confirm_by(confirm_by: str) -> str:
    """
    확인자 ID 검증
    
    Args:
        confirm_by: 확인자 ID
        
    Returns:
        str: 검증된 확인자 ID
        
    Raises:
        ValueError: 잘못된 확인자 ID
    """
    if not confirm_by or not confirm_by.strip():
        raise ValueError(ERROR_MESSAGES["CONFIRM_BY_REQUIRED"])
    
    # 기본적인 형식 검증 (영문자, 숫자, 언더스코어, 하이픈만 허용)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', confirm_by.strip()):
        raise ValueError("확인자 ID는 영문자, 숫자, 언더스코어, 하이픈만 사용할 수 있습니다")
    
    # 길이 검증 (최대 50자)
    if len(confirm_by.strip()) > 50:
        raise ValueError("확인자 ID는 50자를 초과할 수 없습니다")
    
    return confirm_by.strip()


def is_valid_partner_counseling_status(status: str) -> bool:
    """
    고객센터 문의 상담 상태 유효성 검사
    
    Args:
        status: 상담 상태
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_partner_counseling_status(status)
        return True
    except ValueError:
        return False


def is_valid_cc_reply_content(content: str) -> bool:
    """
    고객센터 문의 답변 내용 유효성 검사
    
    Args:
        content: 답변 내용
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_cc_reply_content(content)
        return True
    except ValueError:
        return False


def is_valid_confirm_by(confirm_by: str) -> bool:
    """
    확인자 ID 유효성 검사
    
    Args:
        confirm_by: 확인자 ID
        
    Returns:
        bool: 유효성 여부
    """
    try:
        validate_confirm_by(confirm_by)
        return True
    except ValueError:
        return False