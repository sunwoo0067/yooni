"""
쿠팡 OpenAPI HMAC 인증(Authorization 헤더) 생성 예제
- 모든 HTTP 메서드(POST/GET/PUT/DELETE) 지원
- .env에서 accesskey, secretkey 자동 로딩
- 실제 API 요청은 샘플로만(데이터 변경 없음)
"""
import os
import time
import hmac
import hashlib
import urllib.parse
import urllib.request
import ssl
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")

HOST = "api-gateway.coupang.com"
SCHEMA = "https"

# HMAC 인증 헤더 생성 함수
def generate_hmac_authorization(method, path, query='', secret_key=SECRET_KEY, access_key=ACCESS_KEY):
    # UTC 기준 시각으로 HMAC 서명 생성
    now = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
    message = now + method + path + (f'?{query}' if query else '')
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={now}, signature={signature}"
    )
    # 디버깅용 출력
    print("[디버그] HMAC message:", message)
    print("[디버그] Authorization 헤더:", authorization)
    return authorization, now

# 샘플 요청 함수 (실제 데이터 변경 없음)
def sample_request(method, path, encoded_query, unencoded_query):
    authorization, signed_date = generate_hmac_authorization(method, path, unencoded_query)
    url = f"https://api-gateway.coupang.com{path}"
    if encoded_query:
        url += f"?{encoded_query}"
    print("[디버그] 요청 URL:", url)

    print(f"\n[실제 요청] {method} {url}")
    req = urllib.request.Request(url, data=None, method=method)
    req.add_header("Content-type", "application/json;charset=UTF-8")
    req.add_header("Authorization", authorization)
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode('utf-8')
            print(f"[응답 코드]: {response.status}")
            print(f"[응답 본문]: {resp_body}")
    except urllib.error.HTTPError as e:
        print(f"[HTTPError] 코드: {e.code}, 메시지: {e.reason}")
        print(f"[응답 본문] {e.read().decode('utf-8')}")
    except Exception as ex:
        print(f"[기타 오류] {ex}")

if __name__ == "__main__":
    print("Coupang 공식 예제 코드로 GET 요청을 테스트합니다...")
    vendor_id = os.getenv('COUPANG_VENDOR_ID')
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets"
    created_from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
    created_to_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    query_params = {
        'createdAtFrom': created_from_date,
        'createdAtTo': created_to_date,
        'status': 'INSTRUCT'
    }
    sorted_params = sorted(query_params.items())
    unencoded_query = '&'.join([f"{k}={v}" for k, v in sorted_params])
    encoded_query = urllib.parse.urlencode(sorted_params)
    sample_request("GET", path, encoded_query, unencoded_query) 