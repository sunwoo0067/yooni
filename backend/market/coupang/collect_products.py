#!/usr/bin/env python3
"""
쿠팡 판매 상품 수집 및 DB 저장
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
            'status': status,  # APPROVED(승인완료), REJECTED(승인반려), PARTIAL_APPROVED(부분승인)
            'limit': '50'  # 한 번에 조회할 상품 수
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
    
    def fetch_product_detail(self, auth, vendor_id, product_id):
        """상품 상세 정보 조회"""
        method = "GET"
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}"
        
        query_params = {
            'vendorId': vendor_id
        }
        
        headers = auth.generate_authorization_header(method, path, query_params)
        
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        try:
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, context=self.ssl_context)
            
            return json.loads(response.read().decode('utf-8'))
            
        except Exception as e:
            print(f"상품 상세 조회 실패 ({product_id}): {str(e)}")
            return None
    
    def save_product(self, account_id, product_data):
        """상품 정보 DB 저장"""
        with self.conn.cursor() as cursor:
            # 기본 정보 추출
            product_id = product_data.get('sellerProductId')
            
            # 상세 정보가 있는 경우
            if 'data' in product_data:
                detail = product_data['data']
            else:
                detail = product_data
            
            # 이미지 정보 추출
            images = []
            if 'images' in detail:
                for img in detail['images']:
                    images.append({
                        'order': img.get('imageOrder'),
                        'type': img.get('imageType'),
                        'url': img.get('vendorPath', img.get('cdnPath'))
                    })
            
            # 속성 정보 추출
            attributes = detail.get('attributes', [])
            
            # 고시정보 추출
            notices = detail.get('notices', [])
            
            # 상세 컨텐츠 추출
            content = detail.get('contents', {})
            
            try:
                cursor.execute("""
                    INSERT INTO coupang_products (
                        coupang_account_id, product_id, seller_product_id,
                        seller_product_name, display_category_code, category_id,
                        product_type_name, brand_name, sale_price, original_price,
                        status_name, stock_quantity, adult_only, tax_type, barcode,
                        images, attributes, notices, content, last_sync_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
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
                        content = EXCLUDED.content,
                        updated_at = CURRENT_TIMESTAMP,
                        last_sync_at = EXCLUDED.last_sync_at
                """, (
                    account_id,
                    product_id,
                    detail.get('sellerProductId'),
                    detail.get('sellerProductName'),
                    detail.get('displayCategoryCode'),
                    detail.get('categoryId'),
                    detail.get('productTypeName'),
                    detail.get('brand'),
                    detail.get('salePrice'),
                    detail.get('originalPrice'),
                    detail.get('statusName'),
                    detail.get('stockQuantity', 0),
                    detail.get('adultOnly', False),
                    detail.get('taxType'),
                    detail.get('barcode'),
                    Json(images),
                    Json(attributes),
                    Json(notices),
                    Json(content),
                    datetime.now()
                ))
                
                self.conn.commit()
                return True
                
            except Exception as e:
                self.conn.rollback()
                print(f"상품 저장 실패 ({product_id}): {str(e)}")
                return False
    
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
                
                for product in products:
                    product_id = product.get('sellerProductId')
                    print(f"  - 상품 처리중: {product_id} - {product.get('sellerProductName')}")
                    
                    # 상세 정보 조회
                    time.sleep(0.1)  # API 호출 제한 고려
                    detail_response = self.fetch_product_detail(
                        auth,
                        credentials['vendor_id'],
                        product_id
                    )
                    
                    if detail_response:
                        # 상세 정보를 포함하여 저장
                        product_with_detail = {**product, **detail_response}
                        self.save_product(credentials['account_id'], product_with_detail)
                        total_count += 1
                    else:
                        # 기본 정보만 저장
                        self.save_product(credentials['account_id'], product)
                        total_count += 1
                
                # 다음 페이지 확인
                next_token = response.get('nextToken')
                if not next_token:
                    break
                
                print(f"  다음 페이지 조회중... (현재까지 {total_count}개)")
                time.sleep(0.5)  # API 호출 제한 고려
            
            print(f"{credentials['alias']} 완료: 총 {total_count}개 상품 저장")
    
    def close(self):
        """연결 종료"""
        self.conn.close()


if __name__ == "__main__":
    print("=== 쿠팡 상품 수집 시작 ===")
    
    collector = CoupangProductCollector()
    try:
        collector.collect_all_products()
        
        # 수집 결과 확인
        with collector.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM coupang_products")
            total = cursor.fetchone()[0]
            print(f"\n총 {total}개 상품이 데이터베이스에 저장되었습니다.")
            
    finally:
        collector.close()