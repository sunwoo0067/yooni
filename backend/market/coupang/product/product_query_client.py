#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 조회 클라이언트
상품 검색, 목록 조회, 상태 이력 등 조회 기능
"""

from typing import Dict, Any
from .base_client import BaseClient
from .models import ProductSearchParams, ProductStatusHistoryParams
from .constants import (
    PRODUCT_INFLOW_STATUS_API_PATH, PRODUCT_TIME_FRAME_API_PATH,
    PRODUCT_STATUS_HISTORY_API_PATH, PRODUCT_BY_EXTERNAL_SKU_API_PATH
)
from .validators import (
    validate_product_search_params, validate_time_frame_params,
    validate_product_status_history_params, validate_external_vendor_sku_code
)


class ProductQueryClient(BaseClient):
    """상품 조회 API 클라이언트"""
    
    def get_inflow_status(self) -> Dict[str, Any]:
        """
        등록 상품 유입 현황 조회
        
        Returns:
            Dict[str, Any]: 유입 현황 조회 결과
        """
        return self._execute_api_call(
            method="GET",
            api_path=PRODUCT_INFLOW_STATUS_API_PATH,
            data={},
            operation="등록 상품 유입 현황 조회"
        )
    
    def list_products(self, search_params: ProductSearchParams) -> Dict[str, Any]:
        """
        등록 상품 목록 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 상품 목록 조회 결과
        """
        # 검색 파라미터 검증
        validate_product_search_params(search_params)
        
        # 쿼리 파라미터 생성
        query_params = search_params.to_query_params()
        api_path_with_params = f"{PRODUCT_INFLOW_STATUS_API_PATH}?{query_params}"
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path_with_params,
            data={},
            operation="등록 상품 목록 조회",
            search_params=search_params.to_dict()
        )
    
    def get_products_by_time_frame(self, vendor_id: str, created_at_from: str, created_at_to: str) -> Dict[str, Any]:
        """
        등록일 기준 상품 목록 조회
        
        Args:
            vendor_id: 업체코드
            created_at_from: 조회 시작일 (YYYY-MM-DD)
            created_at_to: 조회 종료일 (YYYY-MM-DD)
            
        Returns:
            Dict[str, Any]: 상품 목록 조회 결과
        """
        # 파라미터 검증
        validate_time_frame_params(vendor_id, created_at_from, created_at_to)
        
        # 쿼리 파라미터 생성
        query_params = f"vendorId={vendor_id}&createdAtFrom={created_at_from}&createdAtTo={created_at_to}"
        api_path_with_params = f"{PRODUCT_TIME_FRAME_API_PATH}?{query_params}"
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path_with_params,
            data={},
            operation="등록일 기준 상품 목록 조회",
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to
        )
    
    def get_product_status_history(self, history_params: ProductStatusHistoryParams) -> Dict[str, Any]:
        """
        상품 상태 변경 이력 조회
        
        Args:
            history_params: 이력 조회 파라미터
            
        Returns:
            Dict[str, Any]: 상태 변경 이력 조회 결과
        """
        # 파라미터 검증
        validate_product_status_history_params(history_params)
        
        api_path = PRODUCT_STATUS_HISTORY_API_PATH.format(history_params.seller_product_id)
        
        # 쿼리 파라미터 생성
        query_params = history_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path_with_params,
            data={},
            operation="상품 상태 변경 이력 조회",
            seller_product_id=history_params.seller_product_id
        )
    
    def get_product_by_external_sku(self, external_vendor_sku_code: str) -> Dict[str, Any]:
        """
        외부 벤더 SKU 코드로 상품 조회
        
        Args:
            external_vendor_sku_code: 외부 벤더 SKU 코드
            
        Returns:
            Dict[str, Any]: 상품 조회 결과
        """
        # SKU 코드 검증
        validate_external_vendor_sku_code(external_vendor_sku_code)
        
        api_path = PRODUCT_BY_EXTERNAL_SKU_API_PATH.format(external_vendor_sku_code)
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path,
            data={},
            operation="외부 벤더 SKU 코드로 상품 조회",
            external_vendor_sku_code=external_vendor_sku_code
        )