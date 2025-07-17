#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 카테고리 추천 클라이언트
머신러닝 기반 상품 카테고리 자동 추천 서비스
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any, Union

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from auth import CoupangAuth


class CoupangCategoryRecommendationClient:
    """쿠팡 카테고리 추천 클라이언트"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    RECOMMENDATION_API_PATH = "/v2/providers/openapi/apis/api/v1/categorization/predict"
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        카테고리 추천 클라이언트 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키  
            vendor_id: 쿠팡 벤더 ID
        """
        self.auth = CoupangAuth(access_key, secret_key, vendor_id)
        
        # SSL 컨텍스트 설정
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def predict_category(self, product_name: str, 
                        product_description: Optional[str] = None,
                        brand: Optional[str] = None,
                        attributes: Optional[Dict[str, Any]] = None,
                        seller_sku_code: Optional[str] = None) -> Dict[str, Any]:
        """
        상품 정보 기반 카테고리 추천
        
        Args:
            product_name: 상품명 (필수)
            product_description: 상품 상세설명 (선택)
            brand: 브랜드 (선택)
            attributes: 상품 속성 정보 (선택) - 예: {"색상": "빨간색", "사이즈": "L"}
            seller_sku_code: 판매자 상품코드 (선택)
            
        Returns:
            Dict[str, Any]: 카테고리 추천 결과
            
        Raises:
            ValueError: 필수 파라미터 누락
            Exception: API 호출 오류
        """
        if not product_name or not product_name.strip():
            raise ValueError("상품명(product_name)은 필수 입력 항목입니다")
        
        # 요청 데이터 구성
        request_data = {
            "productName": product_name.strip()
        }
        
        # 선택적 파라미터 추가
        if product_description and product_description.strip():
            request_data["productDescription"] = product_description.strip()
        
        if brand and brand.strip():
            request_data["brand"] = brand.strip()
        
        if attributes:
            request_data["attributes"] = attributes
        
        if seller_sku_code and seller_sku_code.strip():
            request_data["sellerSkuCode"] = seller_sku_code.strip()
        
        # API 호출
        try:
            # 인증 헤더 생성 (POST 요청)
            headers = self.auth.generate_authorization_header("POST", self.RECOMMENDATION_API_PATH)
            
            # URL 생성
            url = f"{self.BASE_URL}{self.RECOMMENDATION_API_PATH}"
            
            # 요청 객체 생성
            req = urllib.request.Request(url)
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # POST 데이터 설정
            req.data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            req.get_method = lambda: "POST"
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 검증
            if result.get('code') == 200:
                return result
            else:
                raise Exception(f"API 오류 (코드: {result.get('code')}): {result.get('message', '알 수 없는 오류')}")
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                if "should not be empty" in error_body:
                    raise ValueError("상품명이 비어있습니다. 상품명을 입력해주세요.")
                else:
                    raise ValueError(f"잘못된 요청: {error_body}")
            elif e.code == 500:
                if "Internal Server Error" in error_body:
                    raise Exception("서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                else:
                    raise Exception(f"서버 오류: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def get_recommendation_result(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        카테고리 추천 결과 간편 조회
        
        Args:
            product_name: 상품명
            **kwargs: 추가 파라미터 (product_description, brand, attributes, seller_sku_code)
            
        Returns:
            Dict[str, Any]: 추천 결과 요약
        """
        try:
            response = self.predict_category(product_name, **kwargs)
            data = response.get('data', {})
            
            result = {
                "success": True,
                "resultType": data.get('autoCategorizationPredictionResultType'),
                "categoryId": data.get('predictedCategoryId'),
                "categoryName": data.get('predictedCategoryName'),
                "comment": data.get('comment'),
                "confidence": self._get_confidence_level(data.get('autoCategorizationPredictionResultType')),
                "originalResponse": response
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "resultType": "ERROR",
                "categoryId": None,
                "categoryName": None,
                "comment": None,
                "confidence": "없음"
            }
    
    def _get_confidence_level(self, result_type: str) -> str:
        """
        결과 타입에 따른 신뢰도 수준 반환
        
        Args:
            result_type: 결과 타입
            
        Returns:
            str: 신뢰도 수준
        """
        confidence_map = {
            "SUCCESS": "높음",
            "FAILURE": "낮음", 
            "INSUFFICIENT_INFORMATION": "정보부족"
        }
        return confidence_map.get(result_type, "알 수 없음")
    
    def bulk_predict_categories(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 상품에 대한 카테고리 일괄 추천
        
        Args:
            products: 상품 정보 리스트
                예: [{"productName": "상품명1", "brand": "브랜드1"}, ...]
                
        Returns:
            List[Dict[str, Any]]: 각 상품별 추천 결과 리스트
        """
        results = []
        
        for i, product in enumerate(products):
            print(f"📦 상품 {i+1}/{len(products)} 처리 중...")
            
            try:
                product_name = product.get('productName')
                if not product_name:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "상품명이 없습니다",
                        "productName": None
                    })
                    continue
                
                # 카테고리 추천 실행
                result = self.get_recommendation_result(
                    product_name,
                    product_description=product.get('productDescription'),
                    brand=product.get('brand'),
                    attributes=product.get('attributes'),
                    seller_sku_code=product.get('sellerSkuCode')
                )
                
                result["index"] = i
                result["productName"] = product_name
                results.append(result)
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "productName": product.get('productName', 'Unknown')
                })
        
        return results
    
    def validate_product_name(self, product_name: str) -> Dict[str, Any]:
        """
        상품명 품질 검증 및 개선 제안
        
        Args:
            product_name: 검증할 상품명
            
        Returns:
            Dict[str, Any]: 검증 결과 및 개선 제안
        """
        validation_result = {
            "productName": product_name,
            "isValid": True,
            "score": 100,  # 기본 점수
            "issues": [],
            "suggestions": [],
            "examples": []
        }
        
        if not product_name or not product_name.strip():
            validation_result["isValid"] = False
            validation_result["score"] = 0
            validation_result["issues"].append("상품명이 비어있습니다")
            return validation_result
        
        name = product_name.strip()
        
        # 길이 검증
        if len(name) < 10:
            validation_result["score"] -= 20
            validation_result["issues"].append("상품명이 너무 짧습니다 (10자 이상 권장)")
            validation_result["suggestions"].append("브랜드명, 상품 타입, 주요 특징을 포함하세요")
        
        if len(name) > 100:
            validation_result["score"] -= 10
            validation_result["issues"].append("상품명이 너무 깁니다 (100자 이하 권장)")
            validation_result["suggestions"].append("핵심 정보만 간결하게 작성하세요")
        
        # 모호한 키워드 검증
        ambiguous_keywords = ['/', '또는', 'or', '&', '+', '세트']
        for keyword in ambiguous_keywords:
            if keyword in name:
                validation_result["score"] -= 15
                validation_result["issues"].append(f"모호한 키워드 '{keyword}' 포함")
                validation_result["suggestions"].append("하나의 명확한 상품으로 구체화하세요")
        
        # 정보 부족 검증
        if not any(char.isdigit() for char in name):
            validation_result["score"] -= 10
            validation_result["suggestions"].append("용량, 사이즈, 수량 등 구체적 수치 포함 권장")
        
        # 카테고리별 특화 검증
        if any(keyword in name.lower() for keyword in ['티셔츠', '셔츠', '바지', '원피스']):
            if not any(keyword in name for keyword in ['남성', '여성', '남녀공용', '키즈']):
                validation_result["score"] -= 15
                validation_result["issues"].append("의류 상품에 성별 구분이 없습니다")
                validation_result["suggestions"].append("남성용/여성용/남녀공용을 명시하세요")
                validation_result["examples"].append("라운드티셔츠 남성 긴팔 맨투맨")
        
        # 최종 점수에 따른 유효성 판단
        if validation_result["score"] < 60:
            validation_result["isValid"] = False
        
        return validation_result
    
    def check_auto_category_agreement(self, vendor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        카테고리 자동 매칭 서비스 동의 확인
        
        Args:
            vendor_id: 판매자ID (업체코드) - 미제공시 기본 vendor_id 사용
            
        Returns:
            Dict[str, Any]: 동의 확인 결과
            
        Raises:
            ValueError: 잘못된 vendor_id
            Exception: API 호출 오류
        """
        # vendor_id 결정
        check_vendor_id = vendor_id or self.auth.vendor_id
        if not check_vendor_id:
            raise ValueError("vendor_id가 필요합니다. 클라이언트 초기화 시 제공하거나 파라미터로 전달하세요.")
        
        # API 경로 생성
        agreement_path = f"/v2/providers/seller_api/apis/api/v1/marketplace/vendors/{check_vendor_id}/check-auto-category-agreed"
        
        try:
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", agreement_path)
            
            # URL 생성
            url = f"{self.BASE_URL}{agreement_path}"
            
            # 요청 객체 생성
            req = urllib.request.Request(url)
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=self.ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            # 응답 구조화
            if result.get('code') == 'SUCCESS':
                is_agreed = result.get('data', False)
                return {
                    "success": True,
                    "vendorId": check_vendor_id,
                    "isAgreed": is_agreed,
                    "message": "동의함" if is_agreed else "미동의",
                    "status": "AGREED" if is_agreed else "NOT_AGREED",
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "vendorId": check_vendor_id,
                    "error": result.get('message', '알 수 없는 오류'),
                    "isAgreed": False,
                    "status": "ERROR"
                }
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            if e.code == 400:
                if "다른 업체" in error_body and "검색 수 없습니다" in error_body:
                    return {
                        "success": False,
                        "vendorId": check_vendor_id,
                        "error": f"잘못된 판매자ID입니다: {check_vendor_id}",
                        "isAgreed": False,
                        "status": "INVALID_VENDOR_ID"
                    }
                else:
                    return {
                        "success": False,
                        "vendorId": check_vendor_id,
                        "error": f"요청 오류: {error_body}",
                        "isAgreed": False,
                        "status": "BAD_REQUEST"
                    }
            else:
                return {
                    "success": False,
                    "vendorId": check_vendor_id,
                    "error": f"HTTP 오류 {e.code}: {error_body}",
                    "isAgreed": False,
                    "status": "HTTP_ERROR"
                }
                
        except urllib.request.URLError as e:
            return {
                "success": False,
                "vendorId": check_vendor_id,
                "error": f"네트워크 오류: {e.reason}",
                "isAgreed": False,
                "status": "NETWORK_ERROR"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "vendorId": check_vendor_id,
                "error": f"응답 파싱 오류: {e}",
                "isAgreed": False,
                "status": "PARSE_ERROR"
            }
    
    def can_use_auto_category(self, vendor_id: Optional[str] = None) -> bool:
        """
        카테고리 자동 매칭 서비스 사용 가능 여부 확인
        
        Args:
            vendor_id: 판매자ID (업체코드)
            
        Returns:
            bool: 사용 가능 여부
        """
        try:
            result = self.check_auto_category_agreement(vendor_id)
            return result.get("isAgreed", False)
        except Exception:
            return False
    
    def predict_category_with_agreement_check(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        동의 확인 후 카테고리 추천 (안전한 추천)
        
        Args:
            product_name: 상품명
            **kwargs: 추가 파라미터
            
        Returns:
            Dict[str, Any]: 추천 결과 (동의 확인 포함)
        """
        try:
            # 1단계: 동의 확인
            agreement_check = self.check_auto_category_agreement()
            
            if not agreement_check["success"]:
                return {
                    "success": False,
                    "error": f"동의 확인 실패: {agreement_check['error']}",
                    "agreementStatus": agreement_check["status"],
                    "categoryRecommendation": None
                }
            
            if not agreement_check["isAgreed"]:
                return {
                    "success": False,
                    "error": "카테고리 자동 매칭 서비스에 동의하지 않았습니다",
                    "agreementStatus": "NOT_AGREED",
                    "categoryRecommendation": None,
                    "agreementGuide": {
                        "description": "판매관리시스템(WING)에서 동의 필요",
                        "steps": [
                            "1. 판매관리시스템(WING) 로그인",
                            "2. 우측상단 업체명 클릭", 
                            "3. 추가판매정보 클릭",
                            "4. 카테고리 자동매칭 서비스 동의"
                        ]
                    }
                }
            
            # 2단계: 동의 확인됨 - 카테고리 추천 실행
            recommendation_result = self.get_recommendation_result(product_name, **kwargs)
            
            return {
                "success": True,
                "agreementStatus": "AGREED",
                "categoryRecommendation": recommendation_result,
                "vendorId": agreement_check["vendorId"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"처리 중 오류 발생: {str(e)}",
                "agreementStatus": "UNKNOWN",
                "categoryRecommendation": None
            }