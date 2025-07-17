#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 출고지 관리 클라이언트
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
class PlaceAddress:
    """출고지 주소 정보"""
    address_type: str  # JIBUN, ROADNAME, OVERSEA
    country_code: str  # 국가 코드 (예: "KR")
    company_contact_number: str  # 전화번호
    phone_number2: Optional[str] = None  # 보조 전화번호
    return_zip_code: str = ""  # 우편번호
    return_address: str = ""  # 주소
    return_address_detail: str = ""  # 상세주소
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "addressType": self.address_type,
            "countryCode": self.country_code,
            "companyContactNumber": self.company_contact_number,
            "returnZipCode": self.return_zip_code,
            "returnAddress": self.return_address,
            "returnAddressDetail": self.return_address_detail
        }
        
        if self.phone_number2:
            result["phoneNumber2"] = self.phone_number2
            
        return result


@dataclass
class RemoteInfo:
    """도서산간 추가배송비 정보"""
    delivery_code: str  # 택배사 코드
    jeju: int  # 제주 지역 배송비
    not_jeju: int  # 제주 외 지역 배송비
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "deliveryCode": self.delivery_code,
            "jeju": str(self.jeju),
            "notJeju": str(self.not_jeju)
        }


@dataclass
class RemoteInfoUpdate:
    """출고지 수정용 도서산간 배송비 정보"""
    delivery_code: str  # 택배사 코드
    jeju: int  # 제주 지역 배송비
    not_jeju: int  # 제주 외 지역 배송비
    usable: bool = True  # 사용여부
    remote_info_id: Optional[int] = None  # 기존 배송정보 ID (수정/삭제시 필요)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "deliveryCode": self.delivery_code,
            "jeju": self.jeju,
            "notJeju": self.not_jeju,
            "usable": self.usable
        }
        
        # 기존 배송정보 수정/삭제시에만 remote_info_id 포함
        if self.remote_info_id is not None:
            result["remoteInfoId"] = self.remote_info_id
            
        return result


@dataclass
class ShippingCenterRequest:
    """출고지 생성 요청 데이터"""
    vendor_id: str  # 판매자 ID
    user_id: str  # 사용자 아이디
    shipping_place_name: str  # 출고지 이름
    place_addresses: List[PlaceAddress]  # 출고지 주소 목록
    remote_infos: List[RemoteInfo]  # 도서산간 배송비 정보
    usable: bool = True  # 사용가능여부
    global_shipping: bool = False  # 국내/해외 여부
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "vendorId": self.vendor_id,
            "userId": self.user_id,
            "shippingPlaceName": self.shipping_place_name,
            "global": str(self.global_shipping).lower(),
            "usable": str(self.usable).lower(),
            "placeAddresses": [addr.to_dict() for addr in self.place_addresses],
            "remoteInfos": [info.to_dict() for info in self.remote_infos]
        }


@dataclass
class ShippingCenterUpdateRequest:
    """출고지 수정 요청 데이터"""
    vendor_id: str  # 판매자 ID
    user_id: str  # 사용자 아이디
    outbound_shipping_place_code: int  # 출고지 코드
    place_addresses: List[PlaceAddress]  # 출고지 주소 목록
    remote_infos: List[RemoteInfoUpdate]  # 도서산간 배송비 정보 (수정용)
    shipping_place_name: Optional[str] = None  # 출고지 이름 (null이면 변경안함)
    usable: Optional[bool] = None  # 사용가능여부
    global_shipping: Optional[bool] = None  # 국내/해외 여부 (변경 불가능, 참고용)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "vendorId": self.vendor_id,
            "userId": self.user_id,
            "outboundShippingPlaceCode": self.outbound_shipping_place_code,
            "placeAddresses": [addr.to_dict() for addr in self.place_addresses],
            "remoteInfos": [info.to_dict() for info in self.remote_infos]
        }
        
        # 선택적 필드들 (null이면 포함하지 않음)
        if self.shipping_place_name is not None:
            result["shippingPlaceName"] = self.shipping_place_name
            
        if self.usable is not None:
            result["usable"] = self.usable
            
        if self.global_shipping is not None:
            result["global"] = str(self.global_shipping).lower()
            
        return result


@dataclass
class ShippingPlaceAddress:
    """출고지 조회 응답 - 주소 정보"""
    address_type: str  # JIBUN, ROADNAME, OVERSEA
    country_code: str  # 국가 코드
    company_contact_number: str  # 전화번호
    phone_number2: Optional[str]  # 보조 전화번호
    return_zip_code: str  # 우편번호
    return_address: str  # 주소
    return_address_detail: str  # 상세주소
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingPlaceAddress':
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
class ShippingPlaceRemoteInfo:
    """출고지 조회 응답 - 도서산간 배송 정보"""
    remote_info_id: int  # 도서산간 배송정보 ID
    delivery_code: str  # 택배사 코드
    jeju: int  # 제주 지역 배송비
    not_jeju: int  # 제주 외 지역 배송비
    usable: bool  # 도서산간 배송정보 유효여부
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingPlaceRemoteInfo':
        """딕셔너리에서 객체 생성"""
        return cls(
            remote_info_id=data.get('remoteInfoId', 0),
            delivery_code=data.get('deliveryCode', ''),
            jeju=data.get('jeju', 0),
            not_jeju=data.get('notJeju', 0),
            usable=data.get('usable', False)
        )


@dataclass
class ShippingPlace:
    """출고지 조회 응답 - 출고지 정보"""
    outbound_shipping_place_code: int  # 출고지 코드
    shipping_place_name: str  # 출고지 이름
    create_date: str  # 생성일 (YYYY/MM/DD)
    place_addresses: List[ShippingPlaceAddress]  # 출고지 주소 목록
    remote_infos: List[ShippingPlaceRemoteInfo]  # 도서산간 배송정보 목록
    usable: bool  # 사용가능 여부
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingPlace':
        """딕셔너리에서 객체 생성"""
        place_addresses = [
            ShippingPlaceAddress.from_dict(addr) 
            for addr in data.get('placeAddresses', [])
        ]
        
        remote_infos = [
            ShippingPlaceRemoteInfo.from_dict(info) 
            for info in data.get('remoteInfos', [])
        ]
        
        return cls(
            outbound_shipping_place_code=data.get('outboundShippingPlaceCode', 0),
            shipping_place_name=data.get('shippingPlaceName', ''),
            create_date=data.get('createDate', ''),
            place_addresses=place_addresses,
            remote_infos=remote_infos,
            usable=data.get('usable', False)
        )


@dataclass
class ShippingPlacePagination:
    """출고지 조회 응답 - 페이징 정보"""
    current_page: int  # 현재 페이지
    total_pages: int  # 전체 페이지 수
    total_elements: int  # 전체 데이터 수
    count_per_page: int  # 페이지별 데이터 수
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingPlacePagination':
        """딕셔너리에서 객체 생성"""
        return cls(
            current_page=data.get('currentPage', 1),
            total_pages=data.get('totalPages', 1),
            total_elements=data.get('totalElements', 0),
            count_per_page=data.get('countPerPage', 10)
        )


@dataclass
class ShippingPlaceListResponse:
    """출고지 목록 조회 응답"""
    content: List[ShippingPlace]  # 출고지 목록
    pagination: ShippingPlacePagination  # 페이징 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingPlaceListResponse':
        """딕셔너리에서 객체 생성"""
        content = [
            ShippingPlace.from_dict(place_data) 
            for place_data in data.get('content', [])
        ]
        
        pagination = ShippingPlacePagination.from_dict(data.get('pagination', {}))
        
        return cls(content=content, pagination=pagination)


class ShippingCenterClient:
    """쿠팡 출고지 관리 클라이언트"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    SHIPPING_CENTER_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/outboundShippingCenters"
    SHIPPING_PLACE_QUERY_API_PATH = "/v2/providers/marketplace_openapi/apis/api/v1/vendor/shipping-place/outbound"
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        출고지 클라이언트 초기화
        
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
    
    def create_shipping_center(self, request: ShippingCenterRequest) -> Dict[str, Any]:
        """
        출고지 생성
        
        Args:
            request: 출고지 생성 요청 데이터
            
        Returns:
            Dict[str, Any]: 출고지 생성 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 데이터 검증
        self._validate_shipping_center_request(request)
        
        # API 경로 생성
        api_path = self.SHIPPING_CENTER_API_PATH.format(vendor_id=request.vendor_id)
        
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
                    "shippingCenterCode": result.get('data', {}).get('resultMessage', ''),
                    "resultCode": result.get('data', {}).get('resultCode', ''),
                    "message": "출고지 생성 성공",
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
    
    def update_shipping_center(self, request: ShippingCenterUpdateRequest) -> Dict[str, Any]:
        """
        출고지 수정
        
        Args:
            request: 출고지 수정 요청 데이터
            
        Returns:
            Dict[str, Any]: 출고지 수정 결과
            
        Raises:
            ValueError: 잘못된 요청 데이터
            Exception: API 호출 오류
        """
        # 요청 데이터 검증
        self._validate_shipping_center_update_request(request)
        
        # API 경로 생성 (출고지 코드 포함)
        api_path = f"{self.SHIPPING_CENTER_API_PATH}/{request.outbound_shipping_place_code}".format(
            vendor_id=request.vendor_id
        )
        
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
                return {
                    "success": True,
                    "outboundShippingPlaceCode": request.outbound_shipping_place_code,
                    "resultCode": result.get('data', {}).get('resultCode', ''),
                    "resultMessage": result.get('data', {}).get('resultMessage', ''),
                    "message": "출고지 수정 성공",
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "outboundShippingPlaceCode": request.outbound_shipping_place_code,
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
    
    def _validate_shipping_center_request(self, request: ShippingCenterRequest) -> None:
        """출고지 생성 요청 데이터 검증"""
        
        # 필수 필드 검증
        if not request.vendor_id:
            raise ValueError("vendorId는 필수입니다")
        
        if not request.user_id:
            raise ValueError("userId는 필수입니다")
        
        if not request.shipping_place_name:
            raise ValueError("shippingPlaceName은 필수입니다")
        
        if len(request.shipping_place_name) > 50:
            raise ValueError("출고지 이름은 최대 50자까지 입니다")
        
        if not request.place_addresses:
            raise ValueError("placeAddresses는 필수입니다")
        
        # 주소 정보 검증
        for addr in request.place_addresses:
            self._validate_place_address(addr)
        
        # 도서산간 배송비 정보 검증
        if request.remote_infos:
            for remote_info in request.remote_infos:
                self._validate_remote_info(remote_info)
    
    def _validate_place_address(self, addr: PlaceAddress) -> None:
        """출고지 주소 정보 검증"""
        
        if addr.address_type not in ["JIBUN", "ROADNAME", "OVERSEA"]:
            raise ValueError("addressType은 JIBUN, ROADNAME, OVERSEA 중 하나여야 합니다")
        
        if not addr.country_code or len(addr.country_code) != 2:
            raise ValueError("countryCode는 2자리여야 합니다 (예: KR)")
        
        if not addr.company_contact_number:
            raise ValueError("companyContactNumber는 필수입니다")
        
        # 전화번호 형식 검증
        if not self._validate_phone_number(addr.company_contact_number):
            raise ValueError("companyContactNumber 형식이 올바르지 않습니다 (예: 02-1234-5678)")
        
        if addr.phone_number2 and not self._validate_phone_number(addr.phone_number2):
            raise ValueError("phoneNumber2 형식이 올바르지 않습니다")
        
        # 우편번호 검증
        if addr.return_zip_code:
            if not addr.return_zip_code.isdigit() or len(addr.return_zip_code) < 5 or len(addr.return_zip_code) > 6:
                raise ValueError("우편번호는 숫자 5-6자리여야 합니다")
        
        # 주소 길이 검증
        if addr.return_address and len(addr.return_address) > 150:
            raise ValueError("주소는 최대 150자까지 입니다")
        
        if addr.return_address_detail and len(addr.return_address_detail) > 200:
            raise ValueError("상세주소는 최대 200자까지 입니다")
    
    def _validate_remote_info(self, remote_info: RemoteInfo) -> None:
        """도서산간 배송비 정보 검증"""
        
        if not remote_info.delivery_code:
            raise ValueError("deliveryCode는 필수입니다")
        
        # 우체국(EPOST) 특별 규칙
        if remote_info.delivery_code == "EPOST":
            # 우체국: 0원 또는 100-400원
            if remote_info.jeju != 0 and (remote_info.jeju < 100 or remote_info.jeju > 400):
                raise ValueError("우체국 택배사의 제주 배송비는 0원 또는 100원 이상 400원 이하만 가능합니다")
            
            if remote_info.not_jeju != 0 and (remote_info.not_jeju < 100 or remote_info.not_jeju > 400):
                raise ValueError("우체국 택배사의 제주 외 배송비는 0원 또는 100원 이상 400원 이하만 가능합니다")
            
            # 100원 단위 체크
            if remote_info.jeju % 100 != 0:
                raise ValueError("우체국 택배사의 제주 배송비는 100원 단위여야 합니다")
            
            if remote_info.not_jeju % 100 != 0:
                raise ValueError("우체국 택배사의 제주 외 배송비는 100원 단위여야 합니다")
        else:
            # 일반 택배사: 0원 또는 1000-8000원
            if remote_info.jeju != 0 and (remote_info.jeju < 1000 or remote_info.jeju > 8000):
                raise ValueError("제주 배송비는 0원 또는 1000원 이상 8000원 이하만 가능합니다")
            
            if remote_info.not_jeju != 0 and (remote_info.not_jeju < 1000 or remote_info.not_jeju > 8000):
                raise ValueError("제주 외 배송비는 0원 또는 1000원 이상 8000원 이하만 가능합니다")
            
            # 100원 단위 체크
            if remote_info.jeju % 100 != 0:
                raise ValueError("제주 배송비는 100원 단위여야 합니다")
            
            if remote_info.not_jeju % 100 != 0:
                raise ValueError("제주 외 배송비는 100원 단위여야 합니다")
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """전화번호 형식 검증"""
        if not phone_number:
            return False
        
        # 기본 형식: xx-yyy-zzzz 또는 xxx-yyyy-zzzz
        import re
        pattern = r'^\d{2,4}-\d{3,4}-\d{4}$'
        
        if not re.match(pattern, phone_number):
            return False
        
        # 전체 길이 체크 (9-13자)
        if len(phone_number) < 9 or len(phone_number) > 13:
            return False
        
        return True
    
    def _parse_error_message(self, error_body: str) -> str:
        """API 오류 메시지 파싱"""
        try:
            error_data = json.loads(error_body)
            return error_data.get('message', error_body)
        except json.JSONDecodeError:
            return error_body
    
    def create_domestic_shipping_center(self, vendor_id: str, user_id: str, 
                                      shipping_place_name: str,
                                      zip_code: str, address: str, address_detail: str,
                                      contact_number: str, phone_number2: Optional[str] = None,
                                      delivery_infos: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        국내 출고지 생성 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            user_id: 사용자 아이디
            shipping_place_name: 출고지 이름
            zip_code: 우편번호
            address: 주소
            address_detail: 상세주소
            contact_number: 전화번호
            phone_number2: 보조 전화번호 (선택)
            delivery_infos: 택배사별 배송비 정보 [{"code": "KGB", "jeju": 3000, "notJeju": 2500}]
            
        Returns:
            Dict[str, Any]: 출고지 생성 결과
        """
        
        # 기본 주소 정보 설정 (도로명 + 지번 주소 모두 등록)
        place_addresses = [
            PlaceAddress(
                address_type="ROADNAME",
                country_code="KR",
                company_contact_number=contact_number,
                phone_number2=phone_number2,
                return_zip_code=zip_code,
                return_address=address,
                return_address_detail=address_detail
            ),
            PlaceAddress(
                address_type="JIBUN",
                country_code="KR",
                company_contact_number=contact_number,
                phone_number2=phone_number2,
                return_zip_code=zip_code,
                return_address=address,
                return_address_detail=address_detail
            )
        ]
        
        # 기본 배송비 정보 설정
        if not delivery_infos:
            delivery_infos = [
                {"code": "KGB", "jeju": 3000, "notJeju": 2500},  # 로젠택배
                {"code": "CJGLS", "jeju": 3000, "notJeju": 2500}  # CJ대한통운
            ]
        
        remote_infos = []
        for delivery_info in delivery_infos:
            remote_infos.append(RemoteInfo(
                delivery_code=delivery_info["code"],
                jeju=delivery_info["jeju"],
                not_jeju=delivery_info["notJeju"]
            ))
        
        # 출고지 생성 요청
        request = ShippingCenterRequest(
            vendor_id=vendor_id,
            user_id=user_id,
            shipping_place_name=shipping_place_name,
            place_addresses=place_addresses,
            remote_infos=remote_infos,
            usable=True,
            global_shipping=False
        )
        
        return self.create_shipping_center(request)
    
    def get_delivery_codes(self) -> Dict[str, str]:
        """
        주요 택배사 코드 목록 반환
        
        Returns:
            Dict[str, str]: 택배사명 -> 코드 매핑
        """
        return {
            "CJ대한통운": "CJGLS",
            "로젠택배": "KGB", 
            "한진택배": "HANJIN",
            "우체국택배": "EPOST",
            "롯데택배": "LOTTE",
            "GTX로지스": "GTX",
            "경동택배": "KDEXP",
            "일양로지스": "ILYANG",
            "합동택배": "HDEXP",
            "대신택배": "DAESIN",
            "천일택배": "CHUNIL",
            "GSMNtoN": "GSMNTON",
            "홈픽": "HOMEPICK",
            "한의사랑": "HANIPS",
            "SLX": "SLX"
        }
    
    def get_shipping_places(self, page_num: Optional[int] = None, page_size: Optional[int] = None,
                           place_codes: Optional[List[int]] = None, place_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        출고지 목록 조회
        
        Args:
            page_num: 조회 페이지 (1부터 시작, 목록 조회시 필수)
            page_size: 페이지당 최대 호출 수 (기본값: 10, 최대: 50)
            place_codes: 출고지 코드 목록
            place_names: 출고지명 목록
            
        Returns:
            Dict[str, Any]: 출고지 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 요청 파라미터
            Exception: API 호출 오류
        """
        # 파라미터 검증
        self._validate_shipping_place_query_params(page_num, page_size, place_codes, place_names)
        
        # 쿼리 파라미터 생성
        query_params = {}
        
        if page_num is not None and page_size is not None:
            # 목록 조회 모드
            query_params['pageNum'] = str(page_num)
            query_params['pageSize'] = str(page_size)
        elif place_codes:
            # 출고지 코드로 조회
            query_params['placeCodes'] = ','.join(map(str, place_codes))
        elif place_names:
            # 출고지명으로 조회
            query_params['placeNames'] = ','.join(place_names)
        
        try:
            # API 경로 생성
            api_path = self.SHIPPING_PLACE_QUERY_API_PATH
            
            # 쿼리 스트링 추가
            if query_params:
                query_string = urllib.parse.urlencode(query_params)
                api_path = f"{api_path}?{query_string}"
            
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", api_path)
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
            # 요청 객체 생성
            req = urllib.request.Request(url)
            
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
            
            # 응답 구조화
            if result:
                shipping_list_response = ShippingPlaceListResponse.from_dict(result)
                
                return {
                    "success": True,
                    "data": shipping_list_response,
                    "total_count": shipping_list_response.pagination.total_elements,
                    "current_page": shipping_list_response.pagination.current_page,
                    "total_pages": shipping_list_response.pagination.total_pages,
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "error": "응답 데이터가 없습니다",
                    "originalResponse": result
                }
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                error_message = self._parse_error_message(error_body)
                raise ValueError(f"요청 오류: {error_message}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def get_all_shipping_places(self, page_size: int = 50) -> Dict[str, Any]:
        """
        전체 출고지 목록 조회 (모든 페이지)
        
        Args:
            page_size: 페이지당 최대 호출 수 (기본값: 50)
            
        Returns:
            Dict[str, Any]: 전체 출고지 목록
        """
        all_shipping_places = []
        current_page = 1
        total_pages = 1
        
        try:
            while current_page <= total_pages:
                result = self.get_shipping_places(page_num=current_page, page_size=page_size)
                
                if result.get("success"):
                    shipping_data = result.get("data")
                    all_shipping_places.extend(shipping_data.content)
                    
                    # 첫 번째 호출에서 총 페이지 수 확인
                    if current_page == 1:
                        total_pages = shipping_data.pagination.total_pages
                    
                    current_page += 1
                else:
                    return result
            
            return {
                "success": True,
                "total_count": len(all_shipping_places),
                "shipping_places": all_shipping_places,
                "message": f"전체 {len(all_shipping_places)}개 출고지 조회 완료"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"전체 출고지 조회 오류: {e}",
                "total_count": len(all_shipping_places),
                "shipping_places": all_shipping_places
            }
    
    def get_shipping_place_by_code(self, place_code: int) -> Dict[str, Any]:
        """
        출고지 코드로 특정 출고지 조회
        
        Args:
            place_code: 출고지 코드
            
        Returns:
            Dict[str, Any]: 출고지 정보
        """
        try:
            result = self.get_shipping_places(place_codes=[place_code])
            
            if result.get("success"):
                shipping_data = result.get("data")
                if shipping_data.content:
                    return {
                        "success": True,
                        "shipping_place": shipping_data.content[0],
                        "message": "출고지 조회 성공"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"출고지 코드 {place_code}를 찾을 수 없습니다"
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"출고지 조회 오류: {e}"
            }
    
    def get_shipping_place_by_name(self, place_name: str) -> Dict[str, Any]:
        """
        출고지명으로 특정 출고지 조회
        
        Args:
            place_name: 출고지명
            
        Returns:
            Dict[str, Any]: 출고지 정보
        """
        try:
            result = self.get_shipping_places(place_names=[place_name])
            
            if result.get("success"):
                shipping_data = result.get("data")
                if shipping_data.content:
                    return {
                        "success": True,
                        "shipping_place": shipping_data.content[0],
                        "message": "출고지 조회 성공"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"출고지명 '{place_name}'을 찾을 수 없습니다"
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"출고지 조회 오류: {e}"
            }
    
    def find_shipping_places_by_name_pattern(self, name_pattern: str) -> Dict[str, Any]:
        """
        출고지명 패턴으로 출고지 검색
        
        Args:
            name_pattern: 검색할 이름 패턴
            
        Returns:
            Dict[str, Any]: 매칭되는 출고지 목록
        """
        try:
            # 전체 출고지 목록 조회
            all_result = self.get_all_shipping_places()
            
            if not all_result.get("success"):
                return all_result
            
            all_places = all_result.get("shipping_places", [])
            
            # 패턴 매칭
            matched_places = []
            for place in all_places:
                if name_pattern.lower() in place.shipping_place_name.lower():
                    matched_places.append(place)
            
            return {
                "success": True,
                "matched_count": len(matched_places),
                "shipping_places": matched_places,
                "search_pattern": name_pattern,
                "message": f"'{name_pattern}' 패턴으로 {len(matched_places)}개 출고지 발견"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"출고지 패턴 검색 오류: {e}",
                "search_pattern": name_pattern
            }
    
    def get_active_shipping_places(self) -> Dict[str, Any]:
        """
        활성화된 출고지만 조회
        
        Returns:
            Dict[str, Any]: 활성화된 출고지 목록
        """
        try:
            # 전체 출고지 목록 조회
            all_result = self.get_all_shipping_places()
            
            if not all_result.get("success"):
                return all_result
            
            all_places = all_result.get("shipping_places", [])
            
            # 활성화된 출고지만 필터링
            active_places = [place for place in all_places if place.usable]
            
            return {
                "success": True,
                "total_count": len(all_places),
                "active_count": len(active_places),
                "shipping_places": active_places,
                "message": f"전체 {len(all_places)}개 중 활성화된 {len(active_places)}개 출고지"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"활성화된 출고지 조회 오류: {e}"
            }
    
    def _validate_shipping_place_query_params(self, page_num: Optional[int], page_size: Optional[int],
                                            place_codes: Optional[List[int]], place_names: Optional[List[str]]) -> None:
        """출고지 조회 파라미터 검증"""
        
        # 세 가지 조회 모드 중 하나는 반드시 지정되어야 함
        has_pagination = page_num is not None and page_size is not None
        has_place_codes = place_codes is not None and len(place_codes) > 0
        has_place_names = place_names is not None and len(place_names) > 0
        
        if not (has_pagination or has_place_codes or has_place_names):
            raise ValueError("(pageNum & pageSize) 또는 placeCodes 또는 placeNames 중 하나는 반드시 입력해야 합니다")
        
        # 동시에 여러 모드 지정 불가
        mode_count = sum([has_pagination, has_place_codes, has_place_names])
        if mode_count > 1:
            raise ValueError("pageNum/pageSize, placeCodes, placeNames 중 하나만 지정할 수 있습니다")
        
        # 페이지네이션 파라미터 검증
        if has_pagination:
            if page_num < 1:
                raise ValueError("pageNum은 1 이상이어야 합니다")
            
            if page_size < 1 or page_size > 50:
                raise ValueError("pageSize는 1 이상 50 이하여야 합니다")
        
        # 출고지 코드 검증
        if has_place_codes:
            for code in place_codes:
                if not isinstance(code, int) or code <= 0:
                    raise ValueError("placeCodes는 양의 정수 목록이어야 합니다")
        
        # 출고지명 검증
        if has_place_names:
            for name in place_names:
                if not isinstance(name, str) or len(name.strip()) == 0:
                    raise ValueError("placeNames는 비어있지 않은 문자열 목록이어야 합니다")
    
    def _validate_shipping_center_update_request(self, request: ShippingCenterUpdateRequest) -> None:
        """출고지 수정 요청 데이터 검증"""
        
        # 필수 필드 검증
        if not request.vendor_id or not request.vendor_id.strip():
            raise ValueError("vendor_id는 필수입니다")
        
        if not request.user_id or not request.user_id.strip():
            raise ValueError("user_id는 필수입니다")
        
        if not request.outbound_shipping_place_code or request.outbound_shipping_place_code <= 0:
            raise ValueError("outbound_shipping_place_code는 양의 정수여야 합니다")
        
        # 주소 정보 검증
        if not request.place_addresses or len(request.place_addresses) == 0:
            raise ValueError("최소 1개 이상의 주소 정보가 필요합니다")
        
        # 각 주소 정보 검증
        for i, addr in enumerate(request.place_addresses):
            self._validate_place_address(addr, f"주소 {i+1}")
        
        # 배송비 정보 검증
        if not request.remote_infos or len(request.remote_infos) == 0:
            raise ValueError("최소 1개 이상의 배송비 정보가 필요합니다")
        
        # 각 배송비 정보 검증
        for i, remote in enumerate(request.remote_infos):
            self._validate_remote_info_update(remote, f"배송비 정보 {i+1}")
        
        # 택배사 코드 중복 검증
        delivery_codes = [remote.delivery_code for remote in request.remote_infos]
        if len(delivery_codes) != len(set(delivery_codes)):
            raise ValueError("중복된 택배사 코드가 있습니다")
        
        # 출고지명 검증 (선택적)
        if request.shipping_place_name is not None:
            if not request.shipping_place_name.strip():
                raise ValueError("출고지명은 비어있을 수 없습니다")
            
            if len(request.shipping_place_name) > 100:
                raise ValueError("출고지명은 100자를 초과할 수 없습니다")
    
    def _validate_remote_info_update(self, remote: RemoteInfoUpdate, context: str = "") -> None:
        """수정용 배송비 정보 검증"""
        prefix = f"{context}: " if context else ""
        
        # 택배사 코드 검증
        if not remote.delivery_code or not remote.delivery_code.strip():
            raise ValueError(f"{prefix}택배사 코드는 필수입니다")
        
        valid_codes = self.get_delivery_codes()
        if remote.delivery_code not in valid_codes:
            raise ValueError(f"{prefix}지원하지 않는 택배사 코드입니다: {remote.delivery_code}")
        
        # 배송비 검증
        if remote.jeju < 0:
            raise ValueError(f"{prefix}제주 배송비는 0원 이상이어야 합니다")
        
        if remote.not_jeju < 0:
            raise ValueError(f"{prefix}제주외 배송비는 0원 이상이어야 합니다")
        
        # 100원 단위 검증
        if remote.jeju % 100 != 0:
            raise ValueError(f"{prefix}제주 배송비는 100원 단위여야 합니다")
        
        if remote.not_jeju % 100 != 0:
            raise ValueError(f"{prefix}제주외 배송비는 100원 단위여야 합니다")
        
        # 우체국 택배 특별 규칙
        if remote.delivery_code == "EPOST":
            if remote.jeju > 1000 or remote.not_jeju > 1000:
                raise ValueError(f"{prefix}우체국 택배 배송비는 1,000원을 초과할 수 없습니다")
        
        # remote_info_id 검증 (수정/삭제시)
        if remote.remote_info_id is not None and remote.remote_info_id <= 0:
            raise ValueError(f"{prefix}remote_info_id는 양의 정수여야 합니다")
    
    def update_shipping_center_name(self, vendor_id: str, outbound_shipping_place_code: int, 
                                  new_name: str, user_id: str = "nameUpdateUser") -> Dict[str, Any]:
        """
        출고지명만 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            new_name: 새로운 출고지명
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 출고지 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            
            # 기존 주소 정보 그대로 사용
            existing_addresses = []
            for addr in existing_place.place_addresses:
                existing_addr = PlaceAddress(
                    address_type=addr.address_type,
                    country_code=addr.country_code,
                    company_contact_number=addr.company_contact_number,
                    phone_number2=addr.phone_number2,
                    return_zip_code=addr.return_zip_code,
                    return_address=addr.return_address,
                    return_address_detail=addr.return_address_detail
                )
                existing_addresses.append(existing_addr)
            
            # 기존 배송비 정보 그대로 사용
            existing_remote_infos = []
            for remote in existing_place.remote_infos:
                existing_remote = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=remote.usable,
                    remote_info_id=remote.remote_info_id
                )
                existing_remote_infos.append(existing_remote)
            
            # 출고지명만 변경하는 수정 요청
            update_request = ShippingCenterUpdateRequest(
                vendor_id=vendor_id,
                user_id=user_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                place_addresses=existing_addresses,
                remote_infos=existing_remote_infos,
                shipping_place_name=new_name  # 이것만 변경
            )
            
            return self.update_shipping_center(update_request)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"출고지명 수정 오류: {e}"
            }
    
    def update_shipping_center_contact(self, vendor_id: str, outbound_shipping_place_code: int,
                                     new_contact_number: str, new_phone_number2: Optional[str] = None,
                                     user_id: str = "contactUpdateUser") -> Dict[str, Any]:
        """
        출고지 연락처 정보만 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            new_contact_number: 새로운 주 연락처
            new_phone_number2: 새로운 보조 연락처 (선택)
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 출고지 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            
            # 주소 정보에서 연락처만 변경
            updated_addresses = []
            for addr in existing_place.place_addresses:
                updated_addr = PlaceAddress(
                    address_type=addr.address_type,
                    country_code=addr.country_code,
                    company_contact_number=new_contact_number,  # 변경
                    phone_number2=new_phone_number2 if new_phone_number2 is not None else addr.phone_number2,  # 선택적 변경
                    return_zip_code=addr.return_zip_code,
                    return_address=addr.return_address,
                    return_address_detail=addr.return_address_detail
                )
                updated_addresses.append(updated_addr)
            
            # 기존 배송비 정보 그대로 사용
            existing_remote_infos = []
            for remote in existing_place.remote_infos:
                existing_remote = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=remote.usable,
                    remote_info_id=remote.remote_info_id
                )
                existing_remote_infos.append(existing_remote)
            
            # 연락처만 변경하는 수정 요청
            update_request = ShippingCenterUpdateRequest(
                vendor_id=vendor_id,
                user_id=user_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                place_addresses=updated_addresses,
                remote_infos=existing_remote_infos
            )
            
            return self.update_shipping_center(update_request)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"연락처 수정 오류: {e}"
            }
    
    def add_delivery_service(self, vendor_id: str, outbound_shipping_place_code: int,
                           delivery_code: str, jeju_fee: int, not_jeju_fee: int,
                           user_id: str = "deliveryAddUser") -> Dict[str, Any]:
        """
        출고지에 새로운 택배사 배송비 정보 추가하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            delivery_code: 택배사 코드
            jeju_fee: 제주 배송비
            not_jeju_fee: 제주외 배송비
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 출고지 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            
            # 중복 택배사 확인
            existing_codes = [remote.delivery_code for remote in existing_place.remote_infos]
            if delivery_code in existing_codes:
                return {
                    "success": False,
                    "error": f"택배사 {delivery_code}는 이미 등록되어 있습니다. update_delivery_service를 사용하세요."
                }
            
            # 기존 주소 정보 그대로 사용
            existing_addresses = []
            for addr in existing_place.place_addresses:
                existing_addr = PlaceAddress(
                    address_type=addr.address_type,
                    country_code=addr.country_code,
                    company_contact_number=addr.company_contact_number,
                    phone_number2=addr.phone_number2,
                    return_zip_code=addr.return_zip_code,
                    return_address=addr.return_address,
                    return_address_detail=addr.return_address_detail
                )
                existing_addresses.append(existing_addr)
            
            # 기존 배송비 정보 + 새로운 택배사
            updated_remote_infos = []
            
            # 기존 배송비 정보 그대로 추가
            for remote in existing_place.remote_infos:
                existing_remote = RemoteInfoUpdate(
                    delivery_code=remote.delivery_code,
                    jeju=remote.jeju,
                    not_jeju=remote.not_jeju,
                    usable=remote.usable,
                    remote_info_id=remote.remote_info_id
                )
                updated_remote_infos.append(existing_remote)
            
            # 새로운 택배사 추가
            new_delivery = RemoteInfoUpdate(
                delivery_code=delivery_code,
                jeju=jeju_fee,
                not_jeju=not_jeju_fee,
                usable=True
                # remote_info_id는 None (새로운 배송정보)
            )
            updated_remote_infos.append(new_delivery)
            
            # 새 택배사 추가 요청
            update_request = ShippingCenterUpdateRequest(
                vendor_id=vendor_id,
                user_id=user_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                place_addresses=existing_addresses,
                remote_infos=updated_remote_infos
            )
            
            result = self.update_shipping_center(update_request)
            
            if result.get("success"):
                # 성공 메시지에 추가 정보 포함
                result["added_delivery"] = {
                    "delivery_code": delivery_code,
                    "jeju": jeju_fee,
                    "not_jeju": not_jeju_fee
                }
                result["message"] = f"택배사 {delivery_code} 추가 성공"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"택배사 추가 오류: {e}"
            }
    
    def update_delivery_service(self, vendor_id: str, outbound_shipping_place_code: int,
                              delivery_code: str, jeju_fee: int, not_jeju_fee: int,
                              usable: bool = True, user_id: str = "deliveryUpdateUser") -> Dict[str, Any]:
        """
        기존 택배사 배송비 정보 수정하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            delivery_code: 택배사 코드
            jeju_fee: 새로운 제주 배송비
            not_jeju_fee: 새로운 제주외 배송비
            usable: 활성화 여부
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 출고지 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            
            # 해당 택배사 찾기
            target_remote = None
            for remote in existing_place.remote_infos:
                if remote.delivery_code == delivery_code:
                    target_remote = remote
                    break
            
            if not target_remote:
                return {
                    "success": False,
                    "error": f"택배사 {delivery_code}를 찾을 수 없습니다. add_delivery_service를 사용하세요."
                }
            
            # 기존 주소 정보 그대로 사용
            existing_addresses = []
            for addr in existing_place.place_addresses:
                existing_addr = PlaceAddress(
                    address_type=addr.address_type,
                    country_code=addr.country_code,
                    company_contact_number=addr.company_contact_number,
                    phone_number2=addr.phone_number2,
                    return_zip_code=addr.return_zip_code,
                    return_address=addr.return_address,
                    return_address_detail=addr.return_address_detail
                )
                existing_addresses.append(existing_addr)
            
            # 기존 배송비 정보에서 해당 택배사만 수정
            updated_remote_infos = []
            for remote in existing_place.remote_infos:
                if remote.delivery_code == delivery_code:
                    # 해당 택배사 수정
                    updated_remote = RemoteInfoUpdate(
                        delivery_code=delivery_code,
                        jeju=jeju_fee,
                        not_jeju=not_jeju_fee,
                        usable=usable,
                        remote_info_id=remote.remote_info_id
                    )
                    updated_remote_infos.append(updated_remote)
                else:
                    # 다른 택배사는 그대로 유지
                    existing_remote = RemoteInfoUpdate(
                        delivery_code=remote.delivery_code,
                        jeju=remote.jeju,
                        not_jeju=remote.not_jeju,
                        usable=remote.usable,
                        remote_info_id=remote.remote_info_id
                    )
                    updated_remote_infos.append(existing_remote)
            
            # 택배사 수정 요청
            update_request = ShippingCenterUpdateRequest(
                vendor_id=vendor_id,
                user_id=user_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                place_addresses=existing_addresses,
                remote_infos=updated_remote_infos
            )
            
            result = self.update_shipping_center(update_request)
            
            if result.get("success"):
                # 성공 메시지에 수정 정보 포함
                result["updated_delivery"] = {
                    "delivery_code": delivery_code,
                    "jeju": jeju_fee,
                    "not_jeju": not_jeju_fee,
                    "usable": usable
                }
                result["message"] = f"택배사 {delivery_code} 수정 성공"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"택배사 수정 오류: {e}"
            }
    
    def disable_delivery_service(self, vendor_id: str, outbound_shipping_place_code: int,
                               delivery_code: str, user_id: str = "deliveryDisableUser") -> Dict[str, Any]:
        """
        특정 택배사 배송비 정보 비활성화하는 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            delivery_code: 비활성화할 택배사 코드
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 택배사 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            target_remote = None
            for remote in existing_place.remote_infos:
                if remote.delivery_code == delivery_code:
                    target_remote = remote
                    break
            
            if not target_remote:
                return {
                    "success": False,
                    "error": f"택배사 {delivery_code}를 찾을 수 없습니다"
                }
            
            # 해당 택배사를 비활성화로 수정
            return self.update_delivery_service(
                vendor_id=vendor_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                delivery_code=delivery_code,
                jeju_fee=target_remote.jeju,
                not_jeju_fee=target_remote.not_jeju,
                usable=False,  # 비활성화
                user_id=user_id
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": f"택배사 비활성화 오류: {e}"
            }
    
    def update_shipping_center_simple(self, vendor_id: str, outbound_shipping_place_code: int,
                                    delivery_infos: List[Dict[str, Any]], new_name: Optional[str] = None,
                                    new_contact_number: Optional[str] = None, new_phone_number2: Optional[str] = None,
                                    user_id: str = "simpleUpdateUser") -> Dict[str, Any]:
        """
        출고지 정보를 간단하게 수정하는 통합 편의 메서드
        
        Args:
            vendor_id: 판매자 ID
            outbound_shipping_place_code: 출고지 코드
            delivery_infos: 배송비 정보 목록 [{"code": "KGB", "jeju": 3000, "notJeju": 2500}]
            new_name: 새로운 출고지명 (선택)
            new_contact_number: 새로운 연락처 (선택)
            new_phone_number2: 새로운 보조 연락처 (선택)
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 수정 결과
        """
        try:
            # 기존 출고지 정보 조회
            existing_result = self.get_shipping_place_by_code(outbound_shipping_place_code)
            if not existing_result.get("success"):
                return {
                    "success": False,
                    "error": f"출고지 코드 {outbound_shipping_place_code}를 찾을 수 없습니다"
                }
            
            existing_place = existing_result.get("shipping_place")
            
            # 주소 정보 처리 (연락처 변경 가능)
            updated_addresses = []
            for addr in existing_place.place_addresses:
                updated_addr = PlaceAddress(
                    address_type=addr.address_type,
                    country_code=addr.country_code,
                    company_contact_number=new_contact_number if new_contact_number else addr.company_contact_number,
                    phone_number2=new_phone_number2 if new_phone_number2 is not None else addr.phone_number2,
                    return_zip_code=addr.return_zip_code,
                    return_address=addr.return_address,
                    return_address_detail=addr.return_address_detail
                )
                updated_addresses.append(updated_addr)
            
            # 배송비 정보 처리
            updated_remote_infos = []
            existing_remote_map = {remote.delivery_code: remote for remote in existing_place.remote_infos}
            
            for delivery_info in delivery_infos:
                delivery_code = delivery_info.get("code")
                jeju_fee = delivery_info.get("jeju", 0)
                not_jeju_fee = delivery_info.get("notJeju", 0)
                usable = delivery_info.get("usable", True)
                
                # 기존 배송정보가 있으면 remote_info_id 포함
                remote_info_id = None
                if delivery_code in existing_remote_map:
                    remote_info_id = existing_remote_map[delivery_code].remote_info_id
                
                updated_remote = RemoteInfoUpdate(
                    delivery_code=delivery_code,
                    jeju=jeju_fee,
                    not_jeju=not_jeju_fee,
                    usable=usable,
                    remote_info_id=remote_info_id
                )
                updated_remote_infos.append(updated_remote)
            
            # 출고지 수정 요청
            update_request = ShippingCenterUpdateRequest(
                vendor_id=vendor_id,
                user_id=user_id,
                outbound_shipping_place_code=outbound_shipping_place_code,
                place_addresses=updated_addresses,
                remote_infos=updated_remote_infos,
                shipping_place_name=new_name  # None이면 변경하지 않음
            )
            
            result = self.update_shipping_center(update_request)
            
            if result.get("success"):
                # 성공 메시지에 변경 내용 요약 포함
                changes = []
                if new_name:
                    changes.append(f"출고지명: '{new_name}'")
                if new_contact_number:
                    changes.append(f"연락처: '{new_contact_number}'")
                if delivery_infos:
                    changes.append(f"배송비 정보: {len(delivery_infos)}개")
                
                result["changes"] = changes
                result["message"] = f"출고지 수정 성공 ({', '.join(changes)})"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"출고지 간단 수정 오류: {e}"
            }