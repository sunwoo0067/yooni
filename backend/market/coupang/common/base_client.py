#!/usr/bin/env python3
"""
쿠팡 API 클라이언트 베이스 클래스
"""

import ssl
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .config import config
from .errors import error_handler, CoupangAPIError, CoupangAuthError, CoupangNetworkError
from market.coupang.auth.coupang_auth import CoupangAuth


class BaseCoupangClient(ABC):
    """쿠팡 API 클라이언트 베이스 클래스"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    
    def __init__(self, access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        베이스 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 환경변수에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 환경변수에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 환경변수에서 읽음)
        """
        self.config = config
        
        # 인증 정보 설정
        final_access_key = access_key or self.config.coupang_access_key
        final_secret_key = secret_key or self.config.coupang_secret_key
        final_vendor_id = vendor_id or self.config.coupang_vendor_id
        
        if not all([final_access_key, final_secret_key, final_vendor_id]):
            raise CoupangAuthError(
                "쿠팡 API 인증 정보가 필요합니다. "
                "환경변수 COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, COUPANG_VENDOR_ID를 설정해주세요."
            )
        
        try:
            self.auth = CoupangAuth(final_access_key, final_secret_key, final_vendor_id)
            self.vendor_id = final_vendor_id
        except Exception as e:
            raise CoupangAuthError(f"인증 초기화 실패: {str(e)}")
    
    def execute_api_request(self, method: str, api_path: str, 
                           data: Optional[Dict[str, Any]] = None,
                           timeout: int = 30) -> Dict[str, Any]:
        """
        API 요청 실행 (공통 로직)
        
        Args:
            method: HTTP 메서드
            api_path: API 경로
            data: 요청 데이터
            timeout: 타임아웃 (초)
            
        Returns:
            Dict[str, Any]: API 응답
            
        Raises:
            CoupangAPIError: API 호출 실패시
        """
        start_time = time.time()
        
        try:
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
            # 인증 헤더 생성 (쿼리 파라미터 추출)
            path_without_query = api_path.split('?')[0]
            query_params = {}
            if '?' in api_path:
                query_string = api_path.split('?')[1]
                query_params = dict(urllib.parse.parse_qsl(query_string))
            
            headers = self.auth.generate_authorization_header(method, path_without_query, query_params)
            
            # 요청 데이터 준비
            json_data = None
            if data:
                json_data = json.dumps(data).encode('utf-8')
                headers['Content-Length'] = str(len(json_data))
            
            # 요청 로깅
            error_handler.log_api_request(method, url, data)
            
            # HTTP 요청 생성
            request = urllib.request.Request(url, data=json_data, headers=headers)
            request.get_method = lambda: method
            
            # SSL 컨텍스트 생성 (보안 강화)
            ssl_context = ssl.create_default_context()
            
            # API 요청 실행
            with urllib.request.urlopen(request, context=ssl_context, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                
                # 성능 로깅
                duration = time.time() - start_time
                error_handler.log_performance(f"{method} {api_path}", duration)
                
                return result
                
        except urllib.error.HTTPError as e:
            # HTTP 오류 처리
            try:
                error_data = e.read().decode('utf-8')
                error_response = json.loads(error_data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                error_response = {
                    "code": e.code,
                    "message": f"HTTP {e.code} 오류: {e.reason}",
                    "raw_error": error_data if 'error_data' in locals() else str(e)
                }
            
            raise CoupangAPIError(
                f"HTTP {e.code} 오류",
                error_code=e.code,
                response_data=error_response
            )
            
        except urllib.error.URLError as e:
            # 네트워크 오류 처리
            raise CoupangNetworkError(f"네트워크 오류: {str(e.reason)}")
            
        except json.JSONDecodeError as e:
            # JSON 파싱 오류
            raise CoupangAPIError(f"응답 파싱 오류: {str(e)}")
            
        except Exception as e:
            # 기타 예외
            raise CoupangAPIError(f"요청 처리 중 오류: {str(e)}")
    
    def handle_api_response(self, response: Dict[str, Any], 
                           success_message: str = "API 호출 성공",
                           **extra_data) -> Dict[str, Any]:
        """
        API 응답 처리 (성공/실패 판단)
        
        Args:
            response: API 응답 데이터
            success_message: 성공시 메시지
            **extra_data: 추가 데이터
            
        Returns:
            Dict[str, Any]: 처리된 응답
        """
        response_code = response.get("code")
        
        # 성공 응답 처리 (200 또는 "200")
        if response_code == 200 or response_code == "200":
            return error_handler.handle_api_success(
                response, 
                success_message, 
                **extra_data
            )
        else:
            # 실패 응답 처리
            return error_handler.handle_api_error(response)
    
    @abstractmethod
    def get_api_name(self) -> str:
        """
        API 이름 반환 (로깅용)
        
        Returns:
            str: API 이름
        """
        pass
    
    def validate_vendor_id(self, vendor_id: str) -> str:
        """
        벤더 ID 유효성 검증
        
        Args:
            vendor_id: 검증할 벤더 ID
            
        Returns:
            str: 검증된 벤더 ID
            
        Raises:
            ValueError: 유효하지 않은 벤더 ID
        """
        if not vendor_id:
            raise ValueError("벤더 ID가 필요합니다.")
        
        if not vendor_id.startswith('A') or len(vendor_id) != 9:
            raise ValueError("올바른 판매자 ID(vendorId)를 입력했는지 확인합니다. 예) A00012345")
        
        return vendor_id
    
    def validate_receipt_id(self, receipt_id) -> int:
        """
        접수번호 유효성 검증
        
        Args:
            receipt_id: 검증할 접수번호
            
        Returns:
            int: 검증된 접수번호
            
        Raises:
            ValueError: 유효하지 않은 접수번호
        """
        if receipt_id is None:
            raise ValueError("접수번호가 필요합니다.")
        
        try:
            receipt_id_int = int(receipt_id)
            if receipt_id_int <= 0:
                raise ValueError("접수번호는 양의 정수여야 합니다.")
            return receipt_id_int
        except (ValueError, TypeError):
            raise ValueError("올바른 접수번호를 입력해주세요. Number 타입이어야 합니다.")
    
    def get_vendor_api_path(self, endpoint: str) -> str:
        """
        벤더 ID가 포함된 API 경로 생성
        
        Args:
            endpoint: API 엔드포인트
            
        Returns:
            str: 벤더 ID가 포함된 전체 경로
        """
        return f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}{endpoint}"