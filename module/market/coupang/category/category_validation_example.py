#!/usr/bin/env python3
"""
쿠팡 카테고리 유효성 검사 API 사용 예제
카테고리 사용 가능 여부 확인 및 leaf category 검증 테스트
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category.category_client import CoupangCategoryClient


def test_single_category_validation():
    """개별 카테고리 유효성 검사 테스트"""
    print("=" * 60 + " 개별 카테고리 유효성 검사 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = CoupangCategoryClient()
        print("✅ 쿠팡 카테고리 클라이언트 초기화 성공")
        
        # 테스트할 카테고리 코드들 (실제 leaf 카테고리 포함)
        test_categories = [
            {"code": 112143, "description": "TV (leaf category)", "expected": "leaf"},
            {"code": 62588, "description": "가전/디지털 (parent category)", "expected": "parent"},
            {"code": 67983, "description": "남성패션운동화 (leaf category)", "expected": "leaf"},
            {"code": 58646, "description": "봉지라면 (leaf category)", "expected": "leaf"},
            {"code": 69182, "description": "패션의류잡화 (parent category)", "expected": "parent"}
        ]
        
        for test_cat in test_categories:
            code = test_cat["code"]
            description = test_cat["description"]
            expected = test_cat["expected"]
            
            print(f"\n📂 카테고리 {code} ({description}) 유효성 검사 중...")
            
            try:
                # 카테고리 상태 확인
                status_result = client.check_category_status(code)
                
                print(f"✅ 검사 성공:")
                print(f"   📝 카테고리 코드: {status_result['categoryCode']}")
                print(f"   📊 사용 가능: {'✅ 예' if status_result['isAvailable'] else '❌ 아니오'}")
                print(f"   🏷️ 상태: {status_result['status']}")
                print(f"   💬 메시지: {status_result['message']}")
                
                if expected == "leaf":
                    print(f"   ✅ 예상대로 leaf category입니다")
                else:
                    print(f"   ⚠️ 예상과 달리 leaf category로 확인됨")
                
            except ValueError as e:
                print(f"   ⚠️ 예상된 오류 (leaf category 아님): {e}")
                
                if expected == "parent":
                    print(f"   ✅ 예상대로 parent category입니다")
                else:
                    print(f"   ❌ 예상과 달리 parent category임")
                
            except Exception as e:
                print(f"   ❌ 예상치 못한 오류: {e}")
                
    except Exception as e:
        print(f"❌ 클라이언트 초기화 오류: {e}")


def test_simple_availability_check():
    """간단한 사용 가능 여부 확인 테스트"""
    print("\n" + "=" * 60 + " 간단한 사용 가능 여부 확인 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 테스트할 카테고리들
        test_codes = [112143, 67983, 58646, 62588, 69182]
        
        print(f"📊 {len(test_codes)}개 카테고리 간단 확인 중...")
        
        for code in test_codes:
            print(f"\n📦 카테고리 {code}:")
            
            is_available = client.is_category_available(code)
            status_emoji = "✅" if is_available else "❌"
            status_text = "사용 가능" if is_available else "사용 불가능/오류"
            
            print(f"   결과: {status_emoji} {status_text}")
            
    except Exception as e:
        print(f"❌ 간단한 확인 테스트 오류: {e}")


def test_batch_validation():
    """일괄 카테고리 유효성 검사 테스트"""
    print("\n" + "=" * 60 + " 일괄 카테고리 유효성 검사 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 테스트할 카테고리 코드들 (leaf와 parent 혼합)
        test_codes = [
            112143,  # TV (leaf)
            67983,   # 남성패션운동화 (leaf)
            58646,   # 봉지라면 (leaf)
            62588,   # 가전/디지털 (parent)
            69182,   # 패션의류잡화 (parent)
            999999   # 존재하지 않는 카테고리
        ]
        
        print(f"📊 {len(test_codes)}개 카테고리 일괄 검사...")
        
        # 일괄 검사 실행
        results = client.validate_categories_batch(test_codes)
        
        print(f"\n📈 일괄 검사 결과 요약:")
        print(f"   총 카테고리: {results['totalCount']}개")
        print(f"   사용 가능: {results['availableCount']}개")
        print(f"   사용 불가능: {results['unavailableCount']}개")
        print(f"   오류: {results['errorCount']}개")
        
        # 상세 결과 출력
        print(f"\n📋 상세 결과:")
        for detail in results['details']:
            code = detail['categoryCode']
            success = detail['success']
            available = detail.get('isAvailable', False)
            error = detail.get('error')
            
            if success and available:
                print(f"   ✅ [{code}] 사용 가능")
            elif success and not available:
                print(f"   ⚠️ [{code}] 사용 불가능")
            else:
                print(f"   ❌ [{code}] 오류: {error}")
        
        # 요약 정보 출력
        if results['summary']['available']:
            print(f"\n✅ 사용 가능한 카테고리: {results['summary']['available']}")
        
        if results['summary']['unavailable']:
            print(f"\n⚠️ 사용 불가능한 카테고리: {results['summary']['unavailable']}")
        
        if results['summary']['errors']:
            print(f"\n❌ 오류가 발생한 카테고리:")
            for error in results['summary']['errors']:
                print(f"   - {error['code']}: {error['error']}")
                
    except Exception as e:
        print(f"❌ 일괄 검사 테스트 오류: {e}")


def test_leaf_category_finding():
    """leaf category 찾기 테스트"""
    print("\n" + "=" * 60 + " leaf category 찾기 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # parent category들에서 leaf 찾기
        parent_categories = [
            {"code": 62588, "name": "가전/디지털"},
            {"code": 63237, "name": "TV/영상가전"},
            {"code": 69182, "name": "패션의류잡화"}
        ]
        
        for parent in parent_categories:
            code = parent["code"]
            name = parent["name"]
            
            print(f"\n🌳 {name} ({code})의 leaf category 찾기...")
            
            try:
                leaf_categories = client.find_leaf_categories(code)
                
                if leaf_categories:
                    print(f"✅ {len(leaf_categories)}개의 leaf category 발견:")
                    for i, leaf_code in enumerate(leaf_categories[:10], 1):  # 상위 10개만 표시
                        print(f"   {i:2d}. {leaf_code}")
                    
                    if len(leaf_categories) > 10:
                        print(f"   ... 및 {len(leaf_categories) - 10}개 더")
                else:
                    print(f"   ❌ leaf category를 찾을 수 없습니다")
                    
            except Exception as e:
                print(f"   ❌ leaf category 찾기 오류: {e}")
                
    except Exception as e:
        print(f"❌ leaf category 찾기 테스트 오류: {e}")


def test_category_status_summary():
    """카테고리 상태 종합 정보 테스트"""
    print("\n" + "=" * 60 + " 카테고리 상태 종합 정보 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 다양한 타입의 카테고리들
        test_categories = [
            {"code": 112143, "description": "TV (leaf category)"},
            {"code": 62588, "description": "가전/디지털 (parent category)"},
            {"code": 999999, "description": "존재하지 않는 카테고리"}
        ]
        
        for test_cat in test_categories:
            code = test_cat["code"]
            description = test_cat["description"]
            
            print(f"\n📊 {description} - 종합 정보 조회 중...")
            
            try:
                summary = client.get_category_status_summary(code)
                
                print(f"✅ 종합 정보:")
                print(f"   📝 카테고리 코드: {summary['categoryCode']}")
                
                # 카테고리 기본 정보
                category_info = summary.get('categoryInfo', {})
                if 'error' not in category_info:
                    print(f"   🏷️ 이름: {category_info.get('name', 'Unknown')}")
                    print(f"   📊 상태: {category_info.get('status', 'Unknown')}")
                    print(f"   👶 하위 카테고리: {'있음' if category_info.get('hasChildren') else '없음'}")
                else:
                    print(f"   ❌ 기본 정보 오류: {category_info['error']}")
                
                # leaf 여부
                print(f"   🍃 leaf category: {'✅ 예' if summary['isLeafCategory'] else '❌ 아니오'}")
                
                # leaf categories
                if summary['leafCategories']:
                    leaf_count = len(summary['leafCategories'])
                    print(f"   🌿 관련 leaf 카테고리: {leaf_count}개")
                    for i, leaf in enumerate(summary['leafCategories'][:5], 1):
                        print(f"      {i}. {leaf}")
                    if leaf_count > 5:
                        print(f"      ... 및 {leaf_count - 5}개 더")
                
                # 권장사항
                print(f"   💡 권장사항: {summary['recommendation']}")
                
                # 상태 확인 결과
                status_check = summary.get('statusCheck', {})
                if 'error' not in status_check:
                    available = status_check.get('isAvailable', False)
                    print(f"   ✅ 사용 가능: {'예' if available else '아니오'}")
                else:
                    print(f"   ⚠️ 상태 확인: {status_check['error']}")
                
            except Exception as e:
                print(f"   ❌ 종합 정보 조회 오류: {e}")
                
    except Exception as e:
        print(f"❌ 종합 정보 테스트 오류: {e}")


def test_error_handling():
    """오류 처리 테스트"""
    print("\n" + "=" * 60 + " 오류 처리 테스트 " + "=" * 60)
    
    try:
        client = CoupangCategoryClient()
        
        # 오류 케이스들
        error_test_cases = [
            {"code": -1, "description": "음수 카테고리 코드"},
            {"code": 0, "description": "0 카테고리 코드"},
            {"code": 999999, "description": "존재하지 않는 카테고리"},
            {"code": "abc", "description": "문자열 카테고리 코드"}
        ]
        
        for test_case in error_test_cases:
            code = test_case["code"]
            description = test_case["description"]
            
            print(f"\n⚠️ {description} 테스트: {code}")
            
            try:
                if isinstance(code, str):
                    # 문자열은 타입 오류로 클라이언트에서 체크되지 않을 수 있음
                    print(f"   ⚠️ 문자열 입력은 실제로는 사전에 검증되어야 함")
                else:
                    status_result = client.check_category_status(code)
                    print(f"   예상치 못한 성공: {status_result}")
                    
            except ValueError as e:
                print(f"   ✅ 예상된 ValueError: {e}")
            except Exception as e:
                print(f"   ✅ 예상된 오류: {e}")
                
    except Exception as e:
        print(f"❌ 오류 처리 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 카테고리 유효성 검사 API 테스트 시작")
    
    try:
        test_single_category_validation()
        test_simple_availability_check()
        test_batch_validation()
        test_leaf_category_finding()
        test_category_status_summary()
        test_error_handling()
        
        print(f"\n" + "=" * 50 + " 테스트 완료 " + "=" * 50)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("\n💡 주요 학습 내용:")
        print("   1. leaf category만 상품 등록에 사용 가능")
        print("   2. parent category는 leaf category 찾기 필요")
        print("   3. 카테고리 리뉴얼로 인한 상태 변경 주의")
        print("   4. 연 2회 카테고리 리뉴얼 시기에 재검사 권장")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()