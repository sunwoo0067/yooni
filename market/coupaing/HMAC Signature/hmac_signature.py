"""
���� OpenAPI HMAC ����(Signature) ���� �� API ��û ����
- Python 3.x ǥ�� ���̺귯���� ���
- accessKey, secretKey, vendorId�� ���� �Է� �Ǵ� ȯ�溯�� ���
- ���� API ��û(GET) ���� ����

���� ����:
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

# ȯ�溯�� �Ǵ� ���� �Է�
ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', 'your-access-key')
SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', 'your-secret-key')
VENDOR_ID = os.getenv('COUPANG_VENDOR_ID', 'A00******')

HOST = "api-gateway.coupang.com"
SCHEMA = "https"
PORT = 443

# HMAC Signature ���� �Լ�
def generate_hmac_signature(method, path, query, secret_key, access_key):
    datetime = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    message = datetime + method + path + query
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime}, signature={signature}"
    )
    return authorization, datetime

# ���� API GET ��û ���� �Լ�
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

    print("\n[��û URL]", url)
    print("[Authorization ���]", authorization)
    print("[��û �޼���]", method)

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = resp.read().decode(resp.headers.get_content_charset() or 'utf-8')
            print("[���� �ڵ�]", resp.status)
            print("[���� ����]", body)
    except HTTPError as e:
        print(f"[HTTPError] �ڵ�: {e.code}, �޽���: {e.reason}")
        print(e.read().decode())
    except URLError as e:
        print(f"[URLError] {e.reason}")

if __name__ == "__main__":
    # �׽�Ʈ�� �Ķ���� (���� �Է� �Ǵ� ȯ�溯�� ���)
    created_at_from = "2018-08-09"
    created_at_to = "2018-08-09"
    status = "UC"
    print("���� OpenAPI HMAC ���� Signature ���� �� API ��û ���� ����")
    coupang_api_get(ACCESS_KEY, SECRET_KEY, VENDOR_ID, created_at_from, created_at_to, status) 