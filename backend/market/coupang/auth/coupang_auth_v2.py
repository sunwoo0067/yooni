#!/usr/bin/env python3
"""
쿠팡 파트너스 API 인증 모듈 v2
HMAC-SHA256 서명 기반 인증 구현 (DB 설정 지원)
"""

import os
import sys
import time
import hmac
import hashlib
import urllib.parse
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from config import get_config
except ImportError:
    get_config = None


class CoupangAuthV2:
    """쿠팡 파트너스 API 인증 클래스 (DB 설정 지원)"""
    
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
        
        # DB에서 설정 읽기 시도
        if not access_key and get_config:
            access_key = get_config('api_keys', 'COUPANG_ACCESS_KEY')
        if not secret_key and get_config:
            secret_key = get_config('api_keys', 'COUPANG_SECRET_KEY')
        if not vendor_id and get_config:
            vendor_id = get_config('api_keys', 'COUPANG_VENDOR_ID')
        
        # 환경변수에서 읽기 (폴백)
        self.access_key = access_key or os.getenv('COUPANG_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('COUPANG_SECRET_KEY')
        self.vendor_id = vendor_id or os.getenv('COUPANG_VENDOR_ID')
        
        if not all([self.access_key, self.secret_key, self.vendor_id]):
            raise ValueError("쿠팡 API 인증 정보가 필요합니다: access_key, secret_key, vendor_id")
        
        # API URL 설정
        self.api_url = 'https://api-gateway.coupang.com'
        if get_config:
            self.api_url = get_config('marketplace', 'COUPANG_API_URL', self.api_url)
        
        # GMT 시간대 설정
        os.environ['TZ'] = 'GMT+0'
        time.tzset()
    
    def _generate_timestamp(self) -> str:
        """
        쿠팡 API용 타임스탬프 생성
        
        Returns:
            str: YYMMDDTHHMMSSZ 형식의 타임스탬프
        """
        # GMT 기준 현재 시간
        current_time = datetime.utcnow()
        return current_time.strftime('%y%m%dT%H%M%SZ')
    
    def _generate_signature(self, method: str, url: str, timestamp: str, 
                           query_params: Optional[Dict] = None) -> str:
        """
        HMAC-SHA256 서명 생성
        
        Args:
            method: HTTP 메서드 (GET, POST 등)
            url: API 엔드포인트 URL
            timestamp: API 타임스탬프
            query_params: URL 쿼리 파라미터
            
        Returns:
            str: Base64 인코딩된 서명
        """
        # URL 파싱
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        
        # 쿼리 스트링 처리
        query_string = ''
        if query_params:
            # 키로 정렬하여 일관된 순서 보장
            sorted_params = sorted(query_params.items())
            query_string = urllib.parse.urlencode(sorted_params)
        elif parsed_url.query:
            query_string = parsed_url.query
        
        # 정규화된 URL 생성
        if query_string:
            canonical_url = f"{path}?{query_string}"
        else:
            canonical_url = path
        
        # 서명할 메시지 생성
        message = f"{method}{canonical_url}{timestamp}"
        
        # HMAC-SHA256 서명 생성
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}"
    
    def get_headers(self, method: str, url: str, query_params: Optional[Dict] = None) -> Dict[str, str]:
        """
        API 요청용 헤더 생성
        
        Args:
            method: HTTP 메서드
            url: API 엔드포인트 URL
            query_params: URL 쿼리 파라미터
            
        Returns:
            Dict[str, str]: API 요청 헤더
        """
        timestamp = self._generate_timestamp()
        
        return {
            'Authorization': self._generate_signature(method, url, timestamp, query_params),
            'X-EXTENDED-Timestamp': timestamp,
            'X-Coupang-Target-Market': 'KR',  # 한국 마켓 고정
            'Content-Type': 'application/json;charset=UTF-8'
        }
    
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        import requests
        import ssl
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            # 벤더 정보 조회 API로 테스트
            url = f"{self.api_url}/v2/providers/seller_api/apis/api/v1/vendor"
            headers = self.get_headers('GET', url)
            
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                print("쿠팡 API 연결 성공!")
                return True
            else:
                print(f"쿠팡 API 연결 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"쿠팡 API 연결 오류: {e}")
            return False