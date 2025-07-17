#!/usr/bin/env python3
"""
쿠팡 파트너스 API 사용 예제
"""

import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

from market.coupang import CoupangClient


def test_coupang_api():
    """쿠팡 API 테스트"""
    
    try:
        # 클라이언트 초기화
        client = CoupangClient()
        print("✅ 쿠팡 클라이언트 초기화 성공")
        
        # 어제와 오늘 날짜
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📅 조회 기간: {yesterday} ~ {today}")
        
        # 반품 요청 조회
        print("\n🔄 반품 요청 조회 중...")
        return_requests = client.get_return_requests(
            created_at_from=yesterday,
            created_at_to=today,
            status="UC"  # 접수 완료 상태
        )
        print("✅ 반품 요청 조회 성공")
        print(f"📊 반품 요청 수: {len(return_requests.get('data', []))}")
        
        # 주문 조회
        print("\n🔄 주문 조회 중...")
        orders = client.get_orders(
            created_at_from=yesterday,
            created_at_to=today
        )
        print("✅ 주문 조회 성공")
        print(f"📊 주문 수: {len(orders.get('data', []))}")
        
        # 상품 목록 조회
        print("\n🔄 상품 목록 조회 중...")
        products = client.get_products(page=1, size=10)
        print("✅ 상품 목록 조회 성공")
        print(f"📊 상품 수: {len(products.get('data', []))}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    print("🚀 쿠팡 파트너스 API 테스트 시작")
    test_coupang_api()
    print("🏁 테스트 완료")