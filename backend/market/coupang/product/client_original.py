#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 등록 클라이언트
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from auth import CoupangAuth
from .models import (
    ProductRequest, ProductSearchParams, ProductPartialUpdateRequest, ProductStatusHistoryParams
)
from .constants import (
    BASE_URL, PRODUCT_API_PATH, PRODUCT_GET_API_PATH, PRODUCT_PARTIAL_API_PATH,
    PRODUCT_PARTIAL_UPDATE_API_PATH, PRODUCT_APPROVAL_API_PATH,
    PRODUCT_INFLOW_STATUS_API_PATH, PRODUCT_TIME_FRAME_API_PATH,
    PRODUCT_STATUS_HISTORY_API_PATH, PRODUCT_BY_EXTERNAL_SKU_API_PATH,
    VENDOR_ITEM_INVENTORY_API_PATH, VENDOR_ITEM_QUANTITY_UPDATE_API_PATH,
    VENDOR_ITEM_PRICE_UPDATE_API_PATH, VENDOR_ITEM_SALES_RESUME_API_PATH,
    VENDOR_ITEM_SALES_STOP_API_PATH, VENDOR_ITEM_ORIGINAL_PRICE_UPDATE_API_PATH,
    VENDOR_ITEM_AUTO_GENERATED_OPT_IN_API_PATH, VENDOR_ITEM_AUTO_GENERATED_OPT_OUT_API_PATH,
    SELLER_AUTO_GENERATED_OPT_IN_API_PATH, SELLER_AUTO_GENERATED_OPT_OUT_API_PATH,
    CATEGORY_RECOMMENDATION_API_PATH
)
from .validators import (
    validate_product_request, validate_product_update_request,
    validate_product_partial_update_request, validate_product_search_params,
    validate_time_frame_params, validate_product_status_history_params,
    validate_external_vendor_sku_code, validate_vendor_item_id,
    validate_quantity, validate_price, validate_original_price,
    calculate_time_range_minutes
)


class ProductClient:
    """쿠팡 상품 등록 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 환경변수에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 환경변수에서 읽음)
        """
        self.BASE_URL = BASE_URL
        self.auth = CoupangAuth(access_key, secret_key)
    
    def create_product(self, product_request: ProductRequest) -> Dict[str, Any]:
        """
        상품 등록
        
        Args:
            product_request: 상품 등록 요청 데이터
            
        Returns:
            Dict[str, Any]: 상품 등록 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 데이터 검증
        validate_product_request(product_request)
        
        # API 경로 및 요청 데이터 준비
        api_path = PRODUCT_API_PATH
        request_data = product_request.to_dict()
        
        try:
            # API 호출
            response = self._make_request("POST", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "seller_product_id": response.get("data", {}).get("sellerProductId"),
                    "data": response.get("data", {}),
                    "message": response.get("message", "상품 등록 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 등록 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_product(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 조회 (승인필요)
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 상품 조회 결과
        """
        api_path = PRODUCT_GET_API_PATH.format(seller_product_id)
        
        try:
            response = self._make_request("GET", api_path, {})
            
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "data": response.get("data", {}),
                    "message": response.get("message", "상품 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_product_partial(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 조회 (승인불필요)
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 상품 조회 결과
        """
        api_path = PRODUCT_PARTIAL_API_PATH.format(seller_product_id)
        
        try:
            response = self._make_request("GET", api_path, {})
            
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "data": response.get("data", {}),
                    "message": response.get("message", "상품 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def update_product(self, product_request: ProductRequest) -> Dict[str, Any]:
        """
        상품 수정 (승인필요)
        
        Args:
            product_request: 상품 수정 요청 데이터
            
        Returns:
            Dict[str, Any]: 상품 수정 결과
        """
        # 요청 데이터 검증
        validate_product_update_request(product_request)
        
        # API 경로 및 요청 데이터 준비
        api_path = PRODUCT_GET_API_PATH.format(product_request.seller_product_id)
        request_data = product_request.to_dict()
        
        try:
            # API 호출
            response = self._make_request("PUT", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "seller_product_id": product_request.seller_product_id,
                    "data": response.get("data", {}),
                    "message": response.get("message", "상품 수정 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 수정 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def update_product_partial(self, partial_request: ProductPartialUpdateRequest) -> Dict[str, Any]:
        """
        상품 부분 수정 (승인불필요)
        
        Args:
            partial_request: 상품 부분 수정 요청 데이터
            
        Returns:
            Dict[str, Any]: 상품 부분 수정 결과
        """
        # 요청 데이터 검증
        validate_product_partial_update_request(partial_request)
        
        # API 경로 및 요청 데이터 준비
        api_path = PRODUCT_PARTIAL_UPDATE_API_PATH.format(partial_request.seller_product_id)
        request_data = partial_request.to_dict()
        
        try:
            # API 호출
            response = self._make_request("PUT", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "seller_product_id": partial_request.seller_product_id,
                    "data": response.get("data", {}),
                    "message": response.get("message", "상품 부분 수정 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 부분 수정 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def request_product_approval(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 승인 요청
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 승인 요청 결과
        """
        api_path = PRODUCT_APPROVAL_API_PATH.format(seller_product_id)
        
        try:
            response = self._make_request("PUT", api_path, {})
            
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "seller_product_id": seller_product_id,
                    "message": response.get("message", "상품 승인 요청 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 승인 요청 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_inflow_status(self) -> Dict[str, Any]:
        """
        상품 등록 현황 조회
        
        Returns:
            Dict[str, Any]: 상품 등록 현황 결과
        """
        api_path = PRODUCT_INFLOW_STATUS_API_PATH
        
        try:
            response = self._make_request("GET", api_path, {})
            
            if response.get("code") == "SUCCESS":
                data = response.get("data", {})
                
                return {
                    "success": True,
                    "vendor_id": data.get("vendorId"),
                    "restricted": data.get("restricted", False),
                    "registered_count": data.get("registeredCount", 0),
                    "permitted_count": data.get("permittedCount"),
                    "data": data,
                    "message": response.get("message", "상품 등록 현황 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 등록 현황 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def list_products(self, search_params: ProductSearchParams) -> Dict[str, Any]:
        """
        상품 목록 페이징 조회
        
        Args:
            search_params: 상품 검색 파라미터
            
        Returns:
            Dict[str, Any]: 상품 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_product_search_params(search_params)
        
        # API 경로 및 쿼리 파라미터 생성
        api_path = PRODUCT_API_PATH
        query_params = search_params.to_query_params()
        
        # 쿼리 스트링 생성
        query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
        full_path = f"{api_path}?{query_string}"
        
        try:
            # API 호출 (GET 메서드, body 없음)
            response = self._make_request("GET", full_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                data = response.get("data", [])
                next_token = response.get("nextToken", "")
                
                return {
                    "success": True,
                    "data": data,
                    "next_token": next_token if next_token else None,
                    "has_next": bool(next_token),
                    "total_count": len(data),
                    "current_page": search_params.next_token or "1",
                    "max_per_page": search_params.max_per_page,
                    "message": response.get("message", "상품 목록 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 목록 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_products_by_time_frame(self, vendor_id: str, created_at_from: str, created_at_to: str) -> Dict[str, Any]:
        """
        상품 목록 구간 조회 (생성일시 기준)
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 생성 시작일시 (yyyy-MM-ddTHH:mm:ss)
            created_at_to: 생성 종료일시 (yyyy-MM-ddTHH:mm:ss)
            
        Returns:
            Dict[str, Any]: 상품 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_time_frame_params(vendor_id, created_at_from, created_at_to)
        
        # API 경로 및 쿼리 파라미터 생성
        api_path = PRODUCT_TIME_FRAME_API_PATH
        query_params = {
            "vendorId": vendor_id,
            "createdAtFrom": created_at_from,
            "createdAtTo": created_at_to
        }
        
        # 쿼리 스트링 생성
        query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
        full_path = f"{api_path}?{query_string}"
        
        try:
            # API 호출 (GET 메서드, body 없음)
            response = self._make_request("GET", full_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                data = response.get("data", [])
                
                return {
                    "success": True,
                    "data": data,
                    "total_count": len(data),
                    "vendor_id": vendor_id,
                    "created_at_from": created_at_from,
                    "created_at_to": created_at_to,
                    "time_range_minutes": calculate_time_range_minutes(created_at_from, created_at_to),
                    "message": response.get("message", "상품 목록 구간 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 목록 구간 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_product_status_history(self, history_params: ProductStatusHistoryParams) -> Dict[str, Any]:
        """
        상품 상태변경이력 조회
        
        Args:
            history_params: 상태변경이력 조회 파라미터
            
        Returns:
            Dict[str, Any]: 상태변경이력 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_product_status_history_params(history_params)
        
        # API 경로 및 쿼리 파라미터 생성
        api_path = PRODUCT_STATUS_HISTORY_API_PATH.format(history_params.seller_product_id)
        query_params = history_params.to_query_params()
        
        # 쿼리 스트링 생성
        if query_params:
            query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
            full_path = f"{api_path}?{query_string}"
        else:
            full_path = api_path
        
        try:
            # API 호출 (GET 메서드, body 없음)
            response = self._make_request("GET", full_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                data = response.get("data", [])
                next_token = response.get("nextToken", "")
                
                return {
                    "success": True,
                    "data": data,
                    "seller_product_id": history_params.seller_product_id,
                    "next_token": next_token if next_token else None,
                    "has_next": bool(next_token),
                    "total_count": len(data),
                    "current_page": history_params.next_token or "1",
                    "max_per_page": history_params.max_per_page,
                    "message": response.get("message", "상품 상태변경이력 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 상태변경이력 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_product_by_external_sku(self, external_vendor_sku_code: str) -> Dict[str, Any]:
        """
        판매자 상품코드로 상품 요약 정보 조회
        
        Args:
            external_vendor_sku_code: 판매자 상품코드 (업체상품코드)
            
        Returns:
            Dict[str, Any]: 상품 요약 정보 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_external_vendor_sku_code(external_vendor_sku_code)
        
        # API 경로 생성
        api_path = PRODUCT_BY_EXTERNAL_SKU_API_PATH.format(external_vendor_sku_code.strip())
        
        try:
            # API 호출 (GET 메서드, body 없음)
            response = self._make_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                data = response.get("data", [])
                
                return {
                    "success": True,
                    "data": data,
                    "external_vendor_sku_code": external_vendor_sku_code,
                    "total_count": len(data),
                    "message": response.get("message", "상품 요약 정보 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"상품 요약 정보 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def get_vendor_item_inventory(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 재고/가격/상태 조회
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            
        Returns:
            Dict[str, Any]: 아이템 재고/가격/상태 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_INVENTORY_API_PATH.format(vendor_item_id)
        
        try:
            # API 호출 (GET 메서드, body 없음)
            response = self._make_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                data = response.get("data", {})
                
                return {
                    "success": True,
                    "data": data,
                    "vendor_item_id": vendor_item_id,
                    "seller_item_id": data.get("sellerItemId"),
                    "amount_in_stock": data.get("amountInStock"),
                    "sale_price": data.get("salePrice"),
                    "on_sale": data.get("onSale"),
                    "message": response.get("message", "벤더아이템 재고/가격/상태 조회 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 재고/가격/상태 조회 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def update_vendor_item_quantity(self, vendor_item_id: int, quantity: int) -> Dict[str, Any]:
        """
        벤더아이템 재고수량 변경
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            quantity: 재고수량
            
        Returns:
            Dict[str, Any]: 재고수량 변경 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_quantity(quantity)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_QUANTITY_UPDATE_API_PATH.format(vendor_item_id, quantity)
        
        try:
            # API 호출 (PUT 메서드, body 없음)
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "quantity": quantity,
                    "message": response.get("message", "재고 변경을 완료했습니다."),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 재고수량 변경 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def update_vendor_item_price(self, vendor_item_id: int, price: int, force_sale_price_update: bool = False) -> Dict[str, Any]:
        """
        벤더아이템 판매가격 변경
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            price: 가격 (최소 10원 단위)
            force_sale_price_update: 가격 변경 비율 제한 여부 (기본값: False)
            
        Returns:
            Dict[str, Any]: 가격 변경 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_price(price)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_PRICE_UPDATE_API_PATH.format(vendor_item_id, price)
        
        # 쿼리 스트링 추가
        if force_sale_price_update:
            api_path += "?forceSalePriceUpdate=true"
        
        try:
            # API 호출 (PUT 메서드, body 없음)
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "price": price,
                    "force_sale_price_update": force_sale_price_update,
                    "message": response.get("message", "가격 변경을 완료했습니다."),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 가격 변경 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def resume_vendor_item_sales(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 판매 재개
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            
        Returns:
            Dict[str, Any]: 판매 재개 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_SALES_RESUME_API_PATH.format(vendor_item_id)
        
        try:
            # API 호출 (PUT 메서드, body 없음)
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "판매가 재개되었습니다."),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 판매 재개 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def stop_vendor_item_sales(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 판매 중지
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            
        Returns:
            Dict[str, Any]: 판매 중지 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_SALES_STOP_API_PATH.format(vendor_item_id)
        
        try:
            # API 호출 (PUT 메서드, body 없음)
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "판매 중지 처리되었습니다."),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 판매 중지 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def update_vendor_item_original_price(self, vendor_item_id: int, original_price: int) -> Dict[str, Any]:
        """
        벤더아이템 할인율 기준가격 변경
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            original_price: 할인율 기준가격 (0원부터 최소 10원 단위)
            
        Returns:
            Dict[str, Any]: 할인율 기준가격 변경 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_original_price(original_price)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_ORIGINAL_PRICE_UPDATE_API_PATH.format(vendor_item_id, original_price)
        
        try:
            # API 호출 (PUT 메서드, body 없음)
            response = self._make_request("PUT", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "original_price": original_price,
                    "message": response.get("message", "할인율 기준가격이 변경되었습니다."),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 할인율 기준가격 변경 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def enable_vendor_item_auto_generated_option(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 자동생성옵션 활성화 (개별 옵션 상품 단위)
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            
        Returns:
            Dict[str, Any]: 자동생성옵션 활성화 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_AUTO_GENERATED_OPT_IN_API_PATH.format(vendor_item_id)
        
        try:
            # API 호출 (POST 메서드, body 없음)
            response = self._make_request("POST", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "자동생성옵션이 활성화되었습니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            elif response.get("code") == "PROCESSING":
                return {
                    "success": True,
                    "processing": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "자동생성옵션 활성화가 처리 중입니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 자동생성옵션 활성화 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def disable_vendor_item_auto_generated_option(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 자동생성옵션 비활성화 (개별 옵션 상품 단위)
        
        Args:
            vendor_item_id: 벤더아이템ID (옵션ID)
            
        Returns:
            Dict[str, Any]: 자동생성옵션 비활성화 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        
        # API 경로 생성
        api_path = VENDOR_ITEM_AUTO_GENERATED_OPT_OUT_API_PATH.format(vendor_item_id)
        
        try:
            # API 호출 (POST 메서드, body 없음)
            response = self._make_request("POST", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "자동생성옵션이 비활성화되었습니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            elif response.get("code") == "PROCESSING":
                return {
                    "success": True,
                    "processing": True,
                    "vendor_item_id": vendor_item_id,
                    "message": response.get("message", "자동생성옵션 비활성화가 처리 중입니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"벤더아이템 자동생성옵션 비활성화 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def enable_seller_auto_generated_option(self) -> Dict[str, Any]:
        """
        판매자 자동생성옵션 활성화 (전체 상품 단위)
        
        Returns:
            Dict[str, Any]: 자동생성옵션 활성화 결과
            
        Raises:
            Exception: API 호출 오류
        """
        # API 경로 생성
        api_path = SELLER_AUTO_GENERATED_OPT_IN_API_PATH
        
        try:
            # API 호출 (POST 메서드, body 없음)
            response = self._make_request("POST", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "message": response.get("message", "전체 상품 자동생성옵션이 활성화되었습니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            elif response.get("code") == "PROCESSING":
                return {
                    "success": True,
                    "processing": True,
                    "message": response.get("message", "전체 상품 자동생성옵션 활성화가 처리 중입니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"판매자 자동생성옵션 활성화 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def disable_seller_auto_generated_option(self) -> Dict[str, Any]:
        """
        판매자 자동생성옵션 비활성화 (전체 상품 단위)
        
        Returns:
            Dict[str, Any]: 자동생성옵션 비활성화 결과
            
        Raises:
            Exception: API 호출 오류
        """
        # API 경로 생성
        api_path = SELLER_AUTO_GENERATED_OPT_OUT_API_PATH
        
        try:
            # API 호출 (POST 메서드, body 없음)
            response = self._make_request("POST", api_path, {})
            
            # 응답 처리
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "message": response.get("message", "전체 상품 자동생성옵션이 비활성화되었습니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            elif response.get("code") == "PROCESSING":
                return {
                    "success": True,
                    "processing": True,
                    "message": response.get("message", "전체 상품 자동생성옵션 비활성화가 처리 중입니다."),
                    "data": response.get("data"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"판매자 자동생성옵션 비활성화 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def recommend_category(self, product_name: str) -> Dict[str, Any]:
        """
        카테고리 추천
        
        Args:
            product_name: 상품명
            
        Returns:
            Dict[str, Any]: 카테고리 추천 결과
        """
        api_path = CATEGORY_RECOMMENDATION_API_PATH
        request_data = {"productName": product_name}
        
        try:
            response = self._make_request("POST", api_path, request_data)
            
            if response.get("code") == "SUCCESS":
                return {
                    "success": True,
                    "data": response.get("data", []),
                    "message": response.get("message", "카테고리 추천 성공"),
                    "originalResponse": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("message", "알 수 없는 오류"),
                    "code": response.get("code"),
                    "originalResponse": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"카테고리 추천 API 호출 실패: {str(e)}",
                "originalResponse": None
            }
    
    def _make_request(self, method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """API 요청 실행"""
        # 요청 URL 생성
        url = f"{self.BASE_URL}{path}"
        
        # 요청 데이터를 JSON으로 변환
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 인증 헤더 생성
        headers = self.auth.generate_headers(method, path, json_data)
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        
        # HTTP 요청 생성
        request = urllib.request.Request(url, data=json_data, headers=headers)
        request.get_method = lambda: method
        
        try:
            # SSL 컨텍스트 생성 (인증서 검증 비활성화)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
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
                    "code": "ERROR",
                    "message": f"HTTP {e.code} 오류: {error_response}",
                    "data": None
                }
        except Exception as e:
            # 기타 오류 처리
            return {
                "code": "ERROR",
                "message": f"요청 실행 오류: {str(e)}",
                "data": None
            }