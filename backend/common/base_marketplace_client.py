"""
마켓플레이스 클라이언트 기본 클래스
모든 마켓플레이스(쿠팡, 오너클랜, 젠트레이드 등)의 공통 기능을 제공
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class BaseMarketplaceClient:
    """모든 마켓플레이스 클라이언트의 기본 클래스"""
    
    def __init__(
        self, 
        api_key: str, 
        secret_key: str,
        base_url: str,
        vendor_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.vendor_id = vendor_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _create_session(self) -> requests.Session:
        """HTTP 세션 생성 및 설정"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Yoonni/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException,))
    )
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> requests.Response:
        """
        공통 HTTP 요청 처리
        
        Args:
            method: HTTP 메소드 (GET, POST, PUT, DELETE)
            endpoint: API 엔드포인트
            **kwargs: requests 라이브러리에 전달할 추가 인자
            
        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # 타임아웃 설정
        kwargs.setdefault('timeout', self.timeout)
        
        # 요청 로깅
        self.logger.debug(f"{method} {url}")
        
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # 응답 시간 로깅
            elapsed = time.time() - start_time
            self.logger.debug(f"Response received in {elapsed:.2f}s")
            
            return response
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error: {e}")
            self._handle_error_response(e.response)
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise
            
    def _handle_error_response(self, response: requests.Response):
        """에러 응답 처리"""
        if response.status_code == 429:
            # Rate limit 처리
            retry_after = response.headers.get('Retry-After', 60)
            self.logger.warning(f"Rate limit exceeded. Retry after {retry_after}s")
            time.sleep(int(retry_after))
        elif response.status_code == 401:
            self.logger.error("Authentication failed. Check API credentials.")
        elif response.status_code == 403:
            self.logger.error("Access forbidden. Check permissions.")
            
    async def _make_request_async(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """비동기 HTTP 요청 처리"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            self._make_request, 
            method, 
            endpoint, 
            **kwargs
        )
        return response.json()
        
    def _parse_date(self, date_str: str) -> datetime:
        """날짜 문자열 파싱"""
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        raise ValueError(f"Unable to parse date: {date_str}")
        
    def _build_pagination_params(
        self, 
        page: int = 1, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """페이지네이션 파라미터 생성"""
        return {
            'page': page,
            'limit': min(limit, 1000),  # 최대 1000개로 제한
            'offset': (page - 1) * limit
        }
        
    def get_products(
        self, 
        page: int = 1, 
        limit: int = 100,
        **filters
    ) -> List[Dict[str, Any]]:
        """상품 목록 조회 - 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement get_products()")
        
    def get_orders(
        self, 
        start_date: str, 
        end_date: str,
        status: Optional[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """주문 목록 조회 - 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement get_orders()")
        
    def update_stock(
        self, 
        product_id: str, 
        quantity: int
    ) -> Dict[str, Any]:
        """재고 업데이트 - 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement update_stock()")
        
    def close(self):
        """리소스 정리"""
        if self.session:
            self.session.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()