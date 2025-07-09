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

def fetch_and_store_history(vendor_id, shipment_box_id):
    print(f"========== vendorId: {vendor_id}, shipmentBoxId: {shipment_box_id} 배송상태 히스토리 조회를 시작합니다. ==========")
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/history"
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
            history_data = data['data']
            shipment_box_id_from_response = history_data.get('shipmentBoxId')
            details = history_data.get('details', [])
            print(f"조회된 묶음배송번호: {shipment_box_id_from_response}, 히스토리 {len(details)}건")

            if not details:
                print("조회된 배송상태 히스토리가 없습니다.")
                return

            history_to_upsert = []
            for item in details:
                history_to_upsert.append({
                    'shipment_box_id': shipment_box_id_from_response,
                    'delivery_status': item.get('deliveryStatus'),
                    'delivery_status_desc': item.get('deliveryStatusDesc'),
                    'updated_at': item.get('updatedAt')
                })
            
            try:
                # 복합 기본 키: shipment_box_id, delivery_status, updated_at
                response_history = supabase.table('coupang_order_shipment_history').upsert(
                    history_to_upsert,
                    on_conflict='shipment_box_id,delivery_status,updated_at'
                ).execute()
                print(f'Supabase coupang_order_shipment_history upsert 결과: {len(response_history.data)} 건 처리')

            except Exception as e:
                print(f'Supabase 저장 오류: {e}')
                print('참고: coupang_order_shipment_history 테이블이 존재하는지, 복합 기본 키(shipment_box_id, delivery_status, updated_at)가 올바르게 설정되었는지 확인해주세요.')

    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
    
    print(f"========== 배송상태 히스토리 조회를 완료했습니다. ==========")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("조회할 vendorId와 shipmentBoxId를 입력해주세요.")
        print("사용법: python3 get_ordersheet_history.py <vendorId> <shipmentBoxId>")
        sys.exit(1)

    vendor_id_to_fetch = sys.argv[1]
    shipment_box_id_to_fetch = sys.argv[2]
    fetch_and_store_history(vendor_id_to_fetch, shipment_box_id_to_fetch)
