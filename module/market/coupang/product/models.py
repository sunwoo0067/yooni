#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 관련 데이터 모델
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ProductImage:
    """상품 이미지 정보"""
    image_order: int  # 이미지 순서 (0,1,2,3...)
    image_type: str  # REPRESENTATION(대표), DETAIL(기타), USED_PRODUCT(중고상태)
    cdn_path: Optional[str] = None  # 쿠팡 CDN 경로
    vendor_path: Optional[str] = None  # 자체 서버 URL
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "imageOrder": self.image_order,
            "imageType": self.image_type
        }
        
        if self.cdn_path:
            result["cdnPath"] = self.cdn_path
        if self.vendor_path:
            result["vendorPath"] = self.vendor_path
            
        return result


@dataclass
class ProductCertification:
    """상품 인증 정보"""
    certification_type: str  # 인증 타입
    certification_code: str = ""  # 인증 코드
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "certificationType": self.certification_type,
            "certificationCode": self.certification_code
        }


@dataclass
class ProductNotice:
    """상품 고시 정보"""
    notice_category_name: str  # 고시정보 카테고리명
    notice_category_detail_name: str  # 고시정보 세부 카테고리명
    content: str  # 고시정보 내용
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "noticeCategoryName": self.notice_category_name,
            "noticeCategoryDetailName": self.notice_category_detail_name,
            "content": self.content
        }


@dataclass
class ProductAttribute:
    """상품 속성/옵션 정보"""
    attribute_type_name: str  # 속성 타입명
    attribute_value_name: str  # 속성 값명
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "attributeTypeName": self.attribute_type_name,
            "attributeValueName": self.attribute_value_name
        }


@dataclass
class ProductContentDetail:
    """상품 상세 컨텐츠 항목"""
    content_type: str = "TEXT"  # 컨텐츠 타입
    content: str = ""  # 컨텐츠 내용
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "contentType": self.content_type,
            "content": self.content
        }


@dataclass
class ProductContent:
    """상품 상세 컨텐츠"""
    contents: List[ProductContentDetail] = None  # 상세 컨텐츠 리스트
    
    def __post_init__(self):
        if self.contents is None:
            self.contents = []
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "contents": [content.to_dict() for content in self.contents]
        }


@dataclass
class ProductRequiredDocument:
    """상품 필수 서류"""
    document_name: str  # 서류명
    document_path: str  # 서류 경로
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "documentName": self.document_name,
            "documentPath": self.document_path
        }


@dataclass
class ProductItem:
    """상품 아이템 (옵션) 정보"""
    # 기본 정보
    item_name: str  # 옵션명
    original_price: int  # 정가
    sale_price: int  # 판매가
    maximum_buy_count: int  # 판매가능수량
    maximum_buy_for_person: int  # 인당최대구매수량
    maximum_buy_for_person_period: int  # 인당최대구매수량 기간
    outbound_shipping_time_day: int  # 기준출고일
    
    # 선택적 정보
    external_vendor_sku: Optional[str] = None  # 업체상품코드
    barcode: Optional[str] = None  # 바코드
    model_name: Optional[str] = None  # 모델명
    
    # 수정 시 필요한 ID
    seller_product_item_id: Optional[int] = None  # 등록상품옵션ID (수정 시)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "itemName": self.item_name,
            "originalPrice": self.original_price,
            "salePrice": self.sale_price,
            "maximumBuyCount": self.maximum_buy_count,
            "maximumBuyForPerson": self.maximum_buy_for_person,
            "maximumBuyForPersonPeriod": self.maximum_buy_for_person_period,
            "outboundShippingTimeDay": self.outbound_shipping_time_day
        }
        
        # 선택적 필드들
        if self.external_vendor_sku:
            result["externalVendorSku"] = self.external_vendor_sku
        if self.barcode:
            result["barcode"] = self.barcode
        if self.model_name:
            result["modelName"] = self.model_name
        if self.seller_product_item_id is not None:
            result["sellerProductItemId"] = self.seller_product_item_id
            
        return result


@dataclass
class ProductRequest:
    """상품 등록/수정 요청 데이터"""
    # 필수 정보
    display_category_code: int  # 노출카테고리코드
    seller_product_name: str  # 등록상품명
    vendor_id: str  # 업체코드
    sale_started_at: str  # 판매시작일시
    sale_ended_at: str  # 판매종료일시
    vendor_user_id: str  # 쿠팡Wing ID
    
    # 승인 요청 여부
    requested: bool = False  # 승인요청여부
    
    # 상품 정보
    display_product_name: Optional[str] = None  # 노출상품명
    brand: Optional[str] = None  # 브랜드
    general_product_name: Optional[str] = None  # 일반상품명
    product_group: Optional[str] = None  # 상품군
    manufacture: Optional[str] = None  # 제조사
    
    # 배송 정보
    delivery_method: str = "SEQUENCIAL"  # 배송방법
    delivery_company_code: Optional[str] = None  # 택배사코드
    delivery_charge_type: str = "FREE"  # 배송비종류
    delivery_charge: int = 0  # 기본배송비
    delivery_charge_on_return: int = 3000  # 초도반품배송비
    free_ship_over_amount: int = 0  # 무료배송 조건 금액
    remote_area_deliverable: str = "N"  # 도서산간 배송여부
    union_delivery_type: str = "UNION_DELIVERY"  # 묶음 배송여부
    
    # 반품지 정보
    return_center_code: Optional[str] = None  # 반품지센터코드
    return_charge_name: Optional[str] = None  # 반품지명
    company_contact_number: Optional[str] = None  # 반품지연락처
    return_zip_code: Optional[str] = None  # 반품지우편번호
    return_address: Optional[str] = None  # 반품지주소
    return_address_detail: Optional[str] = None  # 반품지상세주소
    return_charge: int = 3000  # 반품배송비
    return_charge_vendor: str = "N"  # 반품배송비 업체부담여부
    
    # A/S 정보
    after_service_information: Optional[str] = None  # A/S 정보
    after_service_contact_number: Optional[str] = None  # A/S 연락처
    
    # 기타 정보
    outbound_shipping_place_code: Optional[int] = None  # 출고지주소코드
    offer_description: Optional[str] = None  # 혜택정보
    extra_info_message: Optional[str] = None  # 추가정보메시지
    
    # 수정 시 필요한 ID
    seller_product_id: Optional[int] = None  # 등록상품ID (수정 시)
    
    # 리스트 데이터
    items: List[ProductItem] = None  # 상품 아이템들
    images: List[ProductImage] = None  # 상품 이미지들
    certifications: List[ProductCertification] = None  # 인증정보들
    search_tags: List[str] = None  # 검색태그들
    notices: List[ProductNotice] = None  # 고시정보들
    attributes: List[ProductAttribute] = None  # 상품속성들
    contents: Optional[ProductContent] = None  # 상세컨텐츠
    required_documents: List[ProductRequiredDocument] = None  # 필수서류들
    
    def __post_init__(self):
        """리스트 필드들 초기화"""
        if self.items is None:
            self.items = []
        if self.images is None:
            self.images = []
        if self.certifications is None:
            self.certifications = []
        if self.search_tags is None:
            self.search_tags = []
        if self.notices is None:
            self.notices = []
        if self.attributes is None:
            self.attributes = []
        if self.required_documents is None:
            self.required_documents = []
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "displayCategoryCode": self.display_category_code,
            "sellerProductName": self.seller_product_name,
            "vendorId": self.vendor_id,
            "saleStartedAt": self.sale_started_at,
            "saleEndedAt": self.sale_ended_at,
            "vendorUserId": self.vendor_user_id,
            "requested": self.requested,
            "deliveryMethod": self.delivery_method,
            "deliveryChargeType": self.delivery_charge_type,
            "deliveryCharge": self.delivery_charge,
            "deliveryChargeOnReturn": self.delivery_charge_on_return,
            "freeShipOverAmount": self.free_ship_over_amount,
            "remoteAreaDeliverable": self.remote_area_deliverable,
            "unionDeliveryType": self.union_delivery_type,
            "returnCharge": self.return_charge,
            "returnChargeVendor": self.return_charge_vendor
        }
        
        # 선택적 필드들
        if self.display_product_name:
            result["displayProductName"] = self.display_product_name
        if self.brand:
            result["brand"] = self.brand
        if self.general_product_name:
            result["generalProductName"] = self.general_product_name
        if self.product_group:
            result["productGroup"] = self.product_group
        if self.manufacture:
            result["manufacture"] = self.manufacture
        if self.delivery_company_code:
            result["deliveryCompanyCode"] = self.delivery_company_code
        if self.return_center_code:
            result["returnCenterCode"] = self.return_center_code
        if self.return_charge_name:
            result["returnChargeName"] = self.return_charge_name
        if self.company_contact_number:
            result["companyContactNumber"] = self.company_contact_number
        if self.return_zip_code:
            result["returnZipCode"] = self.return_zip_code
        if self.return_address:
            result["returnAddress"] = self.return_address
        if self.return_address_detail:
            result["returnAddressDetail"] = self.return_address_detail
        if self.after_service_information:
            result["afterServiceInformation"] = self.after_service_information
        if self.after_service_contact_number:
            result["afterServiceContactNumber"] = self.after_service_contact_number
        if self.outbound_shipping_place_code:
            result["outboundShippingPlaceCode"] = self.outbound_shipping_place_code
        if self.offer_description:
            result["offerDescription"] = self.offer_description
        if self.extra_info_message:
            result["extraInfoMessage"] = self.extra_info_message
        if self.seller_product_id is not None:
            result["sellerProductId"] = self.seller_product_id
        
        # 리스트 필드들
        if self.items:
            result["items"] = [item.to_dict() for item in self.items]
        if self.certifications:
            result["certifications"] = [cert.to_dict() for cert in self.certifications]
        if self.search_tags:
            result["searchTags"] = self.search_tags
        if self.images:
            result["images"] = [image.to_dict() for image in self.images]
        if self.notices:
            result["notices"] = [notice.to_dict() for notice in self.notices]
        if self.attributes:
            result["attributes"] = [attr.to_dict() for attr in self.attributes]
        if self.contents:
            result["contents"] = self.contents.to_dict()
        if self.required_documents:
            result["requiredDocuments"] = [doc.to_dict() for doc in self.required_documents]
        
        return result


@dataclass
class ProductSearchParams:
    """상품 목록 조회 검색 파라미터"""
    vendor_id: str  # 판매자 ID (필수)
    next_token: Optional[str] = None  # 페이지 토큰
    max_per_page: Optional[int] = 10  # 페이지당 건수 (기본 10, 최대 100)
    seller_product_id: Optional[int] = None  # 등록상품ID
    seller_product_name: Optional[str] = None  # 등록상품명 (20자 이하)
    status: Optional[str] = None  # 업체상품상태
    manufacture: Optional[str] = None  # 제조사
    created_at: Optional[str] = None  # 상품등록일시 (yyyy-MM-dd)
    
    def to_query_params(self) -> Dict[str, str]:
        """쿼리 파라미터로 변환"""
        params = {
            "vendorId": self.vendor_id
        }
        
        if self.next_token is not None:
            params["nextToken"] = str(self.next_token)
        if self.max_per_page is not None:
            params["maxPerPage"] = str(self.max_per_page)
        if self.seller_product_id is not None:
            params["sellerProductId"] = str(self.seller_product_id)
        if self.seller_product_name is not None:
            params["sellerProductName"] = self.seller_product_name
        if self.status is not None:
            params["status"] = self.status
        if self.manufacture is not None:
            params["manufacture"] = self.manufacture
        if self.created_at is not None:
            params["createdAt"] = self.created_at
            
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendor_id": self.vendor_id,
            "next_token": self.next_token,
            "max_per_page": self.max_per_page,
            "seller_product_id": self.seller_product_id,
            "seller_product_name": self.seller_product_name,
            "status": self.status,
            "manufacture": self.manufacture,
            "created_at": self.created_at
        }


@dataclass
class ProductStatusHistoryParams:
    """상품 상태변경이력 조회 파라미터"""
    seller_product_id: int  # 등록상품ID (필수)
    next_token: Optional[str] = None  # 페이지 토큰
    max_per_page: Optional[int] = 10  # 페이지당 건수 (기본 10)
    
    def to_query_params(self) -> Dict[str, str]:
        """쿼리 파라미터로 변환"""
        params = {}
        
        if self.next_token is not None:
            params["nextToken"] = str(self.next_token)
        if self.max_per_page is not None:
            params["maxPerPage"] = str(self.max_per_page)
            
        return params


@dataclass
class ProductPartialUpdateRequest:
    """상품 부분 수정 요청 데이터 (승인불필요)"""
    seller_product_id: int  # 등록상품ID (필수)
    
    # 배송 관련 정보 (선택적)
    delivery_method: Optional[str] = None  # 배송방법
    delivery_company_code: Optional[str] = None  # 택배사 코드
    delivery_charge_type: Optional[str] = None  # 배송비종류
    delivery_charge: Optional[int] = None  # 기본배송비
    delivery_charge_on_return: Optional[int] = None  # 초도반품배송비
    free_ship_over_amount: Optional[int] = None  # 무료배송 조건 금액
    remote_area_deliverable: Optional[str] = None  # 도서산간 배송여부
    union_delivery_type: Optional[str] = None  # 묶음 배송여부
    outbound_shipping_place_code: Optional[int] = None  # 출고지주소코드
    outbound_shipping_time_day: Optional[int] = None  # 기준출고일
    
    # 반품지 관련 정보 (선택적)
    return_center_code: Optional[str] = None  # 반품지센터코드
    return_charge_name: Optional[str] = None  # 반품지명
    company_contact_number: Optional[str] = None  # 반품지연락처
    return_zip_code: Optional[str] = None  # 반품지우편번호
    return_address: Optional[str] = None  # 반품지주소
    return_address_detail: Optional[str] = None  # 반품지상세주소
    return_charge: Optional[int] = None  # 반품배송비
    return_charge_vendor: Optional[str] = None  # 반품배송비 업체부담여부
    
    # A/S 관련 정보 (선택적)
    after_service_information: Optional[str] = None  # A/S 정보
    after_service_contact_number: Optional[str] = None  # A/S 연락처
    
    # 기타 정보 (선택적)
    offer_description: Optional[str] = None  # 혜택정보
    extra_info_message: Optional[str] = None  # 추가정보메시지
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (None이 아닌 필드만 포함)"""
        result = {
            "sellerProductId": self.seller_product_id
        }
        
        # 선택적 필드들 (None이 아닌 경우만 추가)
        if self.delivery_method is not None:
            result["deliveryMethod"] = self.delivery_method
        if self.delivery_company_code is not None:
            result["deliveryCompanyCode"] = self.delivery_company_code
        if self.delivery_charge_type is not None:
            result["deliveryChargeType"] = self.delivery_charge_type
        if self.delivery_charge is not None:
            result["deliveryCharge"] = self.delivery_charge
        if self.delivery_charge_on_return is not None:
            result["deliveryChargeOnReturn"] = self.delivery_charge_on_return
        if self.free_ship_over_amount is not None:
            result["freeShipOverAmount"] = self.free_ship_over_amount
        if self.remote_area_deliverable is not None:
            result["remoteAreaDeliverable"] = self.remote_area_deliverable
        if self.union_delivery_type is not None:
            result["unionDeliveryType"] = self.union_delivery_type
        if self.outbound_shipping_place_code is not None:
            result["outboundShippingPlaceCode"] = self.outbound_shipping_place_code
        if self.outbound_shipping_time_day is not None:
            result["outboundShippingTimeDay"] = self.outbound_shipping_time_day
        if self.return_center_code is not None:
            result["returnCenterCode"] = self.return_center_code
        if self.return_charge_name is not None:
            result["returnChargeName"] = self.return_charge_name
        if self.company_contact_number is not None:
            result["companyContactNumber"] = self.company_contact_number
        if self.return_zip_code is not None:
            result["returnZipCode"] = self.return_zip_code
        if self.return_address is not None:
            result["returnAddress"] = self.return_address
        if self.return_address_detail is not None:
            result["returnAddressDetail"] = self.return_address_detail
        if self.return_charge is not None:
            result["returnCharge"] = self.return_charge
        if self.return_charge_vendor is not None:
            result["returnChargeVendor"] = self.return_charge_vendor
        if self.after_service_information is not None:
            result["afterServiceInformation"] = self.after_service_information
        if self.after_service_contact_number is not None:
            result["afterServiceContactNumber"] = self.after_service_contact_number
        if self.offer_description is not None:
            result["offerDescription"] = self.offer_description
        if self.extra_info_message is not None:
            result["extraInfoMessage"] = self.extra_info_message
        
        return result