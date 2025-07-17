#!/usr/bin/env python3
"""
쿠팡 노출 카테고리 조회 API 사용 예제
displayCategoryCode를 이용한 카테고리 정보 조회 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_client import CoupangCategoryClient


def test_first_depth_categories():
    """1 Depth 카테고리 조회 테스트"""
    print("=" * 60 + " 1 Depth 카테고리 조회 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = CoupangCategoryClient()
        print("✅ 쿠팡 카테고리 클라이언트 초기화 성공")
        
        # 1 Depth 카테고리 조회 (displayCategoryCode = 0)
        print(f"\n📂 1 Depth 카테고리 목록 조회 중...")
        categories = client.get_all_first_depth_categories()
        
        if categories:
            print(f"✅ {len(categories)}개의 1 Depth 카테고리 발견")
            print(f"\n📋 카테고리 목록:")
            
            for i, category in enumerate(categories, 1):
                code = category.get('displayItemCategoryCode', 'Unknown')
                name = category.get('name', 'Unknown')
                status = category.get('status', 'Unknown')
                status_emoji = "✅" if status == "ACTIVE" else "⚠️" if status == "READY" else "❌"
                
                print(f"   {i:2d}. [{code:6}] {name} {status_emoji}")
        else:
            print("❌ 1 Depth 카테고리를 찾을 수 없습니다")
            
    except Exception as e:
        print(f"❌ 1 Depth 카테고리 조회 오류: {e}")


def test_specific_category_lookup():
    """특정 노출 카테고리 조회 테스트"""
    print("\n" + "=" * 60 + " 특정 카테고리 조회 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 테스트할 카테고리 코드들
        test_categories = [
            {"code": 62588, "name": "가전/디지털"},
            {"code": 69182, "name": "패션의류잡화"},
            {"code": 59258, "name": "식품"},
            {"code": 0, "name": "ROOT 카테고리"}
        ]
        
        for test_cat in test_categories:
            code = test_cat["code"]
            expected_name = test_cat["name"]
            
            print(f"\n📂 카테고리 {code} ({expected_name}) 조회 중...")
            
            try:
                response = client.get_display_categories(code)
                data = response.get('data', {})
                
                print(f"✅ 조회 성공:")
                print(f"   📝 이름: {data.get('name', 'Unknown')}")
                print(f"   🏷️ 코드: {data.get('displayItemCategoryCode', 'Unknown')}")
                print(f"   📊 상태: {data.get('status', 'Unknown')}")
                
                # 하위 카테고리 정보
                children = data.get('child', [])
                if children:
                    print(f"   👶 하위 카테고리: {len(children)}개")
                    for i, child in enumerate(children[:5], 1):  # 상위 5개만 표시
                        child_name = child.get('name', 'Unknown')
                        child_code = child.get('displayItemCategoryCode', 'Unknown')
                        print(f"      {i}. [{child_code}] {child_name}")
                    
                    if len(children) > 5:
                        print(f"      ... 및 {len(children) - 5}개 더")
                else:
                    print(f"   👶 하위 카테고리: 없음")
                
            except Exception as e:
                print(f"   ❌ 조회 실패: {e}")
                
    except Exception as e:
        print(f"❌ 클라이언트 초기화 오류: {e}")


def test_category_search():
    """카테고리명 검색 테스트"""
    print("\n" + "=" * 60 + " 카테고리명 검색 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 검색할 키워드들
        search_keywords = ["가전", "패션", "디지털", "식품", "TV"]
        
        for keyword in search_keywords:
            print(f"\n🔍 '{keyword}' 검색 중...")
            
            try:
                results = client.search_categories_by_name(keyword)
                
                if results:
                    print(f"✅ {len(results)}개 카테고리 발견:")
                    for i, category in enumerate(results, 1):
                        code = category.get('displayItemCategoryCode', 'Unknown')
                        name = category.get('name', 'Unknown')
                        parent_name = category.get('parentName')
                        
                        if parent_name:
                            print(f"   {i}. [{code}] {parent_name} > {name}")
                        else:
                            print(f"   {i}. [{code}] {name}")
                else:
                    print("   검색 결과 없음")
                    
            except Exception as e:
                print(f"   ❌ 검색 오류: {e}")
                
    except Exception as e:
        print(f"❌ 검색 테스트 오류: {e}")


def test_category_hierarchy():
    """카테고리 계층 구조 조회 테스트"""
    print("\n" + "=" * 60 + " 카테고리 계층 구조 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 테스트할 카테고리들 (1 Depth 카테고리)
        test_categories = [62588, 69182]  # 가전/디지털, 패션의류잡화
        
        for category_code in test_categories:
            print(f"\n🌳 카테고리 {category_code} 계층 구조 조회 중...")
            
            try:
                hierarchy = client.get_category_hierarchy(category_code, max_depth=3)
                
                if hierarchy:
                    print(f"✅ 계층 구조 조회 성공:")
                    print_hierarchy(hierarchy, indent=0)
                else:
                    print("   ❌ 계층 구조 조회 실패")
                    
            except Exception as e:
                print(f"   ❌ 계층 구조 조회 오류: {e}")
                
    except Exception as e:
        print(f"❌ 계층 구조 테스트 오류: {e}")


def print_hierarchy(category: dict, indent: int = 0):
    """카테고리 계층 구조를 들여쓰기로 출력"""
    prefix = "   " + "  " * indent
    name = category.get('name', 'Unknown')
    code = category.get('displayCategoryCode', 'Unknown')
    status = category.get('status', 'Unknown')
    
    status_emoji = "✅" if status == "ACTIVE" else "⚠️" if status == "READY" else "❌"
    print(f"{prefix}📁 [{code}] {name} {status_emoji}")
    
    # 하위 카테고리 출력
    children = category.get('children', [])
    for child in children:
        print_hierarchy(child, indent + 1)


def test_category_path():
    """카테고리 경로 조회 테스트"""
    print("\n" + "=" * 60 + " 카테고리 경로 조회 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 테스트할 카테고리 코드들 (실제 쿠팡 카테고리 코드)
        test_codes = [
            62588,  # 가전/디지털
            69182,  # 패션의류잡화
            59258,  # 식품
        ]
        
        for code in test_codes:
            print(f"\n📍 카테고리 {code} 경로 조회 중...")
            
            try:
                path = client.get_category_path(code)
                print(f"✅ 경로: {path}")
                
            except Exception as e:
                print(f"❌ 경로 조회 오류: {e}")
                
    except Exception as e:
        print(f"❌ 경로 조회 테스트 오류: {e}")


def test_error_handling():
    """오류 처리 테스트"""
    print("\n" + "=" * 60 + " 오류 처리 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 잘못된 카테고리 코드들
        error_test_cases = [
            {"code": 999999, "description": "존재하지 않는 카테고리 코드"},
            {"code": -1, "description": "음수 카테고리 코드"},
        ]
        
        for test_case in error_test_cases:
            code = test_case["code"]
            description = test_case["description"]
            
            print(f"\n⚠️ {description} 테스트: {code}")
            
            try:
                if code < 0:
                    # 음수는 클라이언트에서 체크
                    response = client.get_display_categories(code)
                    print(f"   예상치 못한 성공: {response}")
                else:
                    # 존재하지 않는 코드는 API에서 오류 반환
                    response = client.get_display_categories(code)
                    print(f"   예상치 못한 성공: {response}")
                    
            except ValueError as e:
                print(f"   ✅ 예상된 ValueError: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 오류 처리 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 노출 카테고리 조회 API 테스트 시작")
    
    try:
        test_first_depth_categories()
        test_specific_category_lookup()
        test_category_search()
        test_category_hierarchy()
        test_category_path()
        test_error_handling()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()