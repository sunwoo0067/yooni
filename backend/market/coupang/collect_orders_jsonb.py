#!/usr/bin/env python3
"""
쿠팡 판매내역(주문) 수집 - JSONB 저장 버전
모든 계정의 주문을 수집하여 원본 데이터를 JSONB로 저장
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

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from auth.coupang_auth import CoupangAuth


class CoupangOrderCollectorJsonb:
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
                raise Exception("쿠팡 마켓이 등록되지 않았습니다.")
                
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
    
    def fetch_orders(self, auth, vendor_id, start_date, end_date, next_token=None, status=None):
        """쿠팡 API에서 주문 목록 조회"""
        method = "GET"
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets"
        
        query_params = {
            "createdAtFrom": start_date.strftime("%Y-%m-%d"),
            "createdAtTo": end_date.strftime("%Y-%m-%d"),
            "maxPerPage": "50"
        }
        
        if next_token:
            query_params["nextToken"] = next_token
            
        if status:
            query_params["status"] = status
        
        headers = auth.generate_authorization_header(method, path, query_params)
        headers["X-EXTENDED-Timeout"] = "90000"
        
        query_string = urllib.parse.urlencode(query_params)
        url = f"https://api-gateway.coupang.com{path}?{query_string}"
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"API 오류 {e.code}: {error_body}")
            return None
    
    def save_order(self, account, order_data):
        """주문 정보를 JSONB로 저장"""
        try:
            with self.conn.cursor() as cursor:
                # 주문 날짜와 상태 추출
                order_date = order_data.get('paidAt') or order_data.get('orderedAt')
                if order_date:
                    order_date = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                
                order_status = order_data.get('orderStatus', '')
                
                cursor.execute("""
                    INSERT INTO market_raw_orders (
                        market_id, market_account_id, market_order_id, 
                        order_date, order_status, raw_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (market_id, market_account_id, market_order_id)
                    DO UPDATE SET
                        order_date = EXCLUDED.order_date,
                        order_status = EXCLUDED.order_status,
                        raw_data = EXCLUDED.raw_data,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    self.coupang_market_id,
                    account['id'],
                    str(order_data.get('orderId')),
                    order_date,
                    order_status,
                    Json(order_data)
                ))
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"저장 오류: {e}")
            return False
    
    def collect_account_orders(self, account, days_back=30):
        """특정 계정의 주문 수집"""
        print(f"\n{'='*60}")
        print(f"계정: {account['alias']} (Vendor ID: {account['vendor_id']}) 주문 수집 시작")
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
                'order',
                'started',
                datetime.now()
            ))
            sync_log_id = cursor.fetchone()[0]
            self.conn.commit()
        
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 주문 상태별로 수집 (쿠팡 API는 상태별로 조회해야 함)
        order_statuses = [
            'ACCEPT',           # 결제완료
            'INSTRUCT',         # 상품준비중
            'DEPARTURE',        # 배송지시
            'DELIVERING',       # 배송중
            'FINAL_DELIVERY',   # 배송완료
            'NONE_TRACKING'     # 업체직송
        ]
        
        total_count = 0
        success_count = 0
        
        for status in order_statuses:
            print(f"\n'{status}' 상태 주문 수집 중...")
            
            next_token = "1"
            status_count = 0
            
            while next_token:
                response = self.fetch_orders(auth, account['vendor_id'], 
                                           start_date, end_date, next_token, status)
                
                if not response:
                    break
                    
                if response.get('code') == 'ERROR':
                    print(f"  API 에러: {response.get('message')}")
                    break
                
                # 주문 데이터 처리
                orders = response.get('data', [])
                
                for order in orders:
                    total_count += 1
                    status_count += 1
                    
                    if self.save_order(account, order):
                        success_count += 1
                        
                    if total_count % 10 == 0:
                        print(f"  처리 중: 총 {total_count}개 (현재 상태 {status_count}개)...")
                
                # 다음 페이지 토큰
                next_token = response.get('nextToken')
                
                # API 제한 고려
                time.sleep(0.2)
            
            print(f"  '{status}' 완료: {status_count}개")
        
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
        
        print(f"\n✅ {account['alias']} 계정 주문 수집 완료")
        print(f"   총 주문: {total_count}개")
        print(f"   성공: {success_count}개")
        print(f"   실패: {total_count - success_count}개")
        
        return success_count
    
    def run(self, days_back=30):
        """모든 계정의 주문 수집 실행"""
        print("🚀 쿠팡 주문 수집 시작 (JSONB 저장)")
        print(f"시작 시간: {datetime.now()}")
        print(f"수집 기간: 최근 {days_back}일")
        
        accounts = self.get_coupang_accounts()
        print(f"\n수집할 계정 수: {len(accounts)}개")
        
        total_orders = 0
        
        for account in accounts:
            try:
                count = self.collect_account_orders(account, days_back)
                total_orders += count
            except Exception as e:
                print(f"❌ {account['alias']} 계정 처리 중 오류: {e}")
        
        print(f"\n{'='*60}")
        print(f"🎉 전체 수집 완료!")
        print(f"   총 수집 주문: {total_orders}개")
        print(f"   완료 시간: {datetime.now()}")
        print(f"{'='*60}")
        
        # 수집 결과 요약 출력
        with self.conn.cursor() as cursor:
            # 계정별 주문 현황
            cursor.execute("""
                SELECT 
                    c.alias,
                    COUNT(DISTINCT mro.market_order_id) as order_count,
                    MIN(mro.order_date) as first_order,
                    MAX(mro.order_date) as last_order,
                    MAX(mro.collected_at) as last_collected
                FROM coupang c
                JOIN market_raw_orders mro ON c.id = mro.market_account_id
                WHERE mro.market_id = %s
                GROUP BY c.id, c.alias
                ORDER BY c.id
            """, (self.coupang_market_id,))
            
            print("\n📊 계정별 주문 현황:")
            print(f"{'계정명':<15} {'주문수':<10} {'첫주문':<12} {'최근주문':<12} {'수집시간':<20}")
            print("-" * 70)
            
            for row in cursor.fetchall():
                first_order = row[2].strftime('%Y-%m-%d') if row[2] else 'N/A'
                last_order = row[3].strftime('%Y-%m-%d') if row[3] else 'N/A'
                collected = row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else 'N/A'
                print(f"{row[0]:<15} {row[1]:<10} {first_order:<12} {last_order:<12} {collected:<20}")
            
            # 주문 상태별 통계
            cursor.execute("""
                SELECT 
                    order_status,
                    COUNT(*) as count
                FROM market_raw_orders
                WHERE market_id = %s
                GROUP BY order_status
                ORDER BY count DESC
            """, (self.coupang_market_id,))
            
            print("\n📊 주문 상태별 현황:")
            print(f"{'상태':<20} {'개수':<10}")
            print("-" * 30)
            
            for row in cursor.fetchall():
                print(f"{row[0] or 'N/A':<20} {row[1]:<10}")
            
            # 일별 주문 통계
            cursor.execute("""
                SELECT 
                    DATE(order_date) as order_day,
                    COUNT(*) as order_count,
                    COUNT(DISTINCT market_account_id) as account_count
                FROM market_raw_orders
                WHERE market_id = %s 
                  AND order_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(order_date)
                ORDER BY order_day DESC
            """, (self.coupang_market_id,))
            
            print("\n📊 최근 7일 일별 주문:")
            print(f"{'날짜':<12} {'주문수':<10} {'계정수':<10}")
            print("-" * 35)
            
            for row in cursor.fetchall():
                print(f"{row[0].strftime('%Y-%m-%d'):<12} {row[1]:<10} {row[2]:<10}")
        
        self.conn.close()


if __name__ == "__main__":
    # 기본값: 최근 30일 수집
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            print("사용법: python collect_orders_jsonb.py [수집일수]")
            sys.exit(1)
    
    collector = CoupangOrderCollectorJsonb()
    collector.run(days)