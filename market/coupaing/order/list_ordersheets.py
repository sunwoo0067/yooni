# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv
import urllib.request
import urllib.parse
import ssl
import json
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from market.coupaing.utils.auth import generate_hmac_authorization
from market.coupaing.utils.supabase_client import get_supabase_client

# .env 파일 로드
load_dotenv()

# Coupang API 정보
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID')
BASE_URL = 'https://api-gateway.coupang.com'

def save_orders_to_supabase(orders):
    """
    가져온 주문들을 Supabase에 저장합니다.
    """
    if not orders:
        print("Supabase에 저장할 주문이 없습니다.")
        return

    supabase = get_supabase_client()
    orders_to_insert = []
    items_to_insert = []

    for order in orders:
        # DB 저장을 위해 camelCase key를 snake_case로 변환
        orders_to_insert.append({
            'order_id': order.get('orderId'),
            'shipment_box_id': order.get('shipmentBoxId'),
            'order_status': order.get('status'),
            'ordered_at': order.get('orderedAt'),
            'paid_at': order.get('paidAt'),
            'shipping_price': order.get('shippingPrice'),
            'remote_price': order.get('remotePrice'),
            'delivery_company_code': order.get('deliveryCompanyCode'),
            'delivery_company_name': order.get('deliveryCompanyName'),
            'invoice_number': order.get('invoiceNumber'),
            'receiver_name': order.get('receiverName'),
            'orderer_name': order.get('ordererName'),
            'orderer_phone_number': order.get('ordererPhoneNumber'),
            'receiver_phone_number': order.get('receiverPhoneNumber'),
        })
        
        for item in order.get('orderItems', []):
            items_to_insert.append({
                'order_item_id': item.get('orderItemId'),
                'order_id': order.get('orderId'),
                'vendor_item_id': item.get('vendorItemId'),
                'vendor_item_name': item.get('vendorItemName'),
                'product_id': item.get('productId'),
                'product_name': item.get('productName'),
                'quantity': item.get('shippingCount'),
                'order_price': item.get('orderPrice'),
                'discount_price': item.get('discountPrice'),
            })

    if orders_to_insert:
        print(f"{len(orders_to_insert)}개의 주문 정보를 Supabase에 저장합니다.")
        response_orders = supabase.table('coupang_orders').upsert(orders_to_insert, on_conflict='order_id').execute()
        if response_orders.data:
            print("주문 정보 저장 완료.")
        else:
            print(f"주문 정보 저장 실패: {getattr(response_orders, 'error', 'No error information')}")

    if items_to_insert:
        print(f"{len(items_to_insert)}개의 주문 아이템 정보를 Supabase에 저장합니다.")
        response_items = supabase.table('coupang_order_items').upsert(items_to_insert, on_conflict='order_item_id').execute()
        if response_items.data:
            print("주문 아이템 정보 저장 완료.")
        else:
            print(f"주문 아이템 정보 저장 실패: {getattr(response_items, 'error', 'No error information')}")


def fetch_new_orders(start_date=None, end_date=None, statuses=None):
    """
    Coupang API에서 신규 주문 목록을 가져옵니다.
    """
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    path = '/v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets'
    # 로컬 문서와 hmac_signature.py에서 확인된 최종 경로 사용
    path = '/v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets'
    formatted_path = path.format(vendorId=VENDOR_ID)
    
    all_orders = []
    next_token = None

    print("Coupang API에서 신규 주문 목록을 가져오는 중...")
    while True:
        # 마지막 시도: 올바른 경로 + 정렬된 쿼리 조합
        # vendorId는 경로에 있으므로 쿼리에서 제외하고,
        # 나머지 쿼리 파라미터를 알파벳 순으로 정렬 후 인코딩합니다.
        query_params = {
            'status': ','.join(statuses) if statuses else None,
            'createdAtFrom': start_date.strftime('%Y-%m-%d'),
            'createdAtTo': end_date.strftime('%Y-%m-%d'),
        }
        if next_token:
            query_params['nextToken'] = next_token

        # Remove keys with None values
        query_params = {k: v for k, v in query_params.items() if v is not None}
        sorted_params = sorted(query_params.items())
        query_string = '&'.join(f"{k}={v}" for k, v in sorted_params)  # keep ':' unencoded

        authorization_header = generate_hmac_authorization('GET', formatted_path, query_string)
        headers = {
            'Authorization': authorization_header,
            'Content-Type': 'application/json;charset=UTF-8'
        }

        # 4. 최종 요청 URL을 생성합니다.
        url = f"{BASE_URL}{formatted_path}?{query_string}"

        try:
            # urllib을 사용하여 API 요청
            req = urllib.request.Request(url, headers=headers, method='GET')
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, context=ctx) as resp:
                raw_bytes = resp.read()
                if resp.status >= 400:
                    try:
                        err_msg = raw_bytes.decode(resp.headers.get_content_charset() or 'utf-8')
                    except Exception:
                        err_msg = raw_bytes[:200]
                    raise Exception(f"HTTP Error {resp.status}: {resp.reason}. Body: {err_msg}")
                response_data = json.loads(raw_bytes.decode(resp.headers.get_content_charset() or 'utf-8'))

            if response_data.get('code') == 'SUCCESS' and response_data.get('data'):
                orders = response_data['data']
                all_orders.extend(orders)
                print(f"{len(orders)}개의 주문을 가져왔습니다. (총 {len(all_orders)}개)")
                
                next_token = response_data.get('nextToken')
                if not next_token:
                    break
                time.sleep(1) # API 과부하 방지
            else:
                print(f"API 오류 또는 데이터 없음: {response_data.get('message')}")
                break
        except Exception as e:
            print(f"API 요청 중 예외 발생: {e}")
            break
        except json.JSONDecodeError:
            print(f"JSON 파싱 오류. 응답 내용: {response.text}")
            break
            
    print(f"총 {len(all_orders)}개의 신규 주문을 가져왔습니다.")
    return all_orders


def fetch_orders_monthly(start_date: date, end_date: date, statuses=None):
    """Iterate month by month and fetch + save orders."""
    current_start = start_date
    while current_start <= end_date:
        # Calculate month end
        next_month_first = (current_start.replace(day=1) + relativedelta(months=1))
        current_end = next_month_first - timedelta(days=1)
        if current_end > end_date:
            current_end = end_date

        print(f"\n===== {current_start.strftime('%Y-%m-%d')} ~ {current_end.strftime('%Y-%m-%d')} =====")
        orders = fetch_new_orders(current_start, current_end, statuses=statuses)
        if orders:
            save_orders_to_supabase(orders)
        current_start = current_end + timedelta(days=1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Coupang orders and save to Supabase")
    parser.add_argument("--start", help="Start date YYYY-MM-DD", default=None)
    parser.add_argument("--batch-month", action="store_true", help="Fetch orders month-by-month to avoid API 500 errors")
    parser.add_argument("--status", help="Comma-separated order statuses to filter, e.g. DELIVERY_COMPLETED")
    parser.add_argument("--end", help="End date YYYY-MM-DD", default=None)
    args = parser.parse_args()
    statuses = [s.strip() for s in args.status.split(',')] if args.status else None

    try:
        if args.end:
            end_date_input = datetime.strptime(args.end, '%Y-%m-%d')
        else:
            end_date_input = datetime.utcnow()
        if args.start:
            start_date_input = datetime.strptime(args.start, '%Y-%m-%d')
        else:
            start_date_input = end_date_input - timedelta(days=7)
    except ValueError as e:
        print(f"날짜 형식이 올바르지 않습니다: {e}")
        sys.exit(1)

    print(f"{start_date_input.strftime('%Y-%m-%d')} ~ {end_date_input.strftime('%Y-%m-%d')} 범위의 주문을 조회합니다.")
    if args.batch_month:
        fetch_orders_monthly(start_date_input.date(), end_date_input.date(), statuses=statuses)
        new_orders = None
    else:
        new_orders = fetch_new_orders(start_date=start_date_input, end_date=end_date_input, statuses=statuses)
    # 시스템 시간 문제로 인한 400 오류를 피하기 위해, 테스트를 위한 특정 날짜 범위를 지정합니다.
    # 실제 운영 환경에서는 이 부분을 제거하거나 주석 처리하고, fetch_new_orders()를 파라미터 없이 호출해야 합니다.
    if new_orders:
        save_orders_to_supabase(new_orders)