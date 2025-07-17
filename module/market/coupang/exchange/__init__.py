"""
쿠팡 파트너스 API - 교환요청 관리 모듈
(.env 기반 환경설정 자동 로드)
"""

from .exchange_client import ExchangeClient
from .models import (
    ExchangeRequestSearchParams, 
    ExchangeRequest, 
    ExchangeRequestListResponse,
    ExchangeItem,
    ExchangeAddress,
    DeliveryInvoiceGroup,
    CollectInformation,
    ReturnDelivery,
    ExchangeReceiveConfirmationRequest,
    ExchangeRejectionRequest,
    ExchangeInvoiceUploadRequest,
    ExchangeProcessingResponse
)
from .constants import (
    EXCHANGE_STATUS, 
    EXCHANGE_ORDER_DELIVERY_STATUS, 
    EXCHANGE_REFER_TYPE,
    EXCHANGE_FAULT_TYPE,
    EXCHANGE_CREATED_BY_TYPE,
    EXCHANGE_REJECT_CODES,
    VOC_CODES
)
from .validators import (
    validate_exchange_id, validate_vendor_id, validate_exchange_search_params,
    validate_exchange_reject_code, validate_delivery_code, validate_invoice_number
)
from .utils import (
    generate_exchange_date_range_for_recent_days, 
    generate_exchange_date_range_for_today,
    analyze_exchange_patterns, validate_environment_setup,
    get_default_vendor_id, create_sample_exchange_search_params
)

# 편의 함수 추가
def create_exchange_client(access_key=None, secret_key=None, vendor_id=None):
    """
    교환 클라이언트 생성 편의 함수
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        ExchangeClient: 초기화된 교환 클라이언트
    """
    return ExchangeClient(access_key, secret_key, vendor_id)

def get_today_exchanges_quick(vendor_id=None, days=1):
    """
    오늘 교환 요청 빠른 조회
    
    Args:
        vendor_id: 판매자 ID (None이면 .env에서 읽음)
        days: 조회 기간 (기본값: 1일)
        
    Returns:
        Dict[str, Any]: 교환 요청 조회 결과
    """
    client = create_exchange_client()
    if vendor_id is None:
        vendor_id = get_default_vendor_id()
    
    created_at_from, created_at_to = generate_exchange_date_range_for_recent_days(days)
    params = ExchangeRequestSearchParams(
        vendor_id=vendor_id,
        created_at_from=created_at_from,
        created_at_to=created_at_to
    )
    return client.get_exchange_requests(params)

__all__ = [
    # 편의 함수
    'create_exchange_client',
    'get_today_exchanges_quick',
    
    # 클라이언트
    'ExchangeClient',
    
    # 데이터 모델
    'ExchangeRequestSearchParams',
    'ExchangeRequest',
    'ExchangeRequestListResponse', 
    'ExchangeItem',
    'ExchangeAddress',
    'DeliveryInvoiceGroup',
    'CollectInformation',
    'ReturnDelivery',
    'ExchangeReceiveConfirmationRequest',
    'ExchangeRejectionRequest',
    'ExchangeInvoiceUploadRequest', 
    'ExchangeProcessingResponse',
    
    # 상수
    'EXCHANGE_STATUS',
    'EXCHANGE_ORDER_DELIVERY_STATUS',
    'EXCHANGE_REFER_TYPE', 
    'EXCHANGE_FAULT_TYPE',
    'EXCHANGE_CREATED_BY_TYPE',
    'EXCHANGE_REJECT_CODES',
    'VOC_CODES',
    
    # 검증 함수
    'validate_exchange_id',
    'validate_vendor_id',
    'validate_exchange_search_params',
    'validate_exchange_reject_code',
    'validate_delivery_code',
    'validate_invoice_number',
    
    # 유틸리티 함수  
    'generate_exchange_date_range_for_recent_days',
    'generate_exchange_date_range_for_today',
    'analyze_exchange_patterns',
    'validate_environment_setup',
    'get_default_vendor_id',
    'create_sample_exchange_search_params'
]