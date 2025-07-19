"""
네이버 커머스 API OAuth 2.0 인증
"""
import time
import json
import urllib.request
import urllib.parse
from typing import Dict, Optional
from datetime import datetime, timedelta

class NaverAuth:
    """네이버 OAuth 2.0 인증 관리"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.auth_url = "https://api.commerce.naver.com/external/v1/oauth2/token"
    
    def get_access_token(self) -> str:
        """액세스 토큰 획득 (필요시 갱신)"""
        if self._is_token_valid():
            return self.access_token
        
        return self._request_new_token()
    
    def _is_token_valid(self) -> bool:
        """토큰 유효성 확인"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # 만료 5분 전에 갱신
        buffer_time = timedelta(minutes=5)
        return datetime.now() < (self.token_expires_at - buffer_time)
    
    def _request_new_token(self) -> str:
        """새 토큰 요청"""
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'type': 'SELF'
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(
            self.auth_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                self.access_token = result['access_token']
                expires_in = result.get('expires_in', 3600)  # 기본 1시간
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                return self.access_token
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Token request failed: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"Token request error: {str(e)}")
    
    def get_auth_header(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        token = self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }