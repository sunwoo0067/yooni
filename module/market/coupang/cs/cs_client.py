#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 클라이언트
고객문의 목록 조회 기능
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

from .models import (
    InquirySearchParams, InquiryListResponse, CustomerInquiry,
    InquiryReplyRequest, InquiryReplyResponse
)
from .constants import (
    ONLINE_INQUIRIES_API_PATH, INQUIRY_REPLY_API_PATH, ANSWERED_TYPE, ERROR_MESSAGES,
    EXTENDED_TIMEOUT_HEADER, DEFAULT_TIMEOUT_SECONDS, EXTENDED_TIMEOUT_SECONDS
)
from .validators import validate_inquiry_search_params, validate_timeout_settings, validate_inquiry_reply_request
from .utils import (
    create_inquiry_summary_report, generate_inquiry_date_range_for_recent_days,
    analyze_inquiry_patterns
)


class CSClient(BaseCoupangClient):
    """쿠팡 고객문의(CS) 관리 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        고객문의 관리 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        """
        super().__init__(access_key, secret_key, vendor_id)
        
        # 상위 클래스에서 인증 및 설정이 처리됨
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "고객문의(CS) 관리 API"
    
    def get_customer_inquiries(self, search_params: InquirySearchParams,
                             extended_timeout: bool = False) -> Dict[str, Any]:
        """
        고객문의 목록 조회
        
        Args:
            search_params: 검색 파라미터
            extended_timeout: 확장 타임아웃 사용 여부
            
        Returns:
            Dict[str, Any]: 고객문의 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 검색 파라미터
        """
        # 검색 파라미터 검증
        validate_inquiry_search_params(search_params)
        
        # 타임아웃 설정 확인
        date_range_days = (
            datetime.strptime(search_params.inquiry_end_at, '%Y-%m-%d') - 
            datetime.strptime(search_params.inquiry_start_at, '%Y-%m-%d')
        ).days
        
        timeout_info = validate_timeout_settings(
            search_params.page_size or 10, 
            date_range_days
        )
        
        # API 경로 생성
        api_path = ONLINE_INQUIRIES_API_PATH.format(search_params.vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = search_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
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
            inquiry_response = InquiryListResponse.from_dict(response)
            
            # 요약 통계 계산
            summary_stats = inquiry_response.get_summary_stats()
            
            return self.handle_api_response(
                response,
                success_message="고객문의 목록 조회 성공",
                vendor_id=search_params.vendor_id,
                date_range=f"{search_params.inquiry_start_at} ~ {search_params.inquiry_end_at}",
                answered_type=ANSWERED_TYPE.get(search_params.answered_type, search_params.answered_type),
                total_count=summary_stats["total_count"],
                summary_stats=summary_stats,
                pagination_info=summary_stats.get("pagination_info"),
                timeout_warnings=timeout_info.get("warnings", [])
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객문의 목록 조회 API 호출")
    
    def get_inquiries_by_date_range(self, vendor_id: str, days: int = 1,
                                  answered_type: str = "ALL", 
                                  page_size: int = 10) -> Dict[str, Any]:
        """
        최근 N일간 고객문의 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 일수 (1~7일, 기본값: 1일)
            answered_type: 답변 상태 (기본값: ALL)
            page_size: 페이지 크기 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 고객문의 목록 조회 결과
        """
        if days < 1 or days > 7:
            return error_handler.handle_validation_error("조회 기간은 1~7일 사이여야 합니다.")
        
        # 날짜 범위 생성
        inquiry_start_at, inquiry_end_at = generate_inquiry_date_range_for_recent_days(days)
        
        # 검색 파라미터 생성
        search_params = InquirySearchParams(
            vendor_id=vendor_id,
            answered_type=answered_type,
            inquiry_start_at=inquiry_start_at,
            inquiry_end_at=inquiry_end_at,
            page_size=page_size
        )
        
        return self.get_customer_inquiries(search_params)
    
    def get_today_inquiries(self, vendor_id: str, 
                           answered_type: str = "ALL") -> Dict[str, Any]:
        """
        오늘의 고객문의 목록 조회
        
        Args:
            vendor_id: 판매자 ID  
            answered_type: 답변 상태 (기본값: ALL)
            
        Returns:
            Dict[str, Any]: 오늘의 고객문의 목록
        """
        return self.get_inquiries_by_date_range(vendor_id, days=1, answered_type=answered_type)
    
    def get_unanswered_inquiries(self, vendor_id: str, days: int = 7,
                               page_size: int = 10) -> Dict[str, Any]:
        """
        미답변 고객문의 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 기간 (일수)
            page_size: 페이지 크기
            
        Returns:
            Dict[str, Any]: 미답변 고객문의 목록
        """
        # 미답변 상태로 조회
        result = self.get_inquiries_by_date_range(
            vendor_id, days, answered_type="NOANSWER", page_size=page_size
        )
        
        if result.get("success"):
            # 메시지 업데이트
            total_count = result.get("total_count", 0)
            result["message"] = f"미답변 고객문의 조회 성공 ({total_count}건)"
        
        return result
    
    def get_inquiries_with_pagination(self, search_params: InquirySearchParams,
                                    max_pages: int = 10) -> Dict[str, Any]:
        """
        페이지네이션을 통한 전체 고객문의 조회
        
        Args:
            search_params: 검색 파라미터
            max_pages: 최대 페이지 수 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 전체 고객문의 데이터
        """
        all_inquiries = []
        current_page = 1
        
        while current_page <= max_pages:
            # 페이지 번호 설정
            search_params.page_num = current_page
            
            # API 호출
            result = self.get_customer_inquiries(search_params)
            
            if not result.get("success"):
                return result  # 오류 발생 시 즉시 반환
            
            # 데이터 추가
            if "data" in result and result["data"]:
                page_inquiries = result["data"]
                all_inquiries.extend(page_inquiries)
            
            # 페이지네이션 정보 확인
            pagination_info = result.get("pagination_info", {})
            total_pages = pagination_info.get("total_pages", 0)
            
            if current_page >= total_pages:
                break  # 더 이상 페이지가 없음
            
            current_page += 1
        
        # 전체 데이터로 응답 생성
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK", "data": all_inquiries},
            default_message=f"고객문의 전체 조회 성공 (페이지: {current_page-1}개)",
            vendor_id=search_params.vendor_id,
            total_count=len(all_inquiries),
            page_count=current_page-1
        )
    
    def create_inquiry_analysis_report(self, vendor_id: str, days: int = 7) -> Dict[str, Any]:
        """
        고객문의 분석 보고서 생성
        
        Args:
            vendor_id: 판매자 ID
            days: 분석 기간 (일수)
            
        Returns:
            Dict[str, Any]: 고객문의 분석 보고서
        """
        # 고객문의 데이터 조회 (전체)
        result = self.get_inquiries_by_date_range(vendor_id, days, answered_type="ALL", page_size=50)
        
        if not result.get("success"):
            return result
        
        inquiry_data = result.get("data", [])
        
        if not inquiry_data:
            return error_handler.handle_api_success(
                {"code": 200, "message": "OK"},
                default_message="분석할 고객문의 데이터가 없습니다.",
                analysis_period=f"{days}일",
                total_inquiries=0
            )
        
        # 고객문의 분석
        analysis_result = analyze_inquiry_patterns(inquiry_data)
        
        # 보고서 생성
        report = create_inquiry_summary_report(inquiry_data, analysis_result)
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK"},
            default_message="고객문의 분석 보고서 생성 완료",
            vendor_id=vendor_id,
            analysis_period=f"{days}일",
            total_inquiries=len(inquiry_data),
            analysis_report=report
        )
    
    def reply_to_inquiry(self, inquiry_id: int, vendor_id: str, 
                        content: str, reply_by: str) -> Dict[str, Any]:
        """
        고객문의에 답변하기
        
        Args:
            inquiry_id: 문의 ID
            vendor_id: 판매자 ID
            content: 답변 내용
            reply_by: 응답자 WING ID
            
        Returns:
            Dict[str, Any]: 답변 처리 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 답변 요청 객체 생성
        reply_request = InquiryReplyRequest(
            vendor_id=vendor_id,
            inquiry_id=inquiry_id,
            content=content,
            reply_by=reply_by
        )
        
        # 파라미터 검증
        validate_inquiry_reply_request(reply_request)
        
        # API 경로 생성
        api_path = INQUIRY_REPLY_API_PATH.format(vendor_id, inquiry_id)
        
        # 요청 데이터 생성
        request_data = reply_request.to_json_data()
        
        try:
            # API 호출 (POST)
            response = self.execute_api_request(
                "POST",
                api_path,
                request_data,
                timeout=DEFAULT_TIMEOUT_SECONDS
            )
            
            # 성공 응답 생성
            reply_response = InquiryReplyResponse.from_dict(
                response, inquiry_id, vendor_id, content
            )
            
            return self.handle_api_response(
                response,
                success_message="고객문의 답변 완료",
                inquiry_id=inquiry_id,
                vendor_id=vendor_id,
                reply_by=reply_by,
                content_length=len(content),
                reply_response=reply_response.get_summary()
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객문의 답변 API 호출")
    
    def reply_to_inquiry_simple(self, inquiry_id: int, content: str, 
                               reply_by: str, vendor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        고객문의 간편 답변 (벤더 ID 자동 설정)
        
        Args:
            inquiry_id: 문의 ID
            content: 답변 내용
            reply_by: 응답자 WING ID
            vendor_id: 판매자 ID (None이면 .env에서 읽음)
            
        Returns:
            Dict[str, Any]: 답변 처리 결과
        """
        if vendor_id is None:
            vendor_id = self.vendor_id
        
        return self.reply_to_inquiry(inquiry_id, vendor_id, content, reply_by)
    
    def bulk_reply_to_inquiries(self, reply_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        여러 고객문의에 일괄 답변
        
        Args:
            reply_requests: 답변 요청 리스트
                각 요청: {"inquiry_id": int, "content": str, "reply_by": str, "vendor_id": str (optional)}
                
        Returns:
            Dict[str, Any]: 일괄 답변 처리 결과
        """
        if not reply_requests:
            return error_handler.handle_validation_error("답변할 문의가 없습니다.")
        
        results = []
        success_count = 0
        failure_count = 0
        
        for i, request in enumerate(reply_requests):
            try:
                inquiry_id = request.get("inquiry_id")
                content = request.get("content")
                reply_by = request.get("reply_by")
                vendor_id = request.get("vendor_id", self.vendor_id)
                
                if not all([inquiry_id, content, reply_by, vendor_id]):
                    result = {
                        "index": i,
                        "inquiry_id": inquiry_id,
                        "success": False,
                        "error": "필수 파라미터가 누락되었습니다"
                    }
                    failure_count += 1
                else:
                    # 개별 답변 처리
                    result = self.reply_to_inquiry(inquiry_id, vendor_id, content, reply_by)
                    result["index"] = i
                    result["inquiry_id"] = inquiry_id
                    
                    if result.get("success"):
                        success_count += 1
                    else:
                        failure_count += 1
                
                results.append(result)
                
            except Exception as e:
                result = {
                    "index": i,
                    "inquiry_id": request.get("inquiry_id"),
                    "success": False,
                    "error": str(e)
                }
                results.append(result)
                failure_count += 1
        
        # 전체 결과 반환
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK"},
            default_message="일괄 답변 처리 완료",
            total_requests=len(reply_requests),
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_count / len(reply_requests) * 100,
            results=results
        )