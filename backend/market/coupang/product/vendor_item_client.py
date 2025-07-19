#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 벤더아이템 관리 클라이언트
재고, 가격, 판매상태 등 벤더아이템 관리 기능
"""

from typing import Dict, Any
from .base_client import BaseClient
from .constants import (
    VENDOR_ITEM_INVENTORY_API_PATH, VENDOR_ITEM_QUANTITY_UPDATE_API_PATH,
    VENDOR_ITEM_PRICE_UPDATE_API_PATH, VENDOR_ITEM_SALES_RESUME_API_PATH,
    VENDOR_ITEM_SALES_STOP_API_PATH, VENDOR_ITEM_ORIGINAL_PRICE_UPDATE_API_PATH
)
from .validators import validate_vendor_item_id, validate_quantity, validate_price, validate_original_price


class VendorItemClient(BaseClient):
    """벤더아이템 관리 API 클라이언트"""
    
    def get_vendor_item_inventory(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 재고 조회
        
        Args:
            vendor_item_id: 벤더아이템ID
            
        Returns:
            Dict[str, Any]: 재고 조회 결과
        """
        # 벤더아이템ID 검증
        validate_vendor_item_id(vendor_item_id)
        
        api_path = VENDOR_ITEM_INVENTORY_API_PATH.format(vendor_item_id)
        
        return self._execute_api_call(
            method="GET",
            api_path=api_path,
            data={},
            operation="벤더아이템 재고 조회",
            vendor_item_id=vendor_item_id
        )
    
    def update_vendor_item_quantity(self, vendor_item_id: int, quantity: int) -> Dict[str, Any]:
        """
        벤더아이템 재고수량 변경
        
        Args:
            vendor_item_id: 벤더아이템ID
            quantity: 재고수량
            
        Returns:
            Dict[str, Any]: 재고수량 변경 결과
        """
        # 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_quantity(quantity)
        
        api_path = VENDOR_ITEM_QUANTITY_UPDATE_API_PATH.format(vendor_item_id, quantity)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data={},
            operation="벤더아이템 재고수량 변경",
            vendor_item_id=vendor_item_id,
            quantity=quantity
        )
    
    def update_vendor_item_price(self, vendor_item_id: int, price: int, force_sale_price_update: bool = False) -> Dict[str, Any]:
        """
        벤더아이템 가격 변경
        
        Args:
            vendor_item_id: 벤더아이템ID
            price: 판매가
            force_sale_price_update: 강제 가격 변경 여부
            
        Returns:
            Dict[str, Any]: 가격 변경 결과
        """
        # 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_price(price)
        
        # 쿼리 파라미터 포함 API 경로
        force_param = "true" if force_sale_price_update else "false"
        api_path = f"{VENDOR_ITEM_PRICE_UPDATE_API_PATH.format(vendor_item_id, price)}?forceSalePriceUpdate={force_param}"
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data={},
            operation="벤더아이템 가격 변경",
            vendor_item_id=vendor_item_id,
            price=price,
            force_sale_price_update=force_sale_price_update
        )
    
    def resume_vendor_item_sales(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 판매 재개
        
        Args:
            vendor_item_id: 벤더아이템ID
            
        Returns:
            Dict[str, Any]: 판매 재개 결과
        """
        # 벤더아이템ID 검증
        validate_vendor_item_id(vendor_item_id)
        
        api_path = VENDOR_ITEM_SALES_RESUME_API_PATH.format(vendor_item_id)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data={},
            operation="벤더아이템 판매 재개",
            vendor_item_id=vendor_item_id
        )
    
    def stop_vendor_item_sales(self, vendor_item_id: int) -> Dict[str, Any]:
        """
        벤더아이템 판매 중지
        
        Args:
            vendor_item_id: 벤더아이템ID
            
        Returns:
            Dict[str, Any]: 판매 중지 결과
        """
        # 벤더아이템ID 검증
        validate_vendor_item_id(vendor_item_id)
        
        api_path = VENDOR_ITEM_SALES_STOP_API_PATH.format(vendor_item_id)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data={},
            operation="벤더아이템 판매 중지",
            vendor_item_id=vendor_item_id
        )
    
    def update_vendor_item_original_price(self, vendor_item_id: int, original_price: int) -> Dict[str, Any]:
        """
        벤더아이템 할인율 기준가격 변경
        
        Args:
            vendor_item_id: 벤더아이템ID
            original_price: 할인율 기준가격
            
        Returns:
            Dict[str, Any]: 할인율 기준가격 변경 결과
        """
        # 파라미터 검증
        validate_vendor_item_id(vendor_item_id)
        validate_original_price(original_price)
        
        api_path = VENDOR_ITEM_ORIGINAL_PRICE_UPDATE_API_PATH.format(vendor_item_id, original_price)
        
        return self._execute_api_call(
            method="PUT",
            api_path=api_path,
            data={},
            operation="벤더아이템 할인율 기준가격 변경",
            vendor_item_id=vendor_item_id,
            original_price=original_price
        )