#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈 유틸리티 함수
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from .constants import DEFAULT_ANALYSIS_MONTHS, YEAR_MONTH_FORMAT
from .models import SettlementSearchParams, SettlementHistory


def generate_current_year_month() -> str:
    """현재 년월 생성 (YYYY-MM)"""
    return datetime.now().strftime(YEAR_MONTH_FORMAT)


def generate_previous_year_month(months_ago: int = 1) -> str:
    """N개월 전 년월 생성"""
    current_date = datetime.now()
    
    # N개월 전 계산
    target_month = current_date.month - months_ago
    target_year = current_date.year
    
    while target_month <= 0:
        target_month += 12
        target_year -= 1
    
    return f"{target_year:04d}-{target_month:02d}"


def calculate_settlement_summary(settlements: List[SettlementHistory]) -> Dict[str, Any]:
    """지급내역 리스트로부터 요약 통계 계산"""
    if not settlements:
        return {
            "total_settlements": 0,
            "total_sale": 0,
            "total_service_fee": 0,
            "total_settlement_amount": 0,
            "total_final_amount": 0,
            "completed_count": 0,
            "pending_count": 0,
            "avg_service_fee_ratio": 0
        }
    
    total_settlements = len(settlements)
    total_sale = sum(s.total_sale for s in settlements)
    total_service_fee = sum(s.service_fee for s in settlements)
    total_settlement_amount = sum(s.settlement_amount for s in settlements)
    total_final_amount = sum(s.final_amount for s in settlements)
    
    completed_settlements = [s for s in settlements if s.is_settlement_completed()]
    pending_settlements = [s for s in settlements if s.is_settlement_pending()]
    
    avg_service_fee_ratio = (total_service_fee / total_sale * 100) if total_sale > 0 else 0
    
    return {
        "total_settlements": total_settlements,
        "total_sale": total_sale,
        "total_service_fee": total_service_fee,
        "total_settlement_amount": total_settlement_amount,
        "total_final_amount": total_final_amount,
        "completed_count": len(completed_settlements),
        "pending_count": len(pending_settlements),
        "avg_service_fee_ratio": round(avg_service_fee_ratio, 2),
        "net_settlement": total_settlement_amount - total_service_fee
    }


def format_settlement_amount(amount: int, currency: str = "KRW") -> str:
    """지급내역 금액을 포맷팅된 문자열로 변환"""
    if currency == "KRW":
        return f"{amount:,}원"
    else:
        return f"{amount:,} {currency}"


def get_default_vendor_id() -> Optional[str]:
    """기본 판매자 ID 조회 (.env에서)"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from common.config import config
        return config.coupang_vendor_id
    except ImportError:
        return None


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
            "has_vendor_id": bool(config.coupang_vendor_id),
            "vendor_id": config.coupang_vendor_id
        }
    except ImportError:
        return {
            "is_valid": False,
            "error": "설정 모듈을 불러올 수 없습니다",
            "has_access_key": False,
            "has_secret_key": False,
            "has_vendor_id": False,
            "vendor_id": None
        }


def create_sample_settlement_search_params(year_month: Optional[str] = None) -> SettlementSearchParams:
    """샘플 지급내역 검색 파라미터 생성"""
    if year_month is None:
        year_month = generate_previous_year_month(1)  # 지난 달
    
    return SettlementSearchParams(
        revenue_recognition_year_month=year_month
    )