"""
네이버 스마트스토어 상품 관리 API
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_client import NaverBaseClient

class NaverProductClient(NaverBaseClient):
    """네이버 상품 관리 클라이언트"""
    
    def get_products(self, page: int = 1, size: int = 100, 
                    status: Optional[str] = None) -> Dict:
        """상품 목록 조회
        
        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기 (최대 100)
            status: 상품 상태 (SALE, OUTOFSTOCK, SUSPENSION 등)
        
        Returns:
            상품 목록 및 페이징 정보
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }
        
        if status:
            params['productStatusType'] = status
        
        return self.get('/external/v2/products', params=params)
    
    def get_product_detail(self, product_no: str) -> Dict:
        """상품 상세 조회
        
        Args:
            product_no: 상품 번호
        
        Returns:
            상품 상세 정보
        """
        return self.get(f'/external/v2/products/{product_no}')
    
    def create_product(self, product_data: Dict) -> Dict:
        """상품 등록
        
        Args:
            product_data: 상품 정보
                - name: 상품명 (필수)
                - salePrice: 판매가 (필수)
                - stockQuantity: 재고수량
                - detailContent: 상세설명
                - images: 이미지 URL 리스트
                - category: 카테고리 정보
        
        Returns:
            등록된 상품 정보
        """
        # 필수 필드 검증
        required_fields = ['name', 'salePrice']
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Required field missing: {field}")
        
        return self.post('/external/v2/products', product_data)
    
    def update_product(self, product_no: str, update_data: Dict) -> Dict:
        """상품 수정
        
        Args:
            product_no: 상품 번호
            update_data: 수정할 상품 정보
        
        Returns:
            수정된 상품 정보
        """
        return self.patch(f'/external/v2/products/{product_no}', update_data)
    
    def update_product_status(self, product_no: str, status: str) -> Dict:
        """상품 상태 변경
        
        Args:
            product_no: 상품 번호
            status: 변경할 상태 (SALE, OUTOFSTOCK, SUSPENSION)
        
        Returns:
            변경 결과
        """
        data = {
            'productStatusType': status
        }
        return self.patch(f'/external/v2/products/{product_no}/status', data)
    
    def update_stock(self, product_no: str, stock_quantity: int) -> Dict:
        """재고 수량 변경
        
        Args:
            product_no: 상품 번호
            stock_quantity: 재고 수량
        
        Returns:
            변경 결과
        """
        data = {
            'stockQuantity': stock_quantity
        }
        return self.patch(f'/external/v2/products/{product_no}/stock', data)
    
    def update_price(self, product_no: str, sale_price: int, 
                    discount_price: Optional[int] = None) -> Dict:
        """가격 변경
        
        Args:
            product_no: 상품 번호
            sale_price: 판매가
            discount_price: 할인가 (선택)
        
        Returns:
            변경 결과
        """
        data = {
            'salePrice': sale_price
        }
        if discount_price is not None:
            data['discountPrice'] = discount_price
        
        return self.patch(f'/external/v2/products/{product_no}/price', data)
    
    def delete_product(self, product_no: str) -> Dict:
        """상품 삭제
        
        Args:
            product_no: 상품 번호
        
        Returns:
            삭제 결과
        """
        return self.delete(f'/external/v2/products/{product_no}')
    
    def get_product_options(self, product_no: str) -> Dict:
        """상품 옵션 조회
        
        Args:
            product_no: 상품 번호
        
        Returns:
            옵션 정보
        """
        return self.get(f'/external/v2/products/{product_no}/options')
    
    def update_product_options(self, product_no: str, options: List[Dict]) -> Dict:
        """상품 옵션 수정
        
        Args:
            product_no: 상품 번호
            options: 옵션 리스트
        
        Returns:
            수정 결과
        """
        data = {'options': options}
        return self.put(f'/external/v2/products/{product_no}/options', data)
    
    def get_categories(self, category_id: Optional[str] = None) -> Dict:
        """카테고리 조회
        
        Args:
            category_id: 카테고리 ID (없으면 최상위 카테고리)
        
        Returns:
            카테고리 목록
        """
        params = {}
        if category_id:
            params['categoryId'] = category_id
        
        return self.get('/external/v2/categories', params=params)