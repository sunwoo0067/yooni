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

def cancel_order_product(order_id, vendor_item_ids, receipt_counts, big_cancel_code, middle_cancel_code, user_id):
    """
    [결제완료] 또는 [상품준비중] 상태의 상품을 취소(또는 출고중지)합니다.
    - 상세 API 명세: docs/coupang_api_cancel_order_product.md 참조
    """
    if not all([ACCESS_KEY, SECRET_KEY, VENDOR_ID]):
        return {"error": "API credentials are not set in environment variables."}

    REQUEST_URL = f"/v2/providers/openapi/apis/api/v5/vendors/{VENDOR_ID}/orders/{order_id}/cancel"

    authorization = generate_hmac(METHOD, REQUEST_URL, SECRET_KEY, ACCESS_KEY)

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": authorization,
        "X-EXTENDED-TIMEOUT": "90000"
    }

    payload = {
        "vendorId": VENDOR_ID,
        "orderId": order_id,
        "vendorItemIds": vendor_item_ids,
        "receiptCounts": receipt_counts,
        "bigCancelCode": big_cancel_code,
        "middleCancelCode": middle_cancel_code,
        "userId": user_id
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
    # 아래 값들을 실제 테스트에 맞게 수정해야 합니다.
    example_order_id = 2000006593044
    example_vendor_item_ids = [3145181064, 3145181065]  # 취소할 상품의 vendorItemId 리스트
    example_receipt_counts = [1, 2]                     # 각 상품의 취소 수량 리스트 (vendorItemIds와 순서/개수 일치)
    example_big_cancel_code = "CANERR"                  # 대분류 취소 코드 (재고/가격/제휴사 오류)
    example_middle_cancel_code = "CCTTER"               # 중분류 취소 코드 (재고 연동 오류)
    example_user_id = "wing_login_id_123"               # 판매자의 Coupang Wing 로그인 ID

    print(f"--- 주문 상품 취소 처리 API 호출 예시 ---")
    print(f"주문 ID: {example_order_id}")
    print(f"취소 상품 ID: {example_vendor_item_ids}")
    print(f"-------------------------------------")

    result = cancel_order_product(
        order_id=example_order_id,
        vendor_item_ids=example_vendor_item_ids,
        receipt_counts=example_receipt_counts,
        big_cancel_code=example_big_cancel_code,
        middle_cancel_code=example_middle_cancel_code,
        user_id=example_user_id
    )

    print("API 응답:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
