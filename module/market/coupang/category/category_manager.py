#!/usr/bin/env python3
"""
쿠팡 통합 카테고리 매니저
오프라인 Excel 데이터와 API 클라이언트를 통합한 카테고리 관리 시스템
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_client import CoupangCategoryClient
from market.coupang.category.category_recommendation_client import CoupangCategoryRecommendationClient


class CoupangCategoryManager:
    """쿠팡 통합 카테고리 매니저"""
    
    def __init__(self, 
                 access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None,
                 categories_data_path: Optional[str] = None):
        """
        카테고리 매니저 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키
            vendor_id: 쿠팡 벤더 ID
            categories_data_path: 카테고리 데이터 JSON 파일 경로
        """
        # API 클라이언트들 초기화
        self.api_client = CoupangCategoryClient(access_key, secret_key, vendor_id) if access_key else None
        self.recommendation_client = CoupangCategoryRecommendationClient(access_key, secret_key, vendor_id) if access_key else None
        
        # 오프라인 카테고리 데이터 로드
        self.categories_data = {}
        self.categories_index = {}  # 빠른 검색을 위한 인덱스
        
        if not categories_data_path:
            categories_data_path = os.path.join(current_dir, "coupang_categories_data.json")
        
        self.load_offline_data(categories_data_path)
        self._build_search_index()
    
    def load_offline_data(self, data_path: str) -> None:
        """
        오프라인 카테고리 데이터 로드
        
        Args:
            data_path: JSON 데이터 파일 경로
        """
        try:
            if os.path.exists(data_path):
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories_data = data.get('categories', {})
                    
                print(f"✅ 오프라인 카테고리 데이터 로드 완료: {len(self.categories_data)}개 카테고리")
            else:
                print(f"⚠️ 카테고리 데이터 파일 없음: {data_path}")
                print("   Excel 파싱을 먼저 실행하세요: python excel_category_parser.py")
                
        except Exception as e:
            print(f"❌ 카테고리 데이터 로드 오류: {e}")
            self.categories_data = {}
    
    def _build_search_index(self) -> None:
        """검색 인덱스 구축"""
        self.categories_index = {
            "by_name": {},      # 카테고리명으로 검색
            "by_path": {},      # 경로로 검색  
            "by_level": {},     # 레벨별 분류
            "by_file": {},      # 파일 카테고리별 분류
            "by_commission": {} # 수수료율별 분류
        }
        
        for category_id, category in self.categories_data.items():
            # 이름으로 인덱싱
            if category.get('path'):
                path_parts = category['path'].split('>')
                for part in path_parts:
                    part = part.strip()
                    if part not in self.categories_index["by_name"]:
                        self.categories_index["by_name"][part] = []
                    self.categories_index["by_name"][part].append(category_id)
            
            # 경로로 인덱싱
            if category.get('path'):
                self.categories_index["by_path"][category['path']] = category_id
            
            # 레벨별 인덱싱
            level = category.get('level', 0)
            if level not in self.categories_index["by_level"]:
                self.categories_index["by_level"][level] = []
            self.categories_index["by_level"][level].append(category_id)
            
            # 파일별 인덱싱
            file_cat = category.get('file_category', 'unknown')
            if file_cat not in self.categories_index["by_file"]:
                self.categories_index["by_file"][file_cat] = []
            self.categories_index["by_file"][file_cat].append(category_id)
            
            # 수수료율별 인덱싱
            commission = category.get('commission_rate')
            if commission:
                if commission not in self.categories_index["by_commission"]:
                    self.categories_index["by_commission"][commission] = []
                self.categories_index["by_commission"][commission].append(category_id)
    
    def get_category_info(self, category_id: str, use_api: bool = False) -> Dict[str, Any]:
        """
        카테고리 정보 조회 (오프라인 우선, API 백업)
        
        Args:
            category_id: 카테고리 ID
            use_api: True시 API 우선 사용
            
        Returns:
            Dict[str, Any]: 카테고리 정보
        """
        result = {
            "success": False,
            "category_id": category_id,
            "source": "unknown",
            "data": None
        }
        
        # API 우선 요청
        if use_api and self.api_client:
            try:
                api_data = self.api_client.get_category_metadata(category_id)
                result["success"] = True
                result["source"] = "api"
                result["data"] = api_data
                return result
            except Exception as api_error:
                print(f"⚠️ API 호출 실패, 오프라인 데이터 사용: {api_error}")
        
        # 오프라인 데이터에서 조회
        if category_id in self.categories_data:
            result["success"] = True
            result["source"] = "offline"
            result["data"] = self.categories_data[category_id]
        else:
            result["error"] = f"카테고리 ID {category_id}를 찾을 수 없습니다"
        
        return result
    
    def search_categories(self, 
                         query: str, 
                         search_type: str = "name",
                         limit: int = 20) -> List[Dict[str, Any]]:
        """
        카테고리 검색
        
        Args:
            query: 검색어
            search_type: 검색 타입 ("name", "path", "id")
            limit: 결과 제한 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        results = []
        
        if search_type == "name":
            # 카테고리명으로 검색 (부분 일치)
            for name, category_ids in self.categories_index["by_name"].items():
                if query.lower() in name.lower():
                    for cat_id in category_ids[:limit]:
                        if cat_id in self.categories_data:
                            results.append({
                                "category_id": cat_id,
                                "matched_name": name,
                                "category_info": self.categories_data[cat_id]
                            })
        
        elif search_type == "path":
            # 경로로 검색 (부분 일치)
            for path, category_id in self.categories_index["by_path"].items():
                if query.lower() in path.lower():
                    if category_id in self.categories_data:
                        results.append({
                            "category_id": category_id,
                            "matched_path": path,
                            "category_info": self.categories_data[category_id]
                        })
        
        elif search_type == "id":
            # ID로 검색 (정확 일치)
            if query in self.categories_data:
                results.append({
                    "category_id": query,
                    "matched_id": query,
                    "category_info": self.categories_data[query]
                })
        
        return results[:limit]
    
    def get_categories_by_level(self, level: int) -> List[Dict[str, Any]]:
        """
        레벨별 카테고리 조회
        
        Args:
            level: 카테고리 레벨
            
        Returns:
            List[Dict[str, Any]]: 레벨별 카테고리 리스트
        """
        category_ids = self.categories_index["by_level"].get(level, [])
        return [
            {
                "category_id": cat_id,
                "category_info": self.categories_data[cat_id]
            }
            for cat_id in category_ids
            if cat_id in self.categories_data
        ]
    
    def get_categories_by_file(self, file_category: str) -> List[Dict[str, Any]]:
        """
        파일 카테고리별 조회
        
        Args:
            file_category: 파일 카테고리명
            
        Returns:
            List[Dict[str, Any]]: 파일별 카테고리 리스트
        """
        category_ids = self.categories_index["by_file"].get(file_category, [])
        return [
            {
                "category_id": cat_id,
                "category_info": self.categories_data[cat_id]
            }
            for cat_id in category_ids
            if cat_id in self.categories_data
        ]
    
    def recommend_category(self, product_name: str, **kwargs) -> Dict[str, Any]:
        """
        상품명 기반 카테고리 추천
        
        Args:
            product_name: 상품명
            **kwargs: 추가 파라미터
            
        Returns:
            Dict[str, Any]: 추천 결과
        """
        if not self.recommendation_client:
            return {
                "success": False,
                "error": "카테고리 추천 클라이언트가 초기화되지 않았습니다"
            }
        
        try:
            # API 추천 실행
            recommendation = self.recommendation_client.get_recommendation_result(product_name, **kwargs)
            
            # 추천된 카테고리 ID로 상세 정보 보강
            if recommendation.get("success") and recommendation.get("categoryId"):
                category_id = str(recommendation["categoryId"])
                category_detail = self.get_category_info(category_id)
                
                if category_detail["success"]:
                    recommendation["categoryDetail"] = category_detail["data"]
                    recommendation["enhancedInfo"] = self._enhance_category_info(category_detail["data"])
            
            return recommendation
            
        except Exception as e:
            return {
                "success": False,
                "error": f"카테고리 추천 오류: {str(e)}"
            }
    
    def _enhance_category_info(self, category_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        카테고리 정보 보강
        
        Args:
            category_info: 기본 카테고리 정보
            
        Returns:
            Dict[str, Any]: 보강된 정보
        """
        enhanced = {
            "required_purchase_options": [],
            "available_search_options": [],
            "notice_requirements": {},
            "similar_categories": []
        }
        
        # 필수 구매 옵션 추출
        for option in category_info.get('purchase_options', []):
            if option.get('is_required', True):
                enhanced["required_purchase_options"].append(option)
        
        # 검색 옵션 정리
        enhanced["available_search_options"] = category_info.get('search_options', [])
        
        # 고시정보 요구사항
        enhanced["notice_requirements"] = category_info.get('notice_info', {})
        
        # 유사 카테고리 찾기 (같은 상위 경로)
        if category_info.get('parent_path'):
            similar_cats = self.search_categories(category_info['parent_path'], 'path', 5)
            enhanced["similar_categories"] = [
                {
                    "id": cat["category_id"],
                    "name": cat["category_info"]["path"].split(">")[-1] if cat["category_info"].get("path") else "Unknown"
                }
                for cat in similar_cats
                if cat["category_id"] != category_info.get("id")
            ]
        
        return enhanced
    
    def validate_product_data(self, category_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        상품 데이터 검증 (필수 옵션 체크)
        
        Args:
            category_id: 카테고리 ID
            product_data: 상품 데이터
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        validation_result = {
            "isValid": True,
            "score": 100,
            "missingRequiredOptions": [],
            "invalidOptions": [],
            "suggestions": []
        }
        
        # 카테고리 정보 조회
        category_info = self.get_category_info(category_id)
        
        if not category_info["success"]:
            validation_result["isValid"] = False
            validation_result["score"] = 0
            validation_result["suggestions"].append(f"카테고리 {category_id} 정보를 찾을 수 없습니다")
            return validation_result
        
        category = category_info["data"]
        
        # 필수 구매 옵션 체크
        for option in category.get('purchase_options', []):
            if option.get('is_required', True):
                option_name = option['type']
                
                if option_name not in product_data:
                    validation_result["missingRequiredOptions"].append(option_name)
                    validation_result["score"] -= 20
                    validation_result["suggestions"].append(f"필수 옵션 '{option_name}' 누락")
                else:
                    # 옵션 값 유효성 체크
                    provided_value = product_data[option_name]
                    valid_values = option.get('values', [])
                    
                    if valid_values and provided_value not in valid_values:
                        validation_result["invalidOptions"].append({
                            "option": option_name,
                            "providedValue": provided_value,
                            "validValues": valid_values
                        })
                        validation_result["score"] -= 10
                        validation_result["suggestions"].append(
                            f"옵션 '{option_name}' 값이 유효하지 않습니다. 가능한 값: {', '.join(valid_values[:5])}"
                        )
        
        # 최종 유효성 판단
        if validation_result["score"] < 60:
            validation_result["isValid"] = False
        
        if validation_result["missingRequiredOptions"]:
            validation_result["isValid"] = False
        
        return validation_result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        카테고리 통계 정보 반환
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        stats = {
            "총_카테고리_수": len(self.categories_data),
            "파일별_분포": {},
            "레벨별_분포": {},
            "수수료율_분포": {},
            "최다_구매옵션_카테고리": [],
            "최다_검색옵션_카테고리": []
        }
        
        # 파일별 분포
        for file_cat, cat_ids in self.categories_index["by_file"].items():
            stats["파일별_분포"][file_cat] = len(cat_ids)
        
        # 레벨별 분포
        for level, cat_ids in self.categories_index["by_level"].items():
            stats["레벨별_분포"][f"레벨_{level}"] = len(cat_ids)
        
        # 수수료율 분포
        for commission, cat_ids in self.categories_index["by_commission"].items():
            stats["수수료율_분포"][f"{commission}%"] = len(cat_ids)
        
        # 옵션 수가 많은 카테고리들
        categories_with_options = []
        for cat_id, category in self.categories_data.items():
            purchase_count = len(category.get('purchase_options', []))
            search_count = len(category.get('search_options', []))
            
            if purchase_count > 0 or search_count > 0:
                categories_with_options.append({
                    "id": cat_id,
                    "path": category.get('path', ''),
                    "purchase_options": purchase_count,
                    "search_options": search_count,
                    "total_options": purchase_count + search_count
                })
        
        # 구매 옵션이 많은 상위 5개
        stats["최다_구매옵션_카테고리"] = sorted(
            categories_with_options, 
            key=lambda x: x["purchase_options"], 
            reverse=True
        )[:5]
        
        # 검색 옵션이 많은 상위 5개
        stats["최다_검색옵션_카테고리"] = sorted(
            categories_with_options, 
            key=lambda x: x["search_options"], 
            reverse=True
        )[:5]
        
        return stats


def main():
    """사용 예제"""
    print("🚀 쿠팡 통합 카테고리 매니저 테스트")
    
    # 매니저 초기화 (오프라인 전용)
    manager = CoupangCategoryManager()
    
    # 통계 정보 출력
    print(f"\n📊 카테고리 통계:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        if isinstance(value, dict) and len(value) < 10:
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     - {sub_key}: {sub_value}")
        elif isinstance(value, list) and len(value) < 10:
            print(f"   {key}:")
            for item in value:
                if isinstance(item, dict):
                    path = item.get('path', 'Unknown')[:50]
                    print(f"     - {path}... (구매:{item.get('purchase_options', 0)}, 검색:{item.get('search_options', 0)})")
                else:
                    print(f"     - {item}")
        else:
            print(f"   {key}: {value}")
    
    # 검색 테스트
    print(f"\n🔍 카테고리 검색 테스트:")
    search_queries = ["TV", "티셔츠", "라면"]
    
    for query in search_queries:
        print(f"\n검색어: '{query}'")
        results = manager.search_categories(query, "name", 3)
        for result in results:
            cat_info = result["category_info"]
            print(f"   - [{result['category_id']}] {cat_info.get('path', 'Unknown')}")


if __name__ == "__main__":
    main()