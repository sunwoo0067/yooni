#!/usr/bin/env python3
"""
인증 디버그 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# auth 모듈 직접 import
from auth.coupang_auth import CoupangAuth

# 계정 정보 (데이터베이스에서 가져온 값)
access_key = "2d6becfa-e876-47f1-aeab-b83a468313cc"
secret_key = "38f22728201a5bd4b19a0456227984dc9d26f412"
vendor_id = "A01409684"

# CoupangAuth 인스턴스 생성
auth = CoupangAuth(access_key, secret_key, vendor_id)

# 간단한 API 호출 테스트
import urllib.request
import json
import ssl

# SSL 컨텍스트
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 상품 목록 조회 (테스트)
method = "GET"
path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
query_params = {
    "vendorId": vendor_id,
    "nextToken": "1",
    "maxPerPage": "1"
}

# 헤더 생성
headers = auth.generate_authorization_header(method, path, query_params)
print("Generated headers:")
for k, v in headers.items():
    print(f"  {k}: {v}")

# API 호출
import urllib.parse
query_string = urllib.parse.urlencode(query_params)
url = f"https://api-gateway.coupang.com{path}?{query_string}"

print(f"\nURL: {url}")

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, context=ssl_context) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"\nAPI Response: {result.get('code')}")
        print("✅ 인증 성공!")
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"\n❌ API 오류 {e.code}: {error_body}")
except Exception as e:
    print(f"\n❌ 오류: {e}")