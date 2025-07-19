"""
네이버 커머스 API 기본 클라이언트
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import logging
from .auth import NaverAuth

logger = logging.getLogger(__name__)

class NaverBaseClient:
    """네이버 API 기본 클라이언트"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.base_url = "https://api.commerce.naver.com"
        self.auth = NaverAuth(client_id, client_secret)
        self.retry_count = 3
        self.retry_delay = 1  # seconds
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """API 요청 실행"""
        url = f"{self.base_url}{endpoint}"
        
        # URL 파라미터 추가
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        # 요청 데이터 준비
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        # 재시도 로직
        for attempt in range(self.retry_count):
            try:
                # 요청 객체 생성
                req = urllib.request.Request(
                    url,
                    data=request_data,
                    method=method
                )
                
                # 헤더 추가
                headers = self.auth.get_auth_header()
                for key, value in headers.items():
                    req.add_header(key, value)
                
                # 요청 실행
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
            
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                logger.error(f"HTTP Error {e.code}: {error_body}")
                
                # 429 Too Many Requests - 재시도
                if e.code == 429 and attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                # 401 Unauthorized - 토큰 갱신 후 재시도
                elif e.code == 401 and attempt < self.retry_count - 1:
                    self.auth.access_token = None
                    time.sleep(self.retry_delay)
                    continue
                
                raise Exception(f"API request failed: {e.code} - {error_body}")
            
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET 요청"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict, params: Optional[Dict] = None) -> Dict:
        """POST 요청"""
        return self._make_request('POST', endpoint, params=params, data=data)
    
    def put(self, endpoint: str, data: Dict, params: Optional[Dict] = None) -> Dict:
        """PUT 요청"""
        return self._make_request('PUT', endpoint, params=params, data=data)
    
    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """DELETE 요청"""
        return self._make_request('DELETE', endpoint, params=params)
    
    def patch(self, endpoint: str, data: Dict, params: Optional[Dict] = None) -> Dict:
        """PATCH 요청"""
        return self._make_request('PATCH', endpoint, params=params, data=data)