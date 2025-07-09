"""Worker that updates invoice numbers from Ownerclan to Coupang.

This worker:
1. Queries ownerclan_orders table for orders with tracking numbers
2. Updates the invoice numbers to Coupang via API
3. Updates the order status to SHIPPED
"""
from __future__ import annotations

import sys
import pathlib

# Ensure project root is on sys.path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import os
from typing import Any, Dict, List

from market.coupaing.order.update_order_invoice import update_invoice
from market.coupaing.utils.supabase_client import get_supabase_client
from supplier.ownerclan.get_order import get_order
from supplier.ownerclan.utils.auth import get_ownerclan_token

from workers.base_worker import BaseWorker


class InvoiceUpdateWorker(BaseWorker):
    """Update invoice numbers from Ownerclan to Coupang."""

    def _set_account_env(self):
        """Populate environment variables required by existing COUPANG utils."""
        creds: Dict[str, Any] = self.account.get("credentials") or {}
        if not creds.get("vendor_id"):
            raise ValueError("credentials.vendor_id missing for account")
        os.environ["COUPANG_VENDOR_ID"] = str(creds["vendor_id"])
        if creds.get("access_key"):
            os.environ["COUPANG_ACCESS_KEY"] = creds["access_key"]
        if creds.get("secret_key"):
            os.environ["COUPANG_SECRET_KEY"] = creds["secret_key"]

    def run(self):
        self._set_account_env()
        supabase = get_supabase_client()
        
        # 1. 오너클렌에서 발송 완료된 주문들 조회 (송장번호 업데이트 대상)
        # 먼저 RECEIVED 상태의 주문들을 가져옴
        orders_resp = (
            supabase.table("orders")
            .select("*")
            .eq("account_id", self.account_id)
            .eq("status", "RECEIVED")  # 오너클렌에 발주된 상태
            .execute()
        )
        
        if not orders_resp.data:
            print("No orders pending invoice update.")
            return
            
        # 각 주문에 대한 오너클렌 주문 정보 조회
        ownerclan_orders = []
        for order in orders_resp.data:
            oc_order_resp = (
                supabase.table("ownerclan_orders")
                .select("*")
                .eq("order_id", order["id"])
                .single()
                .execute()
            )
            if oc_order_resp.data:
                oc_order_resp.data["orders"] = order
                ownerclan_orders.append(oc_order_resp.data)
        
        if not ownerclan_orders:
            print("No orders pending invoice update.")
            return
            
        print(f"Found {len(ownerclan_orders)} orders to check for invoice updates")
        
        # 오너클렌 토큰 가져오기
        oc_token = get_ownerclan_token()
        
        # 쿠팡에 업데이트할 송장 정보 목록
        invoice_updates = []
        orders_to_update = []
        
        for oc_order in ownerclan_orders:
            try:
                # 오너클렌에서 주문 상세 정보 조회
                oc_key = oc_order.get("ownerclan_key")
                if not oc_key:
                    continue
                    
                order_data = get_order(oc_key, oc_token)
                order_info = order_data.get("data", {}).get("order", {})
                
                # 송장 번호 확인
                products = order_info.get("products", [])
                if not products:
                    continue
                    
                # 첫 번째 상품의 송장 정보 사용 (보통 같은 송장으로 배송)
                tracking_number = products[0].get("trackingNumber")
                shipping_company = products[0].get("shippingCompanyCode", "CJGLS")  # 기본값 CJ대한통운
                
                if tracking_number:
                    # 쿠팡 주문 정보
                    coupang_order = oc_order.get("orders", {})
                    raw_data = coupang_order.get("raw_data", {})
                    
                    # 송장 업데이트 정보 추가
                    invoice_dto = {
                        "shipmentBoxId": coupang_order.get("shipment_box_id"),
                        "orderId": int(coupang_order.get("market_order_id")),
                        "vendorItemId": None,  # 전체 주문에 대한 송장이므로 None
                        "deliveryCompanyCode": self._map_shipping_company(shipping_company),
                        "invoiceNumber": tracking_number,
                        "splitShipping": False,
                        "preSplitShipped": False,
                        "estimatedShippingDate": ""
                    }
                    
                    # vendorItemId 추출 (첫 번째 아이템 사용)
                    order_items = raw_data.get("orderItems", [])
                    if order_items:
                        invoice_dto["vendorItemId"] = order_items[0].get("vendorItemId")
                    
                    invoice_updates.append(invoice_dto)
                    orders_to_update.append({
                        "order_id": coupang_order.get("id"),
                        "tracking_number": tracking_number,
                        "shipping_company": shipping_company
                    })
                    
                    self.log("INFO", f"Found tracking number {tracking_number} for order {oc_key}")
                    
            except Exception as exc:
                self.log("ERROR", f"Failed to get Ownerclan order details: {exc}", 
                        {"ownerclan_key": oc_order.get("ownerclan_key")})
        
        # 3. 쿠팡에 송장 번호 업데이트
        if invoice_updates:
            print(f"Updating {len(invoice_updates)} invoices to Coupang...")
            vendor_id = os.environ.get("COUPANG_VENDOR_ID")
            
            try:
                result = update_invoice(vendor_id, invoice_updates)
                
                # 성공한 주문들의 상태 업데이트
                if result and result.get("data"):
                    response_list = result["data"].get("responseList", [])
                    
                    for response_item in response_list:
                        if response_item.get("succeed"):
                            shipment_box_id = response_item.get("shipmentBoxId")
                            
                            # 해당 주문 찾기
                            for order_info in orders_to_update:
                                order_resp = supabase.table("orders").select("*").eq("id", order_info["order_id"]).single().execute()
                                order = order_resp.data
                                
                                if order and order.get("shipment_box_id") == shipment_box_id:
                                    # 주문 상태를 SHIPPED로 업데이트
                                    supabase.table("orders").update({
                                        "status": "SHIPPED",
                                        "invoice_number": order_info["tracking_number"]
                                    }).eq("id", order_info["order_id"]).execute()
                                    
                                    self.log("INFO", f"Successfully updated invoice for order {order_info['order_id']}")
                                    break
                                    
            except Exception as exc:
                self.log("ERROR", f"Failed to update invoices to Coupang: {exc}")
    
    def _map_shipping_company(self, oc_code: str) -> str:
        """오너클렌 택배사 코드를 쿠팡 택배사 코드로 매핑"""
        mapping = {
            "CJ": "CJGLS",
            "HANJIN": "HANJIN",
            "LOTTE": "LOTTE",
            "LOGEN": "LOGEN",
            "POST": "EPOST",
            "KDEXP": "KDEXP",
            "CHUNIL": "CHUNIL",
            "DONGBU": "DONGBU",
            "DAESIN": "DAESIN",
            "ILYANG": "ILYANG",
            "HDEXP": "HDEXP",
            "GTX": "GTX",
            "HONAM": "HONAM",
            "KGB": "KGB",
            "KUNYOUNG": "KUNYOUNG",
            "SLX": "SLX",
            "SWGEXP": "SWGEXP",
        }
        return mapping.get(oc_code, "CJGLS")  # 기본값 CJ대한통운


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update invoice numbers from Ownerclan to Coupang")
    parser.add_argument("--account-id", type=int, required=True)
    args = parser.parse_args()

    InvoiceUpdateWorker(account_id=args.account_id).run()