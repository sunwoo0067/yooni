#!/usr/bin/env python3
"""
쿠팡 파트너스 API 인증 모듈
HMAC-SHA256 서명 기반 인증 구현
"""

import os
import time
import hmac
import hashlib
import urllib.parse
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv


class CoupangAuth:
    """쿠팡 파트너스 API 인증 클래스"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        쿠팡 인증 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키
            vendor_id: 쿠팡 벤더 ID
        """
        # .env 파일 로드
        load_dotenv()
        
        self.access_key = access_key or os.getenv('COUPANG_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('COUPANG_SECRET_KEY')
        self.vendor_id = vendor_id or os.getenv('COUPANG_VENDOR_ID')
        
        if not all([self.access_key, self.secret_key, self.vendor_id]):
            raise ValueError("쿠팡 API 인증 정보가 필요합니다: access_key, secret_key, vendor_id")
        
        # GMT 시간대 설정
        os.environ['TZ'] = 'GMT+0'
        time.tzset()
    
    def _generate_timestamp(self) -> str:
        """
        쿠팡 API용 타임스탬프 생성
        
        Returns:
            str: YYMMDDTHHMMSSZ 형식의 타임스탬프
        """
        return time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    
    def _generate_signature(self, method: str, path: str, query: str, timestamp: str) -> str:
        """
        HMAC-SHA256 서명 생성
        
        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            path: API 경로
            query: 쿼리 스트링
            timestamp: 타임스탬프
            
        Returns:
            str: HMAC-SHA256 서명
        """
        message = timestamp + method + path + query
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def generate_authorization_header(self, method: str, path: str, 
                                    query_params: Optional[Dict] = None) -> Dict[str, str]:
        """
        쿠팡 API 인증 헤더 생성
        
        Args:
            method: HTTP 메서드
            path: API 경로
            query_params: 쿼리 파라미터 딕셔너리
            
        Returns:
            Dict[str, str]: 인증 헤더 딕셔너리
        """
        timestamp = self._generate_timestamp()
        
        # 쿼리 스트링 생성
        query = ""
        if query_params:
            query = urllib.parse.urlencode(query_params)
        
        # 서명 생성
        signature = self._generate_signature(method, path, query, timestamp)
        
        # Authorization 헤더 생성
        authorization = (
            f"CEA algorithm=HmacSHA256, "
            f"access-key={self.access_key}, "
            f"signed-date={timestamp}, "
            f"signature={signature}"
        )
        
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": authorization
        }
        
        return headers
    
    def get_vendor_path(self, endpoint: str) -> str:
        """
        벤더 ID가 포함된 API 경로 생성
        
        Args:
            endpoint: API 엔드포인트
            
        Returns:
            str: 벤더 ID가 포함된 전체 경로
        """
        base_path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}"
        return f"{base_path}{endpoint}"