#!/usr/bin/env python3
"""
쿠팡 카테고리 메타정보 조회 API 사용 예제
"""

import os
import sys
import json
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang import CoupangClient, CoupangCategoryClient


def test_category_metadata():
    """카테고리 메타정보 조회 테스트"""
    
    try:
        # 카테고리 클라이언트 초기화
        category_client = CoupangCategoryClient()
        print("✅ 쿠팡 카테고리 클라이언트 초기화 성공")
        
        # 테스트할 카테고리 코드 (자동차용품 예시)
        test_category_code = 78877
        print(f"📂 테스트 카테고리 코드: {test_category_code}")
        
        # 1. 전체 메타정보 조회
        print("\n🔄 카테고리 메타정보 조회 중...")
        metadata = category_client.get_category_metadata(test_category_code)
        print("✅ 카테고리 메타정보 조회 성공")
        print(f"📊 단일상품 등록 가능: {metadata['data']['isAllowSingleItem']}")
        
        # 2. 속성 목록 조회
        print("\n🔄 카테고리 속성 조회 중...")
        attributes = category_client.get_category_attributes(test_category_code)
        print(f"✅ 총 속성 수: {len(attributes)}")
        
        # 3. 필수 속성만 조회
        print("\n🔄 필수 속성 조회 중...")
        required_attrs = category_client.get_required_attributes(test_category_code)
        print(f"✅ 필수 속성 수: {len(required_attrs)}")
        if required_attrs:
            print("📝 필수 속성:")
            for attr in required_attrs:
                print(f"  - {attr['attributeTypeName']} ({attr['dataType']})")
        
        # 4. 구매옵션만 조회
        print("\n🔄 구매옵션 조회 중...")
        purchase_options = category_client.get_purchase_options(test_category_code)
        print(f"✅ 구매옵션 수: {len(purchase_options)}")
        if purchase_options:
            print("🛒 구매옵션:")
            for option in purchase_options:
                print(f"  - {option['attributeTypeName']} (필수: {option['required']})")
        
        # 5. 상품고시정보 조회
        print("\n🔄 상품고시정보 조회 중...")
        notices = category_client.get_notice_categories(test_category_code)
        print(f"✅ 상품고시정보 카테고리 수: {len(notices)}")
        if notices:
            print("📋 상품고시정보:")
            for notice in notices:
                print(f"  - {notice['noticeCategoryName']}")
                for detail in notice['noticeCategoryDetailNames'][:3]:  # 처음 3개만 표시
                    print(f"    └ {detail['noticeCategoryDetailName']} ({detail['required']})")
                if len(notice['noticeCategoryDetailNames']) > 3:
                    print(f"    └ ... 외 {len(notice['noticeCategoryDetailNames']) - 3}개")
        
        # 6. 구비서류 조회
        print("\n🔄 구비서류 조회 중...")
        documents = category_client.get_required_documents(test_category_code)
        print(f"✅ 구비서류 수: {len(documents)}")
        if documents:
            print("📄 구비서류:")
            for doc in documents:
                print(f"  - {doc['templateName']} ({doc['required']})")
        
        # 7. 인증정보 조회
        print("\n🔄 인증정보 조회 중...")
        certifications = category_client.get_certifications(test_category_code)
        print(f"✅ 인증정보 수: {len(certifications)}")
        mandatory_certs = [cert for cert in certifications if cert['required'] == 'MANDATORY']
        if mandatory_certs:
            print("🏆 필수 인증정보:")
            for cert in mandatory_certs:
                print(f"  - {cert['name']} ({cert['certificationType']})")
        
        # 8. 허용된 상품 상태 조회
        print("\n🔄 허용된 상품 상태 조회 중...")
        conditions = category_client.get_allowed_conditions(test_category_code)
        print(f"✅ 허용된 상품 상태: {', '.join(conditions)}")
        
        # 9. 단일상품 등록 가능 여부
        print("\n🔄 단일상품 등록 가능 여부 확인 중...")
        is_single_allowed = category_client.is_single_item_allowed(test_category_code)
        print(f"✅ 단일상품 등록 가능: {'예' if is_single_allowed else '아니오'}")
        
    except ValueError as e:
        print(f"❌ 입력 오류: {e}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def test_with_main_client():
    """메인 클라이언트를 통한 카테고리 조회 테스트"""
    
    try:
        print("\n" + "="*50)
        print("🚀 메인 클라이언트를 통한 카테고리 조회 테스트")
        
        # 메인 클라이언트 초기화
        client = CoupangClient()
        print("✅ 쿠팡 메인 클라이언트 초기화 성공")
        
        # 카테고리 메타정보 조회 (메인 클라이언트의 category 속성 사용)
        test_category_code = 78877
        metadata = client.category.get_category_metadata(test_category_code)
        print(f"✅ 카테고리 {test_category_code} 메타정보 조회 성공")
        print(f"📊 속성 수: {len(metadata['data']['attributes'])}")
        print(f"📊 고시정보 카테고리 수: {len(metadata['data']['noticeCategories'])}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    print("🚀 쿠팡 카테고리 메타정보 조회 API 테스트 시작")
    test_category_metadata()
    test_with_main_client()
    print("🏁 테스트 완료")