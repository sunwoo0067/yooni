#!/usr/bin/env python3
"""
쿠팡 파트너스 API 통합 모듈
"""

# 공통 모듈
from .common.base_client import BaseCoupangClient
from .common.config import config
from .common.errors import error_handler, CoupangAPIError, CoupangAuthError, CoupangNetworkError

# 인증 모듈
from .auth import CoupangAuth

# 핵심 API 클라이언트들
from .cs import CSClient, CallCenterClient
from .sales import SalesClient
from .settlement import SettlementClient
from .order import OrderClient
from .product import ProductClient
from .returns import ReturnClient
from .exchange import ExchangeClient

# 기존 레거시 모듈들
from .coupang_client import CoupangClient
from .category import (
    CoupangCategoryClient, 
    CoupangOptionValidator, 
    CoupangCategoryRecommendationClient, 
    CoupangCategoryManager, 
    CoupangExcelCategoryParser
)
from .ShippingCenters import ShippingCenterClient
from .ReturnCenters import ReturnCenterClient

# 편의 함수들
from .cs import create_cs_client, get_today_inquiries_quick, get_unanswered_inquiries_quick
from .sales import create_sales_client, get_recent_revenue_quick
from .settlement import create_settlement_client, get_current_month_settlement_quick
from .order import create_order_client, get_today_orders_quick
from .product import create_product_client
from .returns import create_return_client, get_today_returns_quick
from .exchange import create_exchange_client, get_today_exchanges_quick

# 멀티 계정 지원
from .common.multi_account_config import (
    MultiAccountConfig, 
    CoupangAccount,
    get_account,
    list_account_names,
    get_default_account_name
)
from .common.multi_client_factory import (
    MultiClientFactory,
    create_client_for_account,
    create_unified_client_for_account,
    execute_on_all_accounts,
    get_multi_account_status
)

__all__ = [
    # 공통 모듈
    'BaseCoupangClient',
    'config',
    'error_handler',
    'CoupangAPIError',
    'CoupangAuthError', 
    'CoupangNetworkError',
    
    # 인증
    'CoupangAuth',
    
    # 핵심 API 클라이언트들
    'CSClient',
    'CallCenterClient',
    'SalesClient',
    'SettlementClient', 
    'OrderClient',
    'ProductClient',
    'ReturnClient',
    'ExchangeClient',
    
    # 레거시 클라이언트들
    'CoupangClient',
    'CoupangCategoryClient',
    'CoupangOptionValidator',
    'CoupangCategoryRecommendationClient',
    'CoupangCategoryManager',
    'CoupangExcelCategoryParser',
    'ShippingCenterClient',
    'ReturnCenterClient',
    
    # 편의 함수들 - CS
    'create_cs_client',
    'get_today_inquiries_quick',
    'get_unanswered_inquiries_quick',
    
    # 편의 함수들 - Sales
    'create_sales_client',
    'get_recent_revenue_quick',
    
    # 편의 함수들 - Settlement
    'create_settlement_client',
    'get_current_month_settlement_quick',
    
    # 편의 함수들 - Order
    'create_order_client',
    'get_today_orders_quick',
    
    # 편의 함수들 - Product
    'create_product_client',
    
    # 편의 함수들 - Return
    'create_return_client',
    'get_today_returns_quick',
    
    # 편의 함수들 - Exchange
    'create_exchange_client',
    'get_today_exchanges_quick',
    
    # 멀티 계정 지원
    'MultiAccountConfig',
    'CoupangAccount',
    'get_account',
    'list_account_names',
    'get_default_account_name',
    'MultiClientFactory',
    'create_client_for_account',
    'create_unified_client_for_account',
    'execute_on_all_accounts',
    'get_multi_account_status'
]

# 버전 정보
__version__ = "2.0.0"
__author__ = "OwnerClan API Team"
__description__ = "쿠팡 파트너스 API 통합 클라이언트"

# 모듈 레벨 편의 함수들
def validate_environment():
    """
    쿠팡 API 환경 설정 검증
    
    Returns:
        bool: 환경 설정이 올바르면 True
    """
    return config.validate_coupang_credentials()


def get_default_vendor_id():
    """
    기본 벤더 ID 조회
    
    Returns:
        str: 벤더 ID
    """
    return config.coupang_vendor_id


def create_unified_client(access_key=None, secret_key=None, vendor_id=None):
    """
    통합 쿠팡 API 클라이언트 생성 (모든 모듈 포함)
    
    Args:
        access_key: 쿠팡 액세스 키 (None이면 .env에서 읽음)
        secret_key: 쿠팡 시크릿 키 (None이면 .env에서 읽음)
        vendor_id: 쿠팡 벤더 ID (None이면 .env에서 읽음)
        
    Returns:
        dict: 모든 클라이언트를 포함한 딕셔너리
    """
    return {
        'cs': create_cs_client(access_key, secret_key, vendor_id),
        'sales': create_sales_client(access_key, secret_key, vendor_id),
        'settlement': create_settlement_client(access_key, secret_key, vendor_id),
        'order': create_order_client(access_key, secret_key, vendor_id),
        'product': create_product_client(access_key, secret_key, vendor_id),
        'returns': create_return_client(access_key, secret_key, vendor_id),
        'exchange': create_exchange_client(access_key, secret_key, vendor_id)
    }


def create_multi_account_unified_client(account_name=None):
    """
    멀티 계정용 통합 클라이언트 생성
    
    Args:
        account_name: 계정 이름 (None이면 기본 계정)
        
    Returns:
        dict: 멀티 계정 지원 통합 클라이언트 또는 None
    """
    return create_unified_client_for_account(account_name)