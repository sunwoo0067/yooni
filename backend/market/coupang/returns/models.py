#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 데이터 모델
"""

import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


@dataclass
class ReturnRequestSearchParams:
    """반품/취소 요청 목록 조회 검색 파라미터"""
    vendor_id: str  # 판매자 ID (A00012345)
    search_type: str  # 검색 타입 (timeFrame: 분단위, 생략시: 일단위)
    created_at_from: str  # 검색 시작일시
    created_at_to: str  # 검색 종료일시
    status: Optional[str] = None  # 반품상태 (RU, UC, CC, PR)
    cancel_type: Optional[str] = "RETURN"  # 취소유형 (RETURN, CANCEL)
    next_token: Optional[str] = None  # 다음 페이지 조회 토큰
    max_per_page: Optional[int] = None  # 페이지당 최대 조회 수
    order_id: Optional[int] = None  # 주문번호
    
    def to_query_params(self) -> str:
        """검색 파라미터를 쿼리 스트링으로 변환"""
        params = {}
        
        # 필수 파라미터
        params['searchType'] = self.search_type
        params['createdAtFrom'] = self.created_at_from
        params['createdAtTo'] = self.created_at_to
        
        # 선택적 파라미터
        if self.status and self.cancel_type != "CANCEL":
            params['status'] = self.status
            
        if self.cancel_type and self.cancel_type != "RETURN":
            params['cancelType'] = self.cancel_type
            
        # timeFrame이 아닌 경우에만 페이징 파라미터 추가
        if self.search_type != "timeFrame":
            if self.next_token:
                params['nextToken'] = self.next_token
            if self.max_per_page:
                params['maxPerPage'] = str(self.max_per_page)
            if self.order_id and not self.status:
                params['orderId'] = str(self.order_id)
        
        return urllib.parse.urlencode(params)


@dataclass
class ReturnDeliveryDto:
    """회수 운송장 정보"""
    delivery_company_code: str  # 회수 택배사코드
    delivery_invoice_no: str  # 회수 운송장번호
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnDeliveryDto':
        """딕셔너리에서 ReturnDeliveryDto 객체 생성"""
        return cls(
            delivery_company_code=data.get('deliveryCompanyCode', ''),
            delivery_invoice_no=data.get('deliveryInvoiceNo', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnDeliveryDto 객체를 딕셔너리로 변환"""
        return {
            'deliveryCompanyCode': self.delivery_company_code,
            'deliveryInvoiceNo': self.delivery_invoice_no
        }


@dataclass 
class ReturnItem:
    """반품 아이템 정보"""
    vendor_item_package_id: int  # 딜번호
    vendor_item_package_name: str  # 딜명
    vendor_item_id: int  # 옵션아이디
    vendor_item_name: str  # 옵션명
    cancel_count: int  # 취소 수량
    purchase_count: int  # 주문 수량
    shipment_box_id: int  # 원 배송번호
    seller_product_id: int  # 업체등록상품번호
    seller_product_name: str  # 업체등록상품명
    release_status: str  # 상품출고여부 (Y, N, S, A)
    cancel_complete_user: str  # 주문취소처리 담당자
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnItem':
        """딕셔너리에서 ReturnItem 객체 생성"""
        return cls(
            vendor_item_package_id=data.get('vendorItemPackageId', 0),
            vendor_item_package_name=data.get('vendorItemPackageName', ''),
            vendor_item_id=data.get('vendorItemId', 0),
            vendor_item_name=data.get('vendorItemName', ''),
            cancel_count=data.get('cancelCount', 0),
            purchase_count=data.get('purchaseCount', 0),
            shipment_box_id=data.get('shipmentBoxId', 0),
            seller_product_id=data.get('sellerProductId', 0),
            seller_product_name=data.get('sellerProductName', ''),
            release_status=data.get('releaseStatus', ''),
            cancel_complete_user=data.get('cancelCompleteUser', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnItem 객체를 딕셔너리로 변환"""
        return {
            'vendorItemPackageId': self.vendor_item_package_id,
            'vendorItemPackageName': self.vendor_item_package_name,
            'vendorItemId': self.vendor_item_id,
            'vendorItemName': self.vendor_item_name,
            'cancelCount': self.cancel_count,
            'purchaseCount': self.purchase_count,
            'shipmentBoxId': self.shipment_box_id,
            'sellerProductId': self.seller_product_id,
            'sellerProductName': self.seller_product_name,
            'releaseStatus': self.release_status,
            'cancelCompleteUser': self.cancel_complete_user
        }
    
    def get_release_status_text(self) -> str:
        """출고 상태 텍스트 반환"""
        status_map = {
            'Y': '출고됨',
            'N': '미출고',
            'S': '출고중지됨',
            'A': '이미출고됨'
        }
        return status_map.get(self.release_status, '알 수 없음')
    
    def is_stop_release_required(self) -> bool:
        """출고중지 처리가 필요한지 확인"""
        return self.release_status == 'N'  # 미출고 상태인 경우


@dataclass
class ReturnRequest:
    """반품/취소 요청 정보"""
    receipt_id: int  # 취소(반품)접수번호
    order_id: int  # 주문번호
    payment_id: int  # 결제번호
    receipt_type: str  # 취소유형 (RETURN, CANCEL)
    receipt_status: str  # 취소(반품)진행 상태
    created_at: str  # 취소(반품) 접수시간
    modified_at: str  # 취소(반품) 상태 최종 변경시간
    requester_name: str  # 반품 신청인 이름
    requester_phone_number: str  # 반품 신청인 전화번호(안심번호)
    requester_real_phone_number: Optional[str]  # 반품 신청인 실전화번호
    requester_address: str  # 반품 회수지 주소
    requester_address_detail: str  # 반품 회수지 상세주소
    requester_zip_code: str  # 반품 회수지 우편번호
    cancel_reason_category1: str  # 반품 사유 카테고리 1
    cancel_reason_category2: str  # 반품 사유 카테고리 2
    cancel_reason: str  # 취소사유 상세내역
    cancel_count_sum: int  # 총 취소수량
    return_delivery_id: int  # 반품배송번호
    return_delivery_type: str  # 회수종류
    release_stop_status: str  # 출고중지처리상태
    enclose_price: int  # 동봉배송비
    fault_by_type: str  # 귀책타입
    pre_refund: bool  # 선환불 여부
    complete_confirm_type: str  # 완료 확인 종류
    complete_confirm_date: str  # 완료 확인 시간
    return_items: List[ReturnItem]  # 반품 아이템 목록
    return_delivery_dtos: List[ReturnDeliveryDto]  # 회수 운송장 정보
    reason_code: str  # 반품사유코드
    reason_code_text: str  # 반품사유설명
    return_shipping_charge: int  # 예상 반품배송비
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnRequest':
        """딕셔너리에서 ReturnRequest 객체 생성"""
        return cls(
            receipt_id=data.get('receiptId', 0),
            order_id=data.get('orderId', 0),
            payment_id=data.get('paymentId', 0),
            receipt_type=data.get('receiptType', ''),
            receipt_status=data.get('receiptStatus', ''),
            created_at=data.get('createdAt', ''),
            modified_at=data.get('modifiedAt', ''),
            requester_name=data.get('requesterName', ''),
            requester_phone_number=data.get('requesterPhoneNumber', ''),
            requester_real_phone_number=data.get('requesterRealPhoneNumber'),
            requester_address=data.get('requesterAddress', ''),
            requester_address_detail=data.get('requesterAddressDetail', ''),
            requester_zip_code=data.get('requesterZipCode', ''),
            cancel_reason_category1=data.get('cancelReasonCategory1', ''),
            cancel_reason_category2=data.get('cancelReasonCategory2', ''),
            cancel_reason=data.get('cancelReason', ''),
            cancel_count_sum=data.get('cancelCountSum', 0),
            return_delivery_id=data.get('returnDeliveryId', 0),
            return_delivery_type=data.get('returnDeliveryType', ''),
            release_stop_status=data.get('releaseStopStatus', ''),
            enclose_price=data.get('enclosePrice', 0),
            fault_by_type=data.get('faultByType', ''),
            pre_refund=data.get('preRefund', False),
            complete_confirm_type=data.get('completeConfirmType', ''),
            complete_confirm_date=data.get('completeConfirmDate', ''),
            return_items=[ReturnItem.from_dict(item) for item in data.get('returnItems', [])],
            return_delivery_dtos=[ReturnDeliveryDto.from_dict(dto) for dto in data.get('returnDeliveryDtos', [])],
            reason_code=data.get('reasonCode', ''),
            reason_code_text=data.get('reasonCodeText', ''),
            return_shipping_charge=data.get('returnShippingCharge', 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnRequest 객체를 딕셔너리로 변환"""
        return {
            'receiptId': self.receipt_id,
            'orderId': self.order_id,
            'paymentId': self.payment_id,
            'receiptType': self.receipt_type,
            'receiptStatus': self.receipt_status,
            'createdAt': self.created_at,
            'modifiedAt': self.modified_at,
            'requesterName': self.requester_name,
            'requesterPhoneNumber': self.requester_phone_number,
            'requesterRealPhoneNumber': self.requester_real_phone_number,
            'requesterAddress': self.requester_address,
            'requesterAddressDetail': self.requester_address_detail,
            'requesterZipCode': self.requester_zip_code,
            'cancelReasonCategory1': self.cancel_reason_category1,
            'cancelReasonCategory2': self.cancel_reason_category2,
            'cancelReason': self.cancel_reason,
            'cancelCountSum': self.cancel_count_sum,
            'returnDeliveryId': self.return_delivery_id,
            'returnDeliveryType': self.return_delivery_type,
            'releaseStopStatus': self.release_stop_status,
            'enclosePrice': self.enclose_price,
            'faultByType': self.fault_by_type,
            'preRefund': self.pre_refund,
            'completeConfirmType': self.complete_confirm_type,
            'completeConfirmDate': self.complete_confirm_date,
            'returnItems': [item.to_dict() for item in self.return_items],
            'returnDeliveryDtos': [dto.to_dict() for dto in self.return_delivery_dtos],
            'reasonCode': self.reason_code,
            'reasonCodeText': self.reason_code_text,
            'returnShippingCharge': self.return_shipping_charge
        }
    
    def get_receipt_status_text(self) -> str:
        """접수 상태 텍스트 반환"""
        status_map = {
            'RELEASE_STOP_UNCHECKED': '출고중지요청',
            'RETURNS_UNCHECKED': '반품접수',
            'VENDOR_WAREHOUSE_CONFIRM': '입고완료',
            'REQUEST_COUPANG_CHECK': '쿠팡확인요청',
            'RETURNS_COMPLETED': '반품완료'
        }
        return status_map.get(self.receipt_status, '알 수 없음')
    
    def get_fault_by_type_text(self) -> str:
        """귀책 타입 텍스트 반환"""
        fault_map = {
            'COUPANG': '쿠팡 과실',
            'VENDOR': '협력사(셀러) 과실',
            'CUSTOMER': '고객 과실',
            'WMS': '물류 과실',
            'GENERAL': '일반'
        }
        return fault_map.get(self.fault_by_type, '알 수 없음')
    
    def is_stop_release_required(self) -> bool:
        """출고중지 처리가 필요한지 확인"""
        return (self.receipt_status == 'RELEASE_STOP_UNCHECKED' and 
                self.release_stop_status == '미처리')
    
    def get_stop_release_items(self) -> List[ReturnItem]:
        """출고중지 처리가 필요한 아이템 목록 반환"""
        return [item for item in self.return_items if item.is_stop_release_required()]
    
    def get_total_cancel_amount(self) -> int:
        """총 취소 금액 계산 (예상)"""
        # 실제로는 아이템별 가격 정보가 필요하지만, 여기서는 배송비만 계산
        return abs(self.return_shipping_charge) if self.return_shipping_charge < 0 else 0
    
    def get_summary_info(self) -> Dict[str, Any]:
        """요약 정보 반환"""
        return {
            'receipt_id': self.receipt_id,
            'order_id': self.order_id,
            'receipt_type': self.receipt_type,
            'receipt_status_text': self.get_receipt_status_text(),
            'cancel_count_sum': self.cancel_count_sum,
            'fault_by_type_text': self.get_fault_by_type_text(),
            'reason_code_text': self.reason_code_text,
            'stop_release_required': self.is_stop_release_required(),
            'created_at': self.created_at
        }


@dataclass
class ReturnRequestDetailResponse:
    """반품/취소 요청 단건 조회 응답"""
    code: int
    message: str
    data: List[ReturnRequest]  # API 응답에서 data는 배열이지만 단건 조회시 1개 요소만 포함
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ReturnRequestDetailResponse':
        """딕셔너리에서 ReturnRequestDetailResponse 객체 생성"""
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            data=[ReturnRequest.from_dict(item) for item in response_data.get('data', [])]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnRequestDetailResponse 객체를 딕셔너리로 변환"""
        return {
            'code': self.code,
            'message': self.message,
            'data': [item.to_dict() for item in self.data]
        }
    
    def get_return_request(self) -> Optional[ReturnRequest]:
        """단건 조회 결과의 ReturnRequest 객체 반환"""
        return self.data[0] if self.data else None
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """상세 정보 반환"""
        request = self.get_return_request()
        if not request:
            return {}
        
        return {
            'basic_info': {
                'receipt_id': request.receipt_id,
                'order_id': request.order_id,
                'payment_id': request.payment_id,
                'receipt_type': request.receipt_type,
                'receipt_status': request.get_receipt_status_text(),
                'created_at': request.created_at,
                'modified_at': request.modified_at
            },
            'requester_info': {
                'name': request.requester_name,
                'phone': request.requester_phone_number,
                'real_phone': request.requester_real_phone_number,
                'address': f"{request.requester_address} {request.requester_address_detail}".strip(),
                'zip_code': request.requester_zip_code
            },
            'return_reason': {
                'category1': request.cancel_reason_category1,
                'category2': request.cancel_reason_category2,
                'reason_detail': request.cancel_reason,
                'reason_code': request.reason_code,
                'reason_text': request.reason_code_text
            },
            'processing_info': {
                'cancel_count_sum': request.cancel_count_sum,
                'return_delivery_id': request.return_delivery_id,
                'return_delivery_type': request.return_delivery_type,
                'release_stop_status': request.release_stop_status,
                'fault_by_type': request.get_fault_by_type_text(),
                'pre_refund': request.pre_refund,
                'complete_confirm_type': request.complete_confirm_type,
                'complete_confirm_date': request.complete_confirm_date
            },
            'financial_info': {
                'enclose_price': request.enclose_price,
                'return_shipping_charge': request.return_shipping_charge,
                'shipping_charge_text': self._format_shipping_charge(request.return_shipping_charge)
            },
            'items': [item.to_dict() for item in request.return_items],
            'delivery_info': [dto.to_dict() for dto in request.return_delivery_dtos]
        }
    
    def _format_shipping_charge(self, charge: int) -> str:
        """배송비 형식화"""
        if charge == 0:
            return "무료"
        elif charge > 0:
            return f"+{charge:,}원 (셀러 부담)"
        else:
            return f"{charge:,}원 (고객 부담)"


@dataclass
class ReturnRequestListResponse:
    """반품/취소 요청 목록 조회 응답"""
    code: int
    message: str
    data: List[ReturnRequest]
    next_token: Optional[str] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ReturnRequestListResponse':
        """딕셔너리에서 ReturnRequestListResponse 객체 생성"""
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            data=[ReturnRequest.from_dict(item) for item in response_data.get('data', [])],
            next_token=response_data.get('nextToken')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnRequestListResponse 객체를 딕셔너리로 변환"""
        result = {
            'code': self.code,
            'message': self.message,
            'data': [item.to_dict() for item in self.data]
        }
        if self.next_token:
            result['nextToken'] = self.next_token
        return result
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """요약 통계 정보 반환"""
        total_count = len(self.data)
        if total_count == 0:
            return {
                'total_count': 0,
                'status_summary': {},
                'fault_type_summary': {},
                'stop_release_required_count': 0
            }
        
        # 상태별 집계
        status_summary = {}
        fault_type_summary = {}
        stop_release_required_count = 0
        
        for request in self.data:
            # 상태별 집계
            status_text = request.get_receipt_status_text()
            status_summary[status_text] = status_summary.get(status_text, 0) + 1
            
            # 귀책 타입별 집계
            fault_text = request.get_fault_by_type_text()
            fault_type_summary[fault_text] = fault_type_summary.get(fault_text, 0) + 1
            
            # 출고중지 필요 건수
            if request.is_stop_release_required():
                stop_release_required_count += 1
        
        return {
            'total_count': total_count,
            'status_summary': status_summary,
            'fault_type_summary': fault_type_summary,
            'stop_release_required_count': stop_release_required_count
        }


@dataclass
class ReturnWithdrawRequest:
    """반품 철회 이력 정보"""
    cancel_id: int  # 반품 접수번호
    order_id: int  # 주문번호
    vendor_id: str  # 판매자 ID
    refund_delivery_duty: str  # 반품 귀책 (COM, CUS, COU)
    created_at: str  # 반품철회 시각
    vendor_item_ids: List[int]  # 반품 옵션아이디 목록
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnWithdrawRequest':
        """딕셔너리에서 ReturnWithdrawRequest 객체 생성"""
        return cls(
            cancel_id=data.get('cancelId', 0),
            order_id=data.get('orderId', 0),
            vendor_id=data.get('vendorId', ''),
            refund_delivery_duty=data.get('refundDeliveryDuty', ''),
            created_at=data.get('createdAt', ''),
            vendor_item_ids=data.get('vendorItemIds', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnWithdrawRequest 객체를 딕셔너리로 변환"""
        return {
            'cancelId': self.cancel_id,
            'orderId': self.order_id,
            'vendorId': self.vendor_id,
            'refundDeliveryDuty': self.refund_delivery_duty,
            'createdAt': self.created_at,
            'vendorItemIds': self.vendor_item_ids
        }
    
    def get_duty_text(self) -> str:
        """귀책 타입 텍스트 반환"""
        duty_map = {
            'COM': '업체',
            'CUS': '고객',
            'COU': '쿠팡'
        }
        return duty_map.get(self.refund_delivery_duty, '알 수 없음')


@dataclass
class ReturnWithdrawListResponse:
    """반품 철회 이력 목록 조회 응답"""
    code: int
    message: str
    data: List[ReturnWithdrawRequest]
    next_page_index: Optional[str] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ReturnWithdrawListResponse':
        """딕셔너리에서 ReturnWithdrawListResponse 객체 생성"""
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            data=[ReturnWithdrawRequest.from_dict(item) for item in response_data.get('data', [])],
            next_page_index=response_data.get('nextPageIndex')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnWithdrawListResponse 객체를 딕셔너리로 변환"""
        result = {
            'code': self.code,
            'message': self.message,
            'data': [item.to_dict() for item in self.data]
        }
        if self.next_page_index:
            result['nextPageIndex'] = self.next_page_index
        return result


@dataclass
class ReturnInvoiceCreateResponse:
    """회수 송장 등록 응답"""
    delivery_company_code: str  # 택배사코드
    invoice_number: str  # 운송장번호
    invoice_number_id: int  # 내부 invoiceNumberId
    receipt_id: int  # 반품 또는 교환 접수ID
    reg_number: Optional[str]  # 택배사 회수번호
    return_delivery_id: int  # 내부 returnDeliveryId
    return_exchange_delivery_type: str  # RETURN or EXCHANGE
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnInvoiceCreateResponse':
        """딕셔너리에서 ReturnInvoiceCreateResponse 객체 생성"""
        return cls(
            delivery_company_code=data.get('deliveryCompanyCode', ''),
            invoice_number=data.get('invoiceNumber', ''),
            invoice_number_id=data.get('invoiceNumberId', 0),
            receipt_id=data.get('receiptId', 0),
            reg_number=data.get('regNumber'),
            return_delivery_id=data.get('returnDeliveryId', 0),
            return_exchange_delivery_type=data.get('returnExchangeDeliveryType', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """ReturnInvoiceCreateResponse 객체를 딕셔너리로 변환"""
        result = {
            'deliveryCompanyCode': self.delivery_company_code,
            'invoiceNumber': self.invoice_number,
            'invoiceNumberId': self.invoice_number_id,
            'receiptId': self.receipt_id,
            'returnDeliveryId': self.return_delivery_id,
            'returnExchangeDeliveryType': self.return_exchange_delivery_type
        }
        if self.reg_number:
            result['regNumber'] = self.reg_number
        return result