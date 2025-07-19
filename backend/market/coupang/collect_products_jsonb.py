#!/usr/bin/env python3
"""
쿠팡 판매 상품 수집 - JSONB 저장 버전
모든 계정의 상품을 수집하여 원본 데이터를 JSONB로 저장
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

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


class CoupangProductCollectorJsonb:
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
            cursor.execute("SELECT id FROM markets WHERE code = 'COUPANG'")
            result = cursor.fetchone()
            if result:
                self.coupang_market_id = result[0]
            else:
                # 쿠팡 마켓이 없으면 오류
                raise Exception("쿠팡 마켓이 등록되지 않았습니다. markets 테이블을 확인하세요.")
                
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
    
    def fetch_products(self, auth, vendor_id, next_token=None):
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
            print(f"API 오류: {e.code} - {e.read().decode('utf-8')}")
            return None
    
    def save_product(self, account, product_data):
        """상품 정보를 JSONB로 저장"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO market_raw_products (
                        market_id, market_account_id, market_product_id, raw_data
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (market_id, market_account_id, market_product_id)
                    DO UPDATE SET
                        raw_data = EXCLUDED.raw_data,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    self.coupang_market_id,
                    account['id'],
                    str(product_data.get('productId')),
                    Json(product_data)
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
        print("🚀 쿠팡 상품 수집 시작 (JSONB 저장)")
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
            # 계정별 상품 현황
            cursor.execute("""
                SELECT 
                    c.alias,
                    COUNT(DISTINCT mrp.market_product_id) as product_count,
                    MAX(mrp.collected_at) as last_collected
                FROM coupang c
                JOIN market_raw_products mrp ON c.id = mrp.market_account_id
                WHERE mrp.market_id = %s
                GROUP BY c.id, c.alias
                ORDER BY c.id
            """, (self.coupang_market_id,))
            
            print("\n📊 계정별 상품 현황:")
            print(f"{'계정명':<15} {'상품수':<10} {'최종수집시간':<20}")
            print("-" * 50)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<15} {row[1]:<10} {row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else 'N/A':<20}")
            
            # 상품 상태별 통계
            cursor.execute("""
                SELECT 
                    raw_data->>'statusName' as status,
                    COUNT(*) as count
                FROM market_raw_products
                WHERE market_id = %s
                GROUP BY raw_data->>'statusName'
                ORDER BY count DESC
            """, (self.coupang_market_id,))
            
            print("\n📊 상품 상태별 현황:")
            print(f"{'상태':<20} {'개수':<10}")
            print("-" * 30)
            
            for row in cursor.fetchall():
                print(f"{row[0] or 'N/A':<20} {row[1]:<10}")
        
        self.conn.close()


if __name__ == "__main__":
    collector = CoupangProductCollectorJsonb()
    collector.run()