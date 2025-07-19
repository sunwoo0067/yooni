#!/usr/bin/env python3
"""
쿠팡 판매 상품 빠른 수집 (상세 정보 제외)
"""

import sys
import json
import urllib.request
import urllib.parse
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import time
import ssl

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


class CoupangProductCollector:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
        # SSL 컨텍스트 설정
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def get_coupang_credentials(self):
        """데이터베이스에서 쿠팡 인증 정보 조회"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, vendor_id, access_key, secret_key, alias 
                FROM coupang 
                WHERE is_active = true
            """)
            results = cursor.fetchall()
            
            credentials = []
            for row in results:
                credentials.append({
                    'account_id': row[0],
                    'vendor_id': row[1],
                    'access_key': row[2],
                    'secret_key': row[3],
                    'alias': row[4]
                })
            return credentials
    
    def fetch_products(self, auth, vendor_id, status='APPROVED', next_token=None):
        """쿠팡 상품 목록 조회"""
        method = "GET"
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        
        # 쿼리 파라미터
        query_params = {
            'vendorId': vendor_id,
            'status': status,
            'limit': '50'
        }
        
        if next_token:
            query_params['nextToken'] = next_token
        
        # 인증 헤더 생성
        headers = auth.generate_authorization_header(method, path, query_params)
        
        # API 요청
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        try:
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, context=self.ssl_context)
            
            return json.loads(response.read().decode('utf-8'))
            
        except urllib.error.HTTPError as e:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"API 에러: {error_data}")
            return None
        except Exception as e:
            print(f"예외 발생: {str(e)}")
            return None
    
    def save_products_batch(self, account_id, products):
        """상품 정보 일괄 DB 저장"""
        with self.conn.cursor() as cursor:
            for product in products:
                try:
                    cursor.execute("""
                        INSERT INTO coupang_products (
                            coupang_account_id, product_id, seller_product_id,
                            seller_product_name, display_category_code,
                            status_name, sale_price, original_price,
                            stock_quantity, barcode, last_sync_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (coupang_account_id, product_id) 
                        DO UPDATE SET
                            seller_product_name = EXCLUDED.seller_product_name,
                            sale_price = EXCLUDED.sale_price,
                            original_price = EXCLUDED.original_price,
                            status_name = EXCLUDED.status_name,
                            stock_quantity = EXCLUDED.stock_quantity,
                            updated_at = CURRENT_TIMESTAMP,
                            last_sync_at = EXCLUDED.last_sync_at
                    """, (
                        account_id,
                        product.get('sellerProductId'),
                        product.get('sellerProductId'),
                        product.get('sellerProductName'),
                        product.get('displayCategoryCode'),
                        product.get('statusName'),
                        product.get('salePrice'),
                        product.get('originalPrice'),
                        product.get('stockQuantity', 0),
                        product.get('barcode'),
                        datetime.now()
                    ))
                    
                except Exception as e:
                    print(f"상품 저장 실패 ({product.get('sellerProductId')}): {str(e)}")
            
            self.conn.commit()
    
    def collect_all_products(self):
        """모든 쿠팡 계정의 상품 수집"""
        credentials_list = self.get_coupang_credentials()
        
        for credentials in credentials_list:
            print(f"\n=== {credentials['alias']} 상품 수집 시작 ===")
            
            auth = CoupangAuth(
                access_key=credentials['access_key'],
                secret_key=credentials['secret_key'],
                vendor_id=credentials['vendor_id']
            )
            
            total_count = 0
            next_token = None
            
            while True:
                # 상품 목록 조회
                response = self.fetch_products(
                    auth, 
                    credentials['vendor_id'],
                    status='APPROVED',
                    next_token=next_token
                )
                
                if not response or 'data' not in response:
                    break
                
                products = response['data']
                
                # 일괄 저장
                self.save_products_batch(credentials['account_id'], products)
                total_count += len(products)
                
                print(f"  {len(products)}개 상품 저장 (누적: {total_count}개)")
                
                # 다음 페이지 확인
                next_token = response.get('nextToken')
                if not next_token:
                    break
                
                time.sleep(0.2)  # API 호출 제한 고려
            
            print(f"{credentials['alias']} 완료: 총 {total_count}개 상품 저장")
    
    def show_summary(self):
        """수집 결과 요약"""
        with self.conn.cursor() as cursor:
            # 전체 상품 수
            cursor.execute("SELECT COUNT(*) FROM coupang_products")
            total = cursor.fetchone()[0]
            
            # 계정별 상품 수
            cursor.execute("""
                SELECT c.alias, COUNT(cp.id) as product_count
                FROM coupang c
                LEFT JOIN coupang_products cp ON c.id = cp.coupang_account_id
                GROUP BY c.id, c.alias
            """)
            
            print(f"\n=== 수집 결과 요약 ===")
            print(f"총 {total}개 상품")
            
            for row in cursor.fetchall():
                print(f"- {row[0]}: {row[1]}개")
    
    def close(self):
        """연결 종료"""
        self.conn.close()


if __name__ == "__main__":
    print("=== 쿠팡 상품 빠른 수집 시작 ===")
    
    collector = CoupangProductCollector()
    try:
        collector.collect_all_products()
        collector.show_summary()
    finally:
        collector.close()