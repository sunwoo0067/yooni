#!/usr/bin/env python3
"""
쿠팡 상품 API 응답 구조 확인
"""

import sys
import json
import urllib.request
import urllib.parse
import psycopg2
import ssl

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


def test_product_api():
    # 데이터베이스 연결
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="yoonni",
        user="postgres",
        password="1234"
    )
    
    # 쿠팡 인증 정보 가져오기
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT vendor_id, access_key, secret_key, alias 
            FROM coupang 
            WHERE is_active = true
            LIMIT 1
        """)
        row = cursor.fetchone()
        
    vendor_id, access_key, secret_key, alias = row
    
    # 인증 객체 생성
    auth = CoupangAuth(access_key, secret_key, vendor_id)
    
    # SSL 컨텍스트 설정
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # 상품 목록 API 호출
    method = "GET"
    path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
    
    query_params = {
        'vendorId': vendor_id,
        'status': 'APPROVED',
        'limit': '2'  # 2개만 테스트
    }
    
    headers = auth.generate_authorization_header(method, path, query_params)
    
    query_string = urllib.parse.urlencode(query_params)
    url = f"https://api-gateway.coupang.com{path}?{query_string}"
    
    try:
        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request, context=ssl_context)
        
        data = json.loads(response.read().decode('utf-8'))
        
        print("=== 상품 목록 API 응답 구조 ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 첫 번째 상품 상세 조회
        if data.get('data') and len(data['data']) > 0:
            product_id = data['data'][0]['sellerProductId']
            print(f"\n\n=== 상품 상세 API 테스트 (상품 ID: {product_id}) ===")
            
            # 상품 상세 API
            detail_path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}"
            detail_query = {'vendorId': vendor_id}
            detail_headers = auth.generate_authorization_header(method, detail_path, detail_query)
            
            detail_url = f"https://api-gateway.coupang.com{detail_path}?vendorId={vendor_id}"
            
            detail_request = urllib.request.Request(detail_url, headers=detail_headers)
            detail_response = urllib.request.urlopen(detail_request, context=ssl_context)
            
            detail_data = json.loads(detail_response.read().decode('utf-8'))
            print(json.dumps(detail_data, indent=2, ensure_ascii=False))
            
            # items 배열 확인
            if detail_data.get('data', {}).get('items'):
                print("\n\n=== Items 배열 첫번째 아이템 ===")
                print(json.dumps(detail_data['data']['items'][0], indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    
    conn.close()


if __name__ == "__main__":
    test_product_api()