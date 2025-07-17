#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 관리 클라이언트
상품 등록, 수정, 승인 등 상품 관리 기능
"""

from typing import Dict, Any, Optional
from .base_client import BaseClient
from .models import ProductRequest, ProductPartialUpdateRequest
from .constants import (
    PRODUCT_API_PATH, PRODUCT_GET_API_PATH, PRODUCT_PARTIAL_API_PATH,
    PRODUCT_PARTIAL_UPDATE_API_PATH, PRODUCT_APPROVAL_API_PATH,
    CATEGORY_RECOMMENDATION_API_PATH
)
from .validators import (
    validate_product_request, validate_product_update_request,
    validate_product_partial_update_request
)


class ProductManagementClient(BaseClient):
    """상품 관리 API 클라이언트"""
    
    def create_product(self, product_request: ProductRequest) -> Dict[str, Any]:
        """
        상품 등록
        
        Args:
            product_request: 상품 등록 요청 데이터
            
        Returns:
            Dict[str, Any]: 상품 등록 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
        """
        # 요청 데이터 검증
        validate_product_request(product_request)
        
        # API 호출 및 응답 처리
        return self._execute_api_call(
            method="POST",
            api_path=PRODUCT_API_PATH,
            data=product_request.to_dict(),
            operation="상품 등록",
            seller_product_id=lambda r: r.get("data", {}).get("sellerProductId")
        )
    
    def get_product(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 조회 (승인필요)
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 상품 조회 결과
        """
        api_path = PRODUCT_GET_API_PATH.format(seller_product_id)
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path,
            data={},
            operation="상품 조회"
        )
    
    def get_product_partial(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 조회 (승인불필요)
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 상품 조회 결과
        """
        api_path = PRODUCT_PARTIAL_API_PATH.format(seller_product_id)
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path,
            data={},
            operation="상품 조회 (승인불필요)"
        )
    
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
        
        api_path = PRODUCT_GET_API_PATH.format(product_request.seller_product_id)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data=product_request.to_dict(),
            operation="상품 수정"
        )
    
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
        
        api_path = PRODUCT_PARTIAL_UPDATE_API_PATH.format(partial_request.seller_product_id)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data=partial_request.to_dict(),
            operation="상품 부분 수정"
        )
    
    def request_product_approval(self, seller_product_id: int) -> Dict[str, Any]:
        """
        상품 승인 요청
        
        Args:
            seller_product_id: 등록상품ID
            
        Returns:
            Dict[str, Any]: 승인 요청 결과
        """
        api_path = PRODUCT_APPROVAL_API_PATH.format(seller_product_id)
        
        return self._execute_api_call(
            method="POST",
            api_path=api_path,
            data={},
            operation="상품 승인 요청"
        )
    
    def recommend_category(self, product_name: str) -> Dict[str, Any]:
        """
        카테고리 추천
        
        Args:
            product_name: 상품명
            
        Returns:
            Dict[str, Any]: 카테고리 추천 결과
        """
        if not product_name or not product_name.strip():
            raise ValueError("상품명은 필수입니다")
        
        return self._execute_api_call(
            method="POST",
            api_path=CATEGORY_RECOMMENDATION_API_PATH,
            data={"productName": product_name.strip()},
            operation="카테고리 추천",
            product_name=product_name.strip()
        )