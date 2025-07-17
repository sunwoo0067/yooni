#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈 검증 함수
"""

import re
from datetime import datetime
from typing import Optional

from .constants import (
    VENDOR_ID_PATTERN, YEAR_MONTH_PATTERN, ERROR_MESSAGES
)
from .models import SettlementSearchParams


def validate_vendor_id(vendor_id: any) -> str:
    """판매자 ID 검증"""
    if not vendor_id or not isinstance(vendor_id, str):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])
    
    if not re.match(VENDOR_ID_PATTERN, vendor_id):
        raise ValueError(ERROR_MESSAGES["INVALID_VENDOR_ID"])
    
    return vendor_id


def validate_revenue_recognition_year_month(year_month: any) -> str:
    """매출인식월 검증 (YYYY-MM)"""
    if not year_month or not isinstance(year_month, str):
        raise ValueError(ERROR_MESSAGES["INVALID_YEAR_MONTH_FORMAT"])
    
    if not re.match(YEAR_MONTH_PATTERN, year_month):
        raise ValueError(ERROR_MESSAGES["INVALID_YEAR_MONTH_FORMAT"])
    
    try:
        target_year, target_month = map(int, year_month.split('-'))
        target_date = datetime(target_year, target_month, 1)
        current_date = datetime.now()
        
        # 현재 월까지만 조회 가능
        if target_date > current_date:
            raise ValueError(ERROR_MESSAGES["YEAR_MONTH_FUTURE"])
        
        # 너무 오래된 데이터 체크 (2년 전까지만)
        two_years_ago = datetime(current_date.year - 2, current_date.month, 1)
        if target_date < two_years_ago:
            raise ValueError(ERROR_MESSAGES["YEAR_MONTH_TOO_OLD"])
            
    except ValueError as e:
        if "YEAR_MONTH" in str(e):
            raise
        raise ValueError(ERROR_MESSAGES["INVALID_YEAR_MONTH_FORMAT"])
    
    return year_month


def validate_settlement_search_params(search_params: SettlementSearchParams) -> SettlementSearchParams:
    """지급내역 검색 파라미터 종합 검증"""
    validated_year_month = validate_revenue_recognition_year_month(
        search_params.revenue_recognition_year_month
    )
    
    return SettlementSearchParams(
        revenue_recognition_year_month=validated_year_month
    )


def is_valid_vendor_id(vendor_id: any) -> bool:
    """판매자 ID 유효성 검사 (불린 반환)"""
    try:
        validate_vendor_id(vendor_id)
        return True
    except ValueError:
        return False


def is_valid_year_month(year_month: any) -> bool:
    """매출인식월 유효성 검사 (불린 반환)"""
    try:
        validate_revenue_recognition_year_month(year_month)
        return True
    except ValueError:
        return False