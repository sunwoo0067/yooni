#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관리 클라이언트
발주서 목록 조회 등 주문 관리 기능
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, List

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from auth.coupang_auth import CoupangAuth
from .models import (
    OrderSheetSearchParams, OrderSheetListResponse, OrderSheetTimeFrameParams, 
    OrderSheetDetailResponse, OrderSheetByOrderIdResponse, OrderSheetHistoryResponse,
    OrderProcessingRequest, InvoiceUploadRequest, StopShippingRequest,
    AlreadyShippedRequest, OrderCancelRequest, CompleteDeliveryRequest, OrderProcessingResponse
)
from .constants import (
    BASE_URL, ORDER_SHEETS_API_PATH, ORDER_SHEET_DETAIL_API_PATH, ORDER_SHEET_BY_ORDER_ID_API_PATH,
    ORDER_SHEET_HISTORY_API_PATH, ORDER_PROCESSING_API_PATH, INVOICE_UPLOAD_API_PATH,
    STOP_SHIPPING_API_PATH, ALREADY_SHIPPED_API_PATH, ORDER_CANCEL_API_PATH, COMPLETE_DELIVERY_API_PATH,
    PROCESSING_AVAILABLE_STATUS, INVOICE_UPLOAD_AVAILABLE_STATUS, STOP_SHIPPING_AVAILABLE_STATUS,
    ALREADY_SHIPPED_AVAILABLE_STATUS, COMPLETE_DELIVERY_AVAILABLE_STATUS
)
from .validators import (
    validate_search_params, validate_shipment_box_id, validate_vendor_id, validate_order_id,
    validate_invoice_number, validate_delivery_company_code, validate_vendor_item_id, 
    validate_reason, validate_order_status_for_processing
)
from .utils import handle_api_success, handle_api_error, handle_exception_error


class OrderClient:
    """쿠팡 주문 관리 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, vendor_id: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 환경변수에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 환경변수에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 환경변수에서 읽음)
        """
        self.BASE_URL = BASE_URL
        
        try:
            self.auth = CoupangAuth(access_key, secret_key, vendor_id)
        except ValueError as e:
            print(f"⚠️  인증 초기화 오류: {e}")
            print("   환경변수 COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, COUPANG_VENDOR_ID를 설정해주세요.")
            raise
    
    def get_order_sheets(self, search_params: OrderSheetSearchParams) -> Dict[str, Any]:
        """
        발주서 목록 조회 (일단위 페이징)
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 발주서 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 검색 파라미터
        """
        # 검색 파라미터 검증
        validate_search_params(search_params)
        
        # API 경로 생성
        api_path = ORDER_SHEETS_API_PATH.format(search_params.vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = search_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
        try:
            # API 호출
            response = self._make_request("GET", api_path_with_params, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                order_sheet_response = OrderSheetListResponse.from_dict(response)
                
                return handle_api_success(
                    response,
                    default_message="발주서 목록 조회 성공",
                    vendor_id=search_params.vendor_id,
                    search_params=search_params.to_dict(),
                    total_count=order_sheet_response.get_total_count(),
                    has_next_page=order_sheet_response.has_next_page(),
                    status_summary=order_sheet_response.get_status_summary()
                )
            else:
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "발주서 목록 조회 API 호출")
    
    def get_order_sheets_all_pages(self, search_params: OrderSheetSearchParams) -> Dict[str, Any]:
        """
        발주서 목록 전체 페이지 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 전체 발주서 목록 조회 결과
        """
        all_order_sheets = []
        current_params = search_params
        page_count = 0
        
        try:
            while True:
                page_count += 1
                print(f"📄 {page_count}페이지 조회 중...")
                
                # 현재 페이지 조회
                result = self.get_order_sheets(current_params)
                
                if not result.get("success"):
                    return result  # 오류 발생 시 즉시 반환
                
                # 데이터 추가
                page_data = result.get("data", [])
                all_order_sheets.extend(page_data)
                
                print(f"   ✅ {len(page_data)}개 발주서 조회됨")
                
                # 다음 페이지 토큰 확인
                next_token = result.get("next_token")
                if not next_token:
                    break  # 마지막 페이지
                
                # 다음 페이지 파라미터 설정
                current_params.next_token = next_token
            
            print(f"🎉 전체 조회 완료: {len(all_order_sheets)}개 발주서, {page_count}페이지")
            
            # 전체 결과 응답 생성
            from .utils import calculate_order_summary
            summary = calculate_order_summary(all_order_sheets)
            
            return handle_api_success(
                {"data": all_order_sheets, "nextToken": None},
                default_message=f"전체 발주서 목록 조회 성공 ({page_count}페이지)",
                vendor_id=search_params.vendor_id,
                search_params=search_params.to_dict(),
                total_count=len(all_order_sheets),
                page_count=page_count,
                has_next_page=False,
                summary=summary
            )
            
        except Exception as e:
            return handle_exception_error(e, "전체 발주서 목록 조회")
    
    def get_order_sheets_by_status(self, vendor_id: str, created_at_from: str, 
                                  created_at_to: str, status: str, 
                                  max_per_page: Optional[int] = None) -> Dict[str, Any]:
        """
        특정 상태의 발주서 목록 조회 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일시
            created_at_to: 검색 종료일시  
            status: 발주서 상태
            max_per_page: 페이지당 최대 조회 수
            
        Returns:
            Dict[str, Any]: 발주서 목록 조회 결과
        """
        search_params = OrderSheetSearchParams(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status=status,
            max_per_page=max_per_page
        )
        
        return self.get_order_sheets_all_pages(search_params)
    
    def get_order_sheets_timeframe(self, search_params: OrderSheetSearchParams) -> Dict[str, Any]:
        """
        발주서 목록 조회 (분단위 전체) - searchType=timeFrame 사용
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 발주서 목록 조회 결과
        """
        # searchType을 timeFrame으로 설정
        search_params.search_type = "timeFrame"
        
        return self.get_order_sheets(search_params)
    
    def get_order_sheets_by_timeframe(self, timeframe_params: OrderSheetTimeFrameParams) -> Dict[str, Any]:
        """
        발주서 목록 조회 (분단위 전체 - 24시간 이내 전용)
        
        Args:
            timeframe_params: 분단위 전체 조회 파라미터 (24시간 이내)
            
        Returns:
            Dict[str, Any]: 발주서 목록 조회 결과
            
        Example:
            # 2024-01-01 오전 9시부터 오후 6시까지의 발주서 조회
            timeframe_params = OrderSheetTimeFrameParams(
                vendor_id="A12345678",
                created_at_from="2024-01-01T09:00",
                created_at_to="2024-01-01T18:00",
                status="ACCEPT"
            )
            result = client.get_order_sheets_by_timeframe(timeframe_params)
        """
        # OrderSheetTimeFrameParams에서 이미 24시간 검증이 완료됨
        order_params = timeframe_params.to_order_sheet_search_params()
        
        try:
            # API 호출
            response = self._make_request("GET", 
                                        f"{ORDER_SHEETS_API_PATH.format(timeframe_params.vendor_id)}?{timeframe_params.to_query_params()}", 
                                        {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                order_sheet_response = OrderSheetListResponse.from_dict(response)
                
                return handle_api_success(
                    response,
                    default_message="분단위 전체 발주서 목록 조회 성공",
                    vendor_id=timeframe_params.vendor_id,
                    search_params=timeframe_params.to_dict(),
                    total_count=order_sheet_response.get_total_count(),
                    has_next_page=order_sheet_response.has_next_page(),
                    status_summary=order_sheet_response.get_status_summary(),
                    time_range=f"{timeframe_params.created_at_from} ~ {timeframe_params.created_at_to}",
                    search_type="timeFrame"
                )
            else:
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "분단위 전체 발주서 목록 조회 API 호출")
    
    def _make_request(self, method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """API 요청 실행"""
        # 요청 URL 생성
        url = f"{self.BASE_URL}{path}"
        
        # 요청 데이터를 JSON으로 변환
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 쿼리 파라미터 추출 (GET 요청인 경우)
        query_params = None
        if '?' in path:
            path_without_query = path.split('?')[0]
            query_string = path.split('?')[1]
            query_params = dict(urllib.parse.parse_qsl(query_string))
        else:
            path_without_query = path
        
        # 인증 헤더 생성
        headers = self.auth.generate_authorization_header(method, path_without_query, query_params)
        
        # HTTP 요청 생성
        request = urllib.request.Request(url, data=json_data, headers=headers)
        request.get_method = lambda: method
        
        try:
            # SSL 컨텍스트 생성 (보안 강화)
            ssl_context = ssl.create_default_context()
            
            # API 요청 실행
            with urllib.request.urlopen(request, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            # HTTP 오류 처리
            error_response = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_response)
                return error_data
            except json.JSONDecodeError:
                return {
                    "code": e.code,
                    "message": f"HTTP {e.code} 오류: {error_response}",
                    "data": None
                }
        except Exception as e:
            # 기타 오류 처리
            return {
                "code": 500,
                "message": f"요청 실행 오류: {str(e)}",
                "data": None
            }
    
    def get_order_summary_by_date_range(self, vendor_id: str, created_at_from: str, 
                                       created_at_to: str) -> Dict[str, Any]:
        """
        날짜 범위별 발주서 요약 정보 조회
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일시
            created_at_to: 검색 종료일시
            
        Returns:
            Dict[str, Any]: 발주서 요약 정보
        """
        from .constants import ORDER_STATUS
        from .utils import calculate_order_summary
        
        summary_by_status = {}
        total_summary = {
            "total_orders": 0,
            "total_amount": 0,
            "total_shipping_fee": 0,
            "status_summary": {},
            "delivery_company_summary": {}
        }
        
        # 각 상태별로 조회
        for status in ORDER_STATUS.keys():
            try:
                result = self.get_order_sheets_by_status(
                    vendor_id, created_at_from, created_at_to, status
                )
                
                if result.get("success"):
                    order_sheets = result.get("data", [])
                    status_summary = calculate_order_summary(order_sheets)
                    summary_by_status[status] = status_summary
                    
                    # 전체 요약에 추가
                    total_summary["total_orders"] += status_summary["total_orders"]
                    total_summary["total_amount"] += status_summary["total_amount"]
                    total_summary["total_shipping_fee"] += status_summary["total_shipping_fee"]
                    
                    # 상태별 집계
                    for s, count in status_summary["status_summary"].items():
                        total_summary["status_summary"][s] = total_summary["status_summary"].get(s, 0) + count
                    
                    # 택배사별 집계
                    for company, count in status_summary["delivery_company_summary"].items():
                        total_summary["delivery_company_summary"][company] = total_summary["delivery_company_summary"].get(company, 0) + count
                        
            except Exception as e:
                print(f"⚠️  {status} 상태 조회 중 오류: {e}")
                continue
        
        return {
            "success": True,
            "data": {
                "vendor_id": vendor_id,
                "date_range": {
                    "from": created_at_from,
                    "to": created_at_to
                },
                "total_summary": total_summary,
                "summary_by_status": summary_by_status
            },
            "message": f"날짜 범위별 발주서 요약 조회 성공 ({created_at_from} ~ {created_at_to})"
        }
    
    def get_order_sheet_detail(self, vendor_id: str, shipment_box_id) -> Dict[str, Any]:
        """
        발주서 단건 조회 (shipmentBoxId 기반)
        
        Args:
            vendor_id: 판매자 ID
            shipment_box_id: 배송번호(묶음배송번호)
            
        Returns:
            Dict[str, Any]: 발주서 단건 조회 결과
            
        Raises:
            ValueError: 잘못된 파라미터
            
        Important:
            - 결제완료 상태에서 고객이 배송지를 변경할 수 있으므로 상품준비중 처리 이후 반드시 배송지 정보 확인 필요
            - 출고 전 "sellerProductName + sellerProductItemName"과 "vendorItemName" 정보 일치 확인 필수
        """
        # 파라미터 검증
        validate_vendor_id(vendor_id)
        
        validated_shipment_box_id = validate_shipment_box_id(shipment_box_id)
        
        # API 경로 생성
        api_path = ORDER_SHEET_DETAIL_API_PATH.format(vendor_id, validated_shipment_box_id)
        
        try:
            # API 호출
            response = self._make_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                order_detail_response = OrderSheetDetailResponse.from_dict(response)
                
                # 배송지 변경 확인 정보
                receiver_info = order_detail_response.get_receiver_info()
                
                # 상품명 검증 정보
                product_validation_info = order_detail_response.get_product_name_validation_info()
                has_mismatch = order_detail_response.has_product_name_mismatch()
                
                # 배송 요약 정보
                shipping_summary = order_detail_response.get_shipping_summary()
                
                return handle_api_success(
                    response,
                    default_message="발주서 단건 조회 성공",
                    vendor_id=vendor_id,
                    shipment_box_id=validated_shipment_box_id,
                    receiver_info=receiver_info,
                    product_validation_info=product_validation_info,
                    has_product_name_mismatch=has_mismatch,
                    shipping_summary=shipping_summary,
                    warnings=self._generate_detail_warnings(order_detail_response.order_sheet, has_mismatch)
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "취소 또는 반품" in error_message:
                        return handle_api_error(response, "해당 주문이 취소 또는 반품되었습니다. 반품/취소 요청 목록 조회 API를 통해 확인하세요.")
                
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "발주서 단건 조회 API 호출")
    
    def _generate_detail_warnings(self, order_sheet, has_product_name_mismatch: bool) -> List[str]:
        """발주서 단건 조회 시 주의사항 생성"""
        warnings = []
        
        # 배송지 변경 가능 상태 확인
        if order_sheet.status in ["ACCEPT", "INSTRUCT"]:
            warnings.append("🚨 배송지 변경 가능 상태입니다. 상품준비중 처리 이후 배송지 정보 재확인 필요!")
        
        # 상품명 불일치 확인
        if has_product_name_mismatch:
            warnings.append("⚠️  상품명 불일치 발견! 출고 보류 후 온라인 문의 접수 필요!")
            warnings.append("   → '상품 정보가 잘못 노출되고 있습니다' > '네' 선택하여 접수")
        
        # 출고 전 확인사항
        if order_sheet.status in ["INSTRUCT", "DEPARTURE"]:
            warnings.append("📋 출고 전 필수 확인사항:")
            warnings.append("   1. sellerProductName + sellerProductItemName ≟ vendorItemName")
            warnings.append("   2. 구성, 수량, 용량 정보 일치 여부")
            warnings.append("   3. 수취인 배송지 정보 최신 여부")
        
        return warnings
    
    def get_order_sheet_with_validation(self, vendor_id: str, shipment_box_id) -> Dict[str, Any]:
        """
        발주서 단건 조회 + 자동 검증 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            shipment_box_id: 배송번호(묶음배송번호)
            
        Returns:
            Dict[str, Any]: 발주서 조회 결과 + 검증 정보
        """
        result = self.get_order_sheet_detail(vendor_id, shipment_box_id)
        
        if not result.get("success"):
            return result
        
        # 자동 검증 결과 추가
        validation_result = {
            "address_change_warning": False,
            "product_mismatch_warning": False,
            "shipping_ready": True,
            "validation_summary": []
        }
        
        # 배송지 변경 경고
        order_data = result.get("data", {})
        status = order_data.get("status", "")
        if status in ["ACCEPT", "INSTRUCT"]:
            validation_result["address_change_warning"] = True
            validation_result["validation_summary"].append("배송지 변경 가능 상태")
        
        # 상품명 불일치 경고
        if result.get("has_product_name_mismatch", False):
            validation_result["product_mismatch_warning"] = True
            validation_result["shipping_ready"] = False
            validation_result["validation_summary"].append("상품명 불일치 발견 - 출고 보류 필요")
        
        # 검증 결과 추가
        result["validation_result"] = validation_result
        
        return result
    
    def get_order_sheet_history(self, vendor_id: str, shipment_box_id) -> Dict[str, Any]:
        """
        배송상태 변경 히스토리 조회
        
        Args:
            vendor_id: 판매자 ID
            shipment_box_id: 배송번호(묶음배송번호)
            
        Returns:
            Dict[str, Any]: 배송상태 변경 히스토리 조회 결과
            
        Raises:
            ValueError: 잘못된 파라미터
            
        Important:
            - 배송상태가 변경될 때마다 히스토리에 기록됨
            - 최신 상태부터 과거 순으로 정렬됨
            - 택배사 송장번호가 등록된 경우 배송추적 가능
        """
        # 파라미터 검증
        validate_vendor_id(vendor_id)
        validated_shipment_box_id = validate_shipment_box_id(shipment_box_id)
        
        # API 경로 생성
        api_path = ORDER_SHEET_HISTORY_API_PATH.format(vendor_id, validated_shipment_box_id)
        
        try:
            # API 호출
            response = self._make_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                history_response = OrderSheetHistoryResponse.from_dict(response)
                
                # 배송추적 가능 여부
                has_tracking = history_response.has_delivery_tracking()
                
                # 최신 상태 정보
                latest_status = history_response.get_latest_status()
                
                return handle_api_success(
                    response,
                    default_message="배송상태 변경 히스토리 조회 성공",
                    vendor_id=vendor_id,
                    shipment_box_id=validated_shipment_box_id,
                    current_status=history_response.current_status,
                    delivery_company_name=history_response.delivery_company_name,
                    invoice_number=history_response.invoice_number,
                    has_delivery_tracking=has_tracking,
                    history_count=history_response.get_status_changes_count(),
                    latest_status=latest_status.to_dict() if latest_status else None,
                    history=history_response.to_dict()["history"]
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "취소 또는 반품" in error_message:
                        return handle_api_error(response, "해당 주문이 취소 또는 반품되었습니다. 반품/취소 요청 목록 조회 API를 통해 확인하세요.")
                
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "배송상태 변경 히스토리 조회 API 호출")
    
    def get_order_sheets_by_order_id(self, vendor_id: str, order_id) -> Dict[str, Any]:
        """
        발주서 주문번호별 조회 (orderId 기반)
        
        Args:
            vendor_id: 판매자 ID
            order_id: 주문번호
            
        Returns:
            Dict[str, Any]: 발주서 목록 조회 결과 (동일 orderId의 모든 shipmentBoxId)
            
        Raises:
            ValueError: 잘못된 파라미터
            
        Important:
            - 하나의 orderId에 여러 shipmentBoxId가 존재할 수 있음 (분리배송)
            - 결제완료 상태에서 고객이 배송지를 변경할 수 있으므로 상품준비중 처리 이후 반드시 배송지 정보 확인 필요
            - 출고 전 "sellerProductName + sellerProductItemName"과 "vendorItemName" 정보 일치 확인 필수
        """
        # 파라미터 검증
        validate_vendor_id(vendor_id)
        validated_order_id = validate_order_id(order_id)
        
        # API 경로 생성
        api_path = ORDER_SHEET_BY_ORDER_ID_API_PATH.format(vendor_id, validated_order_id)
        
        try:
            # API 호출
            response = self._make_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                order_by_id_response = OrderSheetByOrderIdResponse.from_dict(response)
                
                # 수취인 정보 요약 (첫 번째 발주서 기준)
                receiver_info = order_by_id_response.get_receiver_info_summary()
                
                # 상품명 검증 요약 (모든 발주서)
                product_validation_summary = order_by_id_response.get_product_name_validation_summary()
                has_mismatch = order_by_id_response.has_product_name_mismatch()
                
                # 배송 요약 정보 (모든 발주서)
                shipping_summaries = order_by_id_response.get_shipping_summary()
                
                # 분리배송 여부
                is_split = order_by_id_response.is_split_shipping()
                
                # 상태별 요약
                status_summary = order_by_id_response.get_status_summary()
                
                # 배송번호 목록
                shipment_box_ids = order_by_id_response.get_shipment_box_ids()
                
                return handle_api_success(
                    response,
                    default_message=f"주문번호별 발주서 조회 성공 ({len(order_by_id_response.order_sheets)}개 발주서)",
                    vendor_id=vendor_id,
                    order_id=validated_order_id,
                    total_count=order_by_id_response.get_total_count(),
                    shipment_box_ids=shipment_box_ids,
                    is_split_shipping=is_split,
                    receiver_info=receiver_info,
                    product_validation_summary=product_validation_summary,
                    has_product_name_mismatch=has_mismatch,
                    shipping_summaries=shipping_summaries,
                    status_summary=status_summary,
                    total_order_amount=order_by_id_response.get_total_order_amount(),
                    warnings=self._generate_order_id_warnings(order_by_id_response, has_mismatch)
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "취소 또는 반품" in error_message:
                        return handle_api_error(response, "해당 주문이 취소 또는 반품되었습니다. 반품/취소 요청 목록 조회 API를 통해 확인하세요.")
                    elif "유효하지 않은 주문번호" in error_message:
                        return handle_api_error(response, "유효하지 않은 주문번호입니다. 정상적인 주문번호인지 확인하세요.")
                    elif "다른 판매자의 주문" in error_message:
                        return handle_api_error(response, "다른 판매자의 주문을 조회할 수 없습니다. 판매자 ID를 확인하세요.")
                
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "발주서 주문번호별 조회 API 호출")
    
    def _generate_order_id_warnings(self, order_response: OrderSheetByOrderIdResponse, has_product_name_mismatch: bool) -> List[str]:
        """발주서 주문번호별 조회 시 주의사항 생성"""
        warnings = []
        
        # 분리배송 확인
        if order_response.is_split_shipping():
            warnings.append(f"📦 분리배송 주문입니다. ({len(order_response.order_sheets)}개 발주서)")
            warnings.append("   → 각 배송번호별로 개별 관리 필요")
        
        # 배송지 변경 가능 상태 확인
        accept_or_instruct_count = 0
        for sheet in order_response.order_sheets:
            if sheet.status in ["ACCEPT", "INSTRUCT"]:
                accept_or_instruct_count += 1
        
        if accept_or_instruct_count > 0:
            warnings.append(f"🚨 배송지 변경 가능 상태 발주서: {accept_or_instruct_count}개")
            warnings.append("   → 상품준비중 처리 이후 배송지 정보 재확인 필요!")
        
        # 상품명 불일치 확인
        if has_product_name_mismatch:
            validation_summary = order_response.get_product_name_validation_summary()
            mismatch_count = validation_summary.get("mismatchCount", 0)
            total_items = validation_summary.get("totalItems", 0)
            mismatch_rate = validation_summary.get("mismatchRate", 0)
            
            warnings.append(f"⚠️  상품명 불일치 발견! ({mismatch_count}/{total_items}개, {mismatch_rate}%)")
            warnings.append("   → 출고 보류 후 온라인 문의 접수 필요!")
            warnings.append("   → '상품 정보가 잘못 노출되고 있습니다' > '네' 선택하여 접수")
        
        # 출고 전 확인사항
        instruct_or_departure_count = 0
        for sheet in order_response.order_sheets:
            if sheet.status in ["INSTRUCT", "DEPARTURE"]:
                instruct_or_departure_count += 1
        
        if instruct_or_departure_count > 0:
            warnings.append(f"📋 출고 전 확인 필요 발주서: {instruct_or_departure_count}개")
            warnings.append("   1. sellerProductName + sellerProductItemName ≟ vendorItemName")
            warnings.append("   2. 구성, 수량, 용량 정보 일치 여부")
            warnings.append("   3. 수취인 배송지 정보 최신 여부")
        
        return warnings
    
    def get_order_sheets_by_order_id_with_validation(self, vendor_id: str, order_id) -> Dict[str, Any]:
        """
        발주서 주문번호별 조회 + 자동 검증 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            order_id: 주문번호
            
        Returns:
            Dict[str, Any]: 발주서 조회 결과 + 검증 정보
        """
        result = self.get_order_sheets_by_order_id(vendor_id, order_id)
        
        if not result.get("success"):
            return result
        
        # 자동 검증 결과 추가
        validation_result = {
            "address_change_warning": False,
            "product_mismatch_warning": False,
            "split_shipping_warning": False,
            "shipping_ready": True,
            "validation_summary": []
        }
        
        # 분리배송 경고
        is_split = result.get("is_split_shipping", False)
        if is_split:
            validation_result["split_shipping_warning"] = True
            validation_result["validation_summary"].append("분리배송 주문")
        
        # 배송지 변경 경고 (각 발주서별 확인)
        order_data = result.get("data", [])
        accept_instruct_count = 0
        for sheet in order_data:
            if sheet.get("status", "") in ["ACCEPT", "INSTRUCT"]:
                accept_instruct_count += 1
        
        if accept_instruct_count > 0:
            validation_result["address_change_warning"] = True
            validation_result["validation_summary"].append(f"배송지 변경 가능 상태 ({accept_instruct_count}개)")
        
        # 상품명 불일치 경고
        if result.get("has_product_name_mismatch", False):
            validation_result["product_mismatch_warning"] = True
            validation_result["shipping_ready"] = False
            product_summary = result.get("product_validation_summary", {})
            mismatch_count = product_summary.get("mismatchCount", 0)
            total_items = product_summary.get("totalItems", 0)
            validation_result["validation_summary"].append(f"상품명 불일치 ({mismatch_count}/{total_items}개) - 출고 보류 필요")
        
        # 검증 결과 추가
        result["validation_result"] = validation_result
        
        return result
    
    def process_order_to_instruct(self, vendor_id: str, shipment_box_id) -> Dict[str, Any]:
        """
        상품준비중 처리
        """
        # 파라미터 검증
        validate_vendor_id(vendor_id)
        validated_shipment_box_id = validate_shipment_box_id(shipment_box_id)
        
        # API 경로 생성
        api_path = ORDER_PROCESSING_API_PATH.format(vendor_id, validated_shipment_box_id)
        
        try:
            # API 호출
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == 200:
                processing_response = OrderProcessingResponse.from_dict(response)
                
                return handle_api_success(
                    response,
                    default_message="상품준비중 처리 완료",
                    vendor_id=vendor_id,
                    shipment_box_id=validated_shipment_box_id,
                    processing_result=processing_response.to_dict(),
                    new_status="INSTRUCT"
                )
            else:
                return handle_api_error(response)
                
        except Exception as e:
            return handle_exception_error(e, "상품준비중 처리 API 호출")

