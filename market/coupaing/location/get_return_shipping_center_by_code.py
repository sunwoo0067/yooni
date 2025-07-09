"""
쿠팡 반품지 단건/복수 조회(센터코드 기반) API 예제
- HMAC 인증 포함
- .env에서 accesskey, secretkey 자동 로딩
- returnCenterCodes는 예시값 사용(최대 100개까지 지원)
- 실제 요청은 주석 처리(테스트용)
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

ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', 'your-access-key')
SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', 'your-secret-key')

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
    method = "GET"
    path = "/v2/providers/openapi/apis/api/v2/return/shipping-places/center-code"
    # 예시: 단일/복수 센터코드 조회
    returnCenterCodes = "1000000051,1000006047"  # 콤마로 구분, 최대 100개
    query_dict = {
        "returnCenterCodes": returnCenterCodes
    }
    query = urllib.parse.urlencode(query_dict)
    url = f"{SCHEMA}://{HOST}{path}?{query}"

    # HMAC 인증 헤더 생성
    authorization, signed_date = generate_hmac_authorization(method, path, query)

    print(f"[요청 URL] {url}")
    print("[Authorization 헤더]", authorization)
    print("[Content-type] application/json;charset=UTF-8")
    print("[실제 요청은 주석 처리됨]")

    # 실제 요청을 원할 경우 아래 주석 해제
    # req = urllib.request.Request(url, method=method)
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