# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from market.coupaing.utils.auth import generate_hmac_authorization
from market.coupaing.utils.supabase_client import get_supabase_client
from market.coupaing.order.list_ordersheets import fetch_new_orders

# .env 파일 로드
load_dotenv()

# Coupang API 정보
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID')
BASE_URL = 'https://api-gateway.coupang.com'

def update_orders_to_preparing():
    """
    'INSTRUCT' 상태의 주문을 '상품준비중'으로 변경합니다.
    """
    print("========== 'INSTRUCT' 상태의 주문을 '상품준비중'으로 변경 시작 ==========")
    supabase = get_supabase_client()

    # 1. Supabase에서 'INSTRUCT' 상태의 주문 가져오기
    db_response = supabase.table('coupang_orders').select('shipment_box_id').eq('order_status', 'INSTRUCT').execute()
    
    if not db_response.data:
        print("처리할 'INSTRUCT' 상태의 주문이 없습니다.")
        return

    db_shipment_box_ids = {order['shipment_box_id'] for order in db_response.data}

    # 2. Coupang API에서 최신 'INSTRUCT' 상태 주문 가져오기
    print("Coupang API에서 최신 주문 정보를 가져옵니다...")
    latest_orders_data = fetch_new_orders()
    if not latest_orders_data:
        print("Coupang API에서 가져온 최신 주문 정보가 없습니다.")
        return

    # API 응답은 camelCase이므로 'shipmentBoxId'를 사용
    latest_shipment_box_ids = {order['shipmentBoxId'] for order in latest_orders_data}

    # 3. 실제 변경 가능한 주문 ID 선별 (교집합)
    shipment_box_ids_to_update = list(db_shipment_box_ids.intersection(latest_shipment_box_ids))

    if not shipment_box_ids_to_update:
        print("상태를 변경할 유효한 주문이 없습니다. (DB와 API 정보 불일치)")
        return

    print(f"총 {len(shipment_box_ids_to_update)}개의 주문을 '상품준비중'으로 변경합니다.")

    # 4. 50개씩 묶어서 API 호출
    for i in range(0, len(shipment_box_ids_to_update), 50):
        chunk = shipment_box_ids_to_update[i:i+50]
        
        path = f'/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/ordersheets/acknowledgement'
        query = ''
        body = {
            "vendorId": VENDOR_ID,
            "shipmentBoxIds": chunk
        }
        body_str = json.dumps(body)

        authorization_header = generate_hmac_authorization('PATCH', path, query, body_str)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': authorization_header
        }
        url = f"{BASE_URL}{path}"

        print(f"요청 URL: {url}")
        print(f"요청 Body: {body_str}")

        try:
            response = requests.request('PATCH', url, headers=headers, data=body_str)
            response_data = response.json()
            print(f"응답 코드: {response.status_code}")
            print(f"응답 데이터: {response_data}")

            if response.status_code == 200 and response_data.get('code') == 'SUCCESS':
                # 3. Supabase 상태 업데이트
                print(f"{len(chunk)}건의 주문 상태를 'PREPARING'으로 업데이트합니다.")
                supabase.table('coupang_orders').update({'status': 'PREPARING'}).in_('shipment_box_id', chunk).execute()
            else:
                print(f"API 오류 발생: {response_data.get('message')}")

        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 예외 발생: {e}")
        except json.JSONDecodeError:
            print(f"JSON 파싱 오류. 응답 내용: {response.text}")

    print("========== '상품준비중'으로 변경 완료 ==========")

if __name__ == "__main__":
    update_orders_to_preparing()
