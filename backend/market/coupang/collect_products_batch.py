#!/usr/bin/env python3
"""
쿠팡 상품 일괄 수집 (배치 처리 최적화)
"""

import sys
import json
import urllib.request
import urllib.parse
import psycopg2
from psycopg2.extras import Json, execute_values
from datetime import datetime
import time
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


class CoupangBatchCollector:
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
        
        query_params = {
            'vendorId': vendor_id,
            'status': status,
            'limit': '50'
        }
        
        if next_token:
            query_params['nextToken'] = next_token
        
        headers = auth.generate_authorization_header(method, path, query_params)
        
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        try:
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, context=self.ssl_context)
            
            return json.loads(response.read().decode('utf-8'))
            
        except Exception as e:
            print(f"상품 목록 조회 실패: {str(e)}")
            return None
    
    def fetch_product_detail(self, auth, vendor_id, product_id):
        """상품 상세 정보 조회"""
        method = "GET"
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}"
        
        query_params = {'vendorId': vendor_id}
        headers = auth.generate_authorization_header(method, path, query_params)
        
        url = f"https://api-gateway.coupang.com{path}?vendorId={vendor_id}"
        
        try:
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, context=self.ssl_context)
            return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return None
    
    def process_product_batch(self, auth, vendor_id, account_id, products):
        """상품 배치 처리 (병렬 처리)"""
        results = []
        
        # 병렬로 상세 정보 조회
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_product = {}
            
            for product in products:
                future = executor.submit(
                    self.fetch_product_detail, 
                    auth, 
                    vendor_id, 
                    product['sellerProductId']
                )
                future_to_product[future] = product
            
            for future in as_completed(future_to_product):
                product = future_to_product[future]
                try:
                    detail_response = future.result()
                    
                    # 데이터 추출
                    product_data = self.extract_product_data(
                        account_id, 
                        product, 
                        detail_response
                    )
                    results.append(product_data)
                    
                except Exception as e:
                    print(f"상품 처리 실패 ({product['sellerProductId']}): {str(e)}")
        
        return results
    
    def extract_product_data(self, account_id, product, detail_response):
        """상품 데이터 추출"""
        product_id = product.get('sellerProductId')
        
        # 기본값
        sale_price = None
        original_price = None
        stock_quantity = 0
        images = []
        attributes = []
        notices = []
        
        # 상세 정보에서 추출
        if detail_response and detail_response.get('data'):
            detail = detail_response['data']
            
            if detail.get('items') and len(detail['items']) > 0:
                first_item = detail['items'][0]
                sale_price = first_item.get('salePrice')
                original_price = first_item.get('originalPrice')
                stock_quantity = first_item.get('maximumBuyCount', 0)
                
                if first_item.get('images'):
                    for img in first_item['images']:
                        images.append({
                            'order': img.get('imageOrder'),
                            'type': img.get('imageType'),
                            'cdnPath': img.get('cdnPath'),
                            'vendorPath': img.get('vendorPath')
                        })
                
                attributes = first_item.get('attributes', [])
                notices = first_item.get('notices', [])
        
        return (
            account_id,
            product_id,
            product.get('sellerProductId'),
            product.get('sellerProductName'),
            product.get('displayCategoryCode'),
            product.get('categoryId'),
            product.get('brand', '').strip() or None,
            sale_price,
            original_price,
            product.get('statusName'),
            stock_quantity,
            Json(images),
            Json(attributes),
            Json(notices),
            datetime.now()
        )
    
    def save_products_batch(self, products_data):
        """상품 정보 일괄 저장"""
        if not products_data:
            return
        
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO coupang_products (
                    coupang_account_id, product_id, seller_product_id,
                    seller_product_name, display_category_code, category_id,
                    brand_name, sale_price, original_price,
                    status_name, stock_quantity, images, attributes, 
                    notices, last_sync_at
                ) VALUES %s
                ON CONFLICT (coupang_account_id, product_id) 
                DO UPDATE SET
                    seller_product_name = EXCLUDED.seller_product_name,
                    sale_price = EXCLUDED.sale_price,
                    original_price = EXCLUDED.original_price,
                    status_name = EXCLUDED.status_name,
                    stock_quantity = EXCLUDED.stock_quantity,
                    images = EXCLUDED.images,
                    attributes = EXCLUDED.attributes,
                    notices = EXCLUDED.notices,
                    updated_at = CURRENT_TIMESTAMP,
                    last_sync_at = EXCLUDED.last_sync_at
                """,
                products_data
            )
            self.conn.commit()
    
    def collect_all(self, limit=None):
        """전체 상품 수집"""
        credentials_list = self.get_coupang_credentials()
        
        for credentials in credentials_list:
            print(f"\n=== {credentials['alias']} 상품 수집 시작 ===")
            
            auth = CoupangAuth(
                access_key=credentials['access_key'],
                secret_key=credentials['secret_key'],
                vendor_id=credentials['vendor_id']
            )
            
            total_processed = 0
            next_token = None
            
            while True:
                # 상품 목록 조회
                print(f"상품 목록 조회중... (현재까지 {total_processed}개)")
                response = self.fetch_products(
                    auth, 
                    credentials['vendor_id'],
                    status='APPROVED',
                    next_token=next_token
                )
                
                if not response or 'data' not in response:
                    break
                
                products = response['data']
                
                # 배치 처리
                print(f"{len(products)}개 상품 상세 정보 조회중...")
                products_data = self.process_product_batch(
                    auth,
                    credentials['vendor_id'],
                    credentials['account_id'],
                    products
                )
                
                # 일괄 저장
                self.save_products_batch(products_data)
                total_processed += len(products)
                
                print(f"{len(products_data)}개 저장 완료 (누적: {total_processed}개)")
                
                # 제한 확인
                if limit and total_processed >= limit:
                    print(f"제한 수량({limit}개) 도달")
                    break
                
                # 다음 페이지
                next_token = response.get('nextToken')
                if not next_token:
                    break
                
                # API 제한 고려
                time.sleep(0.5)
            
            print(f"{credentials['alias']} 완료: 총 {total_processed}개 처리")
    
    def show_summary(self):
        """수집 결과 요약"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.alias,
                    COUNT(cp.id) as total,
                    COUNT(CASE WHEN cp.sale_price IS NOT NULL THEN 1 END) as with_price,
                    MIN(cp.sale_price) as min_price,
                    MAX(cp.sale_price) as max_price,
                    AVG(cp.sale_price)::INTEGER as avg_price
                FROM coupang c
                LEFT JOIN coupang_products cp ON c.id = cp.coupang_account_id
                GROUP BY c.id, c.alias
            """)
            
            print("\n=== 수집 결과 요약 ===")
            for row in cursor.fetchall():
                print(f"\n{row[0]}:")
                print(f"  - 총 상품 수: {row[1]:,}개")
                print(f"  - 가격 정보 있음: {row[2]:,}개")
                if row[3]:
                    print(f"  - 가격 범위: {row[3]:,}원 ~ {row[4]:,}원")
                    print(f"  - 평균 가격: {row[5]:,}원")


if __name__ == "__main__":
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"=== 쿠팡 상품 수집 (최대 {limit}개) ===")
    else:
        print("=== 쿠팡 전체 상품 수집 ===")
    
    collector = CoupangBatchCollector()
    try:
        collector.collect_all(limit)
        collector.show_summary()
    finally:
        collector.conn.close()