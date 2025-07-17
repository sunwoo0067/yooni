#!/usr/bin/env python3
"""
쿠팡 필수 구매 옵션 검증 및 가이드 사용 예제
"""

import os
import sys
import json
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category import CoupangOptionValidator


def test_option_validation():
    """옵션 검증 테스트 (PDF 가이드 기반)"""
    
    try:
        # 옵션 검증기 초기화
        validator = CoupangOptionValidator()
        print("✅ 쿠팡 옵션 검증기 초기화 성공")
        
        # 테스트할 카테고리 코드
        test_category_code = 78877
        print(f"📂 테스트 카테고리 코드: {test_category_code}")
        
        # 테스트 케이스 1: PDF 예시 기반 정상 케이스
        print("\n" + "="*30 + " 테스트 1: 정상 케이스 " + "="*30)
        correct_options = [
            {
                "attributeTypeName": "수량",
                "attributeValue": "1", 
                "attributeUnit": "개"
            },
            {
                "attributeTypeName": "개당 용량",
                "attributeValue": "500",
                "attributeUnit": "ml"
            }
        ]
        
        print("📋 테스트 옵션 (정상):")
        for opt in correct_options:
            unit_text = f" {opt['attributeUnit']}" if opt.get('attributeUnit') else ""
            print(f"  - {opt['attributeTypeName']}: {opt['attributeValue']}{unit_text}")
        
        validation_result = validator.validate_required_options(test_category_code, correct_options)
        print(f"📊 검증 결과: {'✅ 통과' if validation_result['isValid'] else '❌ 실패'}")
        
        if validation_result.get('warnings'):
            print("⚠️ 경고:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        
        # 테스트 케이스 2: 그룹 충돌 케이스
        print("\n" + "="*30 + " 테스트 2: 그룹 충돌 " + "="*30)
        conflict_options = [
            {
                "attributeTypeName": "수량",
                "attributeValue": "1",
                "attributeUnit": "개"
            },
            {
                "attributeTypeName": "개당 용량", 
                "attributeValue": "500",
                "attributeUnit": "ml"
            },
            {
                "attributeTypeName": "개당 중량",
                "attributeValue": "100", 
                "attributeUnit": "g"
            }
        ]
        
        print("📋 테스트 옵션 (그룹 충돌):")
        for opt in conflict_options:
            unit_text = f" {opt['attributeUnit']}" if opt.get('attributeUnit') else ""
            print(f"  - {opt['attributeTypeName']}: {opt['attributeValue']}{unit_text}")
        
        validation_result = validator.validate_required_options(test_category_code, conflict_options)
        print(f"📊 검증 결과: {'✅ 통과' if validation_result['isValid'] else '❌ 실패 (예상됨)'}")
        
        if validation_result.get('errors'):
            print("❌ 오류 (그룹 충돌):")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        # 테스트 케이스 3: 잘못된 단위 사용
        print("\n" + "="*30 + " 테스트 3: 잘못된 단위 " + "="*30)
        wrong_unit_options = [
            {
                "attributeTypeName": "수량",
                "attributeValue": "1",
                "attributeUnit": "파운드"  # 잘못된 단위
            },
            {
                "attributeTypeName": "개당 용량",
                "attributeValue": "500",
                "attributeUnit": "갤런"  # 잘못된 단위
            }
        ]
        
        print("📋 테스트 옵션 (잘못된 단위):")
        for opt in wrong_unit_options:
            unit_text = f" {opt['attributeUnit']}" if opt.get('attributeUnit') else ""
            print(f"  - {opt['attributeTypeName']}: {opt['attributeValue']}{unit_text}")
        
        validation_result = validator.validate_required_options(test_category_code, wrong_unit_options)
        print(f"📊 검증 결과: {'✅ 통과' if validation_result['isValid'] else '❌ 실패 (예상됨)'}")
        
        if validation_result.get('errors'):
            print("❌ 오류 (단위 검증):")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        # 테스트 케이스 4: 필수 옵션 누락
        print("\n" + "="*30 + " 테스트 4: 필수 옵션 누락 " + "="*30)
        missing_options = [
            {
                "attributeTypeName": "개당 용량",
                "attributeValue": "500",
                "attributeUnit": "ml"
            }
            # 수량 누락
        ]
        
        print("📋 테스트 옵션 (필수 옵션 누락):")
        for opt in missing_options:
            unit_text = f" {opt['attributeUnit']}" if opt.get('attributeUnit') else ""
            print(f"  - {opt['attributeTypeName']}: {opt['attributeValue']}{unit_text}")
        
        validation_result = validator.validate_required_options(test_category_code, missing_options)
        print(f"📊 검증 결과: {'✅ 통과' if validation_result['isValid'] else '❌ 실패 (예상됨)'}")
        
        if validation_result.get('errors'):
            print("❌ 오류 (필수 옵션 누락):")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        if validation_result.get('missingOptions'):
            print("📝 누락된 필수 옵션:")
            for missing in validation_result['missingOptions']:
                print(f"  - {missing['attributeTypeName']} ({missing['dataType']})")
        
    except Exception as e:
        print(f"❌ 옵션 검증 오류: {e}")


def test_option_guide():
    """옵션 가이드 테스트"""
    
    try:
        validator = CoupangOptionValidator()
        test_category_code = 78877
        
        print("\n" + "="*50)
        print("🔄 옵션 설정 가이드 생성 중...")
        
        # 옵션 가이드 조회
        guide = validator.get_option_guide(test_category_code)
        
        if 'error' in guide:
            print(f"❌ 가이드 생성 오류: {guide['error']}")
            return
        
        print(f"✅ 옵션 가이드 생성 완료")
        print(f"📊 카테고리 코드: {guide['categoryCode']}")
        print(f"📊 단일상품 등록 가능: {'예' if guide['isSingleItemAllowed'] else '아니오'}")
        
        # 필수 옵션
        mandatory_opts = guide.get('mandatoryOptions', [])
        print(f"\n📋 필수 옵션 ({len(mandatory_opts)}개):")
        for opt in mandatory_opts:
            print(f"  - {opt['name']} ({opt['dataType']})")
            if opt['usableUnits']:
                print(f"    └ 허용 단위: {', '.join(opt['usableUnits'][:5])}" + 
                      (f" 외 {len(opt['usableUnits'])-5}개" if len(opt['usableUnits']) > 5 else ""))
        
        # 구매 옵션
        purchase_opts = guide.get('purchaseOptions', [])
        print(f"\n🛒 구매 옵션 ({len(purchase_opts)}개):")
        for opt in purchase_opts:
            required_text = "필수" if opt['required'] == 'MANDATORY' else "선택"
            print(f"  - {opt['name']} ({required_text})")
        
        # 그룹 옵션
        group_opts = guide.get('groupOptions', {})
        if group_opts:
            print(f"\n👥 그룹 옵션:")
            for group_num, options in group_opts.items():
                print(f"  - 그룹 {group_num}: {', '.join([opt['name'] for opt in options])}")
        
        # 허용된 상품 상태
        conditions = guide.get('allowedConditions', [])
        print(f"\n📦 허용된 상품 상태: {', '.join(conditions)}")
        
    except Exception as e:
        print(f"❌ 가이드 생성 오류: {e}")


def test_option_combinations():
    """옵션 조합 제안 테스트 (PDF 가이드 기반)"""
    
    try:
        validator = CoupangOptionValidator()
        test_category_code = 78877
        
        print("\n" + "="*50)
        print("🔄 권장 옵션 조합 제안 중 (PDF 가이드 기반)...")
        
        # 옵션 조합 제안
        combinations = validator.suggest_option_combinations(test_category_code)
        
        print(f"✅ 옵션 조합 제안 완료 ({len(combinations)}개)")
        
        for i, combo in enumerate(combinations, 1):
            if 'error' in combo:
                print(f"❌ 조합 {i} 오류: {combo['error']}")
                continue
                
            print(f"\n📋 조합 {i}: {combo['name']}")
            print(f"   📝 설명: {combo['description']}")
            print(f"   🎯 복잡도: {combo['complexity']}")
            print(f"   📊 옵션 수: {len(combo['options'])}개")
            
            # 예시 출력
            if 'example' in combo:
                print(f"   💡 예시: {combo['example']}")
            
            # 그룹 정보 출력
            if combo.get('groupsIncluded'):
                print(f"   👥 포함 그룹: {', '.join(map(str, combo['groupsIncluded']))}")
            
            if combo.get('groupChoices'):
                print(f"   🔄 그룹 선택지: {', '.join(combo['groupChoices'])}")
            
            # 예상 변형 수
            if 'estimatedVariants' in combo:
                print(f"   🔢 예상 변형 수: {combo['estimatedVariants']}개")
            
            # 경고 메시지
            if combo.get('warning'):
                print(f"   ⚠️ 주의: {combo['warning']}")
            
            # 옵션 상세 정보 (처음 5개만)
            print(f"   📋 포함 옵션:")
            for j, opt in enumerate(combo['options'][:5]):
                required_text = "필수" if opt.get('required') == 'MANDATORY' else "선택"
                basic_unit = opt.get('basicUnit', '없음')
                group_text = f" (그룹 {opt.get('groupNumber')})" if opt.get('groupNumber', 'NONE') != 'NONE' else ""
                print(f"     {j+1}. {opt['attributeTypeName']} ({required_text}, {opt.get('dataType')}, 기본단위: {basic_unit}){group_text}")
            
            if len(combo['options']) > 5:
                print(f"     ... 외 {len(combo['options']) - 5}개")
        
    except Exception as e:
        print(f"❌ 조합 제안 오류: {e}")


def test_group_conflicts():
    """그룹 옵션 충돌 검사 테스트"""
    
    try:
        validator = CoupangOptionValidator()
        test_category_code = 78877
        
        print("\n" + "="*50)
        print("🔄 그룹 옵션 충돌 검사 중...")
        
        # 테스트용 선택 옵션 (의도적으로 충돌 가능한 옵션들)
        selected_options = ["수량", "색상", "크기"]  # 예시
        
        print(f"📋 선택된 옵션: {', '.join(selected_options)}")
        
        # 그룹 충돌 검사
        conflict_result = validator.check_group_option_conflicts(
            test_category_code, 
            selected_options
        )
        
        if 'error' in conflict_result:
            print(f"❌ 충돌 검사 오류: {conflict_result['error']}")
            return
        
        print(f"✅ 그룹 충돌 검사 완료")
        print(f"📊 충돌 여부: {'있음' if conflict_result['hasConflicts'] else '없음'}")
        print(f"📊 검증 결과: {'통과' if conflict_result['isValid'] else '실패'}")
        
        if conflict_result.get('conflicts'):
            print("❌ 충돌:")
            for conflict in conflict_result['conflicts']:
                print(f"  - {conflict['message']}")
        
        if conflict_result.get('warnings'):
            print("⚠️ 경고:")
            for warning in conflict_result['warnings']:
                print(f"  - {warning['message']}")
        
    except Exception as e:
        print(f"❌ 충돌 검사 오류: {e}")


if __name__ == "__main__":
    print("🚀 쿠팡 필수 구매 옵션 검증 및 가이드 테스트 시작")
    
    test_option_validation()
    test_option_guide()
    test_option_combinations()
    test_group_conflicts()
    
    print("\n🏁 모든 테스트 완료")