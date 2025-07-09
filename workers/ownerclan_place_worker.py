"""Worker that places orders to Ownerclan for a given account.

Steps
1. Query `orders` where status='NEW' and account_id matches.
2. For each order, map items via `product_mappings` to Ownerclan itemKey.
3. Build Ownerclan GraphQL payload and call create_order.
4. Insert row into `ownerclan_orders`, update `orders.status`.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from supplier.ownerclan.create_order import create_order as oc_create_order
from workers.base_worker import BaseWorker
from market.coupaing.utils.supabase_client import get_supabase_client


class OwnerclanPlaceWorker(BaseWorker):
    """Place NEW orders into Ownerclan."""

    def run(self) -> None:  # noqa: C901 (complexity)
        supabase = get_supabase_client()
        open_orders_resp = (
            supabase.table("orders")
            .select("* , order_items(*)")
            .eq("status", "NEW")
            .eq("account_id", self.account_id)
            .execute()
        )
        if isinstance(open_orders_resp, dict) and open_orders_resp.get("error"):
            raise RuntimeError(open_orders_resp["error"])
        orders: List[Dict[str, Any]] = open_orders_resp.data  # type: ignore
        if not orders:
            print("No NEW orders to process.")
            return
        print(f"Placing {len(orders)} orders to Ownerclan…")
        for order in orders:
            try:
                payload = self._build_ownerclan_payload(order)
                result = oc_create_order(payload)
                # Extract key/id etc.
                oc_order = result.get("data", {}).get("createOrder", {})
                insert_data = {
                    "order_id": order["id"],
                    "ownerclan_key": oc_order.get("key"),
                    "ownerclan_order_id": oc_order.get("id"),
                    "status": oc_order.get("status"),
                    "raw_response": result,
                }
                supabase.table("ownerclan_orders").upsert(insert_data, on_conflict="order_id").execute()
                supabase.table("orders").update({"status": "RECEIVED"}).eq("id", order["id"]).execute()
                self.log("INFO", "Order placed to Ownerclan", {"order_id": order["id"]})
            except Exception as exc:  # pylint: disable=broad-except
                self.log("ERROR", f"Ownerclan order failed: {exc}", {"order_id": order.get("id")})
                supabase.table("orders").update({"status": "ERROR"}).eq("id", order["id"]).execute()

    def _build_ownerclan_payload(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert unified order row to Ownerclan GraphQL input format."""
        supabase = get_supabase_client()
        # Map each item
        items: List[Dict[str, Any]] = []
        for item in order.get("order_items", []):
            mapping_resp = (
                supabase.table("product_mappings")
                .select("ownerclan_item_key")
                .eq("market_id", order["market_id"])
                .eq("account_id", order["account_id"])
                .eq("market_sku", item["raw_item_data"].get("vendorItemId"))
                .single()
                .execute()
            )
            if isinstance(mapping_resp, dict) and mapping_resp.get("error"):
                raise RuntimeError(mapping_resp["error"])
            mapping = mapping_resp.data  # type: ignore
            if not mapping:
                raise ValueError("Product mapping missing for SKU")

            items.append(
                {
                    "itemKey": mapping["ownerclan_item_key"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                }
            )
        # Shipping info placeholder – should be adapted
        # 수신자 정보 추출 (쿠팡 receiver 객체에서)
        receiver = order.get("raw_data", {}).get("receiver", {})
        
        payload = {
            "sender": {
                "name": "발송처",  # TODO configurable
                "phoneNumber": "010-0000-0000",
                "email": "seller@example.com",
            },
            "recipient": {
                "name": receiver.get("name", ""),
                "phoneNumber": receiver.get("safeNumber", ""),
                "destinationAddress": {
                    "addr1": receiver.get("addr1", ""),
                    "addr2": receiver.get("addr2", ""),
                    "postalCode": receiver.get("postCode", ""),
                },
            },
            "products": items,
            "shippingFee": order.get("raw_data", {}).get("shippingPrice", 0),
            "note": f"Coupang order {order.get('market_order_id')}",
        }
        return payload


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Place orders to Ownerclan")
    parser.add_argument("--account-id", type=int, required=True)
    args = parser.parse_args()

    OwnerclanPlaceWorker(account_id=args.account_id).run()
