#!/usr/bin/env python3
"""
쿠팡-오너클렌 자동화 테스트 스크립트

이 스크립트는 전체 자동화 프로세스를 테스트합니다:
1. 쿠팡 주문 수집
2. 오너클렌 자동 발주
3. 송장 번호 업데이트
"""
import os
import sys
from datetime import datetime, date, timedelta

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market.coupaing.utils.supabase_client import get_supabase_client
from workers.coupang_fetch_worker import CoupangFetchWorker
from workers.ownerclan_place_worker import OwnerclanPlaceWorker
from workers.invoice_update_worker import InvoiceUpdateWorker


def test_coupang_fetch(account_id: int):
    """쿠팡 주문 수집 테스트"""
    print("\n=== 쿠팡 주문 수집 테스트 ===")
    try:
        worker = CoupangFetchWorker(account_id=account_id)
        # 어제부터 오늘까지 주문 조회
        today = date.today()
        yesterday = today - timedelta(days=1)
        worker.run(start_date=yesterday, end_date=today)
        print("✅ 쿠팡 주문 수집 완료")
        return True
    except Exception as e:
        print(f"❌ 쿠팡 주문 수집 실패: {e}")
        return False


def test_ownerclan_place(account_id: int):
    """오너클렌 발주 테스트"""
    print("\n=== 오너클렌 발주 테스트 ===")
    try:
        worker = OwnerclanPlaceWorker(account_id=account_id)
        worker.run()
        print("✅ 오너클렌 발주 완료")
        return True
    except Exception as e:
        print(f"❌ 오너클렌 발주 실패: {e}")
        return False


def test_invoice_update(account_id: int):
    """송장 업데이트 테스트"""
    print("\n=== 송장 업데이트 테스트 ===")
    try:
        worker = InvoiceUpdateWorker(account_id=account_id)
        worker.run()
        print("✅ 송장 업데이트 완료")
        return True
    except Exception as e:
        print(f"❌ 송장 업데이트 실패: {e}")
        return False


def check_environment():
    """환경 변수 확인"""
    print("\n=== 환경 변수 확인 ===")
    required_vars = [
        "COUPANG_ACCESS_KEY",
        "COUPANG_SECRET_KEY", 
        "COUPANG_VENDOR_ID",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "OWNERCLAN_USERNAME",
        "OWNERCLAN_PASSWORD"
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
        else:
            print(f"✅ {var}: 설정됨")
    
    if missing:
        print(f"\n❌ 다음 환경 변수가 설정되지 않았습니다:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    return True


def check_database_connection():
    """데이터베이스 연결 확인"""
    print("\n=== 데이터베이스 연결 확인 ===")
    try:
        supabase = get_supabase_client()
        # 간단한 쿼리로 연결 테스트
        result = supabase.table("accounts").select("id").limit(1).execute()
        print("✅ Supabase 연결 성공")
        return True
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return False


def get_test_account():
    """테스트용 계정 ID 가져오기"""
    try:
        supabase = get_supabase_client()
        # 쿠팡 계정 중 첫 번째 활성 계정 선택
        result = supabase.table("accounts").select("id, name").eq("market_id", 1).eq("active", True).limit(1).execute()
        
        if result.data:
            account = result.data[0]
            print(f"\n테스트 계정: {account['name']} (ID: {account['id']})")
            return account['id']
        else:
            print("\n❌ 활성화된 쿠팡 계정이 없습니다.")
            return None
    except Exception as e:
        print(f"\n❌ 계정 조회 실패: {e}")
        return None


def print_order_status(account_id: int):
    """현재 주문 상태 출력"""
    try:
        supabase = get_supabase_client()
        
        # 상태별 주문 수 조회
        statuses = ["NEW", "RECEIVED", "SHIPPED", "ERROR"]
        print("\n=== 주문 상태 현황 ===")
        
        for status in statuses:
            result = supabase.table("orders").select("id").eq("account_id", account_id).eq("status", status).execute()
            count = len(result.data) if result.data else 0
            print(f"{status}: {count}개")
            
    except Exception as e:
        print(f"주문 상태 조회 실패: {e}")


def main():
    """메인 테스트 함수"""
    print("🚀 쿠팡-오너클렌 자동화 테스트 시작")
    print(f"시작 시간: {datetime.now()}")
    
    # 1. 환경 확인
    if not check_environment():
        print("\n⚠️  환경 변수를 먼저 설정해주세요.")
        return
    
    # 2. DB 연결 확인
    if not check_database_connection():
        print("\n⚠️  데이터베이스 연결을 확인해주세요.")
        return
    
    # 3. 테스트 계정 선택
    account_id = get_test_account()
    if not account_id:
        print("\n⚠️  테스트할 계정이 없습니다.")
        return
    
    # 4. 현재 주문 상태 확인
    print_order_status(account_id)
    
    # 5. 각 단계별 테스트
    print("\n" + "="*50)
    input("Enter를 눌러 쿠팡 주문 수집을 시작하세요...")
    
    if test_coupang_fetch(account_id):
        print_order_status(account_id)
        
        print("\n" + "="*50)
        input("Enter를 눌러 오너클렌 발주를 시작하세요...")
        
        if test_ownerclan_place(account_id):
            print_order_status(account_id)
            
            print("\n" + "="*50)
            print("⚠️  송장 업데이트는 오너클렌에서 실제 송장이 등록된 후에 가능합니다.")
            input("Enter를 눌러 송장 업데이트를 시도하세요...")
            
            test_invoice_update(account_id)
            print_order_status(account_id)
    
    print(f"\n✅ 테스트 완료")
    print(f"종료 시간: {datetime.now()}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    main()