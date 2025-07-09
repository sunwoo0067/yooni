"""
쿠팡 OpenAPI HMAC 인증(Signature) 생성 및 API 요청 예제
- Python 3.x 표준 라이브러리만 사용
- accessKey, secretKey, vendorId는 직접 입력 또는 환경변수 사용
- 실제 API 요청(GET) 예제 포함

사용법 예시:
    python hmac_signature.py
"""
import os
import time
import hmac
import hashlib
import urllib.parse
import urllib.request
import ssl
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

load_dotenv()

# 환경변수 또는 직접 입력
ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', 'your-access-key')
SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', 'your-secret-key')
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID', 'A00******')

HOST = "api-gateway.coupang.com"
SCHEMA = "https"
PORT = 443

# HMAC Signature 생성 함수
def generate_hmac_signature(method, path, query, secret_key, access_key):
    datetime = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    message = datetime + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime}, signature={signature}"
    )
    return authorization, datetime

# 쿠팡 API GET 요청 예제 함수
def coupang_api_get(access_key, secret_key, vendor_id, created_at_from, created_at_to, status):
    method = "GET"
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/returnRequests"
    query_dict = {
        "createdAtFrom": created_at_from,
        "createdAtTo": created_at_to,
        "status": status
    }
    query = urllib.parse.urlencode(query_dict)
    authorization, signed_date = generate_hmac_signature(method, path, query, secret_key, access_key)
    url = f"{SCHEMA}://{HOST}{path}?{query}"

    req = urllib.request.Request(url)
    req.add_header("Content-type", "application/json;charset=UTF-8")
    req.add_header("Authorization", authorization)
    req.get_method = lambda: method

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("\n[요청 URL]", url)
    print("[Authorization 헤더]", authorization)
    print("[요청 메서드]", method)

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = resp.read().decode(resp.headers.get_content_charset() or 'utf-8')
            print("[응답 코드]", resp.status)
            print("[응답 본문]", body)
    except HTTPError as e:
        print(f"[HTTPError] 코드: {e.code}, 메시지: {e.reason}")
        print(e.read().decode())
    except URLError as e:
        print(f"[URLError] {e.reason}")

if __name__ == "__main__":
    # 테스트용 파라미터 (직접 입력 또는 환경변수 사용)
    created_at_from = "2018-08-09"
    created_at_to = "2018-08-09"
    status = "UC"
    print("쿠팡 OpenAPI HMAC 인증 Signature 생성 및 API 요청 예제 실행")
    coupang_api_get(ACCESS_KEY, SECRET_KEY, VENDOR_ID, created_at_from, created_at_to, status) 