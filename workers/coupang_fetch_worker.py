"""Worker that fetches Coupang orders for a specific account and stores them
into the unified `orders` / `order_items` tables.
"""
from __future__ import annotations

import sys
import pathlib

# Ensure project root is on sys.path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import os
from datetime import date, timedelta
from typing import Any, Dict, List

from market.coupaing.order.list_ordersheets import fetch_new_orders, save_orders_to_supabase  # noqa: E501
from market.coupaing.utils.supabase_client import get_supabase_client

from workers.base_worker import BaseWorker


class CoupangFetchWorker(BaseWorker):
    """Fetch NEW orders from Coupang for given account_id and upsert into DB."""

    def _set_account_env(self):
        """Populate environment variables required by existing COUPANG utils."""
        creds: Dict[str, Any] = self.account.get("credentials") or {}
        # Expected keys: vendor_id, access_key, secret_key
        if not creds.get("vendor_id"):
            raise ValueError("credentials.vendor_id missing for account")
        os.environ["COUPANG_VENDOR_ID"] = str(creds["vendor_id"])
        if creds.get("access_key"):
            os.environ["COUPANG_ACCESS_KEY"] = creds["access_key"]
        if creds.get("secret_key"):
            os.environ["COUPANG_SECRET_KEY"] = creds["secret_key"]

    def run(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        statuses: List[str] | None = None,
    ):
        self._set_account_env()
        if start_date is None or end_date is None:
            today = date.today()
            yesterday = today - timedelta(days=1)
            start_date = start_date or yesterday
            end_date = end_date or today
        print(
            f"Fetching Coupang orders for account {self.account_id} from {start_date} to {end_date}"
        )
        if statuses is None:
            # 쿠팡 주문 상태: ACCEPT(발주지시), INSTRUCT(상품준비중), DEPARTURE(출고완료), DELIVERING(배송중), FINAL_DELIVERY(배송완료)
            statuses = ["ACCEPT"]
        orders: List[Dict[str, Any]] = fetch_new_orders(
            start_date=start_date, end_date=end_date, statuses=statuses
        )
        if not orders:
            print("No new orders fetched.")
            return

        # Inject market_id & account_id into each order before saving
        market_id = self.account["market_id"]
        for o in orders:
            o["_market_id"] = market_id  # temporary keys for mapping in save
            o["_account_id"] = self.account_id

        # Re-use existing save_orders_to_supabase but adapt inside for new schema.
        self._save_orders_unified(orders)

    def _save_orders_unified(self, orders: List[Dict[str, Any]]):
        """Transform and upsert into new unified tables."""
        supabase = get_supabase_client()
        orders_to_upsert = []
        items_to_upsert = []
        for order in orders:
            # 주문 상태를 ACCEPT인 경우 NEW로 설정 (오너클렌 발주 대상)
            order_status = order.get("status")
            if order_status == "ACCEPT":
                order_status = "NEW"
            
            orders_to_upsert.append(
                {
                    "market_order_id": order.get("orderId"),
                    "shipment_box_id": order.get("shipmentBoxId"),
                    "market_id": order["_market_id"],
                    "account_id": order["_account_id"],
                    "status": order_status,
                    "ordered_at": order.get("orderedAt"),
                    "paid_at": order.get("paidAt"),
                    "invoice_number": order.get("invoiceNumber"),
                    "delivered_date": order.get("deliveredDate") or None,
                    "raw_data": order,
                }
            )
            for item in order.get("orderItems", []):
                if not item.get("orderItemId"):
                    continue
                items_to_upsert.append(
                    {
                        "id": item.get("orderItemId"),
                        "order_id": None,  # will rely on FK constraint via shipment_box later
                        "quantity": item.get("shippingCount"),
                        "price": item.get("salesPrice"),
                        "raw_item_data": item,
                    }
                )
        if orders_to_upsert:
            print(f"Upserting {len(orders_to_upsert)} orders…")
            supabase.table("orders").upsert(
                orders_to_upsert
            ).execute()
        if items_to_upsert:
            print(f"Upserting {len(items_to_upsert)} items…")
            supabase.table("order_items").upsert(items_to_upsert).execute()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Coupang orders")
    parser.add_argument("--account-id", type=int, required=True)
    parser.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD")
    parser.add_argument("--no-status", action="store_true", help="Query without status filter")
    parser.add_argument("--status", action="append", help="Add status filter (can repeat)")
    args = parser.parse_args()

    # Parse dates
    from_dt = date.fromisoformat(args.from_date) if args.from_date else None
    to_dt = date.fromisoformat(args.to_date) if args.to_date else None

    if args.no_status:
        statuses_arg = None
    elif args.status:
        statuses_arg = args.status
    else:
        statuses_arg = None

    CoupangFetchWorker(account_id=args.account_id).run(
        start_date=from_dt, end_date=to_dt, statuses=statuses_arg
    )
