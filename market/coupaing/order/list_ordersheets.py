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
            'status': order.get('status'),
            'ordered_at': order.get('orderedAt'),
            'paid_at': order.get('paidAt'),
            'shipping_price': order.get('shippingPrice'),
            'remote_price': order.get('remotePrice'),
            'delivery_company_code': order.get('deliveryCompanyCode'),
            'invoice_number': order.get('invoiceNumber'),
            'receiver_name': order.get('receiverName'),
            'delivered_date': order.get('deliveredDate') or None,
            'orderer_name': order.get('ordererName'),
            'orderer_phone_number': order.get('ordererPhoneNumber'),
            'receiver_phone_number': order.get('receiverPhoneNumber'),
            'raw_data': order, # 원본 데이터 저장
        })
        
        for item in order.get('orderItems', []):
            if not item.get('orderItemId'):
                print(f"[WARNING] Skipping item due to missing orderItemId: {item}")
                continue
            items_to_insert.append({
                'id': item.get('orderItemId'),
                'order_id': order.get('orderId'),
                'vendor_item_id': item.get('vendorItemId'),
                'vendor_item_name': item.get('vendorItemName'),
                'product_id': item.get('productId'),
                'product_name': item.get('productName'),
                'quantity': item.get('shippingCount'),
                'shipping_count': item.get('shippingCount'),
                'sales_price': item.get('salesPrice'),
                'order_price': item.get('orderPrice'),
                'discount_price': item.get('discountPrice'),
                'canceled': item.get('canceled'),
                'raw_item_data': item,
            })

    if orders_to_insert:
        print(f"{len(orders_to_insert)}개의 주문 정보를 Supabase에 저장합니다.")
        try:
            response_orders = supabase.table('coupang_orders').upsert(orders_to_insert, on_conflict='shipment_box_id').execute()
        except Exception as e:
            # If delivered_date column does not exist yet, retry without it
            if 'delivered_date' in str(e):
                print('[INFO] delivered_date column not found. Retrying without the column…')
                for o in orders_to_insert:
                    o.pop('delivered_date', None)
                response_orders = supabase.table('coupang_orders').upsert(orders_to_insert, on_conflict='shipment_box_id').execute()
            else:
                raise
        print("response_orders:", response_orders)
        if getattr(response_orders, 'data', None):
            print("주문 정보 저장 완료.")
        else:
            print(f"주문 정보 저장 실패: {getattr(response_orders, 'error', 'No error information')}")
        # 오류가 있으면 무조건 출력 (dict 접근)
        if isinstance(response_orders, dict) and response_orders.get('error'):
            print(f"[ERROR] 주문 저장 에러: {response_orders['error']}")

    if items_to_insert:
        print(f"{len(items_to_insert)}개의 주문 아이템 정보를 Supabase에 저장합니다.")
        response_items = supabase.table('coupang_order_items').upsert(items_to_insert, on_conflict='id').execute()
        print("response_items:", response_items)
        if getattr(response_items, 'data', None):
            print("주문 아이템 정보 저장 완료.")
        else:
            print(f"주문 아이템 정보 저장 실패: {getattr(response_items, 'error', 'No error information')}")
        # 오류가 있으면 무조건 출력 (dict 접근)
        if isinstance(response_items, dict) and response_items.get('error'):
            print(f"[ERROR] 아이템 저장 에러: {response_items['error']}")


def fetch_new_orders(start_date, end_date, statuses=None):
    print("Coupang API에서 신규 주문 목록을 가져오는 중...")
    all_orders = []
    next_token = None

    while True:
        try:
            domain = "https://api-gateway.coupang.com"
            method = "GET"
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets"
            
            query_params = {
                'createdAtFrom': start_date.strftime('%Y-%m-%d'),
                'createdAtTo': end_date.strftime('%Y-%m-%d'),
                'status': ','.join(statuses) if statuses else None,
                'maxPerPage': '50', # 페이지당 최대 50개
                'nextToken': next_token
            }

            # Remove keys with None values
            query_params = {k: v for k, v in query_params.items() if v is not None}
            sorted_params = sorted(query_params.items())
            # 인코딩되지 않은 쿼리 문자열 (HMAC 서명용)
            unencoded_query = '&'.join([f"{k}={v}" for k, v in sorted_params])
            # URL 인코딩된 쿼리 문자열 (URL용)
            encoded_query = urllib.parse.urlencode(sorted_params)

            authorization_header = generate_hmac_authorization('GET', path, unencoded_query)
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Authorization': authorization_header,
                'X-EXTENDED-TIMEOUT': '90000'
            }
            
            url = f"{domain}{path}?{encoded_query}"
            request = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    response_body = response.read()
                    data = json.loads(response_body)
                    if data.get('code') == 200:
                        if data.get('data'):
                            all_orders.extend(data['data'])
                        
                        next_token = data.get('nextToken')
                        if not next_token:
                            print(f"모든 페이지 조회를 완료했습니다.")
                            break # 다음 페이지가 없으면 루프 종료
                        else:
                            print(f"다음 페이지 조회 중... (nextToken: {next_token[:10]}...)")
                            time.sleep(1) # API 과부하 방지를 위해 잠시 대기
                    else:
                        print(f"API 응답 오류: {data.get('message')}")
                        break # 오류 발생 시 루프 종료
                else:
                    print(f"API 요청 실패: {response.status} {response.reason}")
                    break # 오류 발생 시 루프 종료

        except urllib.error.HTTPError as e:
            print(e.read().decode())
            print(f"API 요청 중 HTTP 예외 발생: {e}")
            break # 오류 발생 시 루프 종료
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류 발생: {e}")
            break
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")
            break # 오류 발생 시 루프 종료

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
    # 2025년 6월 1일부터 6월 30일까지 배송 완료된 주문 조회
    start_date = date(2025, 6, 1)
    end_date = date(2025, 6, 30)
    statuses = ["FINAL_DELIVERY"] # "배송 완료" 상태

    print(f"\n===== {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} {', '.join(statuses)} 상태 주문 조회 =====")
    
    # 한 달 단위로 주문을 가져와서 처리
    fetch_orders_monthly(start_date, end_date, statuses=statuses)