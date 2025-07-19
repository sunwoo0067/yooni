"""
11번가 통합 클라이언트
"""
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

from .product_client import ElevenProductClient
from .order_client import ElevenOrderClient

load_dotenv()

class ElevenClient:
    """11번가 통합 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: 11번가 Open API 키
        """
        self.api_key = api_key or os.getenv('ELEVEN_API_KEY')
        
        if not self.api_key:
            raise ValueError("11번가 API key is required")
        
        # 서브 클라이언트 초기화
        self.products = ElevenProductClient(self.api_key)
        self.orders = ElevenOrderClient(self.api_key)
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            # 카테고리 조회로 연결 확인 (가장 가벼운 API)
            result = self.products.get_categories()
            return 'Categories' in result
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict:
        """계정 정보 조회 (11번가는 별도 API 없음)"""
        return {
            'api_key': self.api_key[:10] + '***' if len(self.api_key) > 10 else '***',
            'api_type': 'REST API (XML)',
            'status': 'active' if self.test_connection() else 'error'
        }