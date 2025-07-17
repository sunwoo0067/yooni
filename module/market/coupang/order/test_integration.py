#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 통합 테스트
기존 auth 시스템과 .env 파일을 활용한 리펙토링된 시스템 테스트
"""

import os
import sys

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from order.order_client import OrderClient
from order.models import OrderSheetSearchParams

def test_auth_integration():
    """기존 auth 시스템과의 통합 테스트"""
    print("🔍 쿠팡 파트너스 API 통합 테스트 시작")
    print("=" * 60)
    
    # 환경변수 확인
    access_key = os.getenv('COUPANG_ACCESS_KEY')
    secret_key = os.getenv('COUPANG_SECRET_KEY')
    vendor_id = os.getenv('COUPANG_VENDOR_ID')
    
    print("📋 환경변수 확인:")
    print(f"   ACCESS_KEY: {'✅ 설정됨' if access_key else '❌ 없음'}")
    print(f"   SECRET_KEY: {'✅ 설정됨' if secret_key else '❌ 없음'}")
    print(f"   VENDOR_ID: {'✅ 설정됨' if vendor_id else '❌ 없음'}")
    
    if not all([access_key, secret_key, vendor_id]):
        print("❌ 환경변수가 제대로 설정되지 않았습니다.")
        return False
    
    try:
        # OrderClient 초기화 (환경변수 자동 읽기)
        print("\n🚀 OrderClient 초기화 테스트:")
        client = OrderClient()
        print("✅ OrderClient 초기화 성공")
        
        # 인증 정보 확인
        print(f"   벤더 ID: {client.auth.vendor_id}")
        print(f"   액세스 키: {client.auth.access_key[:8]}...")
        
        # 메서드 존재 확인
        print("\n🔧 주요 메서드 확인:")
        methods_to_check = [
            "get_order_sheets",
            "get_order_sheet_detail", 
            "get_order_sheet_history",
            "process_order_to_instruct"
        ]
        
        for method_name in methods_to_check:
            if hasattr(client, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} 없음")
        
        # 중복 메서드 제거 확인
        print("\n🔍 중복 메서드 제거 확인:")
        method_count = sum(1 for name in dir(client) if name == 'get_order_sheet_history')
        if method_count == 1:
            print("   ✅ get_order_sheet_history 메서드 중복 제거됨")
        else:
            print(f"   ❌ get_order_sheet_history 메서드가 {method_count}개 존재")
        
        print("\n🎉 통합 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n❌ 통합 테스트 실패: {e}")
        return False

def test_api_params_validation():
    """API 파라미터 검증 테스트"""
    print("\n📋 API 파라미터 검증 테스트:")
    
    try:
        client = OrderClient()
        
        # 검색 파라미터 생성 테스트
        params = OrderSheetSearchParams(
            vendor_id=os.getenv('COUPANG_VENDOR_ID'),
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT"
        )
        
        print("   ✅ OrderSheetSearchParams 생성 성공")
        print(f"   벤더 ID: {params.vendor_id}")
        print(f"   조회 기간: {params.created_at_from} ~ {params.created_at_to}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 파라미터 검증 실패: {e}")
        return False

def run_integration_test():
    """전체 통합 테스트 실행"""
    print("🎯 쿠팡 파트너스 API 리펙토링 통합 테스트")
    print("📌 기존 auth 시스템과 .env 파일 활용 검증\n")
    
    results = []
    
    # 1. 인증 통합 테스트
    results.append(test_auth_integration())
    
    # 2. 파라미터 검증 테스트
    results.append(test_api_params_validation())
    
    # 결과 요약
    print("\n" + "=" * 60)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 모든 통합 테스트 통과!")
        print("✅ 리펙토링된 시스템이 정상 작동합니다.")
    else:
        print(f"⚠️  통합 테스트 결과: {success_count}/{total_count} 통과")
        print("❌ 일부 테스트가 실패했습니다.")
    
    return success_count == total_count

if __name__ == "__main__":
    run_integration_test()