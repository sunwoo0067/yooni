#!/usr/bin/env python3
"""
쿠팡 파트너스 API 클라이언트
반품 요청, 주문, 상품 관리를 위한 REST API 클라이언트
"""

import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any
from .auth import CoupangAuth
from .category import CoupangCategoryClient, CoupangCategoryRecommendationClient


class CoupangClient:
    """쿠팡 파트너스 API 클라이언트"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        쿠팡 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키  
            vendor_id: 쿠팡 벤더 ID
        """
        self.auth = CoupangAuth(access_key, secret_key, vendor_id)
        
        # SSL 컨텍스트 설정 (인증서 검증 비활성화)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # 카테고리 클라이언트 초기화
        self.category = CoupangCategoryClient(access_key, secret_key, vendor_id)
        
        # 카테고리 추천 클라이언트 초기화
        self.category_recommendation = CoupangCategoryRecommendationClient(access_key, secret_key, vendor_id)
    
    def _make_request(self, method: str, endpoint: str, 
                     query_params: Optional[Dict] = None,
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        API 요청 실행
        
        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            query_params: 쿼리 파라미터
            data: 요청 바디 데이터
            
        Returns:
            Dict[str, Any]: API 응답 데이터
        """
        # 전체 경로 생성
        path = self.auth.get_vendor_path(endpoint)
        
        # 인증 헤더 생성
        headers = self.auth.generate_authorization_header(method, path, query_params)
        
        # URL 생성
        url = f"{self.BASE_URL}{path}"
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            url = f"{url}?{query_string}"
        
        # 요청 객체 생성
        req = urllib.request.Request(url)
        
        # 헤더 추가
        for key, value in headers.items():
            req.add_header(key, value)
        
        # HTTP 메서드 설정
        req.get_method = lambda: method
        
        # 요청 바디 설정 (POST, PUT 등)
        if data and method in ['POST', 'PUT', 'PATCH']:
            req.data = json.dumps(data).encode('utf-8')
        
        try:
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            if response_data:
                return json.loads(response_data)
            else:
                return {"status": "success", "message": "응답 데이터가 없습니다"}
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise Exception(f"HTTP 오류 {e.code}: {error_body}")
        except urllib.request.URLError as e:
            raise Exception(f"URL 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 오류: {e}")
    
    def get_return_requests(self, created_at_from: str, created_at_to: str, 
                           status: Optional[str] = None) -> Dict[str, Any]:
        """
        반품 요청 목록 조회
        
        Args:
            created_at_from: 조회 시작일 (YYYY-MM-DD)
            created_at_to: 조회 종료일 (YYYY-MM-DD)
            status: 반품 상태 (선택사항)
            
        Returns:
            Dict[str, Any]: 반품 요청 목록
        """
        query_params = {
            "createdAtFrom": created_at_from,
            "createdAtTo": created_at_to
        }
        
        if status:
            query_params["status"] = status
        
        return self._make_request("GET", "/returnRequests", query_params)
    
    def get_orders(self, created_at_from: str, created_at_to: str,
                   status: Optional[str] = None) -> Dict[str, Any]:
        """
        주문 목록 조회
        
        Args:
            created_at_from: 조회 시작일 (YYYY-MM-DD)
            created_at_to: 조회 종료일 (YYYY-MM-DD)
            status: 주문 상태 (선택사항)
            
        Returns:
            Dict[str, Any]: 주문 목록
        """
        query_params = {
            "createdAtFrom": created_at_from,
            "createdAtTo": created_at_to
        }
        
        if status:
            query_params["status"] = status
        
        return self._make_request("GET", "/orders", query_params)
    
    def get_products(self, page: int = 1, size: int = 50) -> Dict[str, Any]:
        """
        상품 목록 조회
        
        Args:
            page: 페이지 번호
            size: 페이지 크기
            
        Returns:
            Dict[str, Any]: 상품 목록
        """
        query_params = {
            "page": page,
            "size": size
        }
        
        return self._make_request("GET", "/products", query_params)
    
    def get_product_detail(self, product_id: str) -> Dict[str, Any]:
        """
        상품 상세 정보 조회
        
        Args:
            product_id: 상품 ID
            
        Returns:
            Dict[str, Any]: 상품 상세 정보
        """
        return self._make_request("GET", f"/products/{product_id}")
    
    def update_order_shipping(self, order_id: str, shipping_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 배송 정보 업데이트
        
        Args:
            order_id: 주문 ID
            shipping_info: 배송 정보
            
        Returns:
            Dict[str, Any]: 업데이트 결과
        """
        return self._make_request("PUT", f"/orders/{order_id}/shipping", data=shipping_info)