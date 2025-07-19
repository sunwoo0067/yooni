#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 클라이언트
교환요청 목록 조회 기능
"""

import urllib.parse
from typing import Dict, Any, Optional, List

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import BaseCoupangClient, error_handler, config

from .models import (
    ExchangeRequestSearchParams, ExchangeRequestListResponse, ExchangeRequest,
    ExchangeReceiveConfirmationRequest, ExchangeRejectionRequest, 
    ExchangeInvoiceUploadRequest, ExchangeProcessingResponse
)
from .constants import (
    EXCHANGE_REQUESTS_API_PATH, EXCHANGE_RECEIVE_CONFIRMATION_API_PATH,
    EXCHANGE_REJECTION_API_PATH, EXCHANGE_INVOICE_UPLOAD_API_PATH,
    EXCHANGE_STATUS, ERROR_MESSAGES, EXCHANGE_REJECT_CODES
)
from .validators import validate_exchange_search_params
from .utils import (
    create_exchange_summary_report, generate_exchange_date_range_for_recent_days,
    analyze_exchange_patterns
)


class ExchangeClient(BaseCoupangClient):
    """쿠팡 교환요청 관리 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        교환요청 관리 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        """
        super().__init__(access_key, secret_key, vendor_id)
        
        # 환경변수가 제대로 로드되었는지 확인
        if not config.validate_coupang_credentials():
            error_handler.log_error(
                "초기화 실패", 
                "쿠팡 API 인증 정보가 .env 파일에 설정되지 않았습니다."
            )
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "교환요청 관리 API"
    
    def get_exchange_requests(self, search_params: ExchangeRequestSearchParams) -> Dict[str, Any]:
        """
        교환요청 목록 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 교환요청 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 검색 파라미터
        """
        # 검색 파라미터 검증
        validate_exchange_search_params(search_params)
        
        # API 경로 생성
        api_path = EXCHANGE_REQUESTS_API_PATH.format(search_params.vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = search_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
        try:
            # API 호출
            response = self.execute_api_request("GET", api_path_with_params, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                exchange_response = ExchangeRequestListResponse.from_dict(response)
                
                # 요약 통계 계산
                summary_stats = exchange_response.get_summary_stats()
                
                return error_handler.handle_api_success(
                    response,
                    default_message="교환요청 목록 조회 성공",
                    vendor_id=search_params.vendor_id,
                    date_range=f"{search_params.created_at_from} ~ {search_params.created_at_to}",
                    total_count=summary_stats["total_count"],
                    summary_stats=summary_stats,
                    next_token=exchange_response.next_token
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "7day" in error_message:
                        return error_handler.handle_api_error(response, "조회기간이 7일을 초과했습니다. 기간을 줄여서 다시 시도해주세요.")
                    elif "format should be" in error_message:
                        return error_handler.handle_api_error(response, "날짜 형식이 올바르지 않습니다. yyyy-MM-ddTHH:mm:ss 형식으로 입력해주세요.")
                    elif "start time should early" in error_message:
                        return error_handler.handle_api_error(response, "검색 시작일이 종료일보다 늦을 수 없습니다.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "교환요청 목록 조회 API 호출")
    
    def get_exchange_requests_by_date_range(self, vendor_id: str, days: int = 1, 
                                          status: Optional[str] = None) -> Dict[str, Any]:
        """
        최근 N일간 교환요청 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 일수 (1~7일, 기본값: 1일)
            status: 교환 상태 (선택사항)
            
        Returns:
            Dict[str, Any]: 교환요청 목록 조회 결과
        """
        if days < 1 or days > 7:
            return error_handler.handle_validation_error("조회 기간은 1~7일 사이여야 합니다.")
        
        # 날짜 범위 생성
        created_at_from, created_at_to = generate_exchange_date_range_for_recent_days(days)
        
        # 검색 파라미터 생성
        search_params = ExchangeRequestSearchParams(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status=status
        )
        
        return self.get_exchange_requests(search_params)
    
    def get_today_exchange_requests(self, vendor_id: str, 
                                  status: Optional[str] = None) -> Dict[str, Any]:
        """
        오늘의 교환요청 목록 조회
        
        Args:
            vendor_id: 판매자 ID  
            status: 교환 상태 (선택사항)
            
        Returns:
            Dict[str, Any]: 오늘의 교환요청 목록
        """
        return self.get_exchange_requests_by_date_range(vendor_id, days=1, status=status)
    
    def get_exchange_requests_with_pagination(self, search_params: ExchangeRequestSearchParams,
                                            max_pages: int = 10) -> Dict[str, Any]:
        """
        페이징을 통한 전체 교환요청 조회
        
        Args:
            search_params: 검색 파라미터
            max_pages: 최대 페이지 수 (기본값: 10)
            
        Returns:
            Dict[str, Any]: 전체 교환요청 데이터
        """
        all_exchanges = []
        current_page = 1
        next_token = None
        
        while current_page <= max_pages:
            # 페이징 토큰 설정
            if next_token:
                search_params.next_token = next_token
            
            # API 호출
            result = self.get_exchange_requests(search_params)
            
            if not result.get("success"):
                return result  # 오류 발생 시 즉시 반환
            
            # 데이터 추가
            if "data" in result and result["data"]:
                all_exchanges.extend(result["data"])
            
            # 다음 페이지 토큰 확인
            next_token = result.get("next_token")
            if not next_token:
                break  # 더 이상 페이지가 없음
            
            current_page += 1
        
        # 전체 데이터로 응답 생성
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK", "data": all_exchanges},
            default_message=f"교환요청 전체 조회 성공 (페이지: {current_page-1}개)",
            vendor_id=search_params.vendor_id,
            total_count=len(all_exchanges),
            page_count=current_page-1
        )
    
    def create_exchange_analysis_report(self, vendor_id: str, days: int = 7) -> Dict[str, Any]:
        """
        교환요청 분석 보고서 생성
        
        Args:
            vendor_id: 판매자 ID
            days: 분석 기간 (일수)
            
        Returns:
            Dict[str, Any]: 교환요청 분석 보고서
        """
        # 교환요청 데이터 조회
        result = self.get_exchange_requests_by_date_range(vendor_id, days)
        
        if not result.get("success"):
            return result
        
        exchange_data = result.get("data", [])
        
        if not exchange_data:
            return error_handler.handle_api_success(
                {"code": 200, "message": "OK"},
                default_message="분석할 교환요청 데이터가 없습니다.",
                analysis_period=f"{days}일",
                total_exchanges=0
            )
        
        # 교환요청 분석
        analysis_result = analyze_exchange_patterns(exchange_data)
        
        # 보고서 생성
        report = create_exchange_summary_report(exchange_data, analysis_result)
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK"},
            default_message="교환요청 분석 보고서 생성 완료",
            vendor_id=vendor_id,
            analysis_period=f"{days}일",
            total_exchanges=len(exchange_data),
            analysis_report=report
        )
    
    def get_vendor_fault_exchanges(self, vendor_id: str, days: int = 7) -> Dict[str, Any]:
        """
        업체 과실 교환요청 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회 기간 (일수)
            
        Returns:
            Dict[str, Any]: 업체 과실 교환요청 목록
        """
        # 전체 교환요청 조회
        result = self.get_exchange_requests_by_date_range(vendor_id, days)
        
        if not result.get("success"):
            return result
        
        all_exchanges = result.get("data", [])
        
        # 업체 과실 교환요청 필터링
        vendor_fault_exchanges = [
            exchange for exchange in all_exchanges
            if exchange.get("fault_type") == "VENDOR"
        ]
        
        return error_handler.handle_api_success(
            {"code": 200, "message": "OK", "data": vendor_fault_exchanges},
            default_message="업체 과실 교환요청 조회 성공",
            vendor_id=vendor_id,
            total_count=len(vendor_fault_exchanges),
            analysis_period=f"{days}일",
            fault_rate=len(vendor_fault_exchanges) / len(all_exchanges) * 100 if all_exchanges else 0
        )
    
    def confirm_exchange_receive(self, exchange_id: int, vendor_id: str) -> Dict[str, Any]:
        """
        교환요청 입고 확인 처리
        
        Args:
            exchange_id: 교환 접수번호
            vendor_id: 판매자 ID
            
        Returns:
            Dict[str, Any]: 입고 확인 처리 결과
        """
        try:
            # 입력값 검증
            if not isinstance(exchange_id, int) or exchange_id <= 0:
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_EXCHANGE_ID"])
            
            if not vendor_id or not isinstance(vendor_id, str):
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_VENDOR_ID"])
            
            # 요청 객체 생성
            request_data = ExchangeReceiveConfirmationRequest(
                exchange_id=exchange_id,
                vendor_id=vendor_id
            )
            
            # API 경로 생성
            api_path = EXCHANGE_RECEIVE_CONFIRMATION_API_PATH.format(vendor_id, exchange_id)
            
            # API 호출 (PATCH 메서드)
            response = self.execute_api_request("PATCH", api_path, request_data.to_dict())
            
            # 응답 처리
            processing_response = ExchangeProcessingResponse.from_dict(response)
            
            if processing_response.is_success():
                return error_handler.handle_api_success(
                    response,
                    default_message="교환요청 입고 확인 처리 성공",
                    exchange_id=exchange_id,
                    vendor_id=vendor_id,
                    result_code=processing_response.result_code,
                    result_message=processing_response.result_message
                )
            else:
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "교환요청 입고 확인 처리 API 호출")
    
    def reject_exchange_request(self, exchange_id: int, vendor_id: str, 
                              exchange_reject_code: str) -> Dict[str, Any]:
        """
        교환요청 거부 처리
        
        Args:
            exchange_id: 교환 접수번호
            vendor_id: 판매자 ID  
            exchange_reject_code: 교환 거부 코드 (SOLDOUT 또는 WITHDRAW)
            
        Returns:
            Dict[str, Any]: 교환 거부 처리 결과
        """
        try:
            # 입력값 검증
            if not isinstance(exchange_id, int) or exchange_id <= 0:
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_EXCHANGE_ID"])
            
            if not vendor_id or not isinstance(vendor_id, str):
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_VENDOR_ID"])
            
            if exchange_reject_code not in EXCHANGE_REJECT_CODES:
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_REJECT_CODE"])
            
            # 요청 객체 생성
            request_data = ExchangeRejectionRequest(
                exchange_id=exchange_id,
                vendor_id=vendor_id,
                exchange_reject_code=exchange_reject_code
            )
            
            # API 경로 생성
            api_path = EXCHANGE_REJECTION_API_PATH.format(vendor_id, exchange_id)
            
            # API 호출 (PATCH 메서드)
            response = self.execute_api_request("PATCH", api_path, request_data.to_dict())
            
            # 응답 처리
            processing_response = ExchangeProcessingResponse.from_dict(response)
            
            if processing_response.is_success():
                return error_handler.handle_api_success(
                    response,
                    default_message="교환요청 거부 처리 성공",
                    exchange_id=exchange_id,
                    vendor_id=vendor_id,
                    reject_code=exchange_reject_code,
                    reject_message=EXCHANGE_REJECT_CODES[exchange_reject_code],
                    result_code=processing_response.result_code,
                    result_message=processing_response.result_message
                )
            else:
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "교환요청 거부 처리 API 호출")
    
    def upload_exchange_invoice(self, exchange_id: int, vendor_id: str,
                              goods_delivery_code: str, invoice_number: str,
                              shipment_box_id: int) -> Dict[str, Any]:
        """
        교환상품 송장 업로드 처리
        
        Args:
            exchange_id: 교환 접수번호
            vendor_id: 판매자 ID
            goods_delivery_code: 택배사 코드
            invoice_number: 운송장번호
            shipment_box_id: 배송번호
            
        Returns:
            Dict[str, Any]: 송장 업로드 처리 결과
        """
        try:
            # 입력값 검증
            if not isinstance(exchange_id, int) or exchange_id <= 0:
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_EXCHANGE_ID"])
            
            if not vendor_id or not isinstance(vendor_id, str):
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_VENDOR_ID"])
            
            if not goods_delivery_code or not isinstance(goods_delivery_code, str):
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_DELIVERY_CODE"])
            
            if not invoice_number or not isinstance(invoice_number, str):
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_INVOICE_NUMBER"])
            
            if not isinstance(shipment_box_id, int) or shipment_box_id <= 0:
                return error_handler.handle_validation_error(ERROR_MESSAGES["INVALID_SHIPMENT_BOX_ID"])
            
            # 요청 객체 생성
            request_data = ExchangeInvoiceUploadRequest(
                exchange_id=exchange_id,
                vendor_id=vendor_id,
                goods_delivery_code=goods_delivery_code,
                invoice_number=invoice_number,
                shipment_box_id=shipment_box_id
            )
            
            # API 경로 생성
            api_path = EXCHANGE_INVOICE_UPLOAD_API_PATH.format(vendor_id, exchange_id)
            
            # API 호출 (POST 메서드)
            response = self.execute_api_request("POST", api_path, request_data.to_dict())
            
            # 응답 처리
            processing_response = ExchangeProcessingResponse.from_dict(response)
            
            if processing_response.is_success():
                return error_handler.handle_api_success(
                    response,
                    default_message="교환상품 송장 업로드 성공",
                    exchange_id=exchange_id,
                    vendor_id=vendor_id,
                    delivery_code=goods_delivery_code,
                    invoice_number=invoice_number,
                    shipment_box_id=shipment_box_id,
                    result_code=processing_response.result_code,
                    result_message=processing_response.result_message
                )
            else:
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "교환상품 송장 업로드 API 호출")