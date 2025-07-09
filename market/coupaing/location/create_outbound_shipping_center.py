"""
쿠팡 출고지 생성(POST) API 예제
- HMAC 인증 포함
- .env에서 vendorId, accesskey, secretkey 자동 로딩
- 실제 요청 body 예시 포함
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
    # UTC 기준 시각으로 HMAC 서명 생성
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_str + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_str}, signature={signature}"
    )
    return authorization, datetime_str

if __name__ == "__main__":
    method = "POST"
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/outboundShippingCenters"
    url = f"{SCHEMA}://{HOST}{path}"

    # 실제 요청 예시 body (테스트용 값)
    body_dict = {
        "vendorId": VENDOR_ID,
        "userId": "testId",
        "shippingPlaceName": "상품출고지 생성",
        "global": False,
        "usable": True,
        "placeAddresses": [
            {
                "addressType": "JIBUN",
                "countryCode": "KR",
                "companyContactNumber": "02-1512-1234",
                "phoneNumber2": "010-1212-1278",
                "returnZipCode": "10516",
                "returnAddress": "경기도 파주시 탄현면 월롱산로",
                "returnAddressDetail": "294-58"
            }
        ],
        "remoteInfos": [
            {
                "deliveryCode": "KGB",
                "jeju": 5000,
                "notJeju": 2500
            },
            {
                "deliveryCode": "CJGLS",
                "jeju": 5000,
                "notJeju": 2500
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