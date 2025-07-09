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

METHOD = "POST"
DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac(method, path, secret_key, access_key, body=""):
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + body
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"

def update_invoice(vendor_id, invoice_dtos):
    """
    기존 송장 정보를 수정합니다.
    :param vendor_id: 판매자 ID
    :param invoice_dtos: 수정할 송장 정보 DTO 목록 (list of dicts)
    :return: API 응답 JSON
    """
    print(f"========== vendorId: {vendor_id} 송장 수정을 시작합니다. ==========")
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/orders/updateInvoices"
    
    request_body = {
        "vendorId": vendor_id,
        "orderSheetInvoiceApplyDtos": invoice_dtos
    }
    body_json = json.dumps(request_body, separators=(',', ':'))

    authorization = generate_hmac(METHOD, path, SECRET_KEY, ACCESS_KEY, body_json)
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }

    api_response = None
    try:
        response = requests.post(f"{DOMAIN}{path}", headers=headers, data=body_json)
        response.raise_for_status()  # 2xx 응답 코드가 아닐 경우 HTTPError 발생
        api_response = response.json()

        print(f'응답 코드: {response.status_code}')
        print(f'응답 메시지: {api_response.get("message")}')

        if 'data' in api_response and api_response['data']:
            result_data = api_response['data']
            print(f'전체 결과: {result_data.get("responseMessage")} (코드: {result_data.get("responseCode")})')

            for item in result_data.get('responseList', []):
                print("----------------------------------------")
                shipment_id = item.get('shipmentBoxId')
                succeed = item.get('succeed')
                result_code = item.get('resultCode')
                result_message = item.get('resultMessage')
                retry_required = item.get('retryRequired')
                print(f"  - 묶음배송번호 {shipment_id}: {'성공' if succeed else '실패'}")
                print(f"    - 결과 코드: {result_code}")
                print(f"    - 결과 메시지: {result_message}")
                print(f"    - 재시도 필요: {'예' if retry_required else '아니오'}")

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP 오류 발생: {http_err}')
        if http_err.response:
            print(f'응답 내용: {http_err.response.text}')
            api_response = http_err.response.json()
    except requests.exceptions.RequestException as e:
        print(f'API 요청 오류: {e}')
    
    print(f"========== 송장 수정을 완료했습니다. ==========")
    return api_response

if __name__ == "__main__":
    # 이 스크립트는 복잡한 JSON 구조를 인자로 받기 때문에,
    # 직접 커맨드 라인에서 실행하기보다는 다른 스크リ프트에서 함수를 임포트하여 사용하는 것을 권장합니다.
    # 아래는 예시 사용법입니다.
    
    vendor_id_from_env = os.environ.get("COUPANG_VENDOR_ID")
    if not vendor_id_from_env:
        print("환경변수에서 COUPANG_VENDOR_ID를 찾을 수 없습니다.")
        sys.exit(1)

    # TODO: 아래 예시 데이터를 실제 수정할 송장 정보로 교체해야 합니다.
    # 이 데이터는 데이터베이스나 다른 소스에서 가져와야 합니다.
    example_invoice_dtos_to_update = [
        {
            "shipmentBoxId": 123456789012345678, # 실제 묶음배송번호로 변경 필요
            "orderId": 2000019631453,           # 실제 주문번호로 변경 필요
            "vendorItemId": 3819657333,         # 실제 옵션 ID로 변경 필요
            "deliveryCompanyCode": "HYUNDAI",   # 변경할 택배사 코드로 입력
            "invoiceNumber": "987654321098",    # 변경할 송장번호로 입력
            "splitShipping": False,
            "preSplitShipped": False,
            "estimatedShippingDate": ""
        }
    ]

    print("\n### 예시 송장 수정 실행 ###")
    print("주의: main 블록의 예시 데이터는 실제 데이터가 아니므로, API 호출 시 실패할 수 있습니다.")
    print("실제 사용 시에는 `example_invoice_dtos_to_update`를 유효한 데이터로 채워야 합니다.")
    
    # 아래 라인의 주석을 해제하면 예시 데이터로 API 호출을 시도합니다.
    # update_invoice(vendor_id_from_env, example_invoice_dtos_to_update)
    
    print("\n스크립트 사용 안내:")
    print("1. 이 파일(update_order_invoice.py)을 직접 수정하여 `example_invoice_dtos_to_update` 변수에 실제 수정할 데이터를 넣고 실행할 수 있습니다.")
    print("2. 다른 Python 스크립트에서 `from market.coupaing.order.update_order_invoice import update_invoice`로 함수를 임포트하여 사용할 수 있습니다.")
