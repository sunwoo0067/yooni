"""
쿠팡 파트너스 API - 출고지 관리 모듈
"""

from .shipping_center_client import (
    ShippingCenterClient,
    ShippingCenterRequest,
    ShippingCenterUpdateRequest,
    PlaceAddress,
    RemoteInfo,
    RemoteInfoUpdate,
    ShippingPlace,
    ShippingPlaceAddress,
    ShippingPlaceRemoteInfo,
    ShippingPlacePagination,
    ShippingPlaceListResponse
)

__all__ = [
    'ShippingCenterClient',
    'ShippingCenterRequest', 
    'ShippingCenterUpdateRequest',
    'PlaceAddress',
    'RemoteInfo',
    'RemoteInfoUpdate',
    'ShippingPlace',
    'ShippingPlaceAddress',
    'ShippingPlaceRemoteInfo',
    'ShippingPlacePagination',
    'ShippingPlaceListResponse'
]