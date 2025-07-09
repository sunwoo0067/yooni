import os
import sys
import hmac
import hashlib
import time
import requests
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(dotenv_path="/home/sunwoo/project/yooni/.env")

# Coupang API 키
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

METHOD = "PATCH"
DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac(method, path, secret_key, access_key, body=""):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + body
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def stop_shipment(vendor_id, receipt_id, cancel_count):
    """
    출고중지완료 처리
    :param vendor_id: 판매자 ID
    :param receipt_id: 접수 ID
    :param cancel_count: 출고 중지할 수량
    :return: API 응답 JSON
    """
    print(f"========== 접수번호 {receipt_id} 출고 중지 처리를 시작합니다. ==========")
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/returnRequests/{receipt_id}/stoppedShipment"
    
    request_body = {
        "vendorId": vendor_id,
        "receiptId": receipt_id,
        "cancelCount": cancel_count
    }
    body_json = json.dumps(request_body, separators=(',', ':'))

    authorization = generate_hmac(METHOD, path, SECRET_KEY, ACCESS_KEY, body_json)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }

    api_response = None
    try:
        response = requests.patch(f"{DOMAIN}{path}", headers=headers, data=body_json)
        response.raise_for_status()  # 2xx 응답 코드가 아닐 경우 HTTPError 발생
        api_response = response.json()

        print(f'응답 코드: {api_response.get("code")}')
        print(f'응답 메시지: {api_response.get("message")}')

        if 'data' in api_response and api_response['data']:
            result_data = api_response['data']
            result_code = result_data.get('resultCode')
            result_message = result_data.get('resultMessage')
            print(f"처리 결과: {result_message} ({result_code})")

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP 오류 발생: {http_err}')
        if http_err.response:
            print(f'응답 내용: {http_err.response.text}')
            api_response = http_err.response.json()
    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
    
    print(f"========== 출고 중지 처리를 완료했습니다. ==========")
    return api_response

if __name__ == "__main__":
    vendor_id_from_env = os.environ.get("COUPANG_VENDOR_ID")
    if not vendor_id_from_env:
        print("환경변수에서 COUPANG_VENDOR_ID를 찾을 수 없습니다.")
        sys.exit(1)

    # TODO: 아래 예시 데이터를 실제 처리할 데이터로 교체해야 합니다.
    # 이 데이터는 반품 요청 목록 조회 등을 통해 동적으로 얻어와야 합니다.
    example_receipt_id = 363667 # 실제 접수번호로 변경 필요
    example_cancel_count = 2     # 실제 취소수량으로 변경 필요

    print("\n### 예시 출고 중지 처리 실행 ###")
    print("주의: main 블록의 예시 데이터는 실제 데이터가 아니므로, API 호출 시 실패할 수 있습니다.")
    print("실제 사용 시에는 `example_receipt_id`와 `example_cancel_count`를 유효한 데이터로 채워야 합니다.")
    
    # 아래 라인의 주석을 해제하면 예시 데이터로 API 호출을 시도합니다.
    # stop_shipment(vendor_id_from_env, example_receipt_id, example_cancel_count)
    
    print("\n스크립트 사용 안내:")
    print("1. 이 파일(stop_return_request_shipment.py)을 직접 수정하여 변수에 실제 데이터를 넣고 실행할 수 있습니다.")
    print("2. 다른 Python 스크립트에서 `from market.coupaing.order.stop_return_request_shipment import stop_shipment`로 함수를 임포트하여 사용할 수 있습니다.")
