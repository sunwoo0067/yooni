#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객센터 문의 관리 클라이언트
고객센터 문의 조회, 답변, 확인 기능
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
    CallCenterInquirySearchParams, CallCenterInquiryListResponse, CallCenterInquiry,
    CallCenterInquiryReplyRequest, CallCenterInquiryConfirmRequest
)
from .constants import (
    CALL_CENTER_INQUIRIES_API_PATH, CALL_CENTER_INQUIRY_DETAIL_API_PATH,
    CALL_CENTER_INQUIRY_REPLY_API_PATH, CALL_CENTER_INQUIRY_CONFIRM_API_PATH,
    PARTNER_COUNSELING_STATUS, ERROR_MESSAGES,
    DEFAULT_TIMEOUT_SECONDS
)
from .validators import (
    validate_cc_inquiry_search_params, validate_cc_reply_request, validate_confirm_by
)
from .utils import generate_inquiry_date_range_for_recent_days


class CallCenterClient(BaseCoupangClient):
    """쿠팡 고객센터 문의 관리 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        고객센터 문의 관리 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        """
        super().__init__(access_key, secret_key, vendor_id)
        
        # 상위 클래스에서 인증 및 설정이 처리됨
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "고객센터 문의 관리 API"
    
    def get_call_center_inquiries(self, search_params: CallCenterInquirySearchParams) -> Dict[str, Any]:
        """
        고객센터 문의 목록 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 고객센터 문의 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 검색 파라미터
        """
        # 검색 파라미터 검증
        validate_cc_inquiry_search_params(search_params)
        
        # API 경로 생성
        api_path = CALL_CENTER_INQUIRIES_API_PATH.format(search_params.vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = search_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
        try:
            # API 호출
            response = self.execute_api_request(
                "GET", 
                api_path_with_params, 
                {},
                timeout=DEFAULT_TIMEOUT_SECONDS
            )
            
            # 구조화된 응답 생성
            inquiry_response = CallCenterInquiryListResponse.from_dict(response)
            
            # 요약 통계 계산
            summary_stats = inquiry_response.get_summary_stats()
            
            return self.handle_api_response(
                response,
                success_message="고객센터 문의 목록 조회 성공",
                vendor_id=search_params.vendor_id,
                counseling_status=PARTNER_COUNSELING_STATUS.get(
                    search_params.partner_counseling_status, 
                    search_params.partner_counseling_status
                ),
                date_range=f"{search_params.inquiry_start_at} ~ {search_params.inquiry_end_at}" 
                          if search_params.inquiry_start_at else "전체기간",
                vendor_item_id=search_params.vendor_item_id,
                order_id=search_params.order_id,
                total_count=summary_stats["total_count"],
                summary_stats=summary_stats,
                pagination_info=summary_stats.get("pagination_info")
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객센터 문의 목록 조회 API 호출")
    
    def get_call_center_inquiry_detail(self, inquiry_id: int) -> Dict[str, Any]:
        """
        고객센터 문의 단건 조회
        
        Args:
            inquiry_id: 문의 ID
            
        Returns:
            Dict[str, Any]: 고객센터 문의 상세 정보
        """
        if not inquiry_id or inquiry_id <= 0:
            return error_handler.handle_validation_error("올바른 문의 ID를 입력해주세요.")
        
        # API 경로 생성
        api_path = CALL_CENTER_INQUIRY_DETAIL_API_PATH.format(inquiry_id)
        
        try:
            # API 호출
            response = self.execute_api_request(
                "GET", 
                api_path, 
                {},
                timeout=DEFAULT_TIMEOUT_SECONDS
            )
            
            # 구조화된 응답 생성
            inquiry_data = response.get("data", {})
            inquiry = CallCenterInquiry.from_dict(inquiry_data)
            
            return self.handle_api_response(
                response,
                success_message="고객센터 문의 상세 조회 성공",
                inquiry_id=inquiry_id,
                inquiry_summary=inquiry.get_summary(),
                reply_count=len(inquiry.replies),
                has_pending_answer=inquiry.has_pending_answer()
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객센터 문의 상세 조회 API 호출")
    
    def reply_to_call_center_inquiry(self, inquiry_id: int, vendor_id: str, 
                                   content: str, reply_by: str, 
                                   parent_answer_id: int) -> Dict[str, Any]:
        """
        고객센터 문의에 답변하기
        
        Args:
            inquiry_id: 문의 ID
            vendor_id: 판매자 ID
            content: 답변 내용 (2~1000자)
            reply_by: 응답자 WING ID
            parent_answer_id: 부모 이관글 ID
            
        Returns:
            Dict[str, Any]: 답변 처리 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 답변 요청 객체 생성
        reply_request = CallCenterInquiryReplyRequest(
            vendor_id=vendor_id,
            inquiry_id=inquiry_id,
            content=content,
            reply_by=reply_by,
            parent_answer_id=parent_answer_id
        )
        
        # 파라미터 검증
        validate_cc_reply_request(reply_request)
        
        # API 경로 생성
        api_path = CALL_CENTER_INQUIRY_REPLY_API_PATH.format(vendor_id, inquiry_id)
        
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
            
            return self.handle_api_response(
                response,
                success_message="고객센터 문의 답변 완료",
                inquiry_id=inquiry_id,
                vendor_id=vendor_id,
                reply_by=reply_by,
                parent_answer_id=parent_answer_id,
                content_length=len(content)
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객센터 문의 답변 API 호출")
    
    def confirm_call_center_inquiry(self, inquiry_id: int, vendor_id: str, 
                                  confirm_by: str) -> Dict[str, Any]:
        """
        고객센터 문의 확인 처리 (TRANSFER 상태 → 확인완료)
        
        Args:
            inquiry_id: 문의 ID
            vendor_id: 판매자 ID
            confirm_by: 확인자 WING ID
            
        Returns:
            Dict[str, Any]: 확인 처리 결과
        """
        # 확인자 ID 검증
        validated_confirm_by = validate_confirm_by(confirm_by)
        
        # 확인 요청 객체 생성
        confirm_request = CallCenterInquiryConfirmRequest(
            confirm_by=validated_confirm_by
        )
        
        # API 경로 생성
        api_path = CALL_CENTER_INQUIRY_CONFIRM_API_PATH.format(vendor_id, inquiry_id)
        
        # 요청 데이터 생성
        request_data = confirm_request.to_json_data()
        
        try:
            # API 호출 (POST)
            response = self.execute_api_request(
                "POST",
                api_path,
                request_data,
                timeout=DEFAULT_TIMEOUT_SECONDS
            )
            
            return self.handle_api_response(
                response,
                success_message="고객센터 문의 확인 완료",
                inquiry_id=inquiry_id,
                vendor_id=vendor_id,
                confirm_by=validated_confirm_by
            )
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "고객센터 문의 확인 API 호출")
    
    def get_call_center_inquiries_by_date(self, vendor_id: str, days: int = 1,
                                        counseling_status: str = "NONE", 
                                        page_size: int = 10) -> Dict[str, Any]:
        """
        최근 N일간 고객센터 문의 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 일수 (1~7일, 기본값: 1일)
            counseling_status: 상담 상태 (기본값: NONE - 전체)
            page_size: 페이지 크기 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 고객센터 문의 목록 조회 결과
        """
        if days < 1 or days > 7:
            return error_handler.handle_validation_error("조회 기간은 1~7일 사이여야 합니다.")
        
        # 날짜 범위 생성
        inquiry_start_at, inquiry_end_at = generate_inquiry_date_range_for_recent_days(days)
        
        # 검색 파라미터 생성
        search_params = CallCenterInquirySearchParams(
            vendor_id=vendor_id,
            partner_counseling_status=counseling_status,
            inquiry_start_at=inquiry_start_at,
            inquiry_end_at=inquiry_end_at,
            page_size=page_size
        )
        
        return self.get_call_center_inquiries(search_params)
    
    def get_pending_call_center_inquiries(self, vendor_id: str, days: int = 7,
                                        page_size: int = 20) -> Dict[str, Any]:
        """
        답변 대기 중인 고객센터 문의 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 기간 (일수)
            page_size: 페이지 크기
            
        Returns:
            Dict[str, Any]: 답변 대기 중인 고객센터 문의 목록
        """
        # 미답변 상태로 조회
        result = self.get_call_center_inquiries_by_date(
            vendor_id, days, counseling_status="NO_ANSWER", page_size=page_size
        )
        
        if result.get("success"):
            # 메시지 업데이트
            total_count = result.get("total_count", 0)
            result["message"] = f"답변 대기 중인 고객센터 문의 조회 성공 ({total_count}건)"
        
        return result
    
    def get_transfer_call_center_inquiries(self, vendor_id: str, days: int = 7,
                                         page_size: int = 20) -> Dict[str, Any]:
        """
        확인 대기 중인 고객센터 문의 조회 (TRANSFER 상태)
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 기간 (일수)
            page_size: 페이지 크기
            
        Returns:
            Dict[str, Any]: 확인 대기 중인 고객센터 문의 목록
        """
        # 이관 상태로 조회
        result = self.get_call_center_inquiries_by_date(
            vendor_id, days, counseling_status="TRANSFER", page_size=page_size
        )
        
        if result.get("success"):
            # 메시지 업데이트
            total_count = result.get("total_count", 0)
            result["message"] = f"확인 대기 중인 고객센터 문의 조회 성공 ({total_count}건)"
        
        return result
    
    def get_call_center_inquiries_by_item(self, vendor_id: str, vendor_item_id: str,
                                        counseling_status: str = "NONE",
                                        page_size: int = 10) -> Dict[str, Any]:
        """
        특정 상품의 고객센터 문의 조회
        
        Args:
            vendor_id: 판매자 ID
            vendor_item_id: 옵션 ID
            counseling_status: 상담 상태 (기본값: NONE - 전체)
            page_size: 페이지 크기 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 해당 상품의 고객센터 문의 목록
        """
        # 검색 파라미터 생성 (옵션 ID 기반)
        search_params = CallCenterInquirySearchParams(
            vendor_id=vendor_id,
            partner_counseling_status=counseling_status,
            vendor_item_id=vendor_item_id,
            page_size=page_size
        )
        
        result = self.get_call_center_inquiries(search_params)
        
        if result.get("success"):
            # 메시지 업데이트
            total_count = result.get("total_count", 0)
            result["message"] = f"상품별 고객센터 문의 조회 성공 ({total_count}건)"
            result["vendor_item_id"] = vendor_item_id
        
        return result