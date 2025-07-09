import os
import json
import requests
import datetime
import hmac
import hashlib
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 API 키 및 업체 코드 가져오기
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")

DOMAIN = "https://api-gateway.coupang.com"
METHOD = "POST"

def generate_hmac(method, url, secret_key, access_key):
    """HMAC-SHA256 서명을 생성합니다."""
    now = datetime.datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.datetime.utcnow().strftime('%H%M%S') + 'Z'
    message = now + method + url
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={now}, signature={signature}"

def complete_long_term_undelivery(shipment_box_id, invoice_number):
    """장기 미배송 건을 배송 완료로 처리합니다."""
    if not all([ACCESS_KEY, SECRET_KEY, VENDOR_ID]):
        return {"error": "API credentials are not set in environment variables."}

    REQUEST_URL = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/completeLongTermUndelivery"

    authorization = generate_hmac(METHOD, REQUEST_URL, SECRET_KEY, ACCESS_KEY)

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": authorization,
        "X-EXTENDED-TIMEOUT": "90000"
    }

    payload = {
        "shipmentBoxId": shipment_box_id,
        "invoiceNumber": invoice_number
    }

    try:
        response = requests.post(DOMAIN + REQUEST_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "details": response.text}
    except Exception as err:
        return {"error": f"Other error occurred: {err}"}

if __name__ == '__main__':
    # 사용 예시
    # 실제 값으로 대체해야 합니다.
    example_shipment_box_id = 123456789012345678
    example_invoice_number = "505124853844"

    print(f"--- 장기미배송 배송완료 처리 API 호출 예시 ---")
    print(f"묶음배송번호: {example_shipment_box_id}")
    print(f"운송장번호: {example_invoice_number}")
    print(f"-------------------------------------------")

    result = complete_long_term_undelivery(
        shipment_box_id=example_shipment_box_id,
        invoice_number=example_invoice_number
    )

    print("API 응답:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
