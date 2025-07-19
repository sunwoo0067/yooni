#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관련 데이터 모델
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import urllib.parse


@dataclass
class OrderSheetSearchParams:
    """발주서 목록 조회 검색 파라미터"""
    vendor_id: str  # 판매자 ID (A00012345)
    created_at_from: str  # 검색 시작일시 (yyyy-mm-dd 또는 yyyy-mm-ddTHH:MM)
    created_at_to: str  # 검색 종료일시 (yyyy-mm-dd 또는 yyyy-mm-ddTHH:MM)
    status: str  # 발주서 상태
    next_token: Optional[str] = None  # 다음 페이지 조회를 위한 token값
    max_per_page: Optional[int] = None  # 페이지당 최대 조회 요청 값
    search_type: Optional[str] = None  # 검색 타입 (timeFrame: 분단위 전체, 기본: 일단위 페이징)
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열로 변환"""
        params = {
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to,
            "status": self.status
        }
        
        if self.next_token:
            params["nextToken"] = self.next_token
        if self.max_per_page:
            params["maxPerPage"] = str(self.max_per_page)
        if self.search_type:
            params["searchType"] = self.search_type
            
        return urllib.parse.urlencode(params)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "vendorId": self.vendor_id,
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to,
            "status": self.status
        }
        
        if self.next_token:
            result["nextToken"] = self.next_token
        if self.max_per_page:
            result["maxPerPage"] = self.max_per_page
        if self.search_type:
            result["searchType"] = self.search_type
            
        return result


@dataclass
class Orderer:
    """주문자 정보"""
    name: str  # 주문자 이름
    email: str  # 주문자 email (미사용)
    safe_number: str  # 수취인 연락처(안심번호)
    orderer_number: Optional[str] = None  # 주문자 연락처(실전화번호)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Orderer':
        """딕셔너리에서 생성"""
        return cls(
            name=data.get("name", ""),
            email=data.get("email", ""),
            safe_number=data.get("safeNumber", ""),
            orderer_number=data.get("ordererNumber")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "email": self.email,
            "safeNumber": self.safe_number,
            "ordererNumber": self.orderer_number
        }


@dataclass
class Receiver:
    """수취인 정보"""
    name: str  # 수취인 이름
    safe_number: str  # 수취인 연락처(안심번호)
    addr1: str  # 수취인 배송지1
    addr2: str  # 수취인 배송지2
    post_code: str  # 수취인 우편번호
    receiver_number: Optional[str] = None  # 수취인 연락처(실전화번호)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receiver':
        """딕셔너리에서 생성"""
        return cls(
            name=data.get("name", ""),
            safe_number=data.get("safeNumber", ""),
            addr1=data.get("addr1", ""),
            addr2=data.get("addr2", ""),
            post_code=data.get("postCode", ""),
            receiver_number=data.get("receiverNumber")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "safeNumber": self.safe_number,
            "addr1": self.addr1,
            "addr2": self.addr2,
            "postCode": self.post_code,
            "receiverNumber": self.receiver_number
        }


@dataclass 
class OrderItem:
    """주문 아이템 정보"""
    vendor_item_id: int  # 옵션ID
    vendor_item_name: str  # 노출상품명
    shipping_count: int  # 주문시 item의 구매 수량
    sales_price: int  # 개당 상품 가격
    order_price: int  # 결제 가격
    discount_price: int  # 총 할인 가격
    seller_product_id: int  # 등록상품ID
    seller_product_name: str  # 등록상품명
    seller_product_item_name: str  # 등록옵션명
    cancel_count: int  # 취소수량
    hold_count_for_cancel: int  # 환불대기수량
    
    # 선택적 필드들
    vendor_item_package_id: Optional[int] = None
    vendor_item_package_name: Optional[str] = None
    product_id: Optional[int] = None
    instant_coupon_discount: Optional[int] = None
    downloadable_coupon_discount: Optional[int] = None
    coupang_discount: Optional[int] = None
    external_vendor_sku_code: Optional[str] = None
    etc_info_header: Optional[str] = None
    etc_info_value: Optional[str] = None
    etc_info_values: Optional[List[str]] = None
    first_seller_product_item_name: Optional[str] = None
    estimated_shipping_date: Optional[str] = None
    planned_shipping_date: Optional[str] = None
    invoice_number_upload_date: Optional[str] = None
    extra_properties: Optional[Dict[str, Any]] = None
    pricing_badge: Optional[bool] = None
    used_product: Optional[bool] = None
    confirm_date: Optional[str] = None
    delivery_charge_type_name: Optional[str] = None
    up_bundle_vendor_item_id: Optional[int] = None
    up_bundle_vendor_item_name: Optional[str] = None
    up_bundle_size: Optional[int] = None
    up_bundle_item: Optional[bool] = None
    canceled: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """딕셔너리에서 생성"""
        return cls(
            vendor_item_package_id=data.get("vendorItemPackageId"),
            vendor_item_package_name=data.get("vendorItemPackageName"),
            product_id=data.get("productId"),
            vendor_item_id=data["vendorItemId"],
            vendor_item_name=data["vendorItemName"],
            shipping_count=data["shippingCount"],
            sales_price=data["salesPrice"],
            order_price=data["orderPrice"],
            discount_price=data["discountPrice"],
            instant_coupon_discount=data.get("instantCouponDiscount"),
            downloadable_coupon_discount=data.get("downloadableCouponDiscount"),
            coupang_discount=data.get("coupangDiscount"),
            external_vendor_sku_code=data.get("externalVendorSkuCode"),
            etc_info_header=data.get("etcInfoHeader"),
            etc_info_value=data.get("etcInfoValue"),
            etc_info_values=data.get("etcInfoValues"),
            seller_product_id=data["sellerProductId"],
            seller_product_name=data["sellerProductName"],
            seller_product_item_name=data["sellerProductItemName"],
            first_seller_product_item_name=data.get("firstSellerProductItemName"),
            cancel_count=data["cancelCount"],
            hold_count_for_cancel=data["holdCountForCancel"],
            estimated_shipping_date=data.get("estimatedShippingDate"),
            planned_shipping_date=data.get("plannedShippingDate"),
            invoice_number_upload_date=data.get("invoiceNumberUploadDate"),
            extra_properties=data.get("extraProperties"),
            pricing_badge=data.get("pricingBadge"),
            used_product=data.get("usedProduct"),
            confirm_date=data.get("confirmDate"),
            delivery_charge_type_name=data.get("deliveryChargeTypeName"),
            up_bundle_vendor_item_id=data.get("upBundleVendorItemId"),
            up_bundle_vendor_item_name=data.get("upBundleVendorItemName"),
            up_bundle_size=data.get("upBundleSize"),
            up_bundle_item=data.get("upBundleItem"),
            canceled=data.get("canceled")
        )
    
    def get_available_shipping_count(self) -> int:
        """발주 가능 수량 계산"""
        return self.shipping_count - (self.hold_count_for_cancel + self.cancel_count)


@dataclass
class OverseasShippingInfo:
    """해외배송정보"""
    personal_customs_clearance_code: Optional[str] = None  # 개인통관 고유부호
    orderer_ssn: Optional[str] = None  # 미사용
    orderer_phone_number: Optional[str] = None  # 통관용 구매자 전화번호
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OverseasShippingInfo':
        """딕셔너리에서 생성"""
        return cls(
            personal_customs_clearance_code=data.get("personalCustomsClearanceCode"),
            orderer_ssn=data.get("ordererSsn"),
            orderer_phone_number=data.get("ordererPhoneNumber")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "personalCustomsClearanceCode": self.personal_customs_clearance_code,
            "ordererSsn": self.orderer_ssn,
            "ordererPhoneNumber": self.orderer_phone_number
        }


@dataclass
class OrderSheet:
    """발주서 정보"""
    shipment_box_id: int  # 배송번호(묶음배송번호)
    order_id: int  # 주문번호
    ordered_at: str  # 주문일시
    orderer: Orderer  # 주문자
    paid_at: str  # 결제일시
    status: str  # 발주서 상태
    shipping_price: int  # 배송비
    remote_price: int  # 도서산간배송비
    remote_area: bool  # 도서산간여부
    split_shipping: bool  # 분리배송여부
    able_split_shipping: bool  # 분리배송가능여부
    receiver: Receiver  # 수취인
    order_items: List[OrderItem]  # 주문 아이템들
    
    # 선택적 필드들
    parcel_print_message: Optional[str] = None  # 배송메세지
    overseas_shipping_info: Optional[OverseasShippingInfo] = None  # 해외배송정보
    delivery_company_name: Optional[str] = None  # 택배사
    invoice_number: Optional[str] = None  # 운송장번호
    in_trasit_date_time: Optional[str] = None  # 출고일(발송일)
    delivered_date: Optional[str] = None  # 배송완료일
    refer: Optional[str] = None  # 결제위치
    shipment_type: Optional[str] = None  # 배송유형
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderSheet':
        """딕셔너리에서 생성"""
        orderer = Orderer.from_dict(data["orderer"])
        receiver = Receiver.from_dict(data["receiver"])
        order_items = [OrderItem.from_dict(item) for item in data["orderItems"]]
        
        overseas_info = None
        if data.get("overseaShippingInfoDto"):
            overseas_info = OverseasShippingInfo.from_dict(data["overseaShippingInfoDto"])
        
        return cls(
            shipment_box_id=data["shipmentBoxId"],
            order_id=data["orderId"],
            ordered_at=data["orderedAt"],
            orderer=orderer,
            paid_at=data["paidAt"],
            status=data["status"],
            shipping_price=data["shippingPrice"],
            remote_price=data["remotePrice"],
            remote_area=data["remoteArea"],
            parcel_print_message=data.get("parcelPrintMessage"),
            split_shipping=data["splitShipping"],
            able_split_shipping=data["ableSplitShipping"],
            receiver=receiver,
            order_items=order_items,
            overseas_shipping_info=overseas_info,
            delivery_company_name=data.get("deliveryCompanyName"),
            invoice_number=data.get("invoiceNumber"),
            in_trasit_date_time=data.get("inTrasitDateTime"),
            delivered_date=data.get("deliveredDate"),
            refer=data.get("refer"),
            shipment_type=data.get("shipmentType")
        )
    
    def get_total_order_amount(self) -> int:
        """총 주문 금액 계산"""
        return sum(item.order_price for item in self.order_items)
    
    def get_total_discount_amount(self) -> int:
        """총 할인 금액 계산"""
        return sum(item.discount_price for item in self.order_items)
    
    def get_total_available_shipping_count(self) -> int:
        """총 발주 가능 수량 계산"""
        return sum(item.get_available_shipping_count() for item in self.order_items)
    
    def has_overseas_shipping(self) -> bool:
        """해외배송 여부 확인"""
        return self.overseas_shipping_info is not None
    
    def is_bundle_shipping(self) -> bool:
        """번들 배송 여부 확인"""
        return any(item.up_bundle_item for item in self.order_items if item.up_bundle_item)


@dataclass
class OrderSheetListResponse:
    """발주서 목록 조회 응답"""
    order_sheets: List[OrderSheet]  # 발주서 목록
    next_token: Optional[str] = None  # 다음 페이지 토큰
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderSheetListResponse':
        """딕셔너리에서 생성"""
        order_sheets = [OrderSheet.from_dict(sheet) for sheet in data.get("data", [])]
        return cls(
            order_sheets=order_sheets,
            next_token=data.get("nextToken")
        )
    
    def has_next_page(self) -> bool:
        """다음 페이지 존재 여부"""
        return self.next_token is not None and self.next_token.strip() != ""
    
    def get_total_count(self) -> int:
        """총 발주서 개수"""
        return len(self.order_sheets)
    
    def get_status_summary(self) -> Dict[str, int]:
        """상태별 발주서 개수 요약"""
        summary = {}
        for sheet in self.order_sheets:
            status = sheet.status
            summary[status] = summary.get(status, 0) + 1
        return summary


@dataclass
class OrderSheetTimeFrameParams:
    """발주서 목록 조회 검색 파라미터 (분단위 전체 - 24시간 이내)"""
    vendor_id: str  # 판매자 ID (A00012345)
    created_at_from: str  # 검색 시작일시 (yyyy-mm-ddTHH:MM)
    created_at_to: str  # 검색 종료일시 (yyyy-mm-ddTHH:MM)
    status: str  # 발주서 상태
    
    def __post_init__(self):
        """초기화 후 자동으로 searchType을 timeFrame으로 설정"""
        # 24시간 이내 검증
        from datetime import datetime
        try:
            start_dt = datetime.strptime(self.created_at_from, "%Y-%m-%dT%H:%M")
            end_dt = datetime.strptime(self.created_at_to, "%Y-%m-%dT%H:%M")
            
            # 24시간 이내 확인
            diff = end_dt - start_dt
            if diff.total_seconds() > 24 * 60 * 60:  # 24시간 = 86400초
                raise ValueError("분단위 전체 조회는 24시간 이내로만 가능합니다")
                
        except ValueError as e:
            if "24시간" in str(e):
                raise e
            else:
                raise ValueError("날짜 형식이 올바르지 않습니다. yyyy-mm-ddTHH:MM 형식을 사용해주세요")
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열로 변환"""
        params = {
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to,
            "status": self.status,
            "searchType": "timeFrame"  # 분단위 전체 조회 고정
        }
        
        return urllib.parse.urlencode(params)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to,
            "status": self.status,
            "searchType": "timeFrame"
        }
    
    def to_order_sheet_search_params(self) -> 'OrderSheetSearchParams':
        """기존 OrderSheetSearchParams로 변환"""
        return OrderSheetSearchParams(
            vendor_id=self.vendor_id,
            created_at_from=self.created_at_from,
            created_at_to=self.created_at_to,
            status=self.status,
            search_type="timeFrame"
        )


@dataclass
class OrderSheetDetailResponse:
    """발주서 단건 조회 응답"""
    order_sheet: OrderSheet  # 발주서 상세 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderSheetDetailResponse':
        """딕셔너리에서 생성"""
        order_sheet = OrderSheet.from_dict(data.get("data", {}))
        return cls(order_sheet=order_sheet)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "orderSheet": self.order_sheet.__dict__
        }
    
    def get_receiver_info(self) -> Dict[str, Any]:
        """수취인 정보 반환 (배송지 변경 확인용)"""
        return self.order_sheet.receiver.to_dict()
    
    def get_product_name_validation_info(self) -> List[Dict[str, Any]]:
        """상품명 검증 정보 반환 (sellerProductName + sellerProductItemName vs vendorItemName)"""
        validation_info = []
        
        for item in self.order_sheet.order_items:
            seller_full_name = f"{item.seller_product_name} {item.seller_product_item_name}".strip()
            vendor_name = item.vendor_item_name
            
            validation_info.append({
                "vendorItemId": item.vendor_item_id,
                "sellerFullName": seller_full_name,
                "vendorItemName": vendor_name,
                "isMatched": seller_full_name == vendor_name,
                "sellerProductName": item.seller_product_name,
                "sellerProductItemName": item.seller_product_item_name
            })
        
        return validation_info
    
    def has_product_name_mismatch(self) -> bool:
        """상품명 불일치가 있는지 확인"""
        validation_info = self.get_product_name_validation_info()
        return any(not info["isMatched"] for info in validation_info)
    
    def get_shipping_summary(self) -> Dict[str, Any]:
        """배송 요약 정보"""
        return {
            "shipmentBoxId": self.order_sheet.shipment_box_id,
            "orderId": self.order_sheet.order_id,
            "status": self.order_sheet.status,
            "deliveryCompanyName": self.order_sheet.delivery_company_name,
            "invoiceNumber": self.order_sheet.invoice_number,
            "inTrasitDateTime": self.order_sheet.in_trasit_date_time,
            "deliveredDate": self.order_sheet.delivered_date,
            "shipmentType": self.order_sheet.shipment_type,
            "receiverAddress": f"{self.order_sheet.receiver.addr1} {self.order_sheet.receiver.addr2}".strip()
        }


@dataclass
class OrderSheetByOrderIdResponse:
    """발주서 주문번호별 조회 응답 (orderId 기반)"""
    order_sheets: List[OrderSheet]  # 발주서 목록 (동일 orderId로 여러 shipmentBoxId 존재 가능)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderSheetByOrderIdResponse':
        """딕셔너리에서 생성"""
        order_sheets_data = data.get("data", [])
        order_sheets = [OrderSheet.from_dict(sheet) for sheet in order_sheets_data]
        return cls(order_sheets=order_sheets)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "orderSheets": [sheet.__dict__ for sheet in self.order_sheets]
        }
    
    def get_total_count(self) -> int:
        """총 발주서 개수"""
        return len(self.order_sheets)
    
    def get_shipment_box_ids(self) -> List[int]:
        """모든 배송번호 목록 반환"""
        return [sheet.shipment_box_id for sheet in self.order_sheets]
    
    def get_order_id(self) -> Optional[int]:
        """주문번호 반환 (모든 발주서가 동일한 orderId를 가짐)"""
        if self.order_sheets:
            return self.order_sheets[0].order_id
        return None
    
    def get_receiver_info_summary(self) -> Dict[str, Any]:
        """수취인 정보 요약 (배송지 변경 확인용) - 첫 번째 발주서 기준"""
        if not self.order_sheets:
            return {}
        
        first_sheet = self.order_sheets[0]
        return first_sheet.receiver.to_dict()
    
    def get_product_name_validation_summary(self) -> Dict[str, Any]:
        """모든 발주서의 상품명 검증 요약"""
        all_validation_info = []
        total_items = 0
        mismatch_count = 0
        
        for sheet in self.order_sheets:
            for item in sheet.order_items:
                total_items += 1
                seller_full_name = f"{item.seller_product_name} {item.seller_product_item_name}".strip()
                vendor_name = item.vendor_item_name
                is_matched = seller_full_name == vendor_name
                
                if not is_matched:
                    mismatch_count += 1
                
                all_validation_info.append({
                    "shipmentBoxId": sheet.shipment_box_id,
                    "vendorItemId": item.vendor_item_id,
                    "sellerFullName": seller_full_name,
                    "vendorItemName": vendor_name,
                    "isMatched": is_matched,
                    "sellerProductName": item.seller_product_name,
                    "sellerProductItemName": item.seller_product_item_name
                })
        
        return {
            "totalItems": total_items,
            "mismatchCount": mismatch_count,
            "hasMismatch": mismatch_count > 0,
            "mismatchRate": round(mismatch_count / total_items * 100, 2) if total_items > 0 else 0,
            "validationDetails": all_validation_info
        }
    
    def has_product_name_mismatch(self) -> bool:
        """상품명 불일치가 있는지 확인"""
        validation_summary = self.get_product_name_validation_summary()
        return validation_summary.get("hasMismatch", False)
    
    def get_shipping_summary(self) -> List[Dict[str, Any]]:
        """모든 발주서의 배송 요약 정보"""
        shipping_summaries = []
        
        for sheet in self.order_sheets:
            shipping_summaries.append({
                "shipmentBoxId": sheet.shipment_box_id,
                "orderId": sheet.order_id,
                "status": sheet.status,
                "deliveryCompanyName": sheet.delivery_company_name,
                "invoiceNumber": sheet.invoice_number,
                "inTrasitDateTime": sheet.in_trasit_date_time,
                "deliveredDate": sheet.delivered_date,
                "shipmentType": sheet.shipment_type,
                "receiverAddress": f"{sheet.receiver.addr1} {sheet.receiver.addr2}".strip()
            })
        
        return shipping_summaries
    
    def get_status_summary(self) -> Dict[str, int]:
        """상태별 발주서 개수 요약"""
        status_summary = {}
        for sheet in self.order_sheets:
            status = sheet.status
            status_summary[status] = status_summary.get(status, 0) + 1
        return status_summary
    
    def get_total_order_amount(self) -> int:
        """전체 주문 금액 계산"""
        total_amount = 0
        for sheet in self.order_sheets:
            total_amount += sheet.get_total_order_amount()
        return total_amount
    
    def is_split_shipping(self) -> bool:
        """분리배송 여부 확인"""
        return len(self.order_sheets) > 1 or any(sheet.split_shipping for sheet in self.order_sheets)


@dataclass
class DeliveryHistoryItem:
    """배송상태 변경 히스토리 항목"""
    status: str  # 배송 상태
    status_description: str  # 상태 설명
    changed_at: str  # 상태 변경 일시
    location: Optional[str] = None  # 배송 위치
    tracking_info: Optional[str] = None  # 추적 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryHistoryItem':
        """딕셔너리에서 생성"""
        return cls(
            status=data.get("status", ""),
            status_description=data.get("statusDescription", ""),
            changed_at=data.get("changedAt", ""),
            location=data.get("location"),
            tracking_info=data.get("trackingInfo")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "status": self.status,
            "statusDescription": self.status_description,
            "changedAt": self.changed_at
        }
        if self.location:
            result["location"] = self.location
        if self.tracking_info:
            result["trackingInfo"] = self.tracking_info
        return result


@dataclass 
class OrderSheetHistoryResponse:
    """발주서 배송상태 변경 히스토리 응답"""
    shipment_box_id: int  # 배송번호
    order_id: int  # 주문번호
    current_status: str  # 현재 상태
    delivery_company_name: Optional[str]  # 택배사명
    invoice_number: Optional[str]  # 송장번호
    history: List[DeliveryHistoryItem]  # 배송상태 변경 히스토리
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderSheetHistoryResponse':
        """딕셔너리에서 생성"""
        # API 응답의 data 필드에서 히스토리 정보 추출
        history_data = data.get("data", {})
        
        # 히스토리 항목들 변환
        history_items = []
        for item_data in history_data.get("history", []):
            history_items.append(DeliveryHistoryItem.from_dict(item_data))
        
        return cls(
            shipment_box_id=history_data.get("shipmentBoxId", 0),
            order_id=history_data.get("orderId", 0),
            current_status=history_data.get("currentStatus", ""),
            delivery_company_name=history_data.get("deliveryCompanyName"),
            invoice_number=history_data.get("invoiceNumber"),
            history=history_items
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "shipmentBoxId": self.shipment_box_id,
            "orderId": self.order_id,
            "currentStatus": self.current_status,
            "deliveryCompanyName": self.delivery_company_name,
            "invoiceNumber": self.invoice_number,
            "history": [item.to_dict() for item in self.history]
        }
    
    def get_latest_status(self) -> Optional[DeliveryHistoryItem]:
        """최신 배송상태 조회"""
        if not self.history:
            return None
        return max(self.history, key=lambda x: x.changed_at)
    
    def get_status_changes_count(self) -> int:
        """배송상태 변경 횟수"""
        return len(self.history)
    
    def has_delivery_tracking(self) -> bool:
        """배송추적 가능 여부"""
        return bool(self.delivery_company_name and self.invoice_number)


@dataclass
class OrderProcessingRequest:
    """상품준비중 처리 요청"""
    vendor_id: str  # 판매자 ID
    shipment_box_id: int  # 배송번호
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "shipmentBoxId": self.shipment_box_id
        }


@dataclass
class InvoiceUploadRequest:
    """송장업로드 처리 요청"""
    vendor_id: str  # 판매자 ID
    shipment_box_id: int  # 배송번호
    delivery_company_code: str  # 택배사 코드
    invoice_number: str  # 송장번호
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "shipmentBoxId": self.shipment_box_id,
            "deliveryCompanyCode": self.delivery_company_code,
            "invoiceNumber": self.invoice_number
        }


@dataclass
class StopShippingRequest:
    """출고중지완료 처리 요청"""
    vendor_id: str  # 판매자 ID
    shipment_box_id: int  # 배송번호
    reason: str  # 출고중지 사유
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "shipmentBoxId": self.shipment_box_id,
            "reason": self.reason
        }


@dataclass
class AlreadyShippedRequest:
    """이미출고 처리 요청"""
    vendor_id: str  # 판매자 ID
    shipment_box_id: int  # 배송번호
    delivery_company_code: str  # 택배사 코드
    invoice_number: str  # 송장번호
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "shipmentBoxId": self.shipment_box_id,
            "deliveryCompanyCode": self.delivery_company_code,
            "invoiceNumber": self.invoice_number
        }


@dataclass
class OrderCancelRequest:
    """주문 상품 취소 처리 요청"""
    vendor_id: str  # 판매자 ID
    vendor_item_id: int  # 상품 ID
    reason: str  # 취소 사유
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "vendorItemId": self.vendor_item_id,
            "reason": self.reason
        }


@dataclass
class CompleteDeliveryRequest:
    """장기미배송 배송완료 처리 요청"""
    vendor_id: str  # 판매자 ID
    shipment_box_id: int  # 배송번호
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "shipmentBoxId": self.shipment_box_id
        }


@dataclass
class OrderProcessingResponse:
    """주문 처리 응답"""
    success: bool  # 처리 성공 여부
    message: str  # 처리 결과 메시지
    code: int  # 응답 코드
    processed_at: Optional[str] = None  # 처리 일시
    details: Optional[Dict[str, Any]] = None  # 추가 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderProcessingResponse':
        """딕셔너리에서 생성"""
        return cls(
            success=data.get("code") == 200,
            message=data.get("message", ""),
            code=data.get("code", 0),
            processed_at=data.get("processedAt"),
            details=data.get("data")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "success": self.success,
            "message": self.message,
            "code": self.code
        }
        if self.processed_at:
            result["processedAt"] = self.processed_at
        if self.details:
            result["details"] = self.details
        return result