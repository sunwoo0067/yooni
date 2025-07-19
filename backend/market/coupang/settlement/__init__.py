#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈
"""

from .settlement_client import SettlementClient
from .models import (
    SettlementSearchParams,
    SettlementHistory,
    SettlementHistoryResponse
)
from .constants import SETTLEMENT_TYPE, SETTLEMENT_STATUS, ERROR_MESSAGES
from .validators import (
    validate_revenue_recognition_year_month,
    validate_settlement_search_params,
    is_valid_year_month
)
from .utils import (
    generate_current_year_month,
    generate_previous_year_month,
    calculate_settlement_summary,
    format_settlement_amount,
    get_default_vendor_id,
    validate_environment_setup,
    create_sample_settlement_search_params
)

__all__ = [
    # 메인 클라이언트
    'SettlementClient',
    
    # 데이터 모델
    'SettlementSearchParams',
    'SettlementHistory',
    'SettlementHistoryResponse',
    
    # 상수
    'SETTLEMENT_TYPE',
    'SETTLEMENT_STATUS',
    'ERROR_MESSAGES',
    
    # 검증 함수
    'validate_revenue_recognition_year_month',
    'validate_settlement_search_params',
    'is_valid_year_month',
    
    # 유틸리티 함수
    'generate_current_year_month',
    'generate_previous_year_month',
    'calculate_settlement_summary',
    'format_settlement_amount',
    'get_default_vendor_id',
    'validate_environment_setup',
    'create_sample_settlement_search_params'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "OwnerClan API Team"
__description__ = "쿠팡 파트너스 지급내역 조회 API 클라이언트"

# 모듈 레벨 편의 함수들
def create_settlement_client(access_key=None, secret_key=None, vendor_id=None):
    """
    지급내역 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        SettlementClient: 초기화된 지급내역 클라이언트
    """
    return SettlementClient(access_key, secret_key, vendor_id)


def get_current_month_settlement_quick(vendor_id=None):
    """
    이번 달 지급내역 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        
    Returns:
        Dict[str, Any]: 지급내역 조회 결과
    """
    client = create_settlement_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    
    current_year_month = generate_current_year_month()
    return client.get_settlement_history(current_year_month)


def get_previous_month_settlement_quick(vendor_id=None):
    """
    지난 달 지급내역 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        
    Returns:
        Dict[str, Any]: 지급내역 조회 결과
    """
    client = create_settlement_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    
    previous_year_month = generate_previous_year_month()
    return client.get_settlement_history(previous_year_month)


def get_settlement_summary_quick(vendor_id=None, months=3):
    """
    지급내역 요약 정보 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        months: 조회할 개월 수 (기본값: 3개월)
        
    Returns:
        Dict[str, Any]: 지급내역 요약 정보
    """
    client = create_settlement_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    return client.create_settlement_summary_report(months)