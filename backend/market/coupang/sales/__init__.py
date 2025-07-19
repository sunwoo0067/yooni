#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 모듈
"""

from .sales_client import SalesClient
from .models import (
    RevenueSearchParams,
    RevenueHistory,
    RevenueItem,
    DeliveryFee,
    RevenueHistoryResponse
)
from .constants import SALE_TYPE, TAX_TYPE, ERROR_MESSAGES
from .validators import (
    validate_vendor_id,
    validate_date_format,
    validate_date_range,
    validate_recognition_date_range,
    validate_max_per_page,
    validate_token,
    validate_revenue_search_params,
    is_valid_recognition_date_range,
    is_valid_max_per_page
)
from .utils import (
    generate_revenue_date_range_for_recent_days,
    generate_revenue_date_range_for_month,
    calculate_revenue_summary,
    format_revenue_amount,
    get_default_vendor_id,
    validate_environment_setup,
    create_sample_revenue_search_params
)

__all__ = [
    # 메인 클라이언트
    'SalesClient',
    
    # 데이터 모델
    'RevenueSearchParams',
    'RevenueHistory',
    'RevenueItem',
    'DeliveryFee', 
    'RevenueHistoryResponse',
    
    # 상수
    'SALE_TYPE',
    'TAX_TYPE',
    'ERROR_MESSAGES',
    
    # 검증 함수
    'validate_vendor_id',
    'validate_date_format',
    'validate_date_range',
    'validate_recognition_date_range',
    'validate_max_per_page',
    'validate_token',
    'validate_revenue_search_params',
    'is_valid_recognition_date_range',
    'is_valid_max_per_page',
    
    # 유틸리티 함수
    'generate_revenue_date_range_for_recent_days',
    'generate_revenue_date_range_for_month',
    'calculate_revenue_summary',
    'format_revenue_amount',
    'get_default_vendor_id',
    'validate_environment_setup',
    'create_sample_revenue_search_params'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "OwnerClan API Team"
__description__ = "쿠팡 파트너스 매출내역 조회 API 클라이언트"

# 모듈 레벨 편의 함수들
def create_sales_client(access_key=None, secret_key=None, vendor_id=None):
    """
    매출내역 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        SalesClient: 초기화된 매출내역 클라이언트
    """
    return SalesClient(access_key, secret_key, vendor_id)


def get_recent_revenue_quick(vendor_id=None, days=7, max_per_page=20):
    """
    최근 매출내역 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 7일)
        max_per_page: 페이지당 최대 개수 (기본값: 20)
        
    Returns:
        Dict[str, Any]: 매출내역 조회 결과
    """
    client = create_sales_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_recent_revenue_history(vendor_id, days, max_per_page)


def get_monthly_revenue_quick(vendor_id=None, year=None, month=None):
    """
    월별 매출내역 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        year: 연도 (None이면 현재 년도)
        month: 월 (None이면 현재 월)
        
    Returns:
        Dict[str, Any]: 월별 매출내역 조회 결과
    """
    client = create_sales_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.get_monthly_revenue_history(vendor_id, year, month)


def get_revenue_summary_quick(vendor_id=None, days=30):
    """
    매출 요약 정보 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 30일)
        
    Returns:
        Dict[str, Any]: 매출 요약 정보
    """
    client = create_sales_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.create_revenue_summary_report(vendor_id, days)