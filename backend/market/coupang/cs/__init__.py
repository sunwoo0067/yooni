#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 모듈
"""

from .cs_client import CSClient
from .call_center_client import CallCenterClient
from .models import (
    InquirySearchParams,
    CustomerInquiry,
    InquiryComment,
    InquiryPagination,
    InquiryListResponse,
    InquiryReplyRequest,
    InquiryReplyResponse,
    CallCenterInquirySearchParams,
    CallCenterInquiry,
    CallCenterReply,
    CallCenterInquiryListResponse,
    CallCenterInquiryReplyRequest,
    CallCenterInquiryConfirmRequest
)
from .constants import ANSWERED_TYPE, ERROR_MESSAGES, PARTNER_COUNSELING_STATUS
from .validators import (
    validate_vendor_id,
    validate_date_format,
    validate_date_range,
    validate_answered_type,
    validate_page_num,
    validate_page_size,
    validate_inquiry_search_params,
    validate_inquiry_id,
    is_valid_inquiry_id,
    validate_timeout_settings,
    validate_reply_content,
    validate_reply_by,
    validate_inquiry_reply_request,
    is_valid_reply_content,
    is_valid_reply_by,
    validate_partner_counseling_status,
    validate_cc_inquiry_search_params,
    validate_cc_reply_request,
    validate_confirm_by,
    is_valid_partner_counseling_status,
    is_valid_cc_reply_content,
    is_valid_confirm_by
)
from .utils import (
    generate_inquiry_date_range_for_recent_days,
    generate_inquiry_date_range_for_today,
    analyze_inquiry_patterns,
    analyze_response_times,
    generate_inquiry_recommendations,
    create_inquiry_summary_report,
    get_default_vendor_id,
    validate_environment_setup,
    create_sample_inquiry_search_params
)

__all__ = [
    # 메인 클라이언트
    'CSClient',
    'CallCenterClient',
    
    # 데이터 모델
    'InquirySearchParams',
    'CustomerInquiry', 
    'InquiryComment',
    'InquiryPagination',
    'InquiryListResponse',
    'InquiryReplyRequest',
    'InquiryReplyResponse',
    'CallCenterInquirySearchParams',
    'CallCenterInquiry',
    'CallCenterReply',
    'CallCenterInquiryListResponse',
    'CallCenterInquiryReplyRequest',
    'CallCenterInquiryConfirmRequest',
    
    # 상수
    'ANSWERED_TYPE',
    'ERROR_MESSAGES',
    'PARTNER_COUNSELING_STATUS',
    
    # 검증 함수
    'validate_vendor_id',
    'validate_date_format',
    'validate_date_range',
    'validate_answered_type',
    'validate_page_num',
    'validate_page_size',
    'validate_inquiry_search_params',
    'validate_inquiry_id',
    'is_valid_inquiry_id',
    'validate_timeout_settings',
    'validate_reply_content',
    'validate_reply_by',
    'validate_inquiry_reply_request',
    'is_valid_reply_content',
    'is_valid_reply_by',
    'validate_partner_counseling_status',
    'validate_cc_inquiry_search_params',
    'validate_cc_reply_request',
    'validate_confirm_by',
    'is_valid_partner_counseling_status',
    'is_valid_cc_reply_content',
    'is_valid_confirm_by',
    
    # 유틸리티 함수
    'generate_inquiry_date_range_for_recent_days',
    'generate_inquiry_date_range_for_today',
    'analyze_inquiry_patterns',
    'analyze_response_times',
    'generate_inquiry_recommendations',
    'create_inquiry_summary_report',
    'get_default_vendor_id',
    'validate_environment_setup',
    'create_sample_inquiry_search_params'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "OwnerClan API Team"
__description__ = "쿠팡 파트너스 고객문의(CS) 관리 API 클라이언트"

# 모듈 레벨 편의 함수들
def create_cs_client(access_key=None, secret_key=None, vendor_id=None):
    """
    CS 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        CSClient: 초기화된 CS 클라이언트
    """
    return CSClient(access_key, secret_key, vendor_id)


def create_call_center_client(access_key=None, secret_key=None, vendor_id=None):
    """
    고객센터 문의 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        CallCenterClient: 초기화된 고객센터 클라이언트
    """
    return CallCenterClient(access_key, secret_key, vendor_id)


def get_today_inquiries_quick(vendor_id=None, answered_type="ALL"):
    """
    오늘의 고객문의 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        answered_type: 답변 상태 (기본값: ALL)
        
    Returns:
        Dict[str, Any]: 고객문의 조회 결과
    """
    client = create_cs_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_today_inquiries(vendor_id, answered_type)


def get_unanswered_inquiries_quick(vendor_id=None, days=7):
    """
    미답변 고객문의 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음) 
        days: 조회 기간 (기본값: 7일)
        
    Returns:
        Dict[str, Any]: 미답변 고객문의 조회 결과
    """
    client = create_cs_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_unanswered_inquiries(vendor_id, days)


def create_inquiry_analysis_quick(vendor_id=None, days=7):
    """
    고객문의 분석 보고서 빠른 생성
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 분석 기간 (기본값: 7일)
        
    Returns:
        Dict[str, Any]: 고객문의 분석 보고서
    """
    client = create_cs_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.create_inquiry_analysis_report(vendor_id, days)


def reply_to_inquiry_quick(inquiry_id, content, reply_by, vendor_id=None):
    """
    고객문의 빠른 답변
    
    Args:
        inquiry_id: 문의 ID
        content: 답변 내용
        reply_by: 응답자 WING ID
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        
    Returns:
        Dict[str, Any]: 답변 처리 결과
    """
    client = create_cs_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.reply_to_inquiry(inquiry_id, vendor_id, content, reply_by)


def bulk_reply_quick(reply_requests):
    """
    여러 고객문의 일괄 답변
    
    Args:
        reply_requests: 답변 요청 리스트
            각 요청: {"inquiry_id": int, "content": str, "reply_by": str, "vendor_id": str (optional)}
            
    Returns:
        Dict[str, Any]: 일괄 답변 처리 결과
    """
    client = create_cs_client()
    return client.bulk_reply_to_inquiries(reply_requests)


# 고객센터 문의 편의 함수들
def get_call_center_inquiries_quick(vendor_id=None, counseling_status="NONE", days=1):
    """
    고객센터 문의 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        counseling_status: 상담 상태 (기본값: NONE - 전체)
        days: 조회 기간 (기본값: 1일)
        
    Returns:
        Dict[str, Any]: 고객센터 문의 조회 결과
    """
    client = create_call_center_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_call_center_inquiries_by_date(vendor_id, days, counseling_status)


def get_pending_call_center_inquiries_quick(vendor_id=None, days=7):
    """
    답변 대기 중인 고객센터 문의 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 7일)
        
    Returns:
        Dict[str, Any]: 답변 대기 중인 고객센터 문의 결과
    """
    client = create_call_center_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_pending_call_center_inquiries(vendor_id, days)


def get_transfer_call_center_inquiries_quick(vendor_id=None, days=7):
    """
    확인 대기 중인 고객센터 문의 빠른 조회 (TRANSFER 상태)
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 7일)
        
    Returns:
        Dict[str, Any]: 확인 대기 중인 고객센터 문의 결과
    """
    client = create_call_center_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_transfer_call_center_inquiries(vendor_id, days)


def reply_to_call_center_inquiry_quick(inquiry_id, vendor_id, content, reply_by, parent_answer_id):
    """
    고객센터 문의 빠른 답변
    
    Args:
        inquiry_id: 문의 ID
        vendor_id: 판매자 ID
        content: 답변 내용 (2~1000자)
        reply_by: 응답자 WING ID
        parent_answer_id: 부모 이관글 ID
        
    Returns:
        Dict[str, Any]: 답변 처리 결과
    """
    client = create_call_center_client()
    return client.reply_to_call_center_inquiry(
        inquiry_id, vendor_id, content, reply_by, parent_answer_id
    )


def confirm_call_center_inquiry_quick(inquiry_id, vendor_id, confirm_by):
    """
    고객센터 문의 빠른 확인 처리
    
    Args:
        inquiry_id: 문의 ID
        vendor_id: 판매자 ID
        confirm_by: 확인자 WING ID
        
    Returns:
        Dict[str, Any]: 확인 처리 결과
    """
    client = create_call_center_client()
    return client.confirm_call_center_inquiry(inquiry_id, vendor_id, confirm_by)