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

# 샘플 요청 함수 (실제 데이터 변경 없음)
def sample_request(method, path, query='', body=None):
    authorization, signed_date = generate_hmac_authorization(method, path, query)
    url = f"{SCHEMA}://{HOST}{path}"
    if query:
        url += f"?{query}"
    print(f"\n[샘플 요청] {method} {url}")
    print("[Authorization 헤더]", authorization)
    print("[Content-type] application/json;charset=UTF-8")
    if body:
        print("[Body]", body)
    print("[실제 요청은 생략됨]")
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

if __name__ == "__main__":
    # 1. POST 예제 (상품 생성)
    post_path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
    post_body = '{"sellerProductName": "예시상품", "vendorId": "%s"}' % VENDOR_ID
    sample_request("POST", post_path, '', post_body)

    # 2. GET 예제 (카테고리 메타정보 조회)
    get_path = "/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/77723"
    sample_request("GET", get_path)

    # 3. PUT 예제 (상품 수정)
    put_path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
    put_body = '{"sellerProductId": 123456, "sellerProductName": "수정상품"}'
    sample_request("PUT", put_path, '', put_body)

    # 4. DELETE 예제 (상품 삭제)
    delete_path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/123456"
    sample_request("DELETE", delete_path) 