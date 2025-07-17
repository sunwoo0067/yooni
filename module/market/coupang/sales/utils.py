#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 모듈 유틸리티 함수
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .constants import DEFAULT_SEARCH_DAYS, DATE_FORMAT
from .models import RevenueSearchParams, RevenueItem


def generate_revenue_date_range_for_recent_days(days: int) -> Tuple[str, str]:
    """최근 N일간 매출 인식일 범위 생성"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    return start_date.strftime(DATE_FORMAT), end_date.strftime(DATE_FORMAT)


def generate_revenue_date_range_for_month(year: Optional[int] = None, 
                                        month: Optional[int] = None) -> Tuple[str, str]:
    """월별 매출 인식일 범위 생성"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    start_date = datetime(year, month, 1).date()
    
    # 다음 달의 첫째 날에서 하루 빼서 이번 달 마지막 날 계산
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    end_date = (next_month - timedelta(days=1)).date()
    
    return start_date.strftime(DATE_FORMAT), end_date.strftime(DATE_FORMAT)


def calculate_revenue_summary(revenue_items: List[RevenueItem]) -> Dict[str, Any]:
    """매출 데이터 요약 계산"""
    if not revenue_items:
        return {
            "total_items": 0,
            "total_settlement": 0,
            "total_service_fee": 0,
            "net_revenue": 0,
            "sale_count": 0,
            "refund_count": 0
        }
    
    total_settlement = sum(item.settlement_amount for item in revenue_items)
    total_service_fee = sum(item.service_fee for item in revenue_items)
    sale_items = [item for item in revenue_items if item.is_sale()]
    refund_items = [item for item in revenue_items if item.is_refund()]
    
    return {
        "total_items": len(revenue_items),
        "total_settlement": total_settlement,
        "total_service_fee": total_service_fee,
        "net_revenue": total_settlement - total_service_fee,
        "sale_count": len(sale_items),
        "refund_count": len(refund_items),
        "sale_amount": sum(item.settlement_amount for item in sale_items),
        "refund_amount": sum(abs(item.settlement_amount) for item in refund_items)
    }


def format_revenue_amount(amount: int) -> str:
    """매출 금액 포맷팅 (천 단위 콤마)"""
    return f"{amount:,}원"


def get_default_vendor_id() -> Optional[str]:
    """기본 벤더 ID 조회 (.env에서)"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from common.config import config
        return config.coupang_vendor_id
    except ImportError:
        return os.getenv('COUPANG_VENDOR_ID')


def validate_environment_setup() -> Dict[str, Any]:
    """환경 설정 검증"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from common.config import config
        
        return {
            "is_valid": config.validate_coupang_credentials(),
            "has_access_key": bool(config.coupang_access_key),
            "has_secret_key": bool(config.coupang_secret_key),
            "has_vendor_id": bool(config.coupang_vendor_id)
        }
    except ImportError:
        return {"is_valid": False, "error": "설정 모듈을 불러올 수 없습니다"}


def create_sample_revenue_search_params(vendor_id: Optional[str] = None,
                                       days: int = DEFAULT_SEARCH_DAYS) -> RevenueSearchParams:
    """샘플 매출 검색 파라미터 생성"""
    if vendor_id is None:
        vendor_id = get_default_vendor_id() or "A01234567"
    
    start_date, end_date = generate_revenue_date_range_for_recent_days(days)
    
    return RevenueSearchParams(
        vendor_id=vendor_id,
        recognition_date_from=start_date,
        recognition_date_to=end_date,
        max_per_page=20
    )