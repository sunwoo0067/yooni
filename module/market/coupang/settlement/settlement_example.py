#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 사용 예제
"""

from . import SettlementClient, create_settlement_client, get_current_month_settlement_quick
from .models import SettlementSearchParams
from .utils import get_default_vendor_id, generate_previous_year_month


def example_current_month_settlement():
    """이번 달 지급내역 조회 예제"""
    print("🔄 이번 달 지급내역 조회 예제")
    
    client = create_settlement_client()
    
    result = client.get_current_month_settlements()
    
    if result.get("success"):
        print("✅ 지급내역 조회 성공")
        summary = result.get("summary_stats", {})
        print(f"   총 지급건수: {summary.get('total_settlements', 0)}개")
        print(f"   총 지급액: {summary.get('total_final_amount', 0):,}원")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


def example_previous_month_settlement():
    """지난 달 지급내역 조회 예제"""
    print("🔄 지난 달 지급내역 조회 예제")
    
    client = create_settlement_client()
    
    result = client.get_previous_month_settlements()
    
    if result.get("success"):
        print("✅ 지급내역 조회 성공")
        summary = result.get("summary_stats", {})
        print(f"   총 판매액: {summary.get('total_sale', 0):,}원")
        print(f"   총 지급액: {summary.get('total_final_amount', 0):,}원")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


def example_quick_settlement():
    """빠른 지급내역 조회 예제"""
    print("🔄 빠른 지급내역 조회 예제")
    
    result = get_current_month_settlement_quick()
    
    if result.get("success"):
        print("✅ 빠른 조회 성공")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


def example_settlement_summary():
    """지급내역 요약 보고서 예제"""
    print("🔄 지급내역 요약 보고서 예제")
    
    client = create_settlement_client()
    
    result = client.create_settlement_summary_report(months=3)
    
    if result.get("success"):
        print("✅ 요약 보고서 생성 성공")
        print(f"   분석 기간: {result.get('analysis_period', '')}")
    else:
        print(f"❌ 보고서 생성 실패: {result.get('message', '알 수 없는 오류')}")


if __name__ == "__main__":
    print("💳 쿠팡 지급내역 조회 예제 실행")
    print("=" * 50)
    
    example_current_month_settlement()
    print()
    example_previous_month_settlement()
    print()
    example_quick_settlement()
    print()
    example_settlement_summary()