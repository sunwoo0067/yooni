#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 사용 예제
"""

from . import SalesClient, create_sales_client, get_recent_revenue_quick
from .models import RevenueSearchParams
from .utils import get_default_vendor_id


def example_recent_revenue():
    """최근 매출내역 조회 예제"""
    print("🔄 최근 7일간 매출내역 조회 예제")
    
    client = create_sales_client()
    vendor_id = get_default_vendor_id()
    
    if not vendor_id:
        print("❌ 벤더 ID가 설정되지 않았습니다.")
        return
    
    result = client.get_recent_revenue_history(vendor_id, days=7)
    
    if result.get("success"):
        print("✅ 매출내역 조회 성공")
        summary = result.get("summary_stats", {})
        print(f"   총 건수: {summary.get('total_items', 0)}개")
        print(f"   총 정산금액: {summary.get('total_settlement', 0):,}원")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


def example_monthly_revenue():
    """월별 매출내역 조회 예제"""
    print("🔄 이번 달 매출내역 조회 예제")
    
    client = create_sales_client()
    vendor_id = get_default_vendor_id()
    
    if not vendor_id:
        print("❌ 벤더 ID가 설정되지 않았습니다.")
        return
    
    result = client.get_monthly_revenue_history(vendor_id)
    
    if result.get("success"):
        print("✅ 월별 매출내역 조회 성공")
        print(f"   기간: {result.get('year_month', '')}")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


def example_quick_revenue():
    """빠른 매출내역 조회 예제"""
    print("🔄 빠른 매출내역 조회 예제")
    
    result = get_recent_revenue_quick(days=3, max_per_page=10)
    
    if result.get("success"):
        print("✅ 빠른 조회 성공")
    else:
        print(f"❌ 조회 실패: {result.get('message', '알 수 없는 오류')}")


if __name__ == "__main__":
    print("📊 쿠팡 매출내역 조회 예제 실행")
    print("=" * 50)
    
    example_recent_revenue()
    print()
    example_monthly_revenue()
    print()
    example_quick_revenue()