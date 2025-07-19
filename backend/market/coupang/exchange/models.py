#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 데이터 모델
"""

import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .constants import (
    EXCHANGE_STATUS, EXCHANGE_ORDER_DELIVERY_STATUS, EXCHANGE_REFER_TYPE,
    EXCHANGE_FAULT_TYPE, EXCHANGE_CREATED_BY_TYPE, VOC_CODES, EXCHANGE_REJECT_CODES
)


@dataclass
class ExchangeRequestSearchParams:
    """교환요청 검색 파라미터"""
    vendor_id: str
    created_at_from: str  # yyyy-MM-ddTHH:mm:ss
    created_at_to: str    # yyyy-MM-ddTHH:mm:ss
    status: Optional[str] = None              # EXCHANGE_STATUS
    order_id: Optional[int] = None            # 주문번호
    next_token: Optional[str] = None          # 페이징 토큰
    max_per_page: Optional[int] = None        # 페이지당 최대 조회 수
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열로 변환"""
        params = {
            'createdAtFrom': self.created_at_from,
            'createdAtTo': self.created_at_to
        }
        
        if self.status:
            params['status'] = self.status
        if self.order_id:
            params['orderId'] = str(self.order_id)
        if self.next_token:
            params['nextToken'] = self.next_token
        if self.max_per_page:
            params['maxPerPage'] = str(self.max_per_page)
            
        return urllib.parse.urlencode(params)


@dataclass 
class ExchangeItem:
    """교환 상품 정보"""
    exchange_item_id: int
    order_item_id: int
    order_item_unit_price: int
    order_item_name: Optional[str]
    order_package_id: Optional[int]
    order_package_name: Optional[str]
    target_item_id: int
    target_item_unit_price: int
    target_item_name: str
    target_package_id: int
    target_package_name: str
    quantity: int
    order_item_delivery_complete: Optional[bool]
    order_item_return_complete: Optional[bool] 
    target_item_delivery_complete: Optional[bool]
    created_at: str
    modified_at: str
    original_shipment_box_id: Optional[int]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeItem':
        """딕셔너리에서 ExchangeItem 객체 생성"""
        return cls(
            exchange_item_id=data.get('exchangeItemId', 0),
            order_item_id=data.get('orderItemId', 0),
            order_item_unit_price=data.get('orderItemUnitPrice', 0),
            order_item_name=data.get('orderItemName'),
            order_package_id=data.get('orderPackageId'),
            order_package_name=data.get('orderPackageName'),
            target_item_id=data.get('targetItemId', 0),
            target_item_unit_price=data.get('targetItemUnitPrice', 0),
            target_item_name=data.get('targetItemName', ''),
            target_package_id=data.get('targetPackageId', 0),
            target_package_name=data.get('targetPackageName', ''),
            quantity=data.get('quantity', 0),
            order_item_delivery_complete=data.get('orderItemDeliveryComplete'),
            order_item_return_complete=data.get('orderItemReturnComplete'),
            target_item_delivery_complete=data.get('targetItemDeliveryComplete'),
            created_at=data.get('createdAt', ''),
            modified_at=data.get('modifiedAt', ''),
            original_shipment_box_id=data.get('originalShipmentBoxId')
        )


@dataclass
class ExchangeAddress:
    """교환 주소 정보"""
    exchange_address_id: int
    return_customer_name: str
    return_address_zip_code: str
    return_address: str
    return_address_detail: str
    return_phone: Optional[str]
    return_mobile: str
    return_memo: Optional[str]
    delivery_customer_name: str
    delivery_address_zip_code: str
    delivery_address: str
    delivery_address_detail: str
    delivery_phone: Optional[str]
    delivery_mobile: str
    delivery_memo: Optional[str]
    created_at: str
    modified_at: str
    exchange_id: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeAddress':
        """딕셔너리에서 ExchangeAddress 객체 생성"""
        return cls(
            exchange_address_id=data.get('exchangeAddressId', 0),
            return_customer_name=data.get('returnCustomerName', ''),
            return_address_zip_code=data.get('returnAddressZipCode', ''),
            return_address=data.get('returnAddress', ''),
            return_address_detail=data.get('returnAddressDetail', ''),
            return_phone=data.get('returnPhone'),
            return_mobile=data.get('returnMobile', ''),
            return_memo=data.get('returnMemo'),
            delivery_customer_name=data.get('deliveryCustomerName', ''),
            delivery_address_zip_code=data.get('deliveryAddressZipCode', ''),
            delivery_address=data.get('deliveryAddress', ''),
            delivery_address_detail=data.get('deliveryAddressDetail', ''),
            delivery_phone=data.get('deliveryPhone'),
            delivery_mobile=data.get('deliveryMobile', ''),
            delivery_memo=data.get('deliveryMemo'),
            created_at=data.get('createdAt', ''),
            modified_at=data.get('modifiedAt', ''),
            exchange_id=data.get('exchangeId', 0)
        )


@dataclass
class DeliveryInvoiceGroup:
    """배송 송장 그룹 정보"""
    shipment_box_id: int
    box_price: int
    order_id: int
    order_type: str
    customer_type: str
    bundle_type: str
    extra_message: str
    shipping_delivery_type: str
    delivery_invoice_dtos: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryInvoiceGroup':
        """딕셔너리에서 DeliveryInvoiceGroup 객체 생성"""
        return cls(
            shipment_box_id=data.get('shipmentBoxId', 0),
            box_price=data.get('boxPrice', 0),
            order_id=data.get('orderId', 0),
            order_type=data.get('orderType', ''),
            customer_type=data.get('customerType', ''),
            bundle_type=data.get('bundleType', ''),
            extra_message=data.get('extraMessage', ''),
            shipping_delivery_type=data.get('shippingDeliveryType', ''),
            delivery_invoice_dtos=data.get('deliveryInvoiceDtos', [])
        )


@dataclass
class CollectInformation:
    """회수 정보"""
    return_type: str
    expected_return_date: str
    return_delivery_item_dtos: List[Dict[str, Any]]
    return_delivery_destination_dto: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectInformation':
        """딕셔너리에서 CollectInformation 객체 생성"""
        return cls(
            return_type=data.get('returnType', ''),
            expected_return_date=data.get('expectedReturnDate', ''),
            return_delivery_item_dtos=data.get('returndeliveryItemDtos', []),
            return_delivery_destination_dto=data.get('returndeliveryDestinationDto', {})
        )


@dataclass
class ReturnDelivery:
    """회수 배송 정보"""
    delivery_company_code: str
    delivery_invoice_no: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnDelivery':
        """딕셔너리에서 ReturnDelivery 객체 생성"""
        return cls(
            delivery_company_code=data.get('deliveryCompanyCode', ''),
            delivery_invoice_no=data.get('deliveryInvoiceNo', '')
        )


@dataclass
class ExchangeRequest:
    """교환요청 정보"""
    exchange_id: int
    order_id: int
    vendor_id: str
    order_delivery_status_code: str
    exchange_status: str
    refer_type: str
    fault_type: str
    exchange_amount: int
    reason: Optional[str]
    reason_code: str
    reason_code_text: str
    reason_etc_detail: str
    cancel_reason: Optional[str]
    created_by_type: str
    created_at: str
    modified_by_type: str
    modified_at: str
    exchange_items: List[ExchangeItem] = field(default_factory=list)
    exchange_address: Optional[ExchangeAddress] = None
    delivery_invoice_groups: List[DeliveryInvoiceGroup] = field(default_factory=list)
    delivery_status: str = ''
    collect_status: str = ''
    collect_complete_date: Optional[str] = None
    collect_information: Optional[CollectInformation] = None
    return_deliveries: List[ReturnDelivery] = field(default_factory=list)
    successable: bool = False
    rejectable: bool = False
    delivery_invoice_modifiable: bool = False
    
    # 라벨 정보
    order_delivery_status_label: str = ''
    exchange_status_label: str = ''
    refer_type_label: str = ''
    fault_type_label: str = ''
    created_by_type_label: str = ''
    modified_by_type_label: str = ''
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeRequest':
        """딕셔너리에서 ExchangeRequest 객체 생성"""
        exchange_items = []
        if 'exchangeItemDtoV1s' in data:
            exchange_items = [
                ExchangeItem.from_dict(item) 
                for item in data['exchangeItemDtoV1s']
            ]
        
        exchange_address = None
        if 'exchangeAddressDtoV1' in data and data['exchangeAddressDtoV1']:
            exchange_address = ExchangeAddress.from_dict(data['exchangeAddressDtoV1'])
            
        delivery_invoice_groups = []
        if 'deliveryInvoiceGroupDtos' in data:
            delivery_invoice_groups = [
                DeliveryInvoiceGroup.from_dict(group)
                for group in data['deliveryInvoiceGroupDtos']
            ]
            
        collect_information = None
        if 'collectInformationsDto' in data and data['collectInformationsDto']:
            collect_information = CollectInformation.from_dict(data['collectInformationsDto'])
            
        return_deliveries = []
        if 'returnDeliveryDtos' in data:
            return_deliveries = [
                ReturnDelivery.from_dict(delivery)
                for delivery in data['returnDeliveryDtos']
            ]
        
        return cls(
            exchange_id=data.get('exchangeId', 0),
            order_id=data.get('orderId', 0),
            vendor_id=data.get('vendorId', ''),
            order_delivery_status_code=data.get('orderDeliveryStatusCode', ''),
            exchange_status=data.get('exchangeStatus', ''),
            refer_type=data.get('referType', ''),
            fault_type=data.get('faultType', ''),
            exchange_amount=data.get('exchangeAmount', 0),
            reason=data.get('reason'),
            reason_code=data.get('reasonCode', ''),
            reason_code_text=data.get('reasonCodeText', ''),
            reason_etc_detail=data.get('reasonEtcDetail', ''),
            cancel_reason=data.get('cancelReason'),
            created_by_type=data.get('createdByType', ''),
            created_at=data.get('createdAt', ''),
            modified_by_type=data.get('modifiedByType', ''),
            modified_at=data.get('modifiedAt', ''),
            exchange_items=exchange_items,
            exchange_address=exchange_address,
            delivery_invoice_groups=delivery_invoice_groups,
            delivery_status=data.get('deliveryStatus', ''),
            collect_status=data.get('collectStatus', ''),
            collect_complete_date=data.get('collectCompleteDate'),
            collect_information=collect_information,
            return_deliveries=return_deliveries,
            successable=data.get('successable', False),
            rejectable=data.get('rejectable', False),
            delivery_invoice_modifiable=data.get('deliveryInvoiceModifiable', False),
            order_delivery_status_label=data.get('orderDeliveryStatusLabel', ''),
            exchange_status_label=data.get('exchangeStatusLabel', ''),
            refer_type_label=data.get('referTypeLabel', ''),
            fault_type_label=data.get('faultTypeLabel', ''),
            created_by_type_label=data.get('createdByTypeLabel', ''),
            modified_by_type_label=data.get('modifiedByTypeLabel', '')
        )
    
    def get_priority_level(self) -> str:
        """교환요청 우선순위 레벨 계산"""
        # 업체과실인 경우 높은 우선순위
        if self.fault_type == "VENDOR":
            return "HIGH"
        
        # 완료/불가/철회 상태가 아닌 경우 중간 우선순위  
        if self.exchange_status in ["RECEIPT", "PROGRESS"]:
            return "MEDIUM"
            
        return "LOW"
    
    def get_exchange_summary(self) -> Dict[str, Any]:
        """교환요청 요약 정보"""
        return {
            "exchange_id": self.exchange_id,
            "order_id": self.order_id,
            "status": self.exchange_status,
            "status_label": self.exchange_status_label,
            "fault_type": self.fault_type,
            "fault_type_label": self.fault_type_label,
            "reason_code": self.reason_code,
            "reason_text": self.reason_code_text,
            "created_at": self.created_at,
            "priority_level": self.get_priority_level(),
            "item_count": len(self.exchange_items),
            "successable": self.successable,
            "rejectable": self.rejectable
        }
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """교환요청 상세 정보"""
        return {
            "basic_info": {
                "exchange_id": self.exchange_id,
                "order_id": self.order_id,
                "vendor_id": self.vendor_id,
                "created_at": self.created_at,
                "modified_at": self.modified_at
            },
            "status_info": {
                "exchange_status": self.exchange_status,
                "exchange_status_label": self.exchange_status_label,
                "order_delivery_status": self.order_delivery_status_code,
                "order_delivery_status_label": self.order_delivery_status_label,
                "delivery_status": self.delivery_status,
                "collect_status": self.collect_status
            },
            "reason_info": {
                "reason_code": self.reason_code,
                "reason_code_text": self.reason_code_text,
                "reason_etc_detail": self.reason_etc_detail,
                "fault_type": self.fault_type,
                "fault_type_label": self.fault_type_label,
                "voc_info": VOC_CODES.get(self.reason_code, {})
            },
            "processing_info": {
                "refer_type": self.refer_type,
                "refer_type_label": self.refer_type_label,
                "created_by_type": self.created_by_type,
                "created_by_type_label": self.created_by_type_label,
                "modified_by_type": self.modified_by_type,
                "modified_by_type_label": self.modified_by_type_label
            },
            "action_info": {
                "successable": self.successable,
                "rejectable": self.rejectable,
                "delivery_invoice_modifiable": self.delivery_invoice_modifiable,
                "priority_level": self.get_priority_level()
            },
            "financial_info": {
                "exchange_amount": self.exchange_amount,
                "item_count": len(self.exchange_items),
                "total_item_value": sum(item.target_item_unit_price * item.quantity 
                                      for item in self.exchange_items)
            }
        }


@dataclass
class ExchangeRequestListResponse:
    """교환요청 목록 응답"""
    code: int
    message: str
    data: List[ExchangeRequest] = field(default_factory=list)
    next_token: Optional[str] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ExchangeRequestListResponse':
        """딕셔너리에서 ExchangeRequestListResponse 객체 생성"""
        exchange_requests = []
        if 'data' in response_data and response_data['data']:
            exchange_requests = [
                ExchangeRequest.from_dict(request)
                for request in response_data['data']
            ]
        
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            data=exchange_requests,
            next_token=response_data.get('nextToken')
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """교환요청 요약 통계"""
        if not self.data:
            return {
                "total_count": 0,
                "status_breakdown": {},
                "fault_type_breakdown": {},
                "priority_breakdown": {},
                "total_exchange_amount": 0
            }
        
        # 상태별 분류
        status_breakdown = {}
        for request in self.data:
            status = request.exchange_status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # 귀책별 분류
        fault_type_breakdown = {}
        for request in self.data:
            fault_type = request.fault_type
            fault_type_breakdown[fault_type] = fault_type_breakdown.get(fault_type, 0) + 1
            
        # 우선순위별 분류
        priority_breakdown = {}
        for request in self.data:
            priority = request.get_priority_level()
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
        
        # 총 교환 금액
        total_exchange_amount = sum(request.exchange_amount for request in self.data)
        
        return {
            "total_count": len(self.data),
            "status_breakdown": status_breakdown,
            "fault_type_breakdown": fault_type_breakdown,
            "priority_breakdown": priority_breakdown,
            "total_exchange_amount": total_exchange_amount,
            "vendor_fault_count": fault_type_breakdown.get("VENDOR", 0),
            "customer_fault_count": fault_type_breakdown.get("CUSTOMER", 0),
            "actionable_count": sum(1 for req in self.data 
                                  if req.successable or req.rejectable)
        }


@dataclass
class ExchangeReceiveConfirmationRequest:
    """교환요청 입고 확인 처리 요청"""
    exchange_id: int
    vendor_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "exchangeId": self.exchange_id,
            "vendorId": self.vendor_id
        }


@dataclass
class ExchangeRejectionRequest:
    """교환요청 거부 처리 요청"""
    exchange_id: int
    vendor_id: str
    exchange_reject_code: str  # SOLDOUT 또는 WITHDRAW
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "exchangeId": self.exchange_id,
            "vendorId": self.vendor_id,
            "exchangeRejectCode": self.exchange_reject_code
        }


@dataclass 
class ExchangeInvoiceUploadRequest:
    """교환상품 송장 업로드 요청"""
    exchange_id: int
    vendor_id: str
    goods_delivery_code: str    # 택배사 코드
    invoice_number: str         # 운송장번호
    shipment_box_id: int        # 배송번호
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "exchangeId": self.exchange_id,
            "vendorId": self.vendor_id,
            "goodsDeliveryCode": self.goods_delivery_code,
            "invoiceNumber": self.invoice_number,
            "shipmentBoxId": self.shipment_box_id
        }


@dataclass
class ExchangeProcessingResponse:
    """교환요청 처리 응답"""
    code: int
    message: str
    result_code: Optional[str] = None
    result_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ExchangeProcessingResponse':
        """딕셔너리에서 ExchangeProcessingResponse 객체 생성"""
        data = response_data.get('data', {})
        
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            result_code=data.get('resultCode') if data else None,
            result_message=data.get('resultMessage') if data else None
        )
    
    def is_success(self) -> bool:
        """처리 성공 여부 판단"""
        return (self.code == 200 or self.code == "200") and \
               (self.result_code == "SUCCESS" if self.result_code else True)