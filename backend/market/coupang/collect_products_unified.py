#!/usr/bin/env python3
"""
쿠팡 판매 상품 수집 - 통합 상품 스키마 버전
모든 계정의 상품을 수집하여 통합 테이블에 저장
"""

import sys
import json
import urllib.request
import urllib.parse
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import time
import ssl
import hashlib

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth.coupang_auth import CoupangAuth


class UnifiedCoupangProductCollector:
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
        
        # 쿠팡 마켓 ID 조회
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id FROM markets WHERE name = '쿠팡'")
            result = cursor.fetchone()
            if result:
                self.coupang_market_id = result[0]
            else:
                # 쿠팡 마켓 추가
                cursor.execute(
                    "INSERT INTO markets (name, code, api_url) VALUES (%s, %s, %s) RETURNING id",
                    ('쿠팡', 'COUPANG', 'https://api-gateway.coupang.com')
                )
                self.coupang_market_id = cursor.fetchone()[0]
                self.conn.commit()
                
    def get_coupang_accounts(self):
        """활성화된 쿠팡 계정 조회"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, vendor_id, access_key, secret_key, alias 
                FROM coupang 
                WHERE is_active = true
                ORDER BY id
            """)
            return cursor.fetchall()
    
    def generate_internal_sku(self, vendor_id, product_id):
        """내부 SKU 생성"""
        # 간단한 해시 기반 SKU 생성
        data = f"{vendor_id}_{product_id}"
        hash_value = hashlib.md5(data.encode()).hexdigest()[:8]
        return f"CP_{hash_value}".upper()
    
    def fetch_products(self, auth, vendor_id, next_token=None, retry_count=0):
        """쿠팡 API에서 상품 목록 조회"""
        method = "GET"
        path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        
        query_params = {
            "vendorId": vendor_id,
            "maxPerPage": "50"
        }
        
        if next_token:
            query_params["nextToken"] = next_token
        
        headers = auth.generate_authorization_header(method, path, query_params)
        headers["X-EXTENDED-Timeout"] = "90000"
        
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_message = e.read().decode('utf-8')
            print(f"API 오류: {e.code} - {error_message}")
            
            # 429 오류인 경우 재시도
            if e.code == 429 and retry_count < 3:
                wait_time = (retry_count + 1) * 30  # 30초, 60초, 90초 대기
                print(f"요청 제한 초과. {wait_time}초 대기 후 재시도... (시도 {retry_count + 1}/3)")
                time.sleep(wait_time)
                return self.fetch_products(auth, vendor_id, next_token, retry_count + 1)
            
            return None
    
    def save_product(self, account, product_data):
        """상품 정보를 통합 스키마에 저장"""
        try:
            with self.conn.cursor() as cursor:
                # 1. 내부 SKU 생성
                internal_sku = self.generate_internal_sku(
                    account['vendor_id'], 
                    product_data.get('sellerProductId')
                )
                
                # 2. products 테이블에 마스터 상품 추가/업데이트
                # 기존 테이블 구조에 맞춰 수정
                cursor.execute("""
                    INSERT INTO products (
                        internal_sku, product_key, name, price, base_price, 
                        brand, barcode, status, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (internal_sku) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        price = EXCLUDED.price,
                        base_price = EXCLUDED.base_price,
                        brand = EXCLUDED.brand,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    internal_sku,
                    internal_sku,  # product_key로 internal_sku 사용
                    product_data.get('sellerProductName', ''),
                    product_data.get('salePrice'),
                    product_data.get('originalPrice'),
                    product_data.get('brand', ''),
                    product_data.get('barcode', ''),
                    'active',
                    Json({
                        'vendor_id': account['vendor_id'],
                        'seller_product_id': product_data.get('sellerProductId')
                    })
                ))
                
                product_id = cursor.fetchone()[0]
                
                # 3. 공통 필드와 마켓 특화 필드 분리
                common_fields = {
                    'categoryId': product_data.get('categoryId'),
                    'displayCategoryCode': product_data.get('displayCategoryCode'),
                    'productTypeName': product_data.get('productTypeName'),
                    'images': product_data.get('images', []),
                    'attributes': product_data.get('attributes', []),
                    'notices': product_data.get('notices', [])
                }
                
                market_specific = {
                    'sellerProductId': product_data.get('sellerProductId'),
                    'statusName': product_data.get('statusName'),
                    'taxType': product_data.get('taxType'),
                    'adultOnly': product_data.get('adultOnly'),
                    'content': product_data.get('content', {}),
                    'deliveryMethod': product_data.get('deliveryMethod'),
                    'deliveryCompanyCode': product_data.get('deliveryCompanyCode'),
                    'deliveryChargeType': product_data.get('deliveryChargeType')
                }
                
                # 4. market_products 테이블에 마켓 상품 정보 저장
                cursor.execute("""
                    INSERT INTO market_products (
                        product_id, market_id, market_account_id, market_product_id,
                        market_sku, market_name, market_status, sale_price, 
                        stock_quantity, common_fields, market_specific, last_sync_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (market_id, market_account_id, market_product_id)
                    DO UPDATE SET
                        market_name = EXCLUDED.market_name,
                        market_status = EXCLUDED.market_status,
                        sale_price = EXCLUDED.sale_price,
                        stock_quantity = EXCLUDED.stock_quantity,
                        common_fields = EXCLUDED.common_fields,
                        market_specific = EXCLUDED.market_specific,
                        last_sync_at = EXCLUDED.last_sync_at,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    product_id,
                    self.coupang_market_id,
                    account['id'],
                    str(product_data.get('productId')),
                    product_data.get('sellerProductItemId', ''),
                    product_data.get('sellerProductName', ''),
                    product_data.get('statusName', ''),
                    product_data.get('salePrice'),
                    product_data.get('stockQuantity', 0),
                    Json(common_fields),
                    Json(market_specific),
                    datetime.now()
                ))
                
                market_product_id = cursor.fetchone()[0]
                
                # 5. 가격 이력 저장
                if product_data.get('salePrice'):
                    cursor.execute("""
                        INSERT INTO price_history (
                            market_product_id, price_type, price, changed_by, reason
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        market_product_id,
                        'sale',
                        product_data.get('salePrice'),
                        'system',
                        'API 동기화'
                    ))
                
                # 6. 재고 이력 저장 (첫 동기화인 경우)
                cursor.execute("""
                    SELECT COUNT(*) FROM inventory_history 
                    WHERE market_product_id = %s
                """, (market_product_id,))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO inventory_history (
                            market_product_id, quantity_before, quantity_after, 
                            quantity_change, change_type, changed_by, reason
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        market_product_id,
                        0,
                        product_data.get('stockQuantity', 0),
                        product_data.get('stockQuantity', 0),
                        'adjustment',
                        'system',
                        '첫 동기화'
                    ))
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"저장 오류: {e}")
            return False
    
    def collect_account_products(self, account):
        """특정 계정의 모든 상품 수집"""
        print(f"\n{'='*60}")
        print(f"계정: {account['alias']} (Vendor ID: {account['vendor_id']}) 상품 수집 시작")
        print(f"{'='*60}")
        
        auth = CoupangAuth(
            access_key=account['access_key'],
            secret_key=account['secret_key'],
            vendor_id=account['vendor_id']
        )
        
        # 동기화 로그 시작
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_logs (
                    market_id, market_account_id, sync_type, 
                    sync_status, started_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                self.coupang_market_id,
                account['id'],
                'product',
                'started',
                datetime.now()
            ))
            sync_log_id = cursor.fetchone()[0]
            self.conn.commit()
        
        next_token = "1"
        total_count = 0
        success_count = 0
        page = 1
        
        while next_token:
            print(f"\n페이지 {page} 처리 중...")
            
            response = self.fetch_products(auth, account['vendor_id'], next_token)
            
            if not response or response.get('code') != 'SUCCESS':
                print(f"API 응답 오류: {response}")
                break
            
            products = response.get('data', [])
            
            for product in products:
                total_count += 1
                if self.save_product(account, product):
                    success_count += 1
                    
                if total_count % 10 == 0:
                    print(f"  처리 중: {total_count}개 완료...")
            
            next_token = response.get('nextToken')
            
            # API 요청 간격 유지 (0.5초 대기)
            if next_token:
                time.sleep(0.5)
            page += 1
            
            # API 제한 고려
            time.sleep(0.1)
        
        # 동기화 로그 완료
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sync_logs SET
                    sync_status = %s,
                    total_items = %s,
                    processed_items = %s,
                    success_items = %s,
                    failed_items = %s,
                    completed_at = %s,
                    duration_seconds = EXTRACT(EPOCH FROM (%s - started_at))
                WHERE id = %s
            """, (
                'completed',
                total_count,
                total_count,
                success_count,
                total_count - success_count,
                datetime.now(),
                datetime.now(),
                sync_log_id
            ))
            self.conn.commit()
        
        print(f"\n✅ {account['alias']} 계정 수집 완료")
        print(f"   총 상품: {total_count}개")
        print(f"   성공: {success_count}개")
        print(f"   실패: {total_count - success_count}개")
        
        return success_count
    
    def run(self):
        """모든 계정의 상품 수집 실행"""
        print("🚀 쿠팡 상품 수집 시작 (통합 스키마)")
        print(f"시작 시간: {datetime.now()}")
        
        accounts = self.get_coupang_accounts()
        print(f"\n수집할 계정 수: {len(accounts)}개")
        
        total_products = 0
        
        for account in accounts:
            try:
                count = self.collect_account_products(account)
                total_products += count
            except Exception as e:
                print(f"❌ {account['alias']} 계정 처리 중 오류: {e}")
        
        print(f"\n{'='*60}")
        print(f"🎉 전체 수집 완료!")
        print(f"   총 수집 상품: {total_products}개")
        print(f"   완료 시간: {datetime.now()}")
        print(f"{'='*60}")
        
        # 수집 결과 요약 출력
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.alias,
                    COUNT(DISTINCT mp.market_product_id) as product_count,
                    COUNT(DISTINCT CASE WHEN mp.stock_quantity > 0 THEN mp.market_product_id END) as in_stock,
                    SUM(mp.stock_quantity) as total_stock,
                    MAX(mp.last_sync_at) as last_sync
                FROM coupang c
                JOIN market_products mp ON c.id = mp.market_account_id
                WHERE mp.market_id = %s
                GROUP BY c.id, c.alias
                ORDER BY c.id
            """, (self.coupang_market_id,))
            
            print("\n📊 계정별 상품 현황:")
            print(f"{'계정명':<15} {'상품수':<10} {'재고있음':<10} {'총재고':<10} {'최종동기화':<20}")
            print("-" * 70)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<15} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else 'N/A':<20}")
        
        self.conn.close()


if __name__ == "__main__":
    collector = UnifiedCoupangProductCollector()
    collector.run()