#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 기본 클라이언트
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from auth import CoupangAuth
from .constants import BASE_URL
from .utils import handle_api_success, handle_api_error, handle_exception_error


class BaseClient:
    """쿠팡 API 클라이언트 기본 클래스"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, vendor_id: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키 (None이면 환경변수에서 읽음)
            secret_key: 쿠팡 시크릿 키 (None이면 환경변수에서 읽음)
            vendor_id: 쿠팡 벤더 ID (None이면 환경변수에서 읽음)
        """
        self.BASE_URL = BASE_URL
        
        try:
            self.auth = CoupangAuth(access_key, secret_key, vendor_id)
        except ValueError as e:
            print(f"⚠️  인증 초기화 오류: {e}")
            print("   환경변수 COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, COUPANG_VENDOR_ID를 설정해주세요.")
            raise
    
    def _make_request(self, method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """API 요청 실행"""
        # 요청 URL 생성
        url = f"{self.BASE_URL}{path}"
        
        # 요청 데이터를 JSON으로 변환
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 쿼리 파라미터 추출 (GET 요청인 경우)
        query_params = None
        if '?' in path:
            path_without_query = path.split('?')[0]
            query_string = path.split('?')[1]
            query_params = dict(urllib.parse.parse_qsl(query_string))
        else:
            path_without_query = path
        
        # 인증 헤더 생성
        headers = self.auth.generate_authorization_header(method, path_without_query, query_params)
        
        # HTTP 요청 생성
        request = urllib.request.Request(url, data=json_data, headers=headers)
        request.get_method = lambda: method
        
        try:
            # SSL 컨텍스트 생성 (인증서 검증 비활성화)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # API 요청 실행
            with urllib.request.urlopen(request, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            # HTTP 오류 처리
            error_response = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_response)
                return error_data
            except json.JSONDecodeError:
                return {
                    "code": "ERROR",
                    "message": f"HTTP {e.code} 오류: {error_response}",
                    "data": None
                }
        except Exception as e:
            # 기타 오류 처리
            return {
                "code": "ERROR",
                "message": f"요청 실행 오류: {str(e)}",
                "data": None
            }
    
    def _handle_response(self, response: Dict[str, Any], operation: str, **extra_fields) -> Dict[str, Any]:
        """
        API 응답 처리
        
        Args:
            response: API 원본 응답
            operation: 수행 중인 작업명
            **extra_fields: 추가 필드들
            
        Returns:
            Dict[str, Any]: 처리된 응답
        """
        if response.get("code") == "SUCCESS":
            return handle_api_success(
                response, 
                default_message=f"{operation} 성공",
                **extra_fields
            )
        else:
            return handle_api_error(response)
    
    def _execute_api_call(self, method: str, api_path: str, data: Dict[str, Any], 
                         operation: str, **extra_fields) -> Dict[str, Any]:
        """
        API 호출 실행 및 응답 처리
        
        Args:
            method: HTTP 메서드
            api_path: API 경로
            data: 요청 데이터
            operation: 작업명 (응답 메시지에 사용)
            **extra_fields: 추가 응답 필드들
            
        Returns:
            Dict[str, Any]: 처리된 응답
        """
        try:
            response = self._make_request(method, api_path, data)
            return self._handle_response(response, operation, **extra_fields)
        except Exception as e:
            return handle_exception_error(e, f"{operation} API 호출")