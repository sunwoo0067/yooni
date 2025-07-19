#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관리 패키지
"""

# 메인 클라이언트 클래스
from .order_client import OrderClient

# 데이터 모델들
from .models import (
    OrderSheetSearchParams,
    OrderSheetTimeFrameParams,
    OrderSheetDetailResponse,
    OrderSheetByOrderIdResponse,
    OrderSheetHistoryResponse,
    DeliveryHistoryItem,
    OrderProcessingRequest,
    InvoiceUploadRequest,
    StopShippingRequest,
    AlreadyShippedRequest,
    OrderCancelRequest,
    CompleteDeliveryRequest,
    OrderProcessingResponse,
    Orderer,
    Receiver,
    OrderItem,
    OrderSheet,
    OverseasShippingInfo
)

# 상수들
from .constants import (
    ORDER_STATUS,
    DELIVERY_CHARGE_TYPES,
    SHIPMENT_TYPES,
    DELIVERY_COMPANIES
)

# 검증 함수들
from .validators import (
    validate_vendor_id,
    validate_date_range,
    validate_order_status,
    validate_search_params,
    validate_shipment_box_id,
    validate_order_id,
    validate_invoice_number,
    validate_delivery_company_code,
    validate_vendor_item_id,
    validate_reason
)

# 공통 유틸리티
from .utils import (
    setup_project_path,
    print_order_header,
    print_order_result,
    validate_environment_variables,
    create_timeframe_params_for_today,
    create_timeframe_params_for_hours
)

__version__ = "1.0.0"
__author__ = "Coupang Order API Client"

# 편의성을 위한 별칭들
Client = OrderClient
SearchParams = OrderSheetSearchParams

# 패키지 정보
# 편의 함수 추가
def create_order_client(access_key=None, secret_key=None, vendor_id=None):
    """
    주문 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        OrderClient: 초기화된 주문 클라이언트
    """
    return OrderClient(access_key, secret_key, vendor_id)

def get_today_orders_quick(vendor_id=None, hours=24):
    """
    오늘 주문 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        hours: 조회 시간 범위 (기본값: 24시간)
        
    Returns:
        Dict[str, Any]: 주문 조회 결과
    """
    client = create_order_client()
    if vendor_id is None:
        from ..common.config import config
        vendor_id = config.coupang_vendor_id
    
    params = create_timeframe_params_for_hours(hours)
    return client.get_order_sheet_details_with_timeframe(vendor_id, params)

__all__ = [
    # 메인 클라이언트
    'OrderClient', 'Client',
    
    # 편의 함수
    'create_order_client',
    'get_today_orders_quick',
    
    # 모델 클래스들
    'OrderSheetSearchParams', 'SearchParams',
    'OrderSheetTimeFrameParams',
    'OrderSheetDetailResponse',
    'OrderSheetByOrderIdResponse',
    'OrderSheetHistoryResponse',
    'DeliveryHistoryItem',
    'OrderProcessingRequest',
    'InvoiceUploadRequest',
    'StopShippingRequest',
    'AlreadyShippedRequest',
    'OrderCancelRequest',
    'CompleteDeliveryRequest',
    'OrderProcessingResponse',
    'Orderer',
    'Receiver', 
    'OrderItem',
    'OrderSheet',
    'OverseasShippingInfo',
    
    # 상수들
    'ORDER_STATUS',
    'DELIVERY_CHARGE_TYPES',
    'SHIPMENT_TYPES',
    'DELIVERY_COMPANIES',
    
    # 검증 함수들
    'validate_vendor_id',
    'validate_date_range',
    'validate_order_status',
    'validate_search_params',
    'validate_shipment_box_id',
    'validate_order_id',
    'validate_invoice_number',
    'validate_delivery_company_code',
    'validate_vendor_item_id',
    'validate_reason',
    
    # 유틸리티
    'setup_project_path',
    'print_order_header',
    'print_order_result',
    'validate_environment_variables',
    'create_timeframe_params_for_today',
    'create_timeframe_params_for_hours'
]