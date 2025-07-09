"""Worker that places orders to Ownerclan for multi-account system."""
from __future__ import annotations

import sys
import pathlib

# Ensure project root is on sys.path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import os
from typing import Any, Dict, List

from supplier.ownerclan.create_order import create_order as oc_create_order
from workers.base_worker_v2 import BaseWorkerV2


class OwnerclanPlaceWorkerV2(BaseWorkerV2):
    """Place orders to Ownerclan for a specific supplier account."""

    def _set_account_env(self):
        """Set environment variables from account credentials."""
        if not self.supplier_account:
            raise ValueError("Supplier account not loaded")
        
        creds = self.supplier_account.get("credentials", {})
        supplier = self.supplier_account.get("suppliers", {})
        
        if supplier.get("code") != "ownerclan":
            raise ValueError(f"This worker only supports Ownerclan, not {supplier.get('code')}")
        
        # Set Ownerclan credentials
        os.environ["OWNERCLAN_USERNAME"] = creds.get("username", "")
        os.environ["OWNERCLAN_PASSWORD"] = creds.get("password", "")

    def run(self):
        """Process NEW orders and place them to Ownerclan."""
        self.update_worker_status("RUNNING")
        
        try:
            self._set_account_env()
            
            # Get NEW orders for this user
            orders_response = (
                self.supabase.table("orders")
                .select("*, order_items(*)")
                .eq("user_id", self.user_id)
                .eq("status", "NEW")
                .execute()
            )
            
            orders = orders_response.data
            if not orders:
                self.log("INFO", "No NEW orders to process")
                self.update_worker_status("IDLE")
                return
            
            self.log("INFO", f"Found {len(orders)} orders to place to Ownerclan")
            
            # Process each order
            for order in orders:
                self._process_order(order)
            
            self.update_worker_status("IDLE")
            
        except Exception as e:
            self.log("ERROR", f"Worker failed: {str(e)}")
            self.update_worker_status("ERROR")
            raise

    def _process_order(self, order: Dict[str, Any]):
        """Process a single order."""
        order_id = order["id"]
        
        try:
            # Get product mappings for order items
            mapped_items = []
            unmapped_skus = []
            
            for item in order.get("order_items", []):
                market_sku = item["market_sku"]
                
                # Find product mapping
                mapping_response = (
                    self.supabase.table("product_mappings")
                    .select("*")
                    .eq("user_id", self.user_id)
                    .eq("market_account_id", order["market_account_id"])
                    .eq("supplier_account_id", self.supplier_account_id)
                    .eq("market_sku", market_sku)
                    .eq("is_active", True)
                    .single()
                    .execute()
                )
                
                if mapping_response.data:
                    mapping = mapping_response.data
                    mapped_items.append({
                        "item": item,
                        "mapping": mapping
                    })
                else:
                    unmapped_skus.append(market_sku)
            
            if unmapped_skus:
                self.log("WARNING", f"Unmapped SKUs for order {order_id}: {unmapped_skus}")
                # Update order status to ERROR
                self.supabase.table("orders").update({
                    "status": "ERROR",
                    "updated_at": "now()"
                }).eq("id", order_id).execute()
                return
            
            # Build Ownerclan order payload
            payload = self._build_ownerclan_payload(order, mapped_items)
            
            # Create order in Ownerclan
            self.log("INFO", f"Creating Ownerclan order for {order_id}")
            result = oc_create_order(payload)
            
            # Extract order info from response
            oc_order = result.get("data", {}).get("createOrder", {})
            
            if not oc_order:
                raise Exception(f"Failed to create Ownerclan order: {result}")
            
            # Save supplier order
            supplier_order_data = {
                "order_id": order_id,
                "supplier_account_id": self.supplier_account_id,
                "supplier_order_id": oc_order.get("id"),
                "supplier_order_key": oc_order.get("key"),
                "status": "ORDERED",
                "total_amount": sum(item["item"]["total_price"] for item in mapped_items),
                "raw_response": result,
            }
            
            self.supabase.table("supplier_orders").insert(supplier_order_data).execute()
            
            # Update order status
            self.supabase.table("orders").update({
                "status": "PROCESSING",
                "updated_at": "now()"
            }).eq("id", order_id).execute()
            
            self.log("INFO", f"Successfully placed order {order_id} to Ownerclan")
            
        except Exception as e:
            self.log("ERROR", f"Failed to process order {order_id}: {str(e)}")
            # Update order status to ERROR
            self.supabase.table("orders").update({
                "status": "ERROR",
                "updated_at": "now()"
            }).eq("id", order_id).execute()

    def _build_ownerclan_payload(self, order: Dict[str, Any], mapped_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build Ownerclan order creation payload."""
        # Extract shipping address
        shipping_address = order.get("shipping_address", {})
        
        # Build products list
        products = []
        for item_info in mapped_items:
            item = item_info["item"]
            mapping = item_info["mapping"]
            
            products.append({
                "itemKey": mapping["supplier_item_key"],
                "quantity": item["quantity"],
                "price": item["unit_price"],
            })
        
        # Build payload
        payload = {
            "sender": {
                "name": "발송처",  # TODO: Get from account settings
                "phoneNumber": "010-0000-0000",
                "email": "seller@example.com",
            },
            "recipient": {
                "name": order.get("customer_name", ""),
                "phoneNumber": order.get("customer_phone", ""),
                "destinationAddress": {
                    "addr1": shipping_address.get("addr1", ""),
                    "addr2": shipping_address.get("addr2", ""),
                    "postalCode": shipping_address.get("postal_code", ""),
                },
            },
            "products": products,
            "shippingFee": order.get("shipping_fee", 0),
            "note": f"Order ID: {order['market_order_id']}",
        }
        
        return payload


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Place orders to Ownerclan")
    parser.add_argument("--user-id", required=True, help="User ID")
    parser.add_argument("--supplier-account-id", type=int, required=True, help="Supplier account ID")
    args = parser.parse_args()
    
    worker = OwnerclanPlaceWorkerV2(
        user_id=args.user_id,
        supplier_account_id=args.supplier_account_id
    )
    worker.run()