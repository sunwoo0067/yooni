#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 카테고리 메타정보 조회 클라이언트
"""

import sys
import os
import ssl
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

# 상위 디렉토리 import를 위한 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from auth import CoupangAuth


class CoupangCategoryClient:
    """쿠팡 카테고리 메타정보 조회 클라이언트"""
    
    BASE_URL = "https://api-gateway.coupang.com"
    CATEGORY_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes"
    DISPLAY_CATEGORY_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/meta/display-categories"
    CATEGORY_STATUS_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/meta/display-categories"
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        카테고리 클라이언트 초기화
        
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
    
    def get_category_metadata(self, display_category_code: int) -> Dict[str, Any]:
        """
        카테고리 메타정보 조회
        
        Args:
            display_category_code: 노출카테고리코드 (숫자)
            
        Returns:
            Dict[str, Any]: 카테고리 메타정보
            
        Raises:
            ValueError: 잘못된 카테고리 코드
            Exception: API 호출 오류
        """
        if not isinstance(display_category_code, int) or display_category_code <= 0:
            raise ValueError("노출카테고리코드는 양수여야 합니다")
        
        # API 경로 생성 (vendor_id 없이 직접 사용)
        path = f"{self.CATEGORY_API_PATH}/{display_category_code}"
        
        # 인증 헤더 생성
        headers = self.auth.generate_authorization_header("GET", path)
        
        # URL 생성
        url = f"{self.BASE_URL}{path}"
        
        try:
            import ssl
            import json
            import urllib.request
            
            # SSL 컨텍스트 설정
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 요청 객체 생성
            req = urllib.request.Request(url)
            
            # 헤더 추가
            for key, value in headers.items():
                req.add_header(key, value)
            
            # 요청 실행
            response = urllib.request.urlopen(req, context=ssl_context)
            
            # 응답 읽기
            charset = response.headers.get_content_charset() or 'utf-8'
            response_data = response.read().decode(charset)
            
            # JSON 파싱
            result = json.loads(response_data)
            
            if result.get('code') == 'SUCCESS':
                return result
            else:
                raise Exception(f"API 오류: {result.get('message', '알 수 없는 오류')}")
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            if e.code == 400:
                if "관리카테고리를 찾을 수 없는" in error_body:
                    raise ValueError(f"유효하지 않은 노출카테고리코드입니다: {display_category_code}")
                elif "숫자형으로 입력" in error_body:
                    raise ValueError("노출카테고리코드는 숫자로만 입력 가능합니다")
            
            raise Exception(f"HTTP 오류 {e.code}: {error_body}")
        except urllib.request.URLError as e:
            raise Exception(f"URL 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 오류: {e}")
    
    def get_category_attributes(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        카테고리 속성(옵션) 목록 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 카테고리 속성 목록
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('attributes', [])
    
    def get_required_attributes(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        필수 속성만 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 필수 속성 목록
        """
        attributes = self.get_category_attributes(display_category_code)
        return [attr for attr in attributes if attr.get('required') == 'MANDATORY']
    
    def get_purchase_options(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        구매옵션(노출 속성)만 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 구매옵션 목록
        """
        attributes = self.get_category_attributes(display_category_code)
        return [attr for attr in attributes if attr.get('exposed') == 'EXPOSED']
    
    def get_notice_categories(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        상품고시정보 목록 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 상품고시정보 목록
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('noticeCategories', [])
    
    def get_required_documents(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        구비서류 목록 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 구비서류 목록
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('requiredDocumentNames', [])
    
    def get_certifications(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        인증정보 목록 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 인증정보 목록
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('certifications', [])
    
    def get_allowed_conditions(self, display_category_code: int) -> List[str]:
        """
        허용된 상품 상태 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[str]: 허용된 상품 상태 목록 (NEW, REFURBISHED, USED_BEST, etc.)
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('allowedOfferConditions', [])
    
    def is_single_item_allowed(self, display_category_code: int) -> bool:
        """
        단일상품 등록 가능 여부 확인
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            bool: 단일상품 등록 가능 여부
        """
        metadata = self.get_category_metadata(display_category_code)
        return metadata.get('data', {}).get('isAllowSingleItem', False)
    
    def get_display_categories(self, display_category_code: int = 0) -> Dict[str, Any]:
        """
        노출 카테고리 정보 조회
        
        Args:
            display_category_code: 노출카테고리코드 (0: 1 Depth 카테고리 조회)
            
        Returns:
            Dict[str, Any]: 노출 카테고리 정보
            
        Raises:
            ValueError: 잘못된 카테고리 코드
            Exception: API 호출 오류
        """
        if not isinstance(display_category_code, int) or display_category_code < 0:
            raise ValueError("노출카테고리코드는 0 이상의 숫자여야 합니다")
        
        # API 경로 생성
        api_path = f"{self.DISPLAY_CATEGORY_API_PATH}/{display_category_code}"
        
        try:
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", api_path)
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
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
            
            # 응답 검증
            if result.get('code') == 'SUCCESS':
                return result
            else:
                raise Exception(f"API 오류 (코드: {result.get('code')}): {result.get('message', '알 수 없는 오류')}")
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                if "찾을 수 없습니다" in error_body:
                    raise ValueError(f"전시카테고리[{display_category_code}]를 찾을 수 없습니다. 전시카테고리코드를 확인해 주세요.")
                elif "숫자형으로 입력해주세요" in error_body:
                    raise ValueError("노출카테고리코드는 숫자형으로 입력해주세요.")
                else:
                    raise ValueError(f"잘못된 요청: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def get_all_first_depth_categories(self) -> List[Dict[str, Any]]:
        """
        1 Depth 카테고리 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 1 Depth 카테고리 목록
        """
        try:
            response = self.get_display_categories(0)  # 0으로 설정하면 1 Depth 조회
            data = response.get('data', {})
            
            return data.get('child', [])
            
        except Exception as e:
            print(f"❌ 1 Depth 카테고리 조회 오류: {e}")
            return []
    
    def get_category_hierarchy(self, display_category_code: int, max_depth: int = 3) -> Dict[str, Any]:
        """
        카테고리 계층 구조 조회 (재귀적으로 하위 카테고리까지)
        
        Args:
            display_category_code: 시작 노출카테고리코드
            max_depth: 최대 조회 깊이
            
        Returns:
            Dict[str, Any]: 카테고리 계층 구조
        """
        def _get_hierarchy_recursive(code: int, current_depth: int = 0) -> Dict[str, Any]:
            """재귀적으로 카테고리 계층 구조 조회"""
            if current_depth >= max_depth:
                return None
            
            try:
                response = self.get_display_categories(code)
                data = response.get('data', {})
                
                category_info = {
                    "displayCategoryCode": data.get('displayItemCategoryCode'),
                    "name": data.get('name'),
                    "status": data.get('status'),
                    "depth": current_depth,
                    "children": []
                }
                
                # 하위 카테고리가 있으면 재귀 호출
                children = data.get('child', [])
                if children and current_depth < max_depth - 1:
                    for child in children:
                        child_code = child.get('displayItemCategoryCode')
                        if child_code:
                            child_hierarchy = _get_hierarchy_recursive(child_code, current_depth + 1)
                            if child_hierarchy:
                                category_info["children"].append(child_hierarchy)
                
                return category_info
                
            except Exception as e:
                print(f"⚠️ 카테고리 {code} 조회 실패: {e}")
                return None
        
        return _get_hierarchy_recursive(display_category_code)
    
    def search_categories_by_name(self, search_name: str) -> List[Dict[str, Any]]:
        """
        카테고리명으로 검색
        
        Args:
            search_name: 검색할 카테고리명
            
        Returns:
            List[Dict[str, Any]]: 검색된 카테고리 목록
        """
        results = []
        
        # 1 Depth 카테고리들을 가져와서 검색
        first_depth_categories = self.get_all_first_depth_categories()
        
        for category in first_depth_categories:
            if search_name.lower() in category.get('name', '').lower():
                results.append(category)
                
            # 하위 카테고리도 검색 (2 Depth까지)
            try:
                child_response = self.get_display_categories(category.get('displayItemCategoryCode', 0))
                child_data = child_response.get('data', {})
                child_categories = child_data.get('child', [])
                
                for child in child_categories:
                    if search_name.lower() in child.get('name', '').lower():
                        # 상위 카테고리 정보도 포함
                        child_with_parent = child.copy()
                        child_with_parent['parentName'] = category.get('name')
                        child_with_parent['parentCode'] = category.get('displayItemCategoryCode')
                        results.append(child_with_parent)
                        
            except Exception as e:
                # 개별 카테고리 조회 실패는 무시하고 계속 진행
                continue
        
        return results
    
    def get_category_path(self, display_category_code: int) -> str:
        """
        카테고리 경로 문자열 생성
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            str: 카테고리 경로 (예: "가전/디지털 > TV/영상가전 > TV")
        """
        try:
            # 먼저 해당 카테고리 정보 조회
            response = self.get_display_categories(display_category_code)
            data = response.get('data', {})
            
            current_name = data.get('name', '알 수 없음')
            
            # 1 Depth인 경우 바로 반환
            first_depth_categories = self.get_all_first_depth_categories()
            for category in first_depth_categories:
                if category.get('displayItemCategoryCode') == display_category_code:
                    return current_name
            
            # 2 Depth 이상인 경우 상위 카테고리 찾기
            for parent_category in first_depth_categories:
                try:
                    parent_response = self.get_display_categories(parent_category.get('displayItemCategoryCode', 0))
                    parent_data = parent_response.get('data', {})
                    children = parent_data.get('child', [])
                    
                    for child in children:
                        if child.get('displayItemCategoryCode') == display_category_code:
                            parent_name = parent_category.get('name', '알 수 없음')
                            return f"{parent_name} > {current_name}"
                            
                except Exception:
                    continue
            
            return current_name
            
        except Exception as e:
            return f"경로 조회 실패: {e}"
    
    def check_category_status(self, display_category_code: int) -> Dict[str, Any]:
        """
        카테고리 유효성 검사 (사용 가능 여부 확인)
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            Dict[str, Any]: 카테고리 사용 가능 여부 정보
            
        Raises:
            ValueError: 잘못된 카테고리 코드 또는 leaf category가 아닌 경우
            Exception: API 호출 오류
        """
        if not isinstance(display_category_code, int) or display_category_code <= 0:
            raise ValueError("노출카테고리코드는 양의 정수여야 합니다")
        
        # API 경로 생성
        api_path = f"{self.CATEGORY_STATUS_API_PATH}/{display_category_code}/status"
        
        try:
            # 인증 헤더 생성 (GET 요청)
            headers = self.auth.generate_authorization_header("GET", api_path)
            
            # URL 생성
            url = f"{self.BASE_URL}{api_path}"
            
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
            
            # 응답 검증 및 구조화
            if result.get('code') == 'SUCCESS':
                is_available = result.get('data', False)
                
                return {
                    "success": True,
                    "categoryCode": display_category_code,
                    "isAvailable": is_available,
                    "status": "AVAILABLE" if is_available else "UNAVAILABLE",
                    "message": "사용 가능" if is_available else "사용 불가능",
                    "originalResponse": result
                }
            else:
                return {
                    "success": False,
                    "categoryCode": display_category_code,
                    "isAvailable": False,
                    "error": result.get('message', '알 수 없는 오류'),
                    "originalResponse": result
                }
                
        except urllib.request.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            
            # 구체적인 오류 메시지 처리
            if e.code == 400:
                if "숫자형으로 입력해주세요" in error_body:
                    raise ValueError("노출카테고리코드는 숫자형으로 입력해주세요.")
                elif "leaf category code가 아닙니다" in error_body:
                    # leaf category ID 추출
                    import re
                    leaf_ids_match = re.search(r'leaf category id는 ([0-9,]+)', error_body)
                    leaf_ids = []
                    if leaf_ids_match:
                        leaf_ids = [int(id.strip()) for id in leaf_ids_match.group(1).split(',')]
                    
                    raise ValueError(f"노출카테고리 {display_category_code}은 leaf category가 아닙니다. leaf category ID: {leaf_ids}")
                else:
                    raise ValueError(f"잘못된 요청: {error_body}")
            else:
                raise Exception(f"HTTP 오류 {e.code}: {error_body}")
                
        except urllib.request.URLError as e:
            raise Exception(f"네트워크 오류: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
    
    def is_category_available(self, display_category_code: int) -> bool:
        """
        카테고리 사용 가능 여부 간단 확인
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            bool: 사용 가능 여부 (True: 사용 가능, False: 사용 불가능 또는 오류)
        """
        try:
            status_result = self.check_category_status(display_category_code)
            return status_result.get("isAvailable", False)
        except Exception:
            return False
    
    def validate_categories_batch(self, category_codes: List[int]) -> Dict[str, Any]:
        """
        여러 카테고리 유효성 일괄 검사
        
        Args:
            category_codes: 검사할 노출카테고리코드 리스트
            
        Returns:
            Dict[str, Any]: 일괄 검사 결과
        """
        results = {
            "totalCount": len(category_codes),
            "availableCount": 0,
            "unavailableCount": 0,
            "errorCount": 0,
            "details": [],
            "summary": {
                "available": [],
                "unavailable": [],
                "errors": []
            }
        }
        
        print(f"📊 {len(category_codes)}개 카테고리 일괄 유효성 검사 시작...")
        
        for i, code in enumerate(category_codes, 1):
            print(f"   📦 {i}/{len(category_codes)} - 카테고리 {code} 검사 중...")
            
            try:
                status_result = self.check_category_status(code)
                
                detail = {
                    "categoryCode": code,
                    "success": status_result["success"],
                    "isAvailable": status_result.get("isAvailable", False),
                    "status": status_result.get("status", "UNKNOWN"),
                    "message": status_result.get("message", ""),
                    "error": status_result.get("error")
                }
                
                results["details"].append(detail)
                
                if status_result["success"] and status_result.get("isAvailable"):
                    results["availableCount"] += 1
                    results["summary"]["available"].append(code)
                elif status_result["success"]:
                    results["unavailableCount"] += 1
                    results["summary"]["unavailable"].append(code)
                else:
                    results["errorCount"] += 1
                    results["summary"]["errors"].append({"code": code, "error": status_result.get("error")})
                
            except Exception as e:
                results["errorCount"] += 1
                error_detail = {
                    "categoryCode": code,
                    "success": False,
                    "isAvailable": False,
                    "status": "ERROR",
                    "message": "",
                    "error": str(e)
                }
                results["details"].append(error_detail)
                results["summary"]["errors"].append({"code": code, "error": str(e)})
        
        print(f"✅ 일괄 검사 완료:")
        print(f"   사용 가능: {results['availableCount']}개")
        print(f"   사용 불가능: {results['unavailableCount']}개") 
        print(f"   오류: {results['errorCount']}개")
        
        return results
    
    def find_leaf_categories(self, display_category_code: int) -> List[int]:
        """
        특정 카테고리의 leaf category 찾기
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[int]: leaf category 코드 리스트
        """
        leaf_categories = []
        
        try:
            # 먼저 해당 카테고리가 leaf인지 확인
            try:
                status_result = self.check_category_status(display_category_code)
                if status_result["success"]:
                    # leaf category이면 자기 자신을 반환
                    return [display_category_code]
            except ValueError as e:
                # leaf category가 아닌 경우 오류 메시지에서 leaf ID 추출
                error_message = str(e)
                if "leaf category ID:" in error_message:
                    import re
                    numbers = re.findall(r'\d+', error_message.split("leaf category ID:")[-1])
                    leaf_categories = [int(num) for num in numbers]
                    return leaf_categories
            
            # 하위 카테고리들을 재귀적으로 탐색
            try:
                response = self.get_display_categories(display_category_code)
                data = response.get('data', {})
                children = data.get('child', [])
                
                if not children:
                    # 하위 카테고리가 없으면 자신이 leaf
                    return [display_category_code]
                
                # 하위 카테고리들을 재귀적으로 확인
                for child in children:
                    child_code = child.get('displayItemCategoryCode')
                    if child_code:
                        child_leafs = self.find_leaf_categories(child_code)
                        leaf_categories.extend(child_leafs)
                        
            except Exception:
                pass
            
        except Exception as e:
            print(f"⚠️ leaf category 찾기 실패 ({display_category_code}): {e}")
        
        return leaf_categories
    
    def get_category_status_summary(self, display_category_code: int) -> Dict[str, Any]:
        """
        카테고리 상태 종합 정보 조회
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            Dict[str, Any]: 카테고리 상태 종합 정보
        """
        summary = {
            "categoryCode": display_category_code,
            "categoryInfo": None,
            "statusCheck": None,
            "leafCategories": [],
            "isLeafCategory": False,
            "recommendation": ""
        }
        
        try:
            # 1. 카테고리 기본 정보 조회
            try:
                category_response = self.get_display_categories(display_category_code)
                summary["categoryInfo"] = {
                    "name": category_response.get('data', {}).get('name', 'Unknown'),
                    "status": category_response.get('data', {}).get('status', 'Unknown'),
                    "hasChildren": bool(category_response.get('data', {}).get('child', []))
                }
            except Exception as e:
                summary["categoryInfo"] = {"error": str(e)}
            
            # 2. 카테고리 상태 확인
            try:
                status_result = self.check_category_status(display_category_code)
                summary["statusCheck"] = status_result
                summary["isLeafCategory"] = True
                summary["recommendation"] = "이 카테고리는 상품 등록에 사용할 수 있습니다." if status_result.get("isAvailable") else "이 카테고리는 현재 사용할 수 없습니다."
                
            except ValueError as e:
                summary["statusCheck"] = {"error": str(e)}
                
                # leaf category가 아닌 경우 leaf 찾기
                if "leaf category가 아닙니다" in str(e):
                    summary["isLeafCategory"] = False
                    try:
                        leaf_categories = self.find_leaf_categories(display_category_code)
                        summary["leafCategories"] = leaf_categories
                        summary["recommendation"] = f"이 카테고리는 leaf category가 아닙니다. 다음 leaf category 중 하나를 사용하세요: {leaf_categories}"
                    except Exception:
                        summary["recommendation"] = "leaf category를 찾을 수 없습니다. 하위 카테고리를 확인하세요."
                else:
                    summary["recommendation"] = f"카테고리 확인 중 오류가 발생했습니다: {e}"
            
            except Exception as e:
                summary["statusCheck"] = {"error": str(e)}
                summary["recommendation"] = f"카테고리 상태 확인 중 오류가 발생했습니다: {e}"
        
        except Exception as e:
            summary["recommendation"] = f"전체 조회 중 오류가 발생했습니다: {e}"
        
        return summary