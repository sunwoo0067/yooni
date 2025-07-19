#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 클라이언트
"""

import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional, List

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_client import BaseCoupangClient
from common.errors import error_handler

from .models import RevenueSearchParams, RevenueHistory, RevenueHistoryResponse, RevenueSummaryReport
from .constants import REVENUE_HISTORY_API_PATH, DEFAULT_TIMEOUT_SECONDS, EXTENDED_TIMEOUT_SECONDS
from .validators import validate_revenue_search_params, validate_timeout_settings
from .utils import (
    generate_revenue_date_range_for_recent_days,
    generate_revenue_date_range_for_month,
    calculate_revenue_summary
)


class SalesClient(BaseCoupangClient):
    """쿠팡 매출내역 조회 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        매출내역 조회 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        """
        super().__init__(access_key, secret_key, vendor_id)
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "매출내역 조회 API"
    
    def get_revenue_history(self, search_params: RevenueSearchParams,
                          extended_timeout: bool = False) -> Dict[str, Any]:
        """
        매출내역 조회
        
        Args:
            search_params: 검색 파라미터
            extended_timeout: 확장 타임아웃 사용 여부
            
        Returns:
            Dict[str, Any]: 매출내역 조회 결과
        """
        # 검색 파라미터 검증
        validated_params = validate_revenue_search_params(search_params)
        
        # 타임아웃 설정 확인
        date_range_days = validated_params.get_date_range_days()
        timeout_info = validate_timeout_settings(
            validated_params.max_per_page or 20, 
            date_range_days
        )
        
        # API 경로 생성
        query_params = validated_params.to_query_params()
        api_path_with_params = f"{REVENUE_HISTORY_API_PATH}?{query_params}"
        
        try:
            # 타임아웃 설정
            timeout_seconds = DEFAULT_TIMEOUT_SECONDS
            if extended_timeout or timeout_info["is_risky"]:
                timeout_seconds = EXTENDED_TIMEOUT_SECONDS
            
            # API 호출
            response = self.execute_api_request(
                "GET", 
                api_path_with_params, 
                {},
                timeout=timeout_seconds
            )
            
            # 구조화된 응답 생성
            revenue_history = RevenueHistory.from_dict(response)
            summary_stats = revenue_history.get_summary_stats()
            
            return self.handle_api_response(
                response,
                success_message="매출내역 조회 성공",
                vendor_id=validated_params.vendor_id,
                date_range=f"{validated_params.recognition_date_from} ~ {validated_params.recognition_date_to}",
                period_days=date_range_days,
                total_count=summary_stats["total_items"],
                summary_stats=summary_stats,
                pagination_info=revenue_history.get_pagination_info(),
                timeout_warnings=timeout_info.get("warnings", [])
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "매출내역 조회 API 호출")
    
    def get_recent_revenue_history(self, vendor_id: str, days: int = 7,
                                 max_per_page: int = 20) -> Dict[str, Any]:
        """
        최근 N일간 매출내역 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 일수 (1~31일, 기본값: 7일)
            max_per_page: 페이지당 최대 개수 (기본값: 20)
            
        Returns:
            Dict[str, Any]: 매출내역 조회 결과
        """
        if days < 1 or days > 31:
            return error_handler.handle_validation_error("조회 기간은 1~31일 사이여야 합니다.")
        
        # 날짜 범위 생성
        start_date, end_date = generate_revenue_date_range_for_recent_days(days)
        
        # 검색 파라미터 생성
        search_params = RevenueSearchParams(
            vendor_id=vendor_id,
            recognition_date_from=start_date,
            recognition_date_to=end_date,
            max_per_page=max_per_page
        )
        
        return self.get_revenue_history(search_params)
    
    def get_monthly_revenue_history(self, vendor_id: str, 
                                  year: Optional[int] = None,
                                  month: Optional[int] = None) -> Dict[str, Any]:
        """
        월별 매출내역 조회
        
        Args:
            vendor_id: 판매자 ID
            year: 연도 (None이면 현재 년도)
            month: 월 (None이면 현재 월)
            
        Returns:
            Dict[str, Any]: 월별 매출내역 조회 결과
        """
        # 날짜 범위 생성
        start_date, end_date = generate_revenue_date_range_for_month(year, month)
        
        # 검색 파라미터 생성
        search_params = RevenueSearchParams(
            vendor_id=vendor_id,
            recognition_date_from=start_date,
            recognition_date_to=end_date,
            max_per_page=50  # 월별 조회는 더 큰 페이지 크기 사용
        )
        
        result = self.get_revenue_history(search_params, extended_timeout=True)
        
        if result.get("success"):
            # 메시지 업데이트
            year_month = f"{year or datetime.now().year}년 {month or datetime.now().month}월"
            result["message"] = f"{year_month} 매출내역 조회 성공"
            result["year_month"] = year_month
        
        return result
    
    def get_revenue_with_pagination(self, search_params: RevenueSearchParams,
                                  max_pages: int = 10) -> Dict[str, Any]:
        """
        페이지네이션을 통한 전체 매출내역 조회
        
        Args:
            search_params: 검색 파라미터
            max_pages: 최대 페이지 수 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 전체 매출내역 데이터
        """
        all_items = []
        current_page = 1
        next_token = None
        
        while current_page <= max_pages:
            # 토큰 설정
            search_params.token = next_token
            
            # API 호출
            result = self.get_revenue_history(search_params)
            
            if not result.get("success"):
                return result  # 오류 발생 시 즉시 반환
            
            # 데이터 추가
            if "data" in result and result["data"]:
                page_items = result["data"].get("items", [])
                all_items.extend(page_items)
            
            # 페이지네이션 정보 확인
            pagination_info = result.get("pagination_info", {})
            has_next = pagination_info.get("has_next", False)
            next_token = pagination_info.get("next_token")
            
            if not has_next or not next_token:
                break  # 더 이상 페이지가 없음
            
            current_page += 1
        
        # 전체 데이터로 응답 생성
        total_summary = calculate_revenue_summary(all_items)
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK", "data": {"items": all_items}},
            default_message=f"매출내역 전체 조회 성공 (페이지: {current_page}개)",
            vendor_id=search_params.vendor_id,
            total_count=len(all_items),
            page_count=current_page,
            summary_stats=total_summary
        )
    
    def create_revenue_summary_report(self, vendor_id: str, days: int = 30) -> Dict[str, Any]:
        """
        매출 요약 보고서 생성
        
        Args:
            vendor_id: 판매자 ID
            days: 분석 기간 (일수)
            
        Returns:
            Dict[str, Any]: 매출 요약 보고서
        """
        # 매출 데이터 조회
        result = self.get_recent_revenue_history(vendor_id, days, max_per_page=100)
        
        if not result.get("success"):
            return result
        
        revenue_items = result.get("data", {}).get("items", [])
        
        if not revenue_items:
            return error_handler.handle_api_success(
                {"code": 200, "message": "OK"},
                default_message="분석할 매출 데이터가 없습니다.",
                analysis_period=f"{days}일",
                total_items=0
            )
        
        # 검색 파라미터 재생성 (보고서용)
        start_date, end_date = generate_revenue_date_range_for_recent_days(days)
        search_params = RevenueSearchParams(
            vendor_id=vendor_id,
            recognition_date_from=start_date,
            recognition_date_to=end_date
        )
        
        # 요약 보고서 생성
        summary_report = RevenueSummaryReport.create_from_revenue_data(
            revenue_items, search_params
        )
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK"},
            default_message="매출 요약 보고서 생성 완료",
            vendor_id=vendor_id,
            analysis_period=f"{days}일",
            total_items=len(revenue_items),
            summary_report=summary_report.__dict__
        )