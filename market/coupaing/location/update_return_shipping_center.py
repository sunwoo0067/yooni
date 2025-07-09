"""
쿠팡 반품지 수정(UPDATE) API 예제
- HMAC 인증 포함
- .env에서 accesskey, secretkey, vendorId 자동 로딩
- returnCenterCode 등은 예시값 사용
- 실제 요청은 주석 처리(테스트용)
"""
import os
import time
import hmac
import hashlib
import urllib.parse
import urllib.request
import ssl
import json
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', 'your-access-key')
SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', 'your-secret-key')
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID', 'A00******')

HOST = "api-gateway.coupang.com"
SCHEMA = "https"

# HMAC 인증 헤더 생성 함수
def generate_hmac_authorization(method, path, query='', secret_key=SECRET_KEY, access_key=ACCESS_KEY):
    datetime = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    message = datetime + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime}, signature={signature}"
    )
    return authorization, datetime

if __name__ == "__main__":
    method = "PUT"
    returnCenterCode = "1000558900"  # 예시값, 실제 값으로 교체 필요
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/returnShippingCenters/{returnCenterCode}"
    url = f"{SCHEMA}://{HOST}{path}"

    # 실제 요청 예시 body (테스트용 값)
    body_dict = {
        "userId": "testId",
        "vendorId": VENDOR_ID,
        "returnCenterCode": returnCenterCode,
        "shippingPlaceName": "반품지 -20200214-2modi",
        "usable": True,
        "goodsflowInfoOpenApiDto": {
            "deliverCode": "CJGLS",
            "vendorCreditFee05kg": 2500,
            "vendorCreditFee10kg": 2500,
            "vendorCreditFee20kg": 2500,
            "vendorCashFee05kg": 2500,
            "vendorCashFee10kg": 2500,
            "vendorCashFee20kg": 2500,
            "consumerCashFee05kg": 2500,
            "consumerCashFee10kg": 2500,
            "consumerCashFee20kg": 2500,
            "returnFee05kg": 2500,
            "returnFee10kg": 2500,
            "returnFee20kg": 2500
        },
        "placeAddresses": [
            {
                "addressType": "JIBUN",
                "companyContactNumber": "070-1234-8008",
                "phoneNumber2": "010-1234-7993",
                "returnZipCode": "110794",
                "returnAddress": "서울특별시 종로구 인사동5길 25 (인사동)",
                "returnAddressDetail": "하나로빌딩"
            }
        ]
    }
    body = json.dumps(body_dict).encode("utf-8")

    # HMAC 인증 헤더 생성
    authorization, signed_date = generate_hmac_authorization(method, path)

    print(f"[요청 URL] {url}")
    print("[Authorization 헤더]", authorization)
    print("[Content-type] application/json;charset=UTF-8")
    print("[Body]", json.dumps(body_dict, ensure_ascii=False, indent=2))
    print("[실제 요청은 주석 처리됨]")

    # 실제 요청을 원할 경우 아래 주석 해제
    # req = urllib.request.Request(url, data=body, method=method)
    # req.add_header("Content-type", "application/json;charset=UTF-8")
    # req.add_header("Authorization", authorization)
    # ctx = ssl.create_default_context()
    # ctx.check_hostname = False
    # ctx.verify_mode = ssl.CERT_NONE
    # try:
    #     with urllib.request.urlopen(req, context=ctx) as resp:
    #         print("[응답 코드]", resp.status)
    #         print("[응답 본문]", resp.read().decode(resp.headers.get_content_charset() or 'utf-8'))
    # except HTTPError as e:
    #     print(f"[HTTPError] 코드: {e.code}, 메시지: {e.reason}")
    #     print(e.read().decode())
    # except URLError as e:
    #     print(f"[URLError] {e.reason}") 