"""Worker that fetches Coupang orders for multi-account system."""
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

from market.coupaing.order.list_ordersheets import fetch_new_orders
from workers.base_worker_v2 import BaseWorkerV2


class CoupangFetchWorkerV2(BaseWorkerV2):
    """Fetch orders from Coupang for a specific market account."""

    def _set_account_env(self):
        """Set environment variables from account credentials."""
        if not self.market_account:
            raise ValueError("Market account not loaded")
        
        creds = self.market_account.get("credentials", {})
        market = self.market_account.get("markets", {})
        
        if market.get("code") != "coupang":
            raise ValueError(f"This worker only supports Coupang, not {market.get('code')}")
        
        # Set Coupang API credentials
        os.environ["COUPANG_VENDOR_ID"] = str(creds.get("vendor_id", ""))
        os.environ["COUPANG_ACCESS_KEY"] = creds.get("access_key", "")
        os.environ["COUPANG_SECRET_KEY"] = creds.get("secret_key", "")

    def run(self, start_date: date = None, end_date: date = None, statuses: List[str] = None):
        """Fetch orders from Coupang and save to database."""
        self.update_worker_status("RUNNING")
        
        try:
            self._set_account_env()
            
            # Default date range: yesterday to today
            if not start_date or not end_date:
                today = date.today()
                yesterday = today - timedelta(days=1)
                start_date = start_date or yesterday
                end_date = end_date or today
            
            # Default status: ACCEPT (발주지시)
            if statuses is None:
                statuses = ["ACCEPT"]
            
            self.log("INFO", f"Fetching Coupang orders from {start_date} to {end_date}")
            
            # Fetch orders using existing function
            orders = fetch_new_orders(start_date=start_date, end_date=end_date, statuses=statuses)
            
            if not orders:
                self.log("INFO", "No new orders found")
                self.update_worker_status("IDLE")
                return
            
            self.log("INFO", f"Found {len(orders)} orders to process")
            
            # Save orders to database
            self._save_orders(orders)
            
            self.update_worker_status("IDLE")
            
        except Exception as e:
            self.log("ERROR", f"Worker failed: {str(e)}")
            self.update_worker_status("ERROR")
            raise

    def _save_orders(self, orders: List[Dict[str, Any]]):
        """Save orders to the multi-account database structure."""
        orders_to_insert = []
        items_to_insert = []
        
        for order in orders:
            # Prepare order data
            order_data = {
                "user_id": self.user_id,
                "market_account_id": self.market_account_id,
                "market_order_id": str(order.get("orderId")),
                "shipment_box_id": order.get("shipmentBoxId"),
                "status": "NEW" if order.get("status") == "ACCEPT" else order.get("status"),
                "ordered_at": order.get("orderedAt"),
                "paid_at": order.get("paidAt"),
                "shipping_fee": float(order.get("shippingPrice", 0)),
                "total_amount": float(order.get("orderPrice", 0)),
                "customer_name": order.get("receiverName"),
                "customer_phone": order.get("receiverPhoneNumber"),
                "customer_email": order.get("ordererEmail"),
                "shipping_address": {
                    "addr1": order.get("receiverAddr1"),
                    "addr2": order.get("receiverAddr2"),
                    "postal_code": order.get("receiverPostCode"),
                },
                "invoice_number": order.get("invoiceNumber"),
                "shipping_company_code": order.get("deliveryCompanyCode"),
                "delivered_at": order.get("deliveredDate"),
                "raw_data": order,
            }
            
            # Insert order and get ID
            order_response = self.supabase.table("orders").insert(order_data).execute()
            
            if order_response.data:
                order_id = order_response.data[0]["id"]
                
                # Prepare order items
                for item in order.get("orderItems", []):
                    item_data = {
                        "order_id": order_id,
                        "market_item_id": str(item.get("productId")),
                        "market_sku": str(item.get("vendorItemId")),
                        "product_name": item.get("productName"),
                        "option_name": item.get("vendorItemName"),
                        "quantity": item.get("shippingCount", 0),
                        "unit_price": float(item.get("salesPrice", 0)),
                        "total_price": float(item.get("orderPrice", 0)),
                        "raw_data": item,
                    }
                    items_to_insert.append(item_data)
        
        # Insert all items
        if items_to_insert:
            self.supabase.table("order_items").insert(items_to_insert).execute()
            self.log("INFO", f"Saved {len(orders)} orders with {len(items_to_insert)} items")


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Fetch Coupang orders")
    parser.add_argument("--user-id", required=True, help="User ID")
    parser.add_argument("--market-account-id", type=int, required=True, help="Market account ID")
    parser.add_argument("--from", dest="from_date", help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", help="End date YYYY-MM-DD")
    args = parser.parse_args()
    
    # Parse dates
    from_dt = date.fromisoformat(args.from_date) if args.from_date else None
    to_dt = date.fromisoformat(args.to_date) if args.to_date else None
    
    worker = CoupangFetchWorkerV2(
        user_id=args.user_id,
        market_account_id=args.market_account_id
    )
    worker.run(start_date=from_dt, end_date=to_dt)