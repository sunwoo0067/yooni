import os
import sys
import requests

# 스크립트가 프로젝트의 어느 위치에서 실행되더라도 루트 경로를 찾아서 sys.path에 추가합니다.
# 이렇게 하면 'market' 모듈을 항상 찾을 수 있습니다.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import hashlib
import hmac
import base64
import time
from urllib.parse import urlencode
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 프로젝트 루트 경로를 기준으로 .env 파일을 로드합니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# 공용 Supabase 클라이언트를 임포트합니다.
# 이 코드가 제대로 동작하려면, market/coupaing/utils 폴더가 파이썬 경로에 포함되어야 합니다.
# 일반적으로 VSCode와 같은 IDE는 프로젝트 루트를 자동으로 경로에 추가해줍니다.
# 만약 ModuleNotFoundError가 발생하면, 프로젝트 실행 환경의 PYTHONPATH를 확인해야 합니다.
from market.coupaing.utils.supabase_client import supabase_client as supabase

# Coupang API 키 로드
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID')
ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY')
SECRET_KEY = os.getenv('COUPANG_SECRET_KEY')
API_BASE = 'https://api-gateway.coupang.com'

if not all([VENDOR_ID, ACCESS_KEY, SECRET_KEY]):
    print('Coupang API 관련 환경변수(COUPANG_VENDOR_ID, COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY)가 올바르게 설정되어 있는지 확인하세요.')
    sys.exit(1)

# HMAC 인증 헤더 생성 함수
def generate_hmac_authorization(method, path, query='', secret_key=SECRET_KEY, access_key=ACCESS_KEY):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def fetch_and_store_orders(createdAtFrom, createdAtTo, status, maxPerPage):
    nextToken = ''
    while True:
        params = {
            'createdAtFrom': createdAtFrom,
            'createdAtTo': createdAtTo,
            'status': status,
            'maxPerPage': maxPerPage
        }
        if nextToken:
            params['nextToken'] = nextToken

        path = f'/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets'
        query = urlencode(params)
        url = f'{API_BASE}{path}?{query}'

        authorization = generate_hmac_authorization('GET', path, query)
        headers = {
            'Authorization': authorization,
            'Content-Type': 'application/json;charset=UTF-8'
        }

        print(f'요청 URL: {url}')
        response = requests.get(url, headers=headers)
        print(f'응답 코드: {response.status_code}')

        try:
            data = response.json()
            if response.status_code != 200:
                print('API 오류:', data)
                break

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
                        # 1. Upsert orders
                        response_orders = supabase.table('coupang_orders').upsert(orders_to_insert, on_conflict='order_id').execute()
                        print(f'Supabase orders upsert 결과: {len(response_orders.data)} 건 처리')

                        # 2. Upsert order items
                        if order_items_to_insert:
                            # vendor_item_id가 없는 항목은 upsert에서 제외 (on_conflict 제약조건 위배 방지)
                            items_with_vid = [item for item in order_items_to_insert if item.get('vendor_item_id') is not None]
                            if items_with_vid:
                                response_items = supabase.table('coupang_order_items').upsert(
                                    items_with_vid, 
                                    on_conflict='order_id,vendor_item_id' # 이 복합 키에 대한 UNIQUE 제약조건이 DB에 설정되어 있어야 합니다.
                                ).execute()
                                print(f'Supabase order_items upsert 결과: {len(response_items.data)} 건 처리')
                            else:
                                print('Upsert할 order_items가 없습니다 (vendor_item_id 누락).')

                    except Exception as e:
                        print(f'Supabase 저장 오류: {e}')
            
            if 'nextToken' in data and data['nextToken']:
                nextToken = data['nextToken']
                print('다음 페이지 토큰:', nextToken)
                time.sleep(1)
            else:
                print(f'{createdAtFrom} ~ {createdAtTo} 기간의 모든 페이지를 처리했습니다.')
                break

        except Exception as e:
            print('JSON 파싱 또는 처리 오류:', e)
            break

if __name__ == "__main__":
    createdAtFrom_str = sys.argv[1] if len(sys.argv) > 1 else '2025-06-01'
    createdAtTo_str = sys.argv[2] if len(sys.argv) > 2 else '2025-06-30'
    maxPerPage = sys.argv[3] if len(sys.argv) > 3 else '50'

    ALL_STATUSES = ['ACCEPT', 'INSTRUCT', 'DEPARTURE', 'DELIVERING', 'FINAL_DELIVERY', 'NONE_TRACKING']

    start_date = datetime.strptime(createdAtFrom_str, '%Y-%m-%d')
    end_date = datetime.strptime(createdAtTo_str, '%Y-%m-%d')

    for status in ALL_STATUSES:
        print(f"========== '{status}' 상태의 주문 조회를 시작합니다. ==========")
        current_start = start_date
        while current_start <= end_date:
            current_end = current_start + timedelta(days=30)
            if current_end > end_date:
                current_end = end_date
            
            print(f"--- {current_start.date()} 부터 {current_end.date()} 까지의 데이터 조회 ---")
            fetch_and_store_orders(
                current_start.strftime('%Y-%m-%d'),
                current_end.strftime('%Y-%m-%d'),
                status,
                maxPerPage
            )
            
            current_start = current_end + timedelta(days=1)
        print(f"========== '{status}' 상태의 주문 조회를 완료했습니다. ==========") 