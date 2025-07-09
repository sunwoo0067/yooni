import os
import sys
import hmac
import hashlib
import datetime
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv(dotenv_path="/home/sunwoo/project/yooni/.env")

# Coupang API 키
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")
VENDOR_ID = os.environ.get("COUPANG_VENDOR_ID")

# Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

METHOD = "GET"
DOMAIN = "https://api-gateway.coupang.com"
PATH = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets"

def generate_hmac(method, path, query, secret_key, access_key):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def fetch_and_store_orders(start_dt, end_dt, status):
    print(f"========== '{status}' 상태의 주문 조회를 시작합니다. ==========")
    print(f"--- {start_dt} 부터 {end_dt} 까지의 데이터 조회 ---")

    query = {
        'createdAtFrom': start_dt,
        'createdAtTo': end_dt,
        'status': status,
        'searchType': 'timeFrame'
    }
    query_string = urlencode(query)

    request_url = f"{DOMAIN}{PATH}?{query_string}"
    authorization = generate_hmac(METHOD, PATH, query_string, SECRET_KEY, ACCESS_KEY)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(request_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f'응답 코드: {response.status_code}')
        print('응답 데이터:', data)

        if 'data' in data and data['data']:
            unique_orders = {}
            order_items_to_insert = []

            for order in data['data']:
                order_id = order.get('orderId')
                if order_id and order_id not in unique_orders:
                    print(f"주문번호: {order_id}, 주문자: {order.get('orderer', {}).get('name')}, 상태: {order.get('status')}")
                    unique_orders[order_id] = {
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

                    if 'orderItems' in order and order['orderItems']:
                        for item in order['orderItems']:
                            order_items_to_insert.append({
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

            orders_to_insert = list(unique_orders.values())
            
            if orders_to_insert:
                try:
                    response_orders = supabase.table('coupang_orders').upsert(orders_to_insert, on_conflict='order_id').execute()
                    print(f'Supabase orders upsert 결과: {len(response_orders.data)} 건 처리')

                    if order_items_to_insert:
                        response_items = supabase.table('coupang_order_items').upsert(
                            order_items_to_insert, 
                            on_conflict='order_id,vendor_item_id'
                        ).execute()
                        print(f'Supabase order_items upsert 결과: {len(response_items.data)} 건 처리')

                except Exception as e:
                    print(f'Supabase 저장 오류: {e}')

    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
    
    print(f"========== '{status}' 상태의 주문 조회를 완료했습니다. ==========")

if __name__ == "__main__":
    now = datetime.datetime.now()
    start_dt_str = (now - datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    end_dt_str = now.strftime('%Y-%m-%dT%H:%M')

    createdAtFrom = sys.argv[1] if len(sys.argv) > 1 else start_dt_str
    createdAtTo = sys.argv[2] if len(sys.argv) > 2 else end_dt_str

    statuses = ['ACCEPT', 'INSTRUCT', 'DEPARTURE', 'DELIVERING', 'FINAL_DELIVERY', 'NONE_TRACKING']
    
    for status in statuses:
        fetch_and_store_orders(createdAtFrom, createdAtTo, status)
