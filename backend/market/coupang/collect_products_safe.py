#!/usr/bin/env python3
"""
쿠팡 상품 수집 - 안전한 버전 (API 속도 제한 고려)
- API 속도 제한 준수
- 재시도 로직 개선
- 중단 지점부터 재개 가능
"""

import sys
import json
import urllib.request
import urllib.parse
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime, timedelta
import time
import ssl
import hashlib
import os
from pathlib import Path

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


class SafeCoupangProductCollector:
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
        
        # API 속도 제한 설정
        self.request_delay = 1.0  # 기본 1초 대기
        self.last_request_time = 0
        self.consecutive_errors = 0
        
        # 진행 상태 저장 경로
        self.checkpoint_file = Path("coupang_collect_checkpoint.json")
        
        # 쿠팡 마켓 ID 조회
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id FROM markets WHERE name = '쿠팡'")
            result = cursor.fetchone()
            if result:
                self.coupang_market_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO markets (name, code, api_url) VALUES (%s, %s, %s) RETURNING id",
                    ('쿠팡', 'COUPANG', 'https://api-gateway.coupang.com')
                )
                self.coupang_market_id = cursor.fetchone()[0]
                self.conn.commit()
    
    def load_checkpoint(self):
        """중단된 지점 불러오기"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_checkpoint(self, account_id, next_token, total_count):
        """진행 상태 저장"""
        checkpoint = self.load_checkpoint()
        checkpoint[str(account_id)] = {
            'next_token': next_token,
            'total_count': total_count,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def clear_checkpoint(self, account_id):
        """계정의 체크포인트 삭제"""
        checkpoint = self.load_checkpoint()
        if str(account_id) in checkpoint:
            del checkpoint[str(account_id)]
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def wait_for_rate_limit(self):
        """API 속도 제한을 위한 대기"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_delay:
            wait_time = self.request_delay - elapsed
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def adjust_rate_limit(self, success=True):
        """API 응답에 따라 속도 조절"""
        if success:
            # 성공시 에러 카운트 리셋
            self.consecutive_errors = 0
            # 속도를 조금씩 높임 (최소 0.5초)
            self.request_delay = max(0.5, self.request_delay * 0.95)
        else:
            # 실패시 에러 카운트 증가
            self.consecutive_errors += 1
            # 속도를 낮춤 (최대 10초)
            self.request_delay = min(10.0, self.request_delay * 1.5)
    
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
        data = f"{vendor_id}_{product_id}"
        hash_value = hashlib.md5(data.encode()).hexdigest()[:8]
        return f"CP_{hash_value}".upper()
    
    def fetch_products(self, auth, vendor_id, next_token=None, retry_count=0):
        """쿠팡 API에서 상품 목록 조회 (개선된 재시도 로직)"""
        self.wait_for_rate_limit()
        
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
                self.adjust_rate_limit(success=True)
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_message = e.read().decode('utf-8')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] API 오류: {e.code} - {error_message}")
            
            self.adjust_rate_limit(success=False)
            
            # 429 오류인 경우 재시도
            if e.code == 429:
                if retry_count < 5:  # 최대 5회 재시도
                    wait_time = min(300, (retry_count + 1) * 60)  # 최대 5분 대기
                    print(f"요청 제한 초과. {wait_time}초 대기 후 재시도... (시도 {retry_count + 1}/5)")
                    time.sleep(wait_time)
                    return self.fetch_products(auth, vendor_id, next_token, retry_count + 1)
                else:
                    print("최대 재시도 횟수 초과. 다음에 다시 시도하세요.")
                    return None
            
            # 다른 에러는 잠시 대기 후 재시도
            elif retry_count < 3:
                wait_time = (retry_count + 1) * 10
                print(f"{wait_time}초 대기 후 재시도... (시도 {retry_count + 1}/3)")
                time.sleep(wait_time)
                return self.fetch_products(auth, vendor_id, next_token, retry_count + 1)
            
            return None
    
    def save_product(self, account, product_data):
        """상품 정보를 통합 스키마에 저장"""
        try:
            with self.conn.cursor() as cursor:
                # 1. unified_products 테이블에 저장/업데이트
                internal_sku = self.generate_internal_sku(
                    account['vendor_id'], 
                    product_data.get('productId')
                )
                
                cursor.execute("""
                    INSERT INTO unified_products (
                        internal_sku, product_name, brand_name, manufacturer,
                        category_large, category_medium, category_small, category_detail,
                        description, main_image_url, additional_images,
                        is_active, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (internal_sku) DO UPDATE SET
                        product_name = EXCLUDED.product_name,
                        brand_name = EXCLUDED.brand_name,
                        manufacturer = EXCLUDED.manufacturer,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id
                """, (
                    internal_sku,
                    product_data.get('productName'),
                    product_data.get('brand'),
                    product_data.get('manufacturerName'),
                    product_data.get('categoryName', '').split('>')[0].strip() if product_data.get('categoryName') else None,
                    product_data.get('categoryName', '').split('>')[1].strip() if product_data.get('categoryName') and len(product_data.get('categoryName').split('>')) > 1 else None,
                    product_data.get('categoryName', '').split('>')[2].strip() if product_data.get('categoryName') and len(product_data.get('categoryName').split('>')) > 2 else None,
                    product_data.get('categoryName', '').split('>')[3].strip() if product_data.get('categoryName') and len(product_data.get('categoryName').split('>')) > 3 else None,
                    None,  # description
                    product_data.get('imageUrl'),
                    None,  # additional_images
                    product_data.get('productStatus') == 'ACTIVE',
                    datetime.now(),
                    datetime.now()
                ))
                
                unified_product_id = cursor.fetchone()[0]
                
                # 2. market_products 테이블에 저장/업데이트
                cursor.execute("""
                    INSERT INTO market_products (
                        unified_product_id, market_id, market_account_id,
                        market_product_id, market_product_code,
                        market_product_name, market_category_id, market_category_name,
                        status, current_price, stock_quantity,
                        raw_data, is_active, last_synced_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (market_id, market_product_id) DO UPDATE SET
                        market_product_name = EXCLUDED.market_product_name,
                        market_category_name = EXCLUDED.market_category_name,
                        status = EXCLUDED.status,
                        current_price = EXCLUDED.current_price,
                        stock_quantity = EXCLUDED.stock_quantity,
                        raw_data = EXCLUDED.raw_data,
                        is_active = EXCLUDED.is_active,
                        last_synced_at = EXCLUDED.last_synced_at
                    RETURNING id
                """, (
                    unified_product_id,
                    self.coupang_market_id,
                    account['id'],
                    str(product_data.get('productId')),
                    product_data.get('productCode'),
                    product_data.get('productName'),
                    str(product_data.get('categoryId')) if product_data.get('categoryId') else None,
                    product_data.get('categoryName'),
                    product_data.get('productStatus'),
                    product_data.get('salePrice'),
                    product_data.get('stockQuantity', 0),
                    Json(product_data),
                    product_data.get('productStatus') == 'ACTIVE',
                    datetime.now()
                ))
                
                market_product_id = cursor.fetchone()[0]
                
                # 3. 가격 이력 저장
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
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"저장 오류: {e}")
            return False
    
    def collect_account_products(self, account):
        """특정 계정의 모든 상품 수집"""
        print(f"\n{'='*60}")
        print(f"계정: {account['alias']} (Vendor ID: {account['vendor_id']}) 상품 수집")
        print(f"{'='*60}")
        
        auth = CoupangAuth(
            access_key=account['access_key'],
            secret_key=account['secret_key'],
            vendor_id=account['vendor_id']
        )
        
        # 체크포인트 확인
        checkpoint = self.load_checkpoint()
        account_checkpoint = checkpoint.get(str(account['id']), {})
        
        if account_checkpoint:
            print(f"이전 진행 상태 발견: {account_checkpoint['total_count']}개 완료")
            next_token = account_checkpoint['next_token']
            total_count = account_checkpoint['total_count']
            print("이어서 수집을 시작합니다...")
        else:
            next_token = "1"
            total_count = 0
        
        success_count = 0
        page = total_count // 50 + 1
        
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
        
        start_time = time.time()
        
        while next_token:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 페이지 {page} 처리 중... (현재 속도: {self.request_delay:.1f}초/요청)")
            
            response = self.fetch_products(auth, account['vendor_id'], next_token)
            
            if not response:
                print("API 응답 실패. 수집 중단.")
                # 체크포인트 저장
                self.save_checkpoint(account['id'], next_token, total_count)
                break
            
            if response.get('code') != 'SUCCESS':
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
            
            # 주기적으로 체크포인트 저장 (100개마다)
            if total_count % 100 == 0:
                self.save_checkpoint(account['id'], next_token, total_count)
            
            # 진행률 표시
            elapsed = time.time() - start_time
            rate = total_count / elapsed if elapsed > 0 else 0
            print(f"  진행률: {total_count}개 완료 (속도: {rate:.1f}개/초)")
        
        # 완료시 체크포인트 삭제
        if not next_token:
            self.clear_checkpoint(account['id'])
            print(f"\n{account['alias']} 수집 완료!")
        
        # 동기화 로그 업데이트
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sync_logs 
                SET sync_status = %s, completed_at = %s, 
                    total_records = %s, success_records = %s
                WHERE id = %s
            """, (
                'completed' if not next_token else 'interrupted',
                datetime.now(),
                total_count,
                success_count,
                sync_log_id
            ))
            self.conn.commit()
        
        print(f"{account['alias']} 결과: 총 {total_count}개 중 {success_count}개 성공")
        return total_count, success_count
    
    def collect_all(self):
        """모든 계정의 상품 수집"""
        print(f"🚀 쿠팡 상품 수집 시작 (안전 모드)")
        print(f"시작 시간: {datetime.now()}")
        
        accounts = self.get_coupang_accounts()
        print(f"\n수집할 계정 수: {len(accounts)}개")
        
        total_products = 0
        total_success = 0
        
        for account in accounts:
            try:
                count, success = self.collect_account_products(account)
                total_products += count
                total_success += success
            except Exception as e:
                print(f"\n{account['alias']} 수집 중 오류 발생: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ 전체 수집 완료")
        print(f"총 처리: {total_products}개")
        print(f"성공: {total_success}개")
        print(f"완료 시간: {datetime.now()}")
    
    def show_summary(self):
        """수집 결과 요약"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.alias,
                    COUNT(mp.id) as total,
                    COUNT(CASE WHEN mp.current_price IS NOT NULL THEN 1 END) as with_price,
                    MIN(mp.current_price) as min_price,
                    MAX(mp.current_price) as max_price,
                    AVG(mp.current_price)::INTEGER as avg_price,
                    MAX(mp.last_synced_at) as last_sync
                FROM coupang c
                LEFT JOIN market_products mp ON c.id = mp.market_account_id
                WHERE mp.market_id = %s
                GROUP BY c.id, c.alias
                ORDER BY c.id
            """, (self.coupang_market_id,))
            
            print("\n=== 수집 결과 요약 ===")
            for row in cursor.fetchall():
                print(f"\n{row[0]}:")
                print(f"  - 총 상품 수: {row[1]:,}개")
                print(f"  - 가격 정보 있음: {row[2]:,}개")
                if row[3]:
                    print(f"  - 가격 범위: {row[3]:,.0f}원 ~ {row[4]:,.0f}원")
                    print(f"  - 평균 가격: {row[5]:,}원")
                print(f"  - 마지막 동기화: {row[6]}")


if __name__ == "__main__":
    collector = SafeCoupangProductCollector()
    try:
        collector.collect_all()
        collector.show_summary()
    finally:
        collector.conn.close()