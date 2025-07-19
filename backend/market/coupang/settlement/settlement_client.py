#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 클라이언트
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_client import BaseCoupangClient
from common.errors import error_handler

from .models import SettlementSearchParams, SettlementHistoryResponse, SettlementSummaryReport
from .constants import SETTLEMENT_HISTORIES_API_PATH, DEFAULT_TIMEOUT_SECONDS
from .validators import validate_settlement_search_params
from .utils import (
    generate_current_year_month,
    generate_previous_year_month,
    calculate_settlement_summary
)


class SettlementClient(BaseCoupangClient):
    """쿠팡 지급내역 조회 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        지급내역 조회 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        """
        super().__init__(access_key, secret_key, vendor_id)
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "지급내역 조회 API"
    
    def get_settlement_histories(self, search_params: SettlementSearchParams) -> Dict[str, Any]:
        """
        지급내역 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 지급내역 조회 결과
        """
        # 검색 파라미터 검증
        validated_params = validate_settlement_search_params(search_params)
        
        # API 경로 생성
        query_params = validated_params.to_query_params()
        api_path_with_params = f"{SETTLEMENT_HISTORIES_API_PATH}?{query_params}"
        
        try:
            # API 호출
            response = self.execute_api_request(
                "GET", 
                api_path_with_params, 
                {},
                timeout=DEFAULT_TIMEOUT_SECONDS
            )
            
            # 구조화된 응답 생성
            settlement_response = SettlementHistoryResponse.from_dict(response, validated_params)
            summary_stats = settlement_response.get_summary_stats()
            
            return self.handle_api_response(
                response,
                success_message="지급내역 조회 성공",
                revenue_recognition_year_month=validated_params.revenue_recognition_year_month,
                total_settlements=summary_stats["total_settlements"],
                total_sale=summary_stats["total_sale"],
                total_final_amount=summary_stats["total_final_amount"],
                completed_count=summary_stats["completed_count"],
                pending_count=summary_stats["pending_count"],
                summary_stats=summary_stats
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "지급내역 조회 API 호출")
    
    def get_settlement_history(self, year_month: str) -> Dict[str, Any]:
        """
        특정 년월의 지급내역 조회 (편의 메서드)
        
        Args:
            year_month: 매출인식월 (YYYY-MM)
            
        Returns:
            Dict[str, Any]: 지급내역 조회 결과
        """
        search_params = SettlementSearchParams(
            revenue_recognition_year_month=year_month
        )
        
        return self.get_settlement_histories(search_params)
    
    def get_current_month_settlements(self) -> Dict[str, Any]:
        """
        이번 달 지급내역 조회
        
        Returns:
            Dict[str, Any]: 이번 달 지급내역 조회 결과
        """
        current_year_month = generate_current_year_month()
        result = self.get_settlement_history(current_year_month)
        
        if result.get("success"):
            result["message"] = f"{current_year_month} 지급내역 조회 성공"
            result["period_type"] = "current_month"
        
        return result
    
    def get_previous_month_settlements(self, months_ago: int = 1) -> Dict[str, Any]:
        """
        N개월 전 지급내역 조회
        
        Args:
            months_ago: 몇 개월 전 (기본값: 1개월)
            
        Returns:
            Dict[str, Any]: 지급내역 조회 결과
        """
        target_year_month = generate_previous_year_month(months_ago)
        result = self.get_settlement_history(target_year_month)
        
        if result.get("success"):
            result["message"] = f"{target_year_month} 지급내역 조회 성공"
            result["period_type"] = "previous_month"
            result["months_ago"] = months_ago
        
        return result
    
    def get_settlements_by_range(self, start_year_month: str, 
                                end_year_month: str) -> Dict[str, Any]:
        """
        여러 월의 지급내역 조회
        
        Args:
            start_year_month: 시작 년월 (YYYY-MM)
            end_year_month: 종료 년월 (YYYY-MM)
            
        Returns:
            Dict[str, Any]: 기간별 지급내역 조회 결과
        """
        all_settlements = []
        current_year_month = start_year_month
        
        # 년월 파싱
        start_year, start_month = map(int, start_year_month.split('-'))
        end_year, end_month = map(int, end_year_month.split('-'))
        
        year, month = start_year, start_month
        
        while (year < end_year) or (year == end_year and month <= end_month):
            year_month_str = f"{year:04d}-{month:02d}"
            
            # 개별 월 조회
            result = self.get_settlement_history(year_month_str)
            
            if result.get("success") and "data" in result:
                settlements = result["data"].get("settlements", [])
                all_settlements.extend(settlements)
            
            # 다음 월로 이동
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        # 전체 요약 계산
        total_summary = calculate_settlement_summary(all_settlements)
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK", "data": {"settlements": all_settlements}},
            default_message=f"기간별 지급내역 조회 성공 ({start_year_month} ~ {end_year_month})",
            period_range=f"{start_year_month} ~ {end_year_month}",
            total_months=len(set(s.get("revenue_recognition_year_month", "") for s in all_settlements)),
            total_settlements=len(all_settlements),
            summary_stats=total_summary
        )
    
    def get_completed_settlements(self, year_month: str) -> Dict[str, Any]:
        """
        완료된 지급내역만 조회
        
        Args:
            year_month: 매출인식월 (YYYY-MM)
            
        Returns:
            Dict[str, Any]: 완료된 지급내역 조회 결과
        """
        result = self.get_settlement_history(year_month)
        
        if result.get("success") and "data" in result:
            settlements = result["data"].get("settlements", [])
            completed_settlements = [s for s in settlements if s.get("status") == "DONE"]
            
            # 완료된 지급내역만으로 다시 구성
            result["data"]["settlements"] = completed_settlements
            result["data"]["summary_stats"] = calculate_settlement_summary(completed_settlements)
            result["message"] = f"{year_month} 완료된 지급내역 조회 성공 ({len(completed_settlements)}건)"
            result["filter_type"] = "completed_only"
        
        return result
    
    def get_pending_settlements(self, year_month: str) -> Dict[str, Any]:
        """
        예정된 지급내역만 조회
        
        Args:
            year_month: 매출인식월 (YYYY-MM)
            
        Returns:
            Dict[str, Any]: 예정된 지급내역 조회 결과
        """
        result = self.get_settlement_history(year_month)
        
        if result.get("success") and "data" in result:
            settlements = result["data"].get("settlements", [])
            pending_settlements = [s for s in settlements if s.get("status") == "SUBJECT"]
            
            # 예정된 지급내역만으로 다시 구성
            result["data"]["settlements"] = pending_settlements
            result["data"]["summary_stats"] = calculate_settlement_summary(pending_settlements)
            result["message"] = f"{year_month} 예정된 지급내역 조회 성공 ({len(pending_settlements)}건)"
            result["filter_type"] = "pending_only"
        
        return result
    
    def create_settlement_summary_report(self, analysis_months: int = 3) -> Dict[str, Any]:
        """
        지급내역 요약 보고서 생성
        
        Args:
            analysis_months: 분석할 개월 수 (기본값: 3개월)
            
        Returns:
            Dict[str, Any]: 지급내역 요약 보고서
        """
        if analysis_months < 1 or analysis_months > 12:
            return error_handler.handle_validation_error("분석 개월 수는 1~12개월 사이여야 합니다.")
        
        # 분석할 기간의 년월 생성
        current_year_month = generate_current_year_month()
        end_year_month = generate_previous_year_month(1)  # 지난 달까지
        start_year_month = generate_previous_year_month(analysis_months)
        
        # 기간별 지급내역 조회
        result = self.get_settlements_by_range(start_year_month, end_year_month)
        
        if not result.get("success"):
            return result
        
        settlements = result.get("data", {}).get("settlements", [])
        
        if not settlements:
            return error_handler.handle_api_success(
                {"code": 200, "message": "OK"},
                default_message="분석할 지급내역 데이터가 없습니다.",
                analysis_period=f"{start_year_month} ~ {end_year_month}",
                analysis_months=analysis_months,
                total_settlements=0
            )
        
        # 요약 보고서 생성
        summary_report = SettlementSummaryReport.create_from_settlement_data(
            settlements, analysis_months
        )
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK"},
            default_message="지급내역 요약 보고서 생성 완료",
            analysis_period=f"{start_year_month} ~ {end_year_month}",
            analysis_months=analysis_months,
            total_settlements=len(settlements),
            summary_report=summary_report.__dict__
        )