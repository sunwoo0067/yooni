"""Main automation worker that orchestrates the entire order fulfillment process.

This worker runs the complete automation flow:
1. Fetch new orders from Coupang
2. Place orders to Ownerclan
3. Update invoice numbers back to Coupang
"""
from __future__ import annotations

import sys
import pathlib
import time
from datetime import datetime, timedelta

# Ensure project root is on sys.path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from workers.coupang_fetch_worker import CoupangFetchWorker
from workers.ownerclan_place_worker import OwnerclanPlaceWorker
from workers.invoice_update_worker import InvoiceUpdateWorker
from market.coupaing.utils.supabase_client import get_supabase_client


class MainAutomationWorker:
    """Main worker that orchestrates all sub-workers."""
    
    def __init__(self, account_id: int):
        self.account_id = account_id
        self.supabase = get_supabase_client()
        
    def run(self, continuous: bool = False, interval_minutes: int = 10):
        """
        Run the complete automation process.
        
        Args:
            continuous: If True, run continuously with interval. If False, run once.
            interval_minutes: Minutes between each run if continuous is True.
        """
        print(f"Starting main automation for account {self.account_id}")
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"Starting automation cycle at {datetime.now()}")
                print(f"{'='*60}")
                
                # Step 1: 쿠팡 주문 수집
                print("\n[1/3] Fetching new Coupang orders...")
                try:
                    fetch_worker = CoupangFetchWorker(account_id=self.account_id)
                    fetch_worker.run()
                except Exception as e:
                    print(f"Error in fetch worker: {e}")
                    self._log_error("CoupangFetchWorker", str(e))
                
                # 잠시 대기 (API 제한 방지)
                time.sleep(2)
                
                # Step 2: 오너클렌 자동 발주
                print("\n[2/3] Placing orders to Ownerclan...")
                try:
                    place_worker = OwnerclanPlaceWorker(account_id=self.account_id)
                    place_worker.run()
                except Exception as e:
                    print(f"Error in place worker: {e}")
                    self._log_error("OwnerclanPlaceWorker", str(e))
                
                # 잠시 대기
                time.sleep(2)
                
                # Step 3: 송장 번호 업데이트
                print("\n[3/3] Updating invoice numbers...")
                try:
                    invoice_worker = InvoiceUpdateWorker(account_id=self.account_id)
                    invoice_worker.run()
                except Exception as e:
                    print(f"Error in invoice worker: {e}")
                    self._log_error("InvoiceUpdateWorker", str(e))
                
                # 통계 출력
                self._print_statistics()
                
                if not continuous:
                    break
                    
                # 다음 실행까지 대기
                print(f"\nWaiting {interval_minutes} minutes until next run...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\nAutomation stopped by user.")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                self._log_error("MainAutomationWorker", str(e))
                
                if not continuous:
                    break
                    
                # 에러 발생 시에도 계속 실행
                print(f"Waiting {interval_minutes} minutes before retry...")
                time.sleep(interval_minutes * 60)
    
    def _log_error(self, worker_name: str, error_message: str):
        """Log error to automation_logs table."""
        try:
            self.supabase.table("automation_logs").insert({
                "account_id": self.account_id,
                "worker_type": worker_name,
                "log_level": "ERROR",
                "message": error_message,
                "metadata": {"timestamp": datetime.now().isoformat()}
            }).execute()
        except:
            pass  # Ignore logging errors
    
    def _print_statistics(self):
        """Print current order statistics."""
        try:
            # NEW 상태 주문 수
            new_orders = self.supabase.table("orders").select("id").eq("account_id", self.account_id).eq("status", "NEW").execute()
            new_count = len(new_orders.data) if new_orders.data else 0
            
            # RECEIVED 상태 주문 수 (오너클렌 발주 완료)
            received_orders = self.supabase.table("orders").select("id").eq("account_id", self.account_id).eq("status", "RECEIVED").execute()
            received_count = len(received_orders.data) if received_orders.data else 0
            
            # SHIPPED 상태 주문 수 (송장 업데이트 완료)
            shipped_orders = self.supabase.table("orders").select("id").eq("account_id", self.account_id).eq("status", "SHIPPED").execute()
            shipped_count = len(shipped_orders.data) if shipped_orders.data else 0
            
            print(f"\n📊 Order Statistics:")
            print(f"  - NEW (대기중): {new_count}")
            print(f"  - RECEIVED (발주완료): {received_count}")
            print(f"  - SHIPPED (배송중): {shipped_count}")
            
        except Exception as e:
            print(f"Failed to print statistics: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the main automation process")
    parser.add_argument("--account-id", type=int, required=True, help="Account ID to process")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=10, help="Minutes between runs (default: 10)")
    
    args = parser.parse_args()

    worker = MainAutomationWorker(account_id=args.account_id)
    worker.run(continuous=args.continuous, interval_minutes=args.interval)