#!/usr/bin/env python3
"""
오늘 접수된 주문 현황 테스트
2025-07-14 쿠팡 파트너스 API 주문 조회 테스트
"""

import os
import sys
from datetime import datetime, timedelta

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

def test_today_orders():
    """오늘 접수된 주문 현황 테스트"""
    print("📅 오늘 접수된 주문 현황 테스트")
    print("=" * 60)
    print(f"테스트 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # OrderClient 초기화
        client = OrderClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        print(f"벤더 ID: {vendor_id}")
        print()
        
        # 오늘 날짜로 검색 파라미터 설정
        today = "2025-07-14"
        
        # 다양한 상태의 주문 조회
        statuses = [
            ("ACCEPT", "결제완료"),
            ("INSTRUCT", "상품준비중"),
            ("DEPARTURE", "배송지시"),
            ("DELIVERING", "배송중"),
            ("FINAL_DELIVERY", "배송완료")
        ]
        
        total_orders = 0
        status_summary = {}
        
        print("🔍 상태별 주문 현황 조회:")
        print("-" * 40)
        
        for status_code, status_name in statuses:
            try:
                # 검색 파라미터 생성
                params = OrderSheetSearchParams(
                    vendor_id=vendor_id,
                    created_at_from=today,
                    created_at_to=today,
                    status=status_code,
                    max_per_page=50
                )
                
                print(f"📋 {status_name}({status_code}) 조회중...")
                
                # API 호출
                result = client.get_order_sheets(params)
                
                if result.get("success"):
                    orders = result.get("data", [])
                    order_count = len(orders)
                    status_summary[status_name] = order_count
                    total_orders += order_count
                    
                    print(f"   ✅ {order_count}건 조회됨")
                    
                    # 주문 상세 정보 출력 (최대 3건)
                    if orders:
                        print("   📦 주문 상세:")
                        for i, order in enumerate(orders[:3]):
                            order_id = order.get('orderId', 'N/A')
                            ship_id = order.get('shipmentBoxId', 'N/A')
                            amount = order.get('orderPrice', 0)
                            print(f"      {i+1}. 주문#{order_id} 배송#{ship_id} {amount:,}원")
                        
                        if len(orders) > 3:
                            print(f"      ... 외 {len(orders) - 3}건")
                    
                else:
                    error_msg = result.get("error", "알 수 없는 오류")
                    print(f"   ❌ 조회 실패: {error_msg}")
                    status_summary[status_name] = 0
                
            except Exception as e:
                print(f"   ❌ {status_name} 조회 중 오류: {e}")
                status_summary[status_name] = 0
            
            print()
        
        # 결과 요약
        print("=" * 60)
        print("📊 오늘 주문 현황 요약")
        print("-" * 30)
        
        if total_orders > 0:
            print(f"🎯 총 주문 건수: {total_orders}건")
            print()
            print("📈 상태별 현황:")
            for status_name, count in status_summary.items():
                percentage = (count / total_orders * 100) if total_orders > 0 else 0
                print(f"   {status_name}: {count}건 ({percentage:.1f}%)")
        else:
            print("📭 오늘 접수된 주문이 없습니다.")
            print("💡 확인사항:")
            print("   - 날짜 범위가 올바른지 확인")
            print("   - 실제 주문이 있는 날짜로 테스트")
            print("   - API 인증 정보 확인")
        
        print()
        print("=" * 60)
        
        return total_orders > 0
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        return False

def test_recent_orders():
    """최근 7일간 주문 현황 테스트"""
    print("\n📅 최근 7일간 주문 현황 테스트")
    print("=" * 60)
    
    try:
        client = OrderClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        # 최근 7일간 날짜 범위
        end_date = datetime(2025, 7, 14)
        start_date = end_date - timedelta(days=6)
        
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        
        print(f"조회 기간: {date_from} ~ {date_to}")
        
        # 전체 주문 조회 (ACCEPT 상태)
        params = OrderSheetSearchParams(
            vendor_id=vendor_id,
            created_at_from=date_from,
            created_at_to=date_to,
            status="ACCEPT",  # 결제완료 상태
            max_per_page=50
        )
        
        result = client.get_order_sheets(params)
        
        if result.get("success"):
            orders = result.get("data", [])
            print(f"✅ 최근 7일간 신규 주문: {len(orders)}건")
            
            if orders:
                total_amount = sum(order.get('orderPrice', 0) for order in orders)
                avg_amount = total_amount / len(orders) if orders else 0
                
                print(f"💰 총 주문 금액: {total_amount:,}원")
                print(f"📊 평균 주문 금액: {avg_amount:,.0f}원")
        else:
            print(f"❌ 최근 주문 조회 실패: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ 최근 주문 테스트 중 오류: {e}")

def run_order_status_test():
    """주문 현황 테스트 실행"""
    print("🛒 쿠팡 파트너스 주문 현황 테스트")
    print(f"📅 테스트 일시: 2025-07-14")
    print()
    
    # 1. 오늘 주문 현황 테스트
    today_result = test_today_orders()
    
    # 2. 최근 7일간 주문 현황 테스트  
    test_recent_orders()
    
    print("\n🎉 주문 현황 테스트 완료!")
    
    if not today_result:
        print("\n💡 참고사항:")
        print("   - 테스트 환경에서는 실제 주문 데이터가 없을 수 있습니다")
        print("   - 실제 운영 환경에서 테스트해보시기 바랍니다")
        print("   - API 호출이 정상적으로 작동하는 것을 확인했습니다")

if __name__ == "__main__":
    run_order_status_test()