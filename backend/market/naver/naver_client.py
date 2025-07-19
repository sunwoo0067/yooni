"""
네이버 스마트스토어 통합 클라이언트
"""
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from .product_client import NaverProductClient
from .order_client import NaverOrderClient

load_dotenv()

class NaverClient:
    """네이버 스마트스토어 통합 클라이언트"""
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None):
        """
        Args:
            client_id: 네이버 API 클라이언트 ID
            client_secret: 네이버 API 클라이언트 시크릿
        """
        self.client_id = client_id or os.getenv('NAVER_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Naver API credentials are required")
        
        # 서브 클라이언트 초기화
        self.products = NaverProductClient(self.client_id, self.client_secret)
        self.orders = NaverOrderClient(self.client_id, self.client_secret)
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            # 상품 1개만 조회해서 연결 확인
            result = self.products.get_products(page=1, size=1)
            return 'contents' in result or 'products' in result
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict:
        """계정 정보 조회 (현재 API에서 미지원, 더미 반환)"""
        return {
            'client_id': self.client_id[:10] + '***',
            'api_type': 'OAuth 2.0',
            'status': 'active' if self.test_connection() else 'error'
        }