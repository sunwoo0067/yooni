#!/usr/bin/env python3
"""
오늘 반품/취소 요청 현황 테스트
2025-07-14 쿠팡 파트너스 API 반품 조회 테스트
"""

import os
import sys
from datetime import datetime

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

import importlib
return_module = importlib.import_module('return.return_client')
ReturnClient = return_module.ReturnClient

models_module = importlib.import_module('return.models')
ReturnRequestSearchParams = models_module.ReturnRequestSearchParams

def test_today_returns():
    """오늘 반품/취소 요청 현황 테스트"""
    print("📅 오늘 반품/취소 요청 현황 테스트")
    print("=" * 60)
    print(f"테스트 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # ReturnClient 초기화
        client = ReturnClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        print(f"벤더 ID: {vendor_id}")
        print()
        
        # 오늘 날짜로 검색 파라미터 설정
        today = "2025-07-14"
        
        # 반품 요청 조회 (전체)
        print("🔍 반품 요청 현황 조회:")
        print("-" * 40)
        
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type="daily",
            created_at_from=today,
            created_at_to=today,
            cancel_type="RETURN"
        )
        
        result = client.get_return_requests(params)
        
        if result.get("success"):
            requests = result.get("data", [])
            print(f"✅ 반품 요청 조회 성공: {len(requests)}건")
            
            if requests:
                # 요약 통계 출력
                summary_stats = result.get("summary_stats", {})
                if summary_stats:
                    print(f"\n📊 반품 요청 요약:")
                    print(f"   총 건수: {summary_stats.get('total_count', 0)}건")
                    print(f"   출고중지 처리 필요: {summary_stats.get('stop_release_required_count', 0)}건")
                    
                    status_summary = summary_stats.get("status_summary", {})
                    if status_summary:
                        print(f"   상태별 현황:")
                        for status, count in status_summary.items():
                            print(f"      {status}: {count}건")
                    
                    fault_summary = summary_stats.get("fault_type_summary", {})
                    if fault_summary:
                        print(f"   귀책 타입별 현황:")
                        for fault_type, count in fault_summary.items():
                            print(f"      {fault_type}: {count}건")
            else:
                print("📭 오늘 접수된 반품 요청이 없습니다.")
        else:
            print(f"❌ 반품 요청 조회 실패: {result.get('error')}")
        
        print()
        
        # 취소 요청 조회
        print("🔍 취소 요청 현황 조회:")
        print("-" * 40)
        
        cancel_result = client.get_cancel_requests(
            vendor_id=vendor_id,
            created_at_from=today,
            created_at_to=today
        )
        
        if cancel_result.get("success"):
            cancel_requests = cancel_result.get("data", [])
            print(f"✅ 취소 요청 조회 성공: {len(cancel_requests)}건")
            
            if cancel_requests:
                summary_report = cancel_result.get("summary_report", {})
                if summary_report:
                    print(f"   총 취소 상품: {summary_report.get('total_cancel_items', 0)}개")
            else:
                print("📭 오늘 접수된 취소 요청이 없습니다.")
        else:
            print(f"❌ 취소 요청 조회 실패: {cancel_result.get('error')}")
        
        print()
        print("=" * 60)
        print("🎉 반품/취소 현황 테스트 완료!")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_today_returns()