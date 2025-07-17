#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품지 관리 클라이언트
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from auth import CoupangAuth


@dataclass
class ReturnPlaceAddress:
    """반품지 주소 정보"""
    address_type: str  # JIBUN, ROADNAME
    company_contact_number: str  # 전화번호
    phone_number2: Optional[str] = None  # 보조 전화번호
    return_zip_code: str = ""  # 우편번호
    return_address: str = ""  # 주소
    return_address_detail: str = ""  # 상세주소
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "addressType": self.address_type,
            "companyContactNumber": self.company_contact_number,
            "returnZipCode": self.return_zip_code,
            "returnAddress": self.return_address,
            "returnAddressDetail": self.return_address_detail
        }
        
        if self.phone_number2:
            result["phoneNumber2"] = self.phone_number2
            
        return result


@dataclass
class GoodsflowInfo:
    """택배사 계약 정보"""
    deliver_code: str  # 택배사 코드
    deliver_name: Optional[str] = None  # 택배사명
    contract_number: str = ""  # 택배사 계약코드
    contract_customer_number: str = ""  # 업체코드 (우체국만)
    
    # 신용요금 (판매자 신용)
    vendor_credit_fee_05kg: int = 0  # 5kg 신용요금
    vendor_credit_fee_10kg: int = 0  # 10kg 신용요금
    vendor_credit_fee_20kg: int = 0  # 20kg 신용요금
    
    # 선불요금 (판매자 현금)
    vendor_cash_fee_05kg: int = 0  # 5kg 선불요금
    vendor_cash_fee_10kg: int = 0  # 10kg 선불요금
    vendor_cash_fee_20kg: int = 0  # 20kg 선불요금
    
    # 착불요금 (구매자 현금)
    consumer_cash_fee_05kg: int = 0  # 5kg 착불요금
    consumer_cash_fee_10kg: int = 0  # 10kg 착불요금
    consumer_cash_fee_20kg: int = 0  # 20kg 착불요금
    
    # 반품비
    return_fee_05kg: int = 0  # 5kg 반품비
    return_fee_10kg: int = 0  # 10kg 반품비
    return_fee_20kg: int = 0  # 20kg 반품비
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "deliverCode": self.deliver_code,
            "contractNumber": self.contract_number,
            "contractCustomerNumber": self.contract_customer_number,
            "vendorCreditFee05kg": str(self.vendor_credit_fee_05kg),
            "vendorCreditFee10kg": str(self.vendor_credit_fee_10kg),
            "vendorCreditFee20kg": str(self.vendor_credit_fee_20kg),
            "vendorCashFee05kg": str(self.vendor_cash_fee_05kg),
            "vendorCashFee10kg": str(self.vendor_cash_fee_10kg),
            "vendorCashFee20kg": str(self.vendor_cash_fee_20kg),
            "consumerCashFee05kg": str(self.consumer_cash_fee_05kg),
            "consumerCashFee10kg": str(self.consumer_cash_fee_10kg),
            "consumerCashFee20kg": str(self.consumer_cash_fee_20kg),
            "returnFee05kg": str(self.return_fee_05kg),
            "returnFee10kg": str(self.return_fee_10kg),
            "returnFee20kg": str(self.return_fee_20kg)
        }
        
        if self.deliver_name:
            result["deliverName"] = self.deliver_name
            
        return result


@dataclass
class ReturnCenterRequest:
    """반품지 생성 요청 데이터"""
    vendor_id: str  # 판매자 ID
    user_id: str  # 사용자 아이디
    shipping_place_name: str  # 반품지 이름
    goodsflow_info: GoodsflowInfo  # 택배사 정보
    place_addresses: List[ReturnPlaceAddress]  # 반품지 주소 목록
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "userId": self.user_id,
            "shippingPlaceName": self.shipping_place_name,
            "goodsflowInfoOpenApiDto": self.goodsflow_info.to_dict(),
            "placeAddresses": [addr.to_dict() for addr in self.place_addresses]
        }


@dataclass
class ReturnCenterQueryAddress:
    """반품지 조회 응답 - 주소 정보"""
    address_type: str  # JIBUN, ROADNAME, OVERSEA
    country_code: str  # 국가 코드
    company_contact_number: str  # 전화번호
    phone_number2: Optional[str]  # 보조 전화번호
    return_zip_code: str  # 우편번호
    return_address: str  # 주소
    return_address_detail: str  # 상세주소
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenterQueryAddress':
        """딕셔너리에서 객체 생성"""
        return cls(
            address_type=data.get('addressType', ''),
            country_code=data.get('countryCode', ''),
            company_contact_number=data.get('companyContactNumber', ''),
            phone_number2=data.get('phoneNumber2'),
            return_zip_code=data.get('returnZipCode', ''),
            return_address=data.get('returnAddress', ''),
            return_address_detail=data.get('returnAddressDetail', '')
        )


@dataclass
class ReturnCenter:
    """반품지 조회 응답 - 반품지 정보"""
    vendor_id: str  # 업체 코드
    return_center_code: str  # 반품지 센터코드
    shipping_place_name: str  # 반품지 이름
    deliver_code: str  # 택배사 코드
    deliver_name: str  # 택배사명
    goodsflow_status: str  # 굿스플로 상태
    error_message: str  # 에러 메시지
    created_at: int  # 생성일 (timestamp)
    usable: bool  # 사용여부
    
    # 2kg 요금들 (null 가능)
    vendor_credit_fee_02kg: Optional[int] = None
    vendor_cash_fee_02kg: Optional[int] = None
    consumer_cash_fee_02kg: Optional[int] = None
    return_fee_02kg: Optional[int] = None
    
    # 5kg 요금들
    vendor_credit_fee_05kg: int = 0
    vendor_cash_fee_05kg: int = 0
    consumer_cash_fee_05kg: int = 0
    return_fee_05kg: int = 0
    
    # 10kg 요금들
    vendor_credit_fee_10kg: int = 0
    vendor_cash_fee_10kg: int = 0
    consumer_cash_fee_10kg: int = 0
    return_fee_10kg: int = 0
    
    # 20kg 요금들
    vendor_credit_fee_20kg: int = 0
    vendor_cash_fee_20kg: int = 0
    consumer_cash_fee_20kg: int = 0
    return_fee_20kg: int = 0
    
    place_addresses: List[ReturnCenterQueryAddress] = None  # 반품지 주소 목록
    
    def __post_init__(self):
        if self.place_addresses is None:
            self.place_addresses = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenter':
        """딕셔너리에서 객체 생성"""
        place_addresses = [
            ReturnCenterQueryAddress.from_dict(addr) 
            for addr in data.get('placeAddresses', [])
        ]
        
        return cls(
            vendor_id=data.get('vendorId', ''),
            return_center_code=data.get('returnCenterCode', ''),
            shipping_place_name=data.get('shippingPlaceName', ''),
            deliver_code=data.get('deliverCode', ''),
            deliver_name=data.get('deliverName', ''),
            goodsflow_status=data.get('goodsflowStatus', ''),
            error_message=data.get('errorMessage', ''),
            created_at=data.get('createdAt', 0),
            usable=data.get('usable', False),
            
            # 2kg 요금들 (null 처리)
            vendor_credit_fee_02kg=data.get('vendorCreditFee02kg'),
            vendor_cash_fee_02kg=data.get('vendorCashFee02kg'),
            consumer_cash_fee_02kg=data.get('consumerCashFee02kg'),
            return_fee_02kg=data.get('returnFee02kg'),
            
            # 5kg 요금들
            vendor_credit_fee_05kg=data.get('vendorCreditFee05kg', 0),
            vendor_cash_fee_05kg=data.get('vendorCashFee05kg', 0),
            consumer_cash_fee_05kg=data.get('consumerCashFee05kg', 0),
            return_fee_05kg=data.get('returnFee05kg', 0),
            
            # 10kg 요금들
            vendor_credit_fee_10kg=data.get('vendorCreditFee10kg', 0),
            vendor_cash_fee_10kg=data.get('vendorCashFee10kg', 0),
            consumer_cash_fee_10kg=data.get('consumerCashFee10kg', 0),
            return_fee_10kg=data.get('returnFee10kg', 0),
            
            # 20kg 요금들
            vendor_credit_fee_20kg=data.get('vendorCreditFee20kg', 0),
            vendor_cash_fee_20kg=data.get('vendorCashFee20kg', 0),
            consumer_cash_fee_20kg=data.get('consumerCashFee20kg', 0),
            return_fee_20kg=data.get('returnFee20kg', 0),
            
            place_addresses=place_addresses
        )
    
    def get_created_date_str(self) -> str:
        """생성일을 문자열로 반환"""
        if self.created_at:
            from datetime import datetime
            return datetime.fromtimestamp(self.created_at / 1000).strftime('%Y/%m/%d %H:%M:%S')
        return ""


@dataclass
class ReturnCenterPagination:
    """반품지 조회 응답 - 페이징 정보"""
    current_page: int  # 현재 페이지
    total_pages: int  # 전체 페이지 수
    total_elements: int  # 전체 데이터 수
    count_per_page: int  # 페이지별 데이터 수
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenterPagination':
        """딕셔너리에서 객체 생성"""
        return cls(
            current_page=data.get('currentPage', 1),
            total_pages=data.get('totalPages', 1),
            total_elements=data.get('totalElements', 0),
            count_per_page=data.get('countPerPage', 10)
        )


@dataclass
class ReturnCenterListResponse:
    """반품지 목록 조회 응답"""
    content: List[ReturnCenter]  # 반품지 목록
    pagination: ReturnCenterPagination  # 페이징 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenterListResponse':
        """딕셔너리에서 객체 생성"""
        content = [
            ReturnCenter.from_dict(center_data) 
            for center_data in data.get('content', [])
        ]
        
        pagination = ReturnCenterPagination.from_dict(data.get('pagination', {}))
        
        return cls(content=content, pagination=pagination)


@dataclass 
class ReturnCenterUpdateAddress:
    """반품지 수정 주소 정보"""
    address_type: Optional[str] = None  # JIBUN, ROADNAME (선택사항)
    company_contact_number: Optional[str] = None  # 전화번호
    phone_number2: Optional[str] = None  # 보조 전화번호
    return_zip_code: Optional[str] = None  # 우편번호
    return_address: Optional[str] = None  # 주소
    return_address_detail: Optional[str] = None  # 상세주소
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (None 값 제외)"""
        result = {}
        
        if self.address_type is not None:
            result["addressType"] = self.address_type
        if self.company_contact_number is not None:
            result["companyContactNumber"] = self.company_contact_number
        if self.phone_number2 is not None:
            result["phoneNumber2"] = self.phone_number2
        if self.return_zip_code is not None:
            result["returnZipCode"] = self.return_zip_code
        if self.return_address is not None:
            result["returnAddress"] = self.return_address
        if self.return_address_detail is not None:
            result["returnAddressDetail"] = self.return_address_detail
            
        return result


@dataclass
class ReturnCenterUpdateGoodsflowInfo:
    """반품지 수정용 택배사 계약 정보"""
    # 5kg 요금들 (선택사항)
    vendor_credit_fee_05kg: Optional[int] = None  # 5kg 신용요금
    vendor_cash_fee_05kg: Optional[int] = None  # 5kg 선불요금
    consumer_cash_fee_05kg: Optional[int] = None  # 5kg 착불요금
    return_fee_05kg: Optional[int] = None  # 5kg 반품비
    
    # 10kg 요금들 (선택사항)
    vendor_credit_fee_10kg: Optional[int] = None  # 10kg 신용요금
    vendor_cash_fee_10kg: Optional[int] = None  # 10kg 선불요금
    consumer_cash_fee_10kg: Optional[int] = None  # 10kg 착불요금
    return_fee_10kg: Optional[int] = None  # 10kg 반품비
    
    # 20kg 요금들 (선택사항)
    vendor_credit_fee_20kg: Optional[int] = None  # 20kg 신용요금
    vendor_cash_fee_20kg: Optional[int] = None  # 20kg 선불요금
    consumer_cash_fee_20kg: Optional[int] = None  # 20kg 착불요금
    return_fee_20kg: Optional[int] = None  # 20kg 반품비
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (None 값 제외)"""
        result = {}
        
        # 5kg 요금들
        if self.vendor_credit_fee_05kg is not None:
            result["vendorCreditFee05kg"] = str(self.vendor_credit_fee_05kg)
        if self.vendor_cash_fee_05kg is not None:
            result["vendorCashFee05kg"] = str(self.vendor_cash_fee_05kg)
        if self.consumer_cash_fee_05kg is not None:
            result["consumerCashFee05kg"] = str(self.consumer_cash_fee_05kg)
        if self.return_fee_05kg is not None:
            result["returnFee05kg"] = str(self.return_fee_05kg)
            
        # 10kg 요금들
        if self.vendor_credit_fee_10kg is not None:
            result["vendorCreditFee10kg"] = str(self.vendor_credit_fee_10kg)
        if self.vendor_cash_fee_10kg is not None:
            result["vendorCashFee10kg"] = str(self.vendor_cash_fee_10kg)
        if self.consumer_cash_fee_10kg is not None:
            result["consumerCashFee10kg"] = str(self.consumer_cash_fee_10kg)
        if self.return_fee_10kg is not None:
            result["returnFee10kg"] = str(self.return_fee_10kg)
            
        # 20kg 요금들
        if self.vendor_credit_fee_20kg is not None:
            result["vendorCreditFee20kg"] = str(self.vendor_credit_fee_20kg)
        if self.vendor_cash_fee_20kg is not None:
            result["vendorCashFee20kg"] = str(self.vendor_cash_fee_20kg)
        if self.consumer_cash_fee_20kg is not None:
            result["consumerCashFee20kg"] = str(self.consumer_cash_fee_20kg)
        if self.return_fee_20kg is not None:
            result["returnFee20kg"] = str(self.return_fee_20kg)
            
        return result


@dataclass
class ReturnCenterUpdateRequest:
    """반품지 수정 요청 데이터"""
    vendor_id: str  # 판매자 ID (필수)
    return_center_code: str  # 반품지 코드 (필수)
    user_id: str  # 사용자 아이디 (필수)
    shipping_place_name: Optional[str] = None  # 반품지 이름 (선택)
    usable: Optional[bool] = None  # 사용 가능 여부 (선택)
    place_addresses: Optional[List[ReturnCenterUpdateAddress]] = None  # 반품지 주소 목록 (선택)
    goodsflow_info: Optional[ReturnCenterUpdateGoodsflowInfo] = None  # 택배사 정보 (선택)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "vendorId": self.vendor_id,
            "returnCenterCode": self.return_center_code,
            "userId": self.user_id
        }
        
        # 선택 필드들 (None이 아닌 경우만 포함)
        if self.shipping_place_name is not None:
            result["shippingPlaceName"] = self.shipping_place_name
        if self.usable is not None:
            result["usable"] = str(self.usable).lower()  # boolean을 문자열로
        if self.place_addresses is not None:
            result["placeAddresses"] = [addr.to_dict() for addr in self.place_addresses]
        if self.goodsflow_info is not None:
            goodsflow_dict = self.goodsflow_info.to_dict()
            if goodsflow_dict:  # 빈 딕셔너리가 아닌 경우만
                result["goodsflowInfoOpenApiDto"] = goodsflow_dict
                
        return result


@dataclass 
class ReturnCenterDetailAddress:
    """반품지 단건 조회 응답 - 주소 정보"""
    address_type: str  # JIBUN, ROADNAME
    country_code: str  # 국가 코드 (KR)
    company_contact_number: str  # 전화번호
    phone_number2: Optional[str]  # 보조 전화번호
    return_zip_code: str  # 우편번호
    return_address: str  # 주소
    return_address_detail: str  # 상세주소
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenterDetailAddress':
        """딕셔너리에서 객체 생성"""
        return cls(
            address_type=data.get('addressType', ''),
            country_code=data.get('countryCode', ''),
            company_contact_number=data.get('companyContactNumber', ''),
            phone_number2=data.get('phoneNumber2'),
            return_zip_code=data.get('returnZipCode', ''),
            return_address=data.get('returnAddress', ''),
            return_address_detail=data.get('returnAddressDetail', '')
        )


@dataclass
class ReturnCenterDetail:
    """반품지 단건 조회 응답 - 반품지 상세 정보"""
    vendor_id: str  # 업체 코드
    return_center_code: str  # 반품지 센터코드
    shipping_place_name: str  # 반품지 이름
    deliver_code: str  # 택배사 코드
    deliver_name: str  # 택배사명
    goodsflow_status: str  # 굿스플로 상태
    error_message: str  # 에러 메시지
    created_at: int  # 생성일 (timestamp)
    usable: bool  # 사용여부
    
    # 2kg 요금들
    vendor_credit_fee_02kg: int = 0
    vendor_cash_fee_02kg: int = 0
    consumer_cash_fee_02kg: int = 0
    return_fee_02kg: int = 0
    
    # 5kg 요금들
    vendor_credit_fee_05kg: int = 0
    vendor_cash_fee_05kg: int = 0
    consumer_cash_fee_05kg: int = 0
    return_fee_05kg: int = 0
    
    # 10kg 요금들
    vendor_credit_fee_10kg: int = 0
    vendor_cash_fee_10kg: int = 0
    consumer_cash_fee_10kg: int = 0
    return_fee_10kg: int = 0
    
    # 20kg 요금들
    vendor_credit_fee_20kg: int = 0
    vendor_cash_fee_20kg: int = 0
    consumer_cash_fee_20kg: int = 0
    return_fee_20kg: int = 0
    
    place_addresses: List[ReturnCenterDetailAddress] = None  # 반품지 주소 목록
    
    def __post_init__(self):
        if self.place_addresses is None:
            self.place_addresses = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnCenterDetail':
        """딕셔너리에서 객체 생성"""
        place_addresses = [
            ReturnCenterDetailAddress.from_dict(addr) 
            for addr in data.get('placeAddresses', [])
        ]
        
        return cls(
            vendor_id=data.get('vendorId', ''),
            return_center_code=data.get('returnCenterCode', ''),
            shipping_place_name=data.get('shippingPlaceName', ''),
            deliver_code=data.get('deliverCode', ''),
            deliver_name=data.get('deliverName', ''),
            goodsflow_status=data.get('goodsflowStatus', ''),
            error_message=data.get('errorMessage', ''),
            created_at=data.get('createdAt', 0),
            usable=data.get('usable', False),
            
            # 2kg 요금들
            vendor_credit_fee_02kg=data.get('vendorCreditFee02kg', 0),
            vendor_cash_fee_02kg=data.get('vendorCashFee02kg', 0),
            consumer_cash_fee_02kg=data.get('consumerCashFee02kg', 0),
            return_fee_02kg=data.get('returnFee02kg', 0),
            
            # 5kg 요금들
            vendor_credit_fee_05kg=data.get('vendorCreditFee05kg', 0),
            vendor_cash_fee_05kg=data.get('vendorCashFee05kg', 0),
            consumer_cash_fee_05kg=data.get('consumerCashFee05kg', 0),
            return_fee_05kg=data.get('returnFee05kg', 0),
            
            # 10kg 요금들
            vendor_credit_fee_10kg=data.get('vendorCreditFee10kg', 0),
            vendor_cash_fee_10kg=data.get('vendorCashFee10kg', 0),
            consumer_cash_fee_10kg=data.get('consumerCashFee10kg', 0),
            return_fee_10kg=data.get('returnFee10kg', 0),
            
            # 20kg 요금들
            vendor_credit_fee_20kg=data.get('vendorCreditFee20kg', 0),
            vendor_cash_fee_20kg=data.get('vendorCashFee20kg', 0),
            consumer_cash_fee_20kg=data.get('consumerCashFee20kg', 0),
            return_fee_20kg=data.get('returnFee20kg', 0),
            
            place_addresses=place_addresses
        )
    
    def get_created_date_str(self) -> str:
        """생성일을 문자열로 반환"""
        if self.created_at:
            from datetime import datetime
            return datetime.fromtimestamp(self.created_at / 1000).strftime('%Y/%m/%d %H:%M:%S')
        return ""


class ReturnCenterClient:
    """쿠팡 반품지 관리 클라이언트"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    RETURN_CENTER_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/returnShippingCenters"
    RETURN_CENTER_DETAIL_API_PATH = "/v2/providers/openapi/apis/api/v2/return/shipping-places/center-code"
    
    # 지원 택배사 코드
    SUPPORTED_DELIVERY_CODES = {
        # 주요 택배사
        "HYUNDAI": "롯데택배",
        "KGB": "로젠택배", 
        "EPOST": "우체국",
        "HANJIN": "한진택배",
        "CJGLS": "CJ대한통운",
        "KOREX": "대한통운[합병]",
        "ILYANG": "일양택배",
        "KDEXP": "경동택배",
        "CHUNIL": "천일특송",
        "AJOU": "아주택배",
        "CSLOGIS": "SC로지스",
        "DAESIN": "대신택배",
        "CVS": "CVS택배",
        "HDEXP": "합동택배",
        "SLX": "SLX택배",
        "HONAM": "우리택배",
        "BGF": "BGF",
        "SEBANG": "세방택배",
        "NHLOGIS": "농협택배",
        "LOTTEGLOBAL": "롯데글로벌",
        "HILOGIS": "Hi택배",
        
        # 국제택배
        "DHL": "DHL",
        "UPS": "UPS", 
        "FEDEX": "FEDEX",
        "TNT": "TNT",
        "USPS": "USPS",
        "IPARCEL": "i-parcel",
        "EMS": "우체국 EMS",
        "REGISTPOST": "우편등기",
        
        # 전문택배
        "DIRECT": "업체직송",
        "SWGEXP": "성원글로벌",
        "PANTOS": "범한판토스",
        "ACIEXPRESS": "ACI Express",
        "DAEWOON": "대운글로벌",
        "AIRBOY": "에어보이익스프레스",
        "KGLNET": "KGL네트웍스",
        "KUNYOUNG": "건영택배",
        "LINEEXPRESS": "LineExpress",
        "TWOFASTEXP": "2FastsExpress",
        "HPL": "한의사랑택배",
        "GOODSTOLUCK": "굿투럭",
        "KOREXG": "CJ대한통운특",
        "HANDEX": "한덱스",
        "ECMS": "ECMS익스프레스",
        "WONDERS": "원더스퀵",
        "YONGMA": "용마로지스",
        "GSIEXPRESS": "GSI익스프레스",
        "EFS": "EFS",
        "DHLGLOBALMAIL": "DHL GlobalMail",
        "GPSLOGIX": "GPS로직",
        "CRLX": "시알로지텍",
        "BRIDGE": "브리지로지스",
        "HOMEINNOV": "홈이노베이션로지스",
        "CWAY": "씨웨이",
        "GNETWORK": "자이언트",
        "ACEEXP": "ACE Express",
        "WEVILL": "우리동네택배",
        "FOREVERPS": "퍼레버택배",
        "WARPEX": "워펙스",
        "QXPRESS": "큐익스프레스",
        "SMARTLOGIS": "스마트로지스",
        "HOMEPICK": "홈픽택배",
        
        # 특수택배
        "GTSLOGIS": "GTS로지스",
        "ESTHER": "에스더쉬핑",
        "INTRAS": "로토스",
        "EUNHA": "은하쉬핑",
        "UFREIGHT": "유프레이트 코리아",
        "LSERVICE": "엘서비스",
        "TPMLOGIS": "로지스밸리",
        "ZENIELSYSTEM": "제니엘시스템",
        "ANYTRACK": "애니트랙",
        "JLOGIST": "제이로지스트",
        "CHAINLOGIS": "두발히어로(4시간당일택배)",
        "QRUN": "큐런",
        "FRESHSOLUTIONS": "프레시솔루션",
        "HIVECITY": "하이브시티",
        "HANSSEM": "한샘",
        "SFC": "SFC(Santai)",
        "JNET": "J-NET",
        "GENIEGO": "지니고",
        "PANASIA": "판아시아",
        "ELIAN": "elianpost",
        "LOTTECHILSUNG": "롯데칠성",
        "SBGLS": "SBGLS",
        "ALLTAKOREA": "올타코리아",
        "YUNDA": "yunda express",
        "VALEX": "발렉스",
        "KOKUSAI": "국제익스프레스",
        "XINPATEK": "윈핸드해운항공",
        "HEREWEGO": "탱고앤고",
        "WOONGJI": "웅지익스프레스",
        "PINGPONG": "핑퐁",
        "YDH": "YDH",
        "CARGOPLEASE": "화물부탁해",
        "LOGISPOT": "로지스팟",
        "FRESHMATES": "프레시메이트",
        "VROONG": "부릉",
        "NKLS": "NK로지솔루션",
        "DODOFLEX": "도도플렉스",
        "ETOMARS": "이투마스",
        "SHIPNERGY": "배송하기좋은날",
        "VENDORPIA": "벤더피아",
        "COSHIP": "캐나다쉬핑",
        "GDAKOREA": "지디에이코리아",
        "BABABA": "바바바로지스",
        "TEAMFRESH": "팀프레시",
        "HOME1004": "1004홈",
        "NAEUN": "나은물류",
        "ACCCARGO": "acccargo",
        "NTLPS": "엔티엘피스",
        "EKDP": "삼다수가정배송",
        "HOTSINGCARGO": "허싱카고코리아",
        "SINOEX": "SINOTRANS EXPRESS",
        "DRABBIT": "딜리래빗",
        "HOMEPICKTODAY": "홈픽오늘도착",
        "DAERIM": "대림통운",
        "LOGISPARTNER": "로지스파트너",
        "GOBOX": "고박스",
        "FASTBOX": "패스트박스",
        "PANSTAR": "팬스타국제특송",
        "ACTCORE": "에이씨티앤코아물류",
        "KJT": "케이제이티",
        "THEBAO": "더바오",
        "RUSH": "오늘회러쉬",
        "KT": "kt express",
        "IBP": "ibpcorp",
        "HY": "HY",
        "LOGISVALLEY": "로지스밸리",
        "TODAY": "투데이",
        "ONEDAYLOGIS": "라스트마일시스템즈",
        "HKHOLDINGS": "에이치케이홀딩스",
        "JIKGUMOON": "직구문",
        "CUBEFLOW": "큐브플로우",
        "SHFLY": "성훈물류",
        "GBS": "지비에스",
        "BANPOOM": "반품구조대",
        "GLOVIS": "현대글로비스",
        "ARGO": "아르고",
        "JMNP": "딜리박스",
        "SELC": "삼성로지텍",
        "MTINTER": "엠티인터네셔널",
        "GDSP": "골드스넵스",
        "TODAYPICKUP": "오늘의픽업",
        "YJSGLOBAL": "yjs글로벌",
        "DUXGLOBAL": "유로택배",
        "INTERLOGIS": "인터로지스",
        "WOOJIN": "우진인터로지스",
        "GHSPEED": "지에이치스피드",
        "WIDETECH": "와이드테크",
        "ECOHAI": "에코하이",
        "TONAMI": "토나미",
        "DAIICHI": "제1화물",
        "FUKUYAMA": "후쿠야마통운",
        "KURLYNEXTMILE": "컬리넥스트마일",
        "ARAMEX": "ARAMEX",
        "BISNZ": "BISNZ",
        "INNOS": "이노스",
        "SEORIM": "서림물류",
        "WEMOVE": "위무브",
        "POOLATHOME": "풀앳홈",
        "SPARKLE": "스파클직배송",
        "ICS": "ICS",
        "HANMI": "한미포스트",
        "CAINIAO": "CAINIAO",
        "HWATONG": "화통",
        "ESTLA": "이스트라",
        "IK": "IK물류",
        "PULMUONEWATER": "풀무원샘물",
        "TSG": "티에스지로지스",
        "OCS": "ocs코리아",
        "MDLOGIS": "모든로지스",
        "GCS": "지씨에스",
        "FTF": "물류대장LCS",
        "HUBNET": "Hubnet Logistics",
        "WINION_3P": "위니온로지스",
        "WOORIHB": "우리한방택배",
        "LETUS": "레터스",
        "JWTNL": "JWTNL",
        "JCLS": "JCLS",
        "GKGLOBAL": "지케이글로벌",
        "GONELO": "고넬로",
        "DNDN": "든든택배",
        "KGBLS": "KGB로지스",
        "KGBPS": "KGB택배",
        "DONGBU": "드림택배",
        "YELLOW": "옐로우캡",
        "INNOGIS": "GTX로지스",
        "DADREAM": "다드림",
        "IQS": "굿스포스트",
        "SFEXPRESS": "순풍택배",
        "LGE": "LG전자",
        "WINION": "위니온",
        "WINION2": "위니온(에어컨)"
    }
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        반품지 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키  
            vendor_id: 쿠팡 벤더 ID
        """
        self.auth = CoupangAuth(access_key, secret_key, vendor_id)
        
        # SSL 컨텍스트 설정
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def create_return_center(self, request: ReturnCenterRequest) -> Dict[str, Any]:
        """
        반품지 생성
        
        Args:
            request: 반품지 생성 요청 데이터
            
        Returns:
            Dict[str, Any]: 반품지 생성 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 데이터 검증
        self._validate_return_center_request(request)
        
        # API 경로 생성
        api_path = self.RETURN_CENTER_API_PATH.format(vendor_id=request.vendor_id)
        
        # 요청 본문 데이터
        request_data = request.to_dict()
        
        try:
            # 인증 헤더 생성 (POST 요청)
            headers = self.auth.generate_authorization_header("POST", api_path, request_data)
            
            # Content-Type 헤더 추가
            headers["Content-Type"] = "application/json;charset=UTF-8"
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
            # 요청 본문을 JSON으로 변환
            json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            
            # 요청 객체 생성
            req = urllib.request.Request(url, data=json_data, method='POST')
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 검증
            if result.get('code') == '200' or result.get('code') == 200:
                return {
                    "success": True,
                    "returnCenterCode": result.get('data', {}).get('resultMessage', ''),
                    "resultCode": result.get('data', {}).get('resultCode', ''),
                    "message": "반품지 생성 성공",
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get('message', '알 수 없는 오류'),
                    "code": result.get('code'),
                    "originalResponse": result
                }
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                error_message = self._parse_error_message(error_body)
                raise ValueError(f"요청 오류: {error_message}")
            elif e.code == 500:
                raise Exception(f"서버 오류: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def create_domestic_return_center(self, vendor_id: str, user_id: str, shipping_place_name: str,
                                    zip_code: str, address: str, address_detail: str, 
                                    contact_number: str, phone_number2: Optional[str] = None,
                                    delivery_code: str = "CJGLS", contract_number: str = "",
                                    contract_customer_number: str = "",
                                    vendor_credit_fee: int = 2500, vendor_cash_fee: int = 2500,
                                    consumer_cash_fee: int = 2500, return_fee: int = 2500) -> Dict[str, Any]:
        """
        국내 반품지 생성 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            user_id: 사용자 ID
            shipping_place_name: 반품지 이름
            zip_code: 우편번호
            address: 주소
            address_detail: 상세주소
            contact_number: 연락처
            phone_number2: 보조 연락처 (선택)
            delivery_code: 택배사 코드 (기본: CJGLS)
            contract_number: 택배사 계약코드
            contract_customer_number: 업체코드 (우체국만)
            vendor_credit_fee: 판매자 신용요금 (모든 중량 동일)
            vendor_cash_fee: 판매자 선불요금 (모든 중량 동일)
            consumer_cash_fee: 구매자 착불요금 (모든 중량 동일)  
            return_fee: 반품비 (모든 중량 동일)
            
        Returns:
            Dict[str, Any]: 반품지 생성 결과
        """
        # 반품지 주소 생성
        place_address = ReturnPlaceAddress(
            address_type="JIBUN",
            company_contact_number=contact_number,
            phone_number2=phone_number2,
            return_zip_code=zip_code,
            return_address=address,
            return_address_detail=address_detail
        )
        
        # 택배사 정보 생성 (모든 중량 동일 요금)
        goodsflow_info = GoodsflowInfo(
            deliver_code=delivery_code,
            deliver_name=self.SUPPORTED_DELIVERY_CODES.get(delivery_code),
            contract_number=contract_number,
            contract_customer_number=contract_customer_number,
            vendor_credit_fee_05kg=vendor_credit_fee,
            vendor_credit_fee_10kg=vendor_credit_fee,
            vendor_credit_fee_20kg=vendor_credit_fee,
            vendor_cash_fee_05kg=vendor_cash_fee,
            vendor_cash_fee_10kg=vendor_cash_fee,
            vendor_cash_fee_20kg=vendor_cash_fee,
            consumer_cash_fee_05kg=consumer_cash_fee,
            consumer_cash_fee_10kg=consumer_cash_fee,
            consumer_cash_fee_20kg=consumer_cash_fee,
            return_fee_05kg=return_fee,
            return_fee_10kg=return_fee,
            return_fee_20kg=return_fee
        )
        
        # 반품지 생성 요청
        request = ReturnCenterRequest(
            vendor_id=vendor_id,
            user_id=user_id,
            shipping_place_name=shipping_place_name,
            goodsflow_info=goodsflow_info,
            place_addresses=[place_address]
        )
        
        return self.create_return_center(request)
    
    def get_supported_delivery_codes(self) -> Dict[str, str]:
        """
        지원하는 택배사 코드 목록 반환
        
        Returns:
            Dict[str, str]: {코드: 택배사명} 딕셔너리
        """
        return self.SUPPORTED_DELIVERY_CODES.copy()
    
    def _validate_return_center_request(self, request: ReturnCenterRequest) -> None:
        """반품지 생성 요청 데이터 검증"""
        
        # 필수 필드 검증
        if not request.vendor_id:
            raise ValueError("vendor_id는 필수입니다")
        
        if not request.user_id:
            raise ValueError("user_id는 필수입니다")
        
        if not request.shipping_place_name or not request.shipping_place_name.strip():
            raise ValueError("shipping_place_name는 필수입니다")
        
        if len(request.shipping_place_name) > 100:
            raise ValueError("반품지 이름은 100자를 초과할 수 없습니다")
        
        # 주소 정보 검증
        if not request.place_addresses or len(request.place_addresses) == 0:
            raise ValueError("최소 1개 이상의 주소 정보가 필요합니다")
        
        for i, addr in enumerate(request.place_addresses):
            self._validate_return_place_address(addr, f"주소 {i+1}")
        
        # 택배사 정보 검증
        self._validate_goodsflow_info(request.goodsflow_info)
    
    def _validate_return_place_address(self, addr: ReturnPlaceAddress, context: str = "") -> None:
        """반품지 주소 정보 검증"""
        prefix = f"{context}: " if context else ""
        
        # 주소 타입 검증
        valid_address_types = ["JIBUN", "ROADNAME"]
        if addr.address_type not in valid_address_types:
            raise ValueError(f"{prefix}주소 타입은 {valid_address_types} 중 하나여야 합니다")
        
        # 전화번호 검증
        if not addr.company_contact_number or not addr.company_contact_number.strip():
            raise ValueError(f"{prefix}전화번호는 필수입니다")
        
        if not self._validate_phone_number(addr.company_contact_number):
            raise ValueError(f"{prefix}전화번호 형식이 올바르지 않습니다 (xx-yyy-zzzz)")
        
        # 보조 전화번호 검증 (선택사항)
        if addr.phone_number2 and not self._validate_phone_number(addr.phone_number2):
            raise ValueError(f"{prefix}보조 전화번호 형식이 올바르지 않습니다")
        
        # 우편번호 검증
        if not addr.return_zip_code or not addr.return_zip_code.strip():
            raise ValueError(f"{prefix}우편번호는 필수입니다")
        
        if not addr.return_zip_code.isdigit() or len(addr.return_zip_code) < 5 or len(addr.return_zip_code) > 6:
            raise ValueError(f"{prefix}우편번호는 5-6자리 숫자여야 합니다")
        
        # 주소 검증
        if not addr.return_address or not addr.return_address.strip():
            raise ValueError(f"{prefix}주소는 필수입니다")
        
        if len(addr.return_address) > 150:
            raise ValueError(f"{prefix}주소는 150자를 초과할 수 없습니다")
        
        # 상세주소 검증
        if len(addr.return_address_detail) > 200:
            raise ValueError(f"{prefix}상세주소는 200자를 초과할 수 없습니다")
    
    def _validate_goodsflow_info(self, goodsflow: GoodsflowInfo) -> None:
        """택배사 정보 검증"""
        
        # 택배사 코드 검증
        if not goodsflow.deliver_code or not goodsflow.deliver_code.strip():
            raise ValueError("택배사 코드는 필수입니다")
        
        if goodsflow.deliver_code not in self.SUPPORTED_DELIVERY_CODES:
            supported_codes = list(self.SUPPORTED_DELIVERY_CODES.keys())
            raise ValueError(f"지원하지 않는 택배사 코드입니다. 지원 코드: {supported_codes}")
        
        # 우체국 택배인 경우 업체코드 필수
        if goodsflow.deliver_code == "EPOST" and not goodsflow.contract_customer_number:
            raise ValueError("우체국 택배 이용시 업체코드(contract_customer_number)는 필수입니다")
        
        # 요금 검증 (모든 요금은 0보다 커야 함)
        fee_fields = [
            ("vendor_credit_fee_05kg", goodsflow.vendor_credit_fee_05kg),
            ("vendor_credit_fee_10kg", goodsflow.vendor_credit_fee_10kg),
            ("vendor_credit_fee_20kg", goodsflow.vendor_credit_fee_20kg),
            ("vendor_cash_fee_05kg", goodsflow.vendor_cash_fee_05kg),
            ("vendor_cash_fee_10kg", goodsflow.vendor_cash_fee_10kg),
            ("vendor_cash_fee_20kg", goodsflow.vendor_cash_fee_20kg),
            ("consumer_cash_fee_05kg", goodsflow.consumer_cash_fee_05kg),
            ("consumer_cash_fee_10kg", goodsflow.consumer_cash_fee_10kg),
            ("consumer_cash_fee_20kg", goodsflow.consumer_cash_fee_20kg),
            ("return_fee_05kg", goodsflow.return_fee_05kg),
            ("return_fee_10kg", goodsflow.return_fee_10kg),
            ("return_fee_20kg", goodsflow.return_fee_20kg)
        ]
        
        for field_name, fee_value in fee_fields:
            if fee_value < 0:
                raise ValueError(f"{field_name}은 0 이상이어야 합니다")
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """전화번호 형식 검증 (xx-yyy-zzzz)"""
        if not phone_number:
            return False
        
        # 전체 길이 검증 (9-13자)
        if len(phone_number) < 9 or len(phone_number) > 13:
            return False
        
        # '-' 포함 여부 및 형식 검증
        if '-' not in phone_number:
            return False
        
        parts = phone_number.split('-')
        if len(parts) != 3:
            return False
        
        x, y, z = parts
        
        # 각 부분이 숫자인지 검증
        if not (x.isdigit() and y.isdigit() and z.isdigit()):
            return False
        
        # 길이 검증
        if not (2 <= len(x) <= 4):  # x: 2-4자
            return False
        if not (3 <= len(y) <= 4):  # y: 3-4자
            return False
        if len(z) != 4:  # z: 4자
            return False
        
        return True
    
    def get_return_centers(self, vendor_id: str, page_num: int = 1, page_size: int = 10) -> ReturnCenterListResponse:
        """
        반품지 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            page_num: 페이지 번호 (1부터 시작)
            page_size: 페이지당 데이터 수 (1-100)
            
        Returns:
            ReturnCenterListResponse: 반품지 목록 및 페이징 정보
            
        Raises:
            ValueError: 잘못된 요청 파라미터
            Exception: API 호출 오류
        """
        # 파라미터 검증
        if not vendor_id or not vendor_id.strip():
            raise ValueError("vendor_id는 필수입니다")
        
        if page_num < 1:
            raise ValueError("page_num은 1 이상이어야 합니다")
        
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size는 1-100 사이여야 합니다")
        
        # API 경로 생성
        api_path = self.RETURN_CENTER_API_PATH.format(vendor_id=vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = {
            "pageNum": str(page_num),
            "pageSize": str(page_size)
        }
        
        query_string = urllib.parse.urlencode(query_params)
        api_path_with_query = f"{api_path}?{query_string}"
        
        try:
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", api_path_with_query)
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path_with_query}"
            
            # 요청 객체 생성
            req = urllib.request.Request(url, method='GET')
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 검증 및 데이터 파싱
            if result.get('code') == '200' or result.get('code') == 200:
                data = result.get('data', {})
                return ReturnCenterListResponse.from_dict(data)
            else:
                raise Exception(f"API 오류: {result.get('message', '알 수 없는 오류')}")
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                error_message = self._parse_error_message(error_body)
                raise ValueError(f"요청 오류: {error_message}")
            elif e.code == 404:
                raise Exception(f"반품지를 찾을 수 없습니다: {error_body}")
            elif e.code == 500:
                raise Exception(f"서버 오류: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def get_all_return_centers(self, vendor_id: str, page_size: int = 50) -> List[ReturnCenter]:
        """
        모든 반품지 목록 조회 (페이징 처리 자동)
        
        Args:
            vendor_id: 판매자 ID
            page_size: 페이지당 데이터 수 (기본: 50)
            
        Returns:
            List[ReturnCenter]: 모든 반품지 목록
        """
        all_centers = []
        page_num = 1
        
        while True:
            response = self.get_return_centers(vendor_id, page_num, page_size)
            all_centers.extend(response.content)
            
            # 마지막 페이지인지 확인
            if page_num >= response.pagination.total_pages:
                break
                
            page_num += 1
        
        return all_centers
    
    def find_return_center_by_name(self, vendor_id: str, shipping_place_name: str) -> Optional[ReturnCenter]:
        """
        반품지명으로 반품지 검색
        
        Args:
            vendor_id: 판매자 ID
            shipping_place_name: 반품지명
            
        Returns:
            Optional[ReturnCenter]: 찾은 반품지 (없으면 None)
        """
        all_centers = self.get_all_return_centers(vendor_id)
        
        for center in all_centers:
            if center.shipping_place_name == shipping_place_name:
                return center
                
        return None
    
    def find_return_center_by_code(self, vendor_id: str, return_center_code: str) -> Optional[ReturnCenter]:
        """
        반품지 코드로 반품지 검색
        
        Args:
            vendor_id: 판매자 ID
            return_center_code: 반품지 센터 코드
            
        Returns:
            Optional[ReturnCenter]: 찾은 반품지 (없으면 None)
        """
        all_centers = self.get_all_return_centers(vendor_id)
        
        for center in all_centers:
            if center.return_center_code == return_center_code:
                return center
                
        return None
    
    def get_usable_return_centers(self, vendor_id: str) -> List[ReturnCenter]:
        """
        사용 가능한 반품지 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            
        Returns:
            List[ReturnCenter]: 사용 가능한 반품지 목록
        """
        all_centers = self.get_all_return_centers(vendor_id)
        return [center for center in all_centers if center.usable]
    
    def get_return_centers_by_delivery_code(self, vendor_id: str, delivery_code: str) -> List[ReturnCenter]:
        """
        택배사별 반품지 목록 조회
        
        Args:
            vendor_id: 판매자 ID
            delivery_code: 택배사 코드
            
        Returns:
            List[ReturnCenter]: 해당 택배사의 반품지 목록
        """
        all_centers = self.get_all_return_centers(vendor_id)
        return [center for center in all_centers if center.deliver_code == delivery_code]

    def update_return_center(self, request: ReturnCenterUpdateRequest) -> Dict[str, Any]:
        """
        반품지 수정
        
        Args:
            request: 반품지 수정 요청 데이터
            
        Returns:
            Dict[str, Any]: 반품지 수정 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 데이터 검증
        self._validate_return_center_update_request(request)
        
        # API 경로 생성 (반품지 코드 포함)
        api_path = f"{self.RETURN_CENTER_API_PATH.format(vendor_id=request.vendor_id)}/{request.return_center_code}"
        
        # 요청 본문 데이터
        request_data = request.to_dict()
        
        try:
            # 인증 헤더 생성 (PUT 요청)
            headers = self.auth.generate_authorization_header("PUT", api_path, request_data)
            
            # Content-Type 헤더 추가
            headers["Content-Type"] = "application/json;charset=UTF-8"
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
            # 요청 본문을 JSON으로 변환
            json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            
            # 요청 객체 생성
            req = urllib.request.Request(url, data=json_data, method='PUT')
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 검증
            if result.get('code') == '200' or result.get('code') == 200:
                data = result.get('data', {})
                return {
                    "success": True,
                    "resultCode": data.get('resultCode', ''),
                    "resultMessage": data.get('resultMessage', ''),
                    "message": "반품지 수정 성공",
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get('message', '알 수 없는 오류'),
                    "code": result.get('code'),
                    "originalResponse": result
                }
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                error_message = self._parse_error_message(error_body)
                raise ValueError(f"요청 오류: {error_message}")
            elif e.code == 404:
                raise Exception(f"반품지를 찾을 수 없습니다: {error_body}")
            elif e.code == 500:
                raise Exception(f"서버 오류: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def update_return_center_name(self, vendor_id: str, return_center_code: str, user_id: str, 
                                new_name: str) -> Dict[str, Any]:
        """
        반품지명만 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            return_center_code: 반품지 코드
            user_id: 사용자 ID
            new_name: 새로운 반품지명
            
        Returns:
            Dict[str, Any]: 반품지 수정 결과
        """
        request = ReturnCenterUpdateRequest(
            vendor_id=vendor_id,
            return_center_code=return_center_code,
            user_id=user_id,
            shipping_place_name=new_name
        )
        
        return self.update_return_center(request)
    
    def update_return_center_usable(self, vendor_id: str, return_center_code: str, user_id: str,
                                  usable: bool) -> Dict[str, Any]:
        """
        반품지 사용여부만 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            return_center_code: 반품지 코드
            user_id: 사용자 ID
            usable: 사용여부 (True: 사용, False: 사용안함)
            
        Returns:
            Dict[str, Any]: 반품지 수정 결과
        """
        request = ReturnCenterUpdateRequest(
            vendor_id=vendor_id,
            return_center_code=return_center_code,
            user_id=user_id,
            usable=usable
        )
        
        return self.update_return_center(request)
    
    def update_return_center_address(self, vendor_id: str, return_center_code: str, user_id: str,
                                   zip_code: str, address: str, address_detail: str, 
                                   contact_number: str, phone_number2: Optional[str] = None,
                                   address_type: str = "JIBUN") -> Dict[str, Any]:
        """
        반품지 주소만 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            return_center_code: 반품지 코드
            user_id: 사용자 ID
            zip_code: 우편번호
            address: 주소
            address_detail: 상세주소
            contact_number: 연락처
            phone_number2: 보조 연락처 (선택)
            address_type: 주소 타입 (기본: JIBUN)
            
        Returns:
            Dict[str, Any]: 반품지 수정 결과
        """
        update_address = ReturnCenterUpdateAddress(
            address_type=address_type,
            company_contact_number=contact_number,
            phone_number2=phone_number2,
            return_zip_code=zip_code,
            return_address=address,
            return_address_detail=address_detail
        )
        
        request = ReturnCenterUpdateRequest(
            vendor_id=vendor_id,
            return_center_code=return_center_code,
            user_id=user_id,
            place_addresses=[update_address]
        )
        
        return self.update_return_center(request)
    
    def update_return_center_fees(self, vendor_id: str, return_center_code: str, user_id: str,
                                vendor_credit_fee: Optional[int] = None,
                                vendor_cash_fee: Optional[int] = None,
                                consumer_cash_fee: Optional[int] = None,
                                return_fee: Optional[int] = None) -> Dict[str, Any]:
        """
        반품지 요금만 수정하는 편의 메서드 (모든 중량 동일)
        
        Args:
            vendor_id: 판매자 ID
            return_center_code: 반품지 코드
            user_id: 사용자 ID
            vendor_credit_fee: 판매자 신용요금 (모든 중량 적용)
            vendor_cash_fee: 판매자 선불요금 (모든 중량 적용)
            consumer_cash_fee: 구매자 착불요금 (모든 중량 적용)
            return_fee: 반품비 (모든 중량 적용)
            
        Returns:
            Dict[str, Any]: 반품지 수정 결과
        """
        goodsflow_info = ReturnCenterUpdateGoodsflowInfo()
        
        # 모든 중량에 동일 요금 적용
        if vendor_credit_fee is not None:
            goodsflow_info.vendor_credit_fee_05kg = vendor_credit_fee
            goodsflow_info.vendor_credit_fee_10kg = vendor_credit_fee
            goodsflow_info.vendor_credit_fee_20kg = vendor_credit_fee
            
        if vendor_cash_fee is not None:
            goodsflow_info.vendor_cash_fee_05kg = vendor_cash_fee
            goodsflow_info.vendor_cash_fee_10kg = vendor_cash_fee
            goodsflow_info.vendor_cash_fee_20kg = vendor_cash_fee
            
        if consumer_cash_fee is not None:
            goodsflow_info.consumer_cash_fee_05kg = consumer_cash_fee
            goodsflow_info.consumer_cash_fee_10kg = consumer_cash_fee
            goodsflow_info.consumer_cash_fee_20kg = consumer_cash_fee
            
        if return_fee is not None:
            goodsflow_info.return_fee_05kg = return_fee
            goodsflow_info.return_fee_10kg = return_fee
            goodsflow_info.return_fee_20kg = return_fee
        
        request = ReturnCenterUpdateRequest(
            vendor_id=vendor_id,
            return_center_code=return_center_code,
            user_id=user_id,
            goodsflow_info=goodsflow_info
        )
        
        return self.update_return_center(request)

    def get_return_center_details(self, return_center_codes: Union[str, List[str]]) -> List[ReturnCenterDetail]:
        """
        반품지 센터코드로 반품지 상세 정보 조회 (단건/다건)
        
        Args:
            return_center_codes: 반품지 센터코드 (문자열 또는 리스트, 최대 100개)
            
        Returns:
            List[ReturnCenterDetail]: 반품지 상세 정보 목록
            
        Raises:
            ValueError: 잘못된 요청 파라미터
            Exception: API 호출 오류
        """
        # 파라미터 검증 및 변환
        if isinstance(return_center_codes, str):
            codes_list = [return_center_codes]
            codes_str = return_center_codes
        elif isinstance(return_center_codes, list):
            if not return_center_codes:
                raise ValueError("return_center_codes가 빈 목록입니다")
            if len(return_center_codes) > 100:
                raise ValueError("return_center_codes는 최대 100개까지 조회 가능합니다")
            codes_list = return_center_codes
            codes_str = ",".join(str(code) for code in return_center_codes)
        else:
            raise ValueError("return_center_codes는 문자열 또는 리스트여야 합니다")
        
        # 빈 코드 검증
        for code in codes_list:
            if not str(code).strip():
                raise ValueError("반품지 센터코드가 빈 값입니다")
        
        # 쿼리 파라미터 생성
        query_params = {"returnCenterCodes": codes_str}
        query_string = urllib.parse.urlencode(query_params)
        api_path_with_query = f"{self.RETURN_CENTER_DETAIL_API_PATH}?{query_string}"
        
        try:
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", api_path_with_query)
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path_with_query}"
            
            # 요청 객체 생성
            req = urllib.request.Request(url, method='GET')
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 검증 및 데이터 파싱
            if result.get('code') == '200' or result.get('code') == 200:
                data_list = result.get('data', [])
                return [ReturnCenterDetail.from_dict(item) for item in data_list]
            else:
                raise Exception(f"API 오류: {result.get('message', '알 수 없는 오류')}")
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                error_message = self._parse_error_message(error_body)
                raise ValueError(f"요청 오류: {error_message}")
            elif e.code == 404:
                raise Exception(f"반품지를 찾을 수 없습니다: {error_body}")
            elif e.code == 500:
                raise Exception(f"서버 오류: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def get_return_center_detail(self, return_center_code: str) -> Optional[ReturnCenterDetail]:
        """
        반품지 센터코드로 단건 반품지 상세 정보 조회
        
        Args:
            return_center_code: 반품지 센터코드
            
        Returns:
            Optional[ReturnCenterDetail]: 반품지 상세 정보 (없으면 None)
        """
        details = self.get_return_center_details(return_center_code)
        return details[0] if details else None
    
    def get_multiple_return_center_details(self, return_center_codes: List[str]) -> List[ReturnCenterDetail]:
        """
        여러 반품지 센터코드로 다건 반품지 상세 정보 조회
        
        Args:
            return_center_codes: 반품지 센터코드 목록 (최대 100개)
            
        Returns:
            List[ReturnCenterDetail]: 반품지 상세 정보 목록
        """
        return self.get_return_center_details(return_center_codes)
    
    def get_return_center_details_by_chunks(self, return_center_codes: List[str], 
                                          chunk_size: int = 50) -> List[ReturnCenterDetail]:
        """
        대량의 반품지 센터코드를 청크 단위로 나누어 조회
        
        Args:
            return_center_codes: 반품지 센터코드 목록
            chunk_size: 청크 크기 (기본: 50, 최대: 100)
            
        Returns:
            List[ReturnCenterDetail]: 모든 반품지 상세 정보 목록
        """
        if chunk_size > 100:
            chunk_size = 100
            
        all_details = []
        
        # 청크 단위로 나누어 조회
        for i in range(0, len(return_center_codes), chunk_size):
            chunk_codes = return_center_codes[i:i + chunk_size]
            chunk_details = self.get_return_center_details(chunk_codes)
            all_details.extend(chunk_details)
        
        return all_details

    def _validate_return_center_update_request(self, request: ReturnCenterUpdateRequest) -> None:
        """반품지 수정 요청 데이터 검증"""
        
        # 필수 필드 검증
        if not request.vendor_id:
            raise ValueError("vendor_id는 필수입니다")
        
        if not request.return_center_code:
            raise ValueError("return_center_code는 필수입니다")
        
        if not request.user_id:
            raise ValueError("user_id는 필수입니다")
        
        # 반품지명 검증 (입력된 경우만)
        if request.shipping_place_name is not None:
            if not request.shipping_place_name.strip():
                raise ValueError("shipping_place_name이 빈 문자열입니다")
            if len(request.shipping_place_name) > 100:
                raise ValueError("반품지 이름은 100자를 초과할 수 없습니다")
        
        # 주소 정보 검증 (입력된 경우만)
        if request.place_addresses is not None:
            if len(request.place_addresses) == 0:
                raise ValueError("place_addresses가 빈 목록입니다")
            
            for i, addr in enumerate(request.place_addresses):
                self._validate_return_center_update_address(addr, f"주소 {i+1}")
        
        # 택배사 정보 검증 (입력된 경우만)
        if request.goodsflow_info is not None:
            self._validate_return_center_update_goodsflow_info(request.goodsflow_info)
    
    def _validate_return_center_update_address(self, addr: ReturnCenterUpdateAddress, context: str = "") -> None:
        """반품지 수정 주소 정보 검증"""
        prefix = f"{context}: " if context else ""
        
        # 주소 타입 검증 (입력된 경우만)
        if addr.address_type is not None:
            valid_address_types = ["JIBUN", "ROADNAME"]
            if addr.address_type not in valid_address_types:
                raise ValueError(f"{prefix}주소 타입은 {valid_address_types} 중 하나여야 합니다")
        
        # 전화번호 검증 (입력된 경우만)
        if addr.company_contact_number is not None:
            if not addr.company_contact_number.strip():
                raise ValueError(f"{prefix}전화번호가 빈 문자열입니다")
            if not self._validate_phone_number(addr.company_contact_number):
                raise ValueError(f"{prefix}전화번호 형식이 올바르지 않습니다 (xx-yyy-zzzz)")
        
        # 보조 전화번호 검증 (입력된 경우만)
        if addr.phone_number2 is not None and addr.phone_number2.strip():
            if not self._validate_phone_number(addr.phone_number2):
                raise ValueError(f"{prefix}보조 전화번호 형식이 올바르지 않습니다")
        
        # 우편번호 검증 (입력된 경우만)
        if addr.return_zip_code is not None:
            if not addr.return_zip_code.strip():
                raise ValueError(f"{prefix}우편번호가 빈 문자열입니다")
            if not addr.return_zip_code.isdigit() or len(addr.return_zip_code) < 5 or len(addr.return_zip_code) > 6:
                raise ValueError(f"{prefix}우편번호는 5-6자리 숫자여야 합니다")
        
        # 주소 검증 (입력된 경우만)
        if addr.return_address is not None:
            if not addr.return_address.strip():
                raise ValueError(f"{prefix}주소가 빈 문자열입니다")
            if len(addr.return_address) > 150:
                raise ValueError(f"{prefix}주소는 150자를 초과할 수 없습니다")
        
        # 상세주소 검증 (입력된 경우만)
        if addr.return_address_detail is not None:
            if len(addr.return_address_detail) > 200:
                raise ValueError(f"{prefix}상세주소는 200자를 초과할 수 없습니다")
    
    def _validate_return_center_update_goodsflow_info(self, goodsflow: ReturnCenterUpdateGoodsflowInfo) -> None:
        """반품지 수정용 택배사 정보 검증"""
        
        # 요금 검증 (입력된 경우만, 모든 요금은 0 이상이어야 함)
        fee_fields = [
            ("vendor_credit_fee_05kg", goodsflow.vendor_credit_fee_05kg),
            ("vendor_credit_fee_10kg", goodsflow.vendor_credit_fee_10kg),
            ("vendor_credit_fee_20kg", goodsflow.vendor_credit_fee_20kg),
            ("vendor_cash_fee_05kg", goodsflow.vendor_cash_fee_05kg),
            ("vendor_cash_fee_10kg", goodsflow.vendor_cash_fee_10kg),
            ("vendor_cash_fee_20kg", goodsflow.vendor_cash_fee_20kg),
            ("consumer_cash_fee_05kg", goodsflow.consumer_cash_fee_05kg),
            ("consumer_cash_fee_10kg", goodsflow.consumer_cash_fee_10kg),
            ("consumer_cash_fee_20kg", goodsflow.consumer_cash_fee_20kg),
            ("return_fee_05kg", goodsflow.return_fee_05kg),
            ("return_fee_10kg", goodsflow.return_fee_10kg),
            ("return_fee_20kg", goodsflow.return_fee_20kg)
        ]
        
        for field_name, fee_value in fee_fields:
            if fee_value is not None and fee_value < 0:
                raise ValueError(f"{field_name}은 0 이상이어야 합니다")

    def _parse_error_message(self, error_body: str) -> str:
        """오류 응답에서 메시지 파싱"""
        try:
            error_data = json.loads(error_body)
            return error_data.get('message', error_body)
        except:
            return error_body