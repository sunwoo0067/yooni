#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 관리 패키지
"""

from .return_client import ReturnClient
from .models import (
    ReturnRequestSearchParams,
    ReturnRequest,
    ReturnItem,
    ReturnDeliveryDto,
    ReturnRequestListResponse
)
from .constants import (
    RETURN_STATUS,
    RECEIPT_STATUS,
    CANCEL_TYPE,
    RELEASE_STATUS,
    FAULT_BY_TYPE
)
from .validators import (
    validate_search_params,
    validate_vendor_id,
    validate_receipt_id,
    is_valid_receipt_id
)
from .utils import (
    handle_api_success,
    handle_api_error,
    handle_exception_error,
    format_korean_datetime,
    format_currency,
    create_return_summary_report,
    print_return_summary_table,
    generate_date_range_for_recent_days
)

# 편의 함수 추가
def create_return_client(access_key=None, secret_key=None, vendor_id=None):
    """
    반품 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        ReturnClient: 초기화된 반품 클라이언트
    """
    return ReturnClient(access_key, secret_key, vendor_id)

def get_today_returns_quick(vendor_id=None, days=1):
    """
    오늘 반품 요청 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 1일)
        
    Returns:
        Dict[str, Any]: 반품 요청 조회 결과
    """
    client = create_return_client()
    if vendor_id is None:
        from ..common.config import config
        vendor_id = config.coupang_vendor_id
    
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = ReturnRequestSearchParams(
        vendor_id=vendor_id,
        created_at_from=start_date.strftime('%Y-%m-%d'),
        created_at_to=end_date.strftime('%Y-%m-%d')
    )
    return client.get_return_requests(params)

__all__ = [
    # 편의 함수
    'create_return_client',
    'get_today_returns_quick',
    
    # 클라이언트
    'ReturnClient',
    
    # 모델
    'ReturnRequestSearchParams',
    'ReturnRequest',
    'ReturnItem', 
    'ReturnDeliveryDto',
    'ReturnRequestListResponse',
    
    # 상수
    'RETURN_STATUS',
    'RECEIPT_STATUS',
    'CANCEL_TYPE',
    'RELEASE_STATUS',
    'FAULT_BY_TYPE',
    
    # 검증 함수
    'validate_search_params',
    'validate_vendor_id',
    'validate_receipt_id',
    'is_valid_receipt_id',
    
    # 유틸리티 함수
    'handle_api_success',
    'handle_api_error',
    'handle_exception_error',
    'format_korean_datetime',
    'format_currency',
    'create_return_summary_report',
    'print_return_summary_table',
    'generate_date_range_for_recent_days'
]

__version__ = '1.0.0'
__author__ = 'Coupang Partners API Integration'
__description__ = '쿠팡 파트너스 반품/취소 요청 관리 API 클라이언트'