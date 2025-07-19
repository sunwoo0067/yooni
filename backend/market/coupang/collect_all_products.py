#!/usr/bin/env python3
"""
쿠팡 전체 상품 수집 (가격 정보 포함)
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
        
        # 통계
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'api_calls': 0
        }
        
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
            'limit': '10'  # 테스트를 위해 10개씩만
        }
        
        if next_token:
            query_params['nextToken'] = next_token
        
        headers = auth.generate_authorization_header(method, path, query_params)
        
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        try:
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request, context=self.ssl_context)
            self.stats['api_calls'] += 1
            
            return json.loads(response.read().decode('utf-8'))
            
        except urllib.error.HTTPError as e:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"API 에러: {error_data}")
            return None
        except Exception as e:
            print(f"예외 발생: {str(e)}")
            return None
    
    def fetch_product_detail(self, auth, vendor_id, product_id):
        """상품 상세 정보 조회 (가격 정보 포함)"""
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
            self.stats['api_calls'] += 1
            
            return json.loads(response.read().decode('utf-8'))
            
        except Exception as e:
            print(f"상품 상세 조회 실패 ({product_id}): {str(e)}")
            return None
    
    def save_product(self, account_id, product_data, detail_data=None):
        """상품 정보 DB 저장"""
        with self.conn.cursor() as cursor:
            # 기본 정보
            product_id = product_data.get('sellerProductId')
            
            # 상세 정보에서 가격 추출
            sale_price = None
            original_price = None
            stock_quantity = 0
            images = []
            attributes = []
            notices = []
            
            if detail_data and detail_data.get('data'):
                detail = detail_data['data']
                
                # items 배열에서 첫 번째 아이템의 가격 정보 추출
                if detail.get('items') and len(detail['items']) > 0:
                    first_item = detail['items'][0]
                    sale_price = first_item.get('salePrice')
                    original_price = first_item.get('originalPrice')
                    stock_quantity = first_item.get('maximumBuyCount', 0)
                    
                    # 이미지 정보
                    if first_item.get('images'):
                        for img in first_item['images']:
                            images.append({
                                'order': img.get('imageOrder'),
                                'type': img.get('imageType'),
                                'cdnPath': img.get('cdnPath'),
                                'vendorPath': img.get('vendorPath')
                            })
                    
                    # 속성 정보
                    attributes = first_item.get('attributes', [])
                    
                    # 고시정보
                    notices = first_item.get('notices', [])
            
            try:
                cursor.execute("""
                    INSERT INTO coupang_products (
                        coupang_account_id, product_id, seller_product_id,
                        seller_product_name, display_category_code, category_id,
                        brand_name, sale_price, original_price,
                        status_name, stock_quantity, images, attributes, 
                        notices, last_sync_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                        updated_at = CURRENT_TIMESTAMP,
                        last_sync_at = EXCLUDED.last_sync_at
                """, (
                    account_id,
                    product_id,
                    product_data.get('sellerProductId'),
                    product_data.get('sellerProductName'),
                    product_data.get('displayCategoryCode'),
                    product_data.get('categoryId'),
                    product_data.get('brand', '').strip() or None,
                    sale_price,
                    original_price,
                    product_data.get('statusName'),
                    stock_quantity,
                    Json(images),
                    Json(attributes),
                    Json(notices),
                    datetime.now()
                ))
                
                self.conn.commit()
                self.stats['success'] += 1
                return True
                
            except Exception as e:
                self.conn.rollback()
                print(f"상품 저장 실패 ({product_id}): {str(e)}")
                self.stats['failed'] += 1
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
            
            account_total = 0
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
                
                # 배치 처리
                for i, product in enumerate(products):
                    product_id = product.get('sellerProductId')
                    self.stats['total'] += 1
                    
                    # 진행 상황 표시 (10개마다)
                    if (i + 1) % 10 == 0 or (i + 1) == len(products):
                        print(f"  처리중: {account_total + i + 1}개 (전체: {self.stats['total']}개)")
                    
                    # 상세 정보 조회
                    detail_response = self.fetch_product_detail(
                        auth,
                        credentials['vendor_id'],
                        product_id
                    )
                    
                    # 저장
                    self.save_product(
                        credentials['account_id'], 
                        product,
                        detail_response
                    )
                    
                    # API 호출 제한 고려 (초당 10회 제한)
                    time.sleep(0.1)
                
                account_total += len(products)
                
                # 다음 페이지 확인
                next_token = response.get('nextToken')
                if not next_token:
                    break
                
                print(f"  다음 페이지 조회중... (현재까지 {account_total}개)")
                time.sleep(0.5)
            
            print(f"{credentials['alias']} 완료: {account_total}개 상품 처리")
    
    def show_summary(self):
        """수집 결과 요약"""
        with self.conn.cursor() as cursor:
            # 전체 상품 수
            cursor.execute("SELECT COUNT(*) FROM coupang_products")
            total = cursor.fetchone()[0]
            
            # 가격 정보가 있는 상품 수
            cursor.execute("SELECT COUNT(*) FROM coupang_products WHERE sale_price IS NOT NULL")
            with_price = cursor.fetchone()[0]
            
            # 계정별 통계
            cursor.execute("""
                SELECT c.alias, 
                       COUNT(cp.id) as total_products,
                       COUNT(CASE WHEN cp.sale_price IS NOT NULL THEN 1 END) as with_price
                FROM coupang c
                LEFT JOIN coupang_products cp ON c.id = cp.coupang_account_id
                GROUP BY c.id, c.alias
            """)
            
            print(f"\n=== 수집 결과 요약 ===")
            print(f"총 API 호출 수: {self.stats['api_calls']}회")
            print(f"처리 시도: {self.stats['total']}개")
            print(f"성공: {self.stats['success']}개")
            print(f"실패: {self.stats['failed']}개")
            print(f"\nDB 저장 현황:")
            print(f"총 상품 수: {total}개")
            print(f"가격 정보 있음: {with_price}개")
            
            print(f"\n계정별 현황:")
            for row in cursor.fetchall():
                print(f"- {row[0]}: 총 {row[1]}개 (가격정보: {row[2]}개)")
    
    def close(self):
        """연결 종료"""
        self.conn.close()


if __name__ == "__main__":
    print("=== 쿠팡 전체 상품 수집 시작 (가격 정보 포함) ===")
    print("※ 상품별로 상세 API를 호출하므로 시간이 걸립니다.")
    
    collector = CoupangProductCollector()
    try:
        # 기존 데이터 초기화 여부 확인
        with collector.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM coupang_products")
            existing = cursor.fetchone()[0]
            if existing > 0:
                print(f"\n기존 상품 {existing}개가 있습니다. 업데이트됩니다.")
        
        collector.collect_all_products()
        collector.show_summary()
        
    finally:
        collector.close()