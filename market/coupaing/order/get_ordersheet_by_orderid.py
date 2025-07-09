import os
import sys
import hmac
import hashlib
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv(dotenv_path="/home/sunwoo/project/yooni/.env")

# Coupang API 키
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

# Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

METHOD = "GET"
DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac(method, path, secret_key, access_key):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def fetch_and_update_order_by_orderid(vendor_id, order_id):
    print(f"========== vendorId: {vendor_id}, orderId: {order_id} 주문 단건 조회를 시작합니다. ==========")
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/{order_id}/ordersheets"
    authorization = generate_hmac(METHOD, path, SECRET_KEY, ACCESS_KEY)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{DOMAIN}{path}", headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f'응답 코드: {response.status_code}')

        if 'data' in data and data['data']:
            order = data['data']
            order_id = order.get('orderId')
            print(f"주문번호: {order_id}, 주문자: {order.get('orderer', {}).get('name')}, 상태: {order.get('status')}")

            order_to_update = {
                'order_id': order_id,
                'shipment_box_id': order.get('shipmentBoxId'),
                'ordered_at': order.get('orderedAt'),
                'paid_at': order.get('paidAt'),
                'status': order.get('status'),
                'shipping_price': order.get('shippingPrice'),
                'orderer_name': order.get('orderer', {}).get('name'),
                'receiver_name': order.get('receiver', {}).get('name'),
                'receiver_address': f"{order.get('receiver', {}).get('addr1')} {order.get('receiver', {}).get('addr2')}",
                'raw_data': order
            }

            items_to_update = []
            if 'orderItems' in order and order['orderItems']:
                for item in order['orderItems']:
                    items_to_update.append({
                        'order_id': order_id,
                        'vendor_item_id': item.get('vendorItemId'),
                        'seller_product_id': item.get('sellerProductId'),
                        'vendor_item_name': item.get('vendorItemName'),
                        'seller_product_name': item.get('sellerProductName'),
                        'shipping_count': item.get('shippingCount'),
                        'sales_price': item.get('salesPrice'),
                        'order_price': item.get('orderPrice'),
                        'discount_price': item.get('discountPrice'),
                        'canceled': item.get('canceled'),
                        'raw_item_data': item
                    })
            
            try:
                response_order = supabase.table('coupang_orders').upsert(order_to_update, on_conflict='order_id').execute()
                print(f'Supabase orders upsert 결과: {len(response_order.data)} 건 처리')

                if items_to_update:
                    response_items = supabase.table('coupang_order_items').upsert(
                        items_to_update, 
                        on_conflict='order_id,vendor_item_id'
                    ).execute()
                    print(f'Supabase order_items upsert 결과: {len(response_items.data)} 건 처리')

            except Exception as e:
                print(f'Supabase 저장 오류: {e}')

    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
    
    print(f"========== 주문 단건 조회를 완료했습니다. ==========")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("조회할 vendorId와 orderId를 입력해주세요.")
        print("사용법: python3 get_ordersheet_by_orderid.py <vendorId> <orderId>")
        sys.exit(1)

    vendor_id_to_fetch = sys.argv[1]
    order_id_to_fetch = sys.argv[2]
    fetch_and_update_order_by_orderid(vendor_id_to_fetch, order_id_to_fetch)
