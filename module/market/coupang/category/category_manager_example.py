#!/usr/bin/env python3
"""
쿠팡 통합 카테고리 매니저 사용 예제
오프라인 데이터와 API 클라이언트 통합 활용 데모
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_manager import CoupangCategoryManager


def test_offline_category_search():
    """오프라인 카테고리 검색 테스트"""
    print("=" * 60 + " 오프라인 카테고리 검색 테스트 " + "=" * 60)
    
    # 매니저 초기화 (오프라인 전용)
    manager = CoupangCategoryManager()
    
    # 다양한 검색 테스트
    test_cases = [
        {"query": "TV", "type": "name", "description": "TV 관련 카테고리"},
        {"query": "티셔츠", "type": "name", "description": "티셔츠 관련 카테고리"},
        {"query": "라면", "type": "name", "description": "라면 관련 카테고리"},
        {"query": "112143", "type": "id", "description": "특정 카테고리 ID 검색"},
        {"query": "가전/디지털>TV", "type": "path", "description": "경로로 검색"}
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['description']}: '{test_case['query']}'")
        results = manager.search_categories(
            test_case["query"], 
            test_case["type"], 
            limit=5
        )
        
        if results:
            for i, result in enumerate(results, 1):
                cat_info = result["category_info"]
                print(f"   {i}. [{result['category_id']}] {cat_info.get('path', 'Unknown')}")
                if cat_info.get('commission_rate'):
                    print(f"      💰 수수료: {cat_info['commission_rate']}%")
                if cat_info.get('purchase_options'):
                    option_names = [opt['type'] for opt in cat_info['purchase_options'][:3]]
                    print(f"      🛒 구매옵션: {', '.join(option_names)}")
        else:
            print("   검색 결과 없음")


def test_category_detail_info():
    """카테고리 상세 정보 조회 테스트"""
    print("\n" + "=" * 60 + " 카테고리 상세 정보 테스트 " + "=" * 60)
    
    manager = CoupangCategoryManager()
    
    # 특정 카테고리들의 상세 정보 조회
    test_categories = ["112143", "67983", "58646"]  # TV, 남성운동화, 봉지라면
    
    for category_id in test_categories:
        print(f"\n📂 카테고리 ID: {category_id}")
        
        category_info = manager.get_category_info(category_id)
        
        if category_info["success"]:
            data = category_info["data"]
            print(f"   📝 경로: {data.get('path', 'Unknown')}")
            print(f"   📁 파일: {data.get('file_category', 'Unknown')}")
            print(f"   💰 수수료: {data.get('commission_rate', 'Unknown')}%")
            print(f"   📊 레벨: {data.get('level', 'Unknown')}")
            
            # 구매 옵션
            purchase_options = data.get('purchase_options', [])
            if purchase_options:
                print(f"   🛒 구매옵션 ({len(purchase_options)}개):")
                for opt in purchase_options[:5]:  # 상위 5개만 표시
                    values_preview = ', '.join(opt.get('values', [])[:3])
                    if len(opt.get('values', [])) > 3:
                        values_preview += "..."
                    print(f"      - {opt['type']}: {values_preview}")
            
            # 검색 옵션
            search_options = data.get('search_options', [])
            if search_options:
                print(f"   🔍 검색옵션 ({len(search_options)}개):")
                for opt in search_options[:3]:  # 상위 3개만 표시
                    values_preview = ', '.join(opt.get('values', [])[:3])
                    if len(opt.get('values', [])) > 3:
                        values_preview += "..."
                    print(f"      - {opt['type']}: {values_preview}")
            
            # 고시정보
            notice_info = data.get('notice_info', {})
            if notice_info:
                print(f"   📋 고시정보:")
                if notice_info.get('category'):
                    print(f"      카테고리: {notice_info['category']}")
                required_fields = notice_info.get('required_fields', [])
                if required_fields:
                    print(f"      필수항목: {len(required_fields)}개")
        else:
            print(f"   ❌ 조회 실패: {category_info.get('error', 'Unknown error')}")


def test_level_and_file_grouping():
    """레벨별/파일별 카테고리 그룹핑 테스트"""
    print("\n" + "=" * 60 + " 레벨별/파일별 그룹핑 테스트 " + "=" * 60)
    
    manager = CoupangCategoryManager()
    
    # 레벨별 분포 확인
    print(f"\n📊 레벨별 카테고리 분포:")
    for level in [3, 4, 5, 6]:
        categories = manager.get_categories_by_level(level)
        print(f"   레벨 {level}: {len(categories)}개")
        
        # 각 레벨의 예시 몇 개 표시
        if categories:
            print("   예시:")
            for cat in categories[:3]:
                cat_info = cat["category_info"]
                path = cat_info.get('path', 'Unknown')
                print(f"     - [{cat['category_id']}] {path}")
    
    # 파일별 분포 확인 (상위 5개 파일)
    print(f"\n📁 주요 파일별 카테고리 분포:")
    major_files = ["도서", "패션의류잡화", "식품", "가전디지털", "생활용품"]
    
    for file_name in major_files:
        categories = manager.get_categories_by_file(file_name)
        print(f"   {file_name}: {len(categories)}개")
        
        # 각 파일의 예시 몇 개 표시
        if categories:
            print("   예시:")
            for cat in categories[:2]:
                cat_info = cat["category_info"]
                path = cat_info.get('path', 'Unknown')[:60]
                commission = cat_info.get('commission_rate', 'Unknown')
                print(f"     - [{cat['category_id']}] {path}... (수수료: {commission}%)")


def test_product_validation():
    """상품 데이터 검증 테스트"""
    print("\n" + "=" * 60 + " 상품 데이터 검증 테스트 " + "=" * 60)
    
    manager = CoupangCategoryManager()
    
    # 테스트용 상품 데이터들
    test_cases = [
        {
            "category_id": "112143",  # TV 카테고리
            "product_data": {
                "화면크기(cm)": "165",
                "화면크기(in)": "65",
                "해상도": "4K UHD"
            },
            "description": "TV 상품 (완전한 데이터)"
        },
        {
            "category_id": "112143",  # TV 카테고리
            "product_data": {
                "화면크기(cm)": "165"
                # 화면크기(in) 누락
            },
            "description": "TV 상품 (필수 옵션 누락)"
        },
        {
            "category_id": "58646",   # 봉지라면 카테고리
            "product_data": {
                "라면 종류": "유탕면",
                "라면 맛": "매운맛"
            },
            "description": "라면 상품"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📦 {test_case['description']}")
        print(f"   카테고리 ID: {test_case['category_id']}")
        print(f"   상품 데이터: {test_case['product_data']}")
        
        validation_result = manager.validate_product_data(
            test_case["category_id"], 
            test_case["product_data"]
        )
        
        status = "✅ 유효" if validation_result["isValid"] else "❌ 무효"
        print(f"   검증 결과: {status} (점수: {validation_result['score']}/100)")
        
        if validation_result["missingRequiredOptions"]:
            print(f"   🚨 누락된 필수 옵션: {', '.join(validation_result['missingRequiredOptions'])}")
        
        if validation_result["invalidOptions"]:
            print(f"   ⚠️ 잘못된 옵션:")
            for invalid in validation_result["invalidOptions"]:
                print(f"      - {invalid['option']}: '{invalid['providedValue']}'")
                print(f"        가능한 값: {', '.join(invalid['validValues'][:5])}")
        
        if validation_result["suggestions"]:
            print(f"   💡 개선 제안:")
            for suggestion in validation_result["suggestions"]:
                print(f"      - {suggestion}")


def test_category_statistics():
    """카테고리 통계 분석 테스트"""
    print("\n" + "=" * 60 + " 카테고리 통계 분석 테스트 " + "=" * 60)
    
    manager = CoupangCategoryManager()
    stats = manager.get_statistics()
    
    print(f"📊 전체 통계:")
    print(f"   총 카테고리 수: {stats['총_카테고리_수']:,}개")
    
    print(f"\n💰 수수료율 분포 (상위 5개):")
    commission_items = sorted(
        stats["수수료율_분포"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    for rate, count in commission_items[:5]:
        print(f"   {rate}: {count:,}개 카테고리")
    
    print(f"\n📁 파일별 분포 (상위 5개):")
    file_items = sorted(
        stats["파일별_분포"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    for file_name, count in file_items[:5]:
        print(f"   {file_name}: {count:,}개 카테고리")
    
    print(f"\n🛒 구매 옵션이 많은 카테고리:")
    for i, cat in enumerate(stats["최다_구매옵션_카테고리"], 1):
        path = cat["path"][:60] + "..." if len(cat["path"]) > 60 else cat["path"]
        print(f"   {i}. {path}")
        print(f"      구매옵션: {cat['purchase_options']}개, 검색옵션: {cat['search_options']}개")
    
    print(f"\n🔍 검색 옵션이 많은 카테고리:")
    for i, cat in enumerate(stats["최다_검색옵션_카테고리"], 1):
        path = cat["path"][:60] + "..." if len(cat["path"]) > 60 else cat["path"]
        print(f"   {i}. {path}")
        print(f"      구매옵션: {cat['purchase_options']}개, 검색옵션: {cat['search_options']}개")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 통합 카테고리 매니저 종합 테스트")
    
    try:
        test_offline_category_search()
        test_category_detail_info()
        test_level_and_file_grouping()
        test_product_validation()
        test_category_statistics()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()