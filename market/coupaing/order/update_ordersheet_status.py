import os
import sys
import hmac
import hashlib
import time
import requests
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# 기존 스크립트에서 함수 임포트
from market.coupaing.order.get_ordersheet import fetch_and_update_order

# .env 파일 로드
load_dotenv(dotenv_path="/home/sunwoo/project/yooni/.env")

# Coupang API 키
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

# Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

METHOD = "PATCH"
DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac(method, path, secret_key, access_key, body=""):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + body
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def update_status_to_preparing(vendor_id, shipment_box_ids):
    print(f"========== vendorId: {vendor_id}, shipmentBoxIds: {shipment_box_ids} 상품준비중 처리를 시작합니다. ==========")
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/acknowledgement"
    
    request_body = {
        "vendorId": vendor_id,
        "shipmentBoxIds": shipment_box_ids
    }
    body_json = json.dumps(request_body, separators=(',', ':'))

    authorization = generate_hmac(METHOD, path, SECRET_KEY, ACCESS_KEY, body_json)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.patch(f"{DOMAIN}{path}", headers=headers, data=body_json)
        response.raise_for_status()
        data = response.json()

        print(f'응답 코드: {response.status_code}')
        print(f'응답 메시지: {data.get("message")}')

        if 'data' in data and data['data']:
            result_data = data['data']
            print(f'전체 결과: {result_data.get("responseMessage")}')

            for item in result_data.get('responseList', []):
                shipment_id = item.get('shipmentBoxId')
                succeed = item.get('succeed')
                result_message = item.get('resultMessage')
                print(f"  - 묶음배송번호 {shipment_id}: {'성공' if succeed else '실패'} ({result_message})")

                if succeed:
                    print(f"    -> 상품준비중 처리 성공. 변경된 배송지 정보를 확인하기 위해 발주서 단건 조회를 실행합니다.")
                    # 성공한 건에 대해 배송지 정보 업데이트를 위해 단건 조회 실행
                    fetch_and_update_order(shipment_id)

    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
        if e.response:
            print(f'응답 내용: {e.response.text}')
    
    print(f"========== 상품준비중 처리를 완료했습니다. ==========")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("조회할 vendorId와 하나 이상의 shipmentBoxId를 입력해주세요.")
        print("사용법: python3 update_ordersheet_status.py <vendorId> <shipmentBoxId1> <shipmentBoxId2> ...")
        sys.exit(1)

    vendor_id_to_fetch = sys.argv[1]
    # shipmentBoxId는 숫자여야 하므로 변환 시도
    try:
        shipment_box_ids_to_fetch = [int(sid) for sid in sys.argv[2:]]
    except ValueError:
        print("shipmentBoxId는 숫자여야 합니다.")
        sys.exit(1)

    if len(shipment_box_ids_to_fetch) > 50:
        print("최대 50개의 묶음배송번호만 요청할 수 있습니다.")
        sys.exit(1)

    update_status_to_preparing(vendor_id_to_fetch, shipment_box_ids_to_fetch)
