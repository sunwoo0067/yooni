"""
11번가 상품 관리 API
"""
from typing import Dict, List, Optional
from .base_client import ElevenBaseClient

class ElevenProductClient(ElevenBaseClient):
    """11번가 상품 관리 클라이언트"""
    
    def get_products(self, page: int = 1) -> Dict:
        """판매중인 상품 목록 조회
        
        Args:
            page: 페이지 번호 (1부터 시작)
        
        Returns:
            상품 목록
        """
        params = {
            'page': page,
            'rows': 100  # 최대 100개
        }
        
        result = self.get('prodmarketservice/prodmarket/seller', params)
        
        # 응답 구조 정규화
        if 'Products' in result and 'Product' in result['Products']:
            products = result['Products']['Product']
            # 단일 상품인 경우 리스트로 변환
            if not isinstance(products, list):
                products = [products]
            result['Products']['Product'] = products
        
        return result
    
    def get_product_detail(self, product_no: str) -> Dict:
        """상품 상세 조회
        
        Args:
            product_no: 상품 번호
        
        Returns:
            상품 상세 정보
        """
        params = {
            'prdNo': product_no
        }
        
        return self.get('prodmarketservice/prodmarket/seller', params)
    
    def get_product_stock(self, product_no: str) -> Dict:
        """상품 재고 조회
        
        Args:
            product_no: 상품 번호
        
        Returns:
            재고 정보
        """
        params = {
            'prdNo': product_no
        }
        
        return self.get('prodmarketservice/prodstock', params)
    
    def update_stock(self, product_no: str, stock_data: Dict) -> Dict:
        """재고 수정
        
        Args:
            product_no: 상품 번호
            stock_data: 재고 정보
                - sellerPrdCd: 판매자 상품코드
                - prdStckNo: 재고번호
                - stckQty: 재고수량
        
        Returns:
            수정 결과
        
        Note:
            11번가 API는 POST를 지원하지 않아 실제 수정은 웹 인터페이스에서만 가능
        """
        # 11번가는 재고 수정 API를 제공하지 않음
        raise NotImplementedError("11번가는 API를 통한 재고 수정을 지원하지 않습니다.")
    
    def get_categories(self, category_cd: Optional[str] = None) -> Dict:
        """카테고리 조회
        
        Args:
            category_cd: 카테고리 코드 (없으면 대분류)
        
        Returns:
            카테고리 목록
        """
        params = {}
        if category_cd:
            params['dispCtgrNo'] = category_cd
        
        result = self.get('categoryservice/category', params)
        
        # 응답 구조 정규화
        if 'Categories' in result and 'Category' in result['Categories']:
            categories = result['Categories']['Category']
            if not isinstance(categories, list):
                categories = [categories]
            result['Categories']['Category'] = categories
        
        return result
    
    def search_products(self, keyword: str, page: int = 1) -> Dict:
        """상품 검색
        
        Args:
            keyword: 검색 키워드
            page: 페이지 번호
        
        Returns:
            검색 결과
        """
        params = {
            'keyword': keyword,
            'pageNum': page,
            'pageSize': 100
        }
        
        return self.get('searchservice/search', params)