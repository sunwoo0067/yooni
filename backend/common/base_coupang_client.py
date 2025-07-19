"""
쿠팡 API 클라이언트 기본 클래스
HMAC 인증 및 쿠팡 특화 기능 제공
"""
import hmac
import hashlib
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
from .base_marketplace_client import BaseMarketplaceClient


class BaseCoupangClient(BaseMarketplaceClient):
    """쿠팡 API 클라이언트 기본 클래스"""
    
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        vendor_id: str,
        base_url: str = "https://api-gateway.coupang.com",
        timeout: int = 30
    ):
        super().__init__(
            api_key=access_key,
            secret_key=secret_key,
            base_url=base_url,
            vendor_id=vendor_id,
            timeout=timeout
        )
        self.access_key = access_key
        
    def _generate_hmac_signature(
        self, 
        method: str, 
        path: str, 
        query_string: str = ""
    ) -> str:
        """HMAC-SHA256 서명 생성"""
        datetime_str = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
        
        # 메시지 생성
        message = f"{datetime_str}{method}{path}{query_string}"
        
        # HMAC 서명 생성
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Authorization 헤더 생성
        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}"
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> requests.Response:
        """쿠팡 API 요청 처리 (HMAC 인증 포함)"""
        # URL 파싱
        parsed = urllib.parse.urlparse(endpoint)
        path = parsed.path
        query_string = parsed.query
        
        # HMAC 서명 생성
        auth_header = self._generate_hmac_signature(method, path, query_string)
        
        # 헤더 업데이트
        headers = kwargs.get('headers', {})
        headers.update({
            'Authorization': auth_header,
            'X-Reqeusted-By': str(self.vendor_id),
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        
        # 기본 클래스의 요청 메서드 호출
        return super()._make_request(method, endpoint, **kwargs)
        
    def _parse_coupang_date(self, date_str: str) -> datetime:
        """쿠팡 날짜 형식 파싱"""
        # 쿠팡은 주로 ISO 8601 형식 사용
        if 'T' in date_str:
            if date_str.endswith('Z'):
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
            
    def _handle_coupang_error(self, error_data: Dict[str, Any]):
        """쿠팡 특화 에러 처리"""
        error_code = error_data.get('code')
        error_message = error_data.get('message', '')
        
        error_map = {
            'INVALID_ACCESS_TOKEN': '유효하지 않은 액세스 토큰',
            'INVALID_SECRET_KEY': '유효하지 않은 시크릿 키',
            'INVALID_VENDOR_ID': '유효하지 않은 벤더 ID',
            'RATE_LIMIT_EXCEEDED': 'API 호출 제한 초과',
            'INVALID_DATE_RANGE': '유효하지 않은 날짜 범위'
        }
        
        korean_message = error_map.get(error_code, error_message)
        self.logger.error(f"쿠팡 API 에러: {error_code} - {korean_message}")
        
    def get_vendor_items(self, next_token: Optional[str] = None) -> Dict[str, Any]:
        """벤더 상품 목록 조회"""
        params = {}
        if next_token:
            params['nextToken'] = next_token
            
        endpoint = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        if params:
            query_string = urllib.parse.urlencode(params)
            endpoint = f"{endpoint}?{query_string}"
            
        response = self._make_request('GET', endpoint)
        return response.json()