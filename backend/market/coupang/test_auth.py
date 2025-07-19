#!/usr/bin/env python3
"""
쿠팡 API 인증 테스트
데이터베이스에서 인증 정보를 가져와 테스트
"""

import sys
import json
import urllib.request
import psycopg2
from auth.coupang_auth import CoupangAuth


def get_coupang_credentials():
    """데이터베이스에서 쿠팡 인증 정보 조회"""
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="yoonni",
        user="postgres",
        password="1234"
    )
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT vendor_id, access_key, secret_key, alias 
                FROM coupang 
                WHERE is_active = true
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                return {
                    'vendor_id': result[0],
                    'access_key': result[1],
                    'secret_key': result[2],
                    'alias': result[3]
                }
            else:
                raise ValueError("활성화된 쿠팡 계정이 없습니다.")
    finally:
        conn.close()


def test_coupang_auth():
    """쿠팡 인증 테스트"""
    # 데이터베이스에서 인증 정보 가져오기
    credentials = get_coupang_credentials()
    print(f"테스트 계정: {credentials['alias']}")
    print(f"업체코드: {credentials['vendor_id']}")
    
    # 인증 객체 생성
    auth = CoupangAuth(
        access_key=credentials['access_key'],
        secret_key=credentials['secret_key'],
        vendor_id=credentials['vendor_id']
    )
    
    # 테스트 API 호출 - 반품 요청 조회 API (가장 기본적인 API)
    method = "GET"
    # 날짜 파라미터 설정 (오늘 날짜)
    from datetime import datetime, timedelta
    today = datetime.now()
    search_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    search_end = today.strftime('%Y-%m-%d')
    
    path = f"/v2/providers/openapi/apis/api/v4/vendors/{credentials['vendor_id']}/returnRequests"
    
    # 쿼리 파라미터
    query_params = {
        'createdAtFrom': search_start,
        'createdAtTo': search_end,
        'status': 'UC',  # 처리되지 않은 반품 요청
        'maxPerPage': '1'
    }
    
    # 인증 헤더 생성
    headers = auth.generate_authorization_header(method, path, query_params)
    headers['X-EXTENDED-Timestamp'] = headers['Authorization'].split('signed-date=')[1].split(',')[0]
    
    print("\n생성된 인증 헤더:")
    for key, value in headers.items():
        print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
    
    # API 요청
    query_string = urllib.parse.urlencode(query_params)
    url = f"https://api-gateway.coupang.com{path}?{query_string}"
    
    try:
        # SSL 인증서 검증 비활성화를 위한 설정
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request, context=ssl_context)
        
        # 응답 처리
        response_data = json.loads(response.read().decode('utf-8'))
        
        print(f"\n✅ 인증 성공!")
        print(f"응답 코드: {response_data.get('code', 'N/A')}")
        print(f"메시지: {response_data.get('message', 'N/A')}")
        
        if 'data' in response_data and isinstance(response_data['data'], list) and len(response_data['data']) > 0:
            print(f"상품 수: {len(response_data['data'])}")
            print(f"첫 번째 상품 ID: {response_data['data'][0].get('productId', 'N/A')}")
        
        return True
        
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        print(f"\n❌ 인증 실패!")
        print(f"HTTP 에러 코드: {e.code}")
        print(f"에러 메시지: {error_data.get('message', str(e))}")
        print(f"에러 코드: {error_data.get('code', 'N/A')}")
        return False
        
    except Exception as e:
        print(f"\n❌ 예외 발생!")
        print(f"에러: {str(e)}")
        return False


if __name__ == "__main__":
    print("=== 쿠팡 API 인증 테스트 ===")
    success = test_coupang_auth()
    sys.exit(0 if success else 1)