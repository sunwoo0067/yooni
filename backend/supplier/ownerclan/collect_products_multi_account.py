#!/usr/bin/env python3
"""
오너클랜 멀티 계정 대량 상품 수집 스크립트
2개 계정을 활용하여 700만개 상품을 효율적으로 수집
"""

import os
import sys
import json
import requests
import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_batch
from datetime import datetime, timedelta
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from queue import Queue
import hashlib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ownerclan_multi_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OwnerClanMultiAccountCollector:
    def __init__(self, accounts_file='accounts.json'):
        self.api_url = "https://api.ownerclan.com/v1/graphql"
        self.auth_url = "https://auth.ownerclan.com/auth"
        
        # 계정 정보 로드
        self.accounts = self.load_accounts(accounts_file)
        self.account_tokens = {}  # 계정별 토큰 저장
        self.account_expires = {}  # 계정별 토큰 만료 시간
        
        # 데이터베이스 연결 풀
        self.conn_pool = []
        self.max_connections = 20
        
        # 작업 큐 (계정별로 분산)
        self.work_queue = Queue()
        
        # 수집 통계
        self.stats = {
            'total_products': 0,
            'new_products': 0,
            'updated_products': 0,
            'failed_products': 0,
            'start_time': datetime.now(),
            'account_stats': {}  # 계정별 통계
        }
        
        # 계정별 통계 초기화
        for account in self.accounts:
            self.stats['account_stats'][account['name']] = {
                'collected': 0,
                'new': 0,
                'updated': 0,
                'failed': 0
            }
        
        # 체크포인트 파일
        self.checkpoint_file = 'ownerclan_multi_checkpoint.json'
        self.checkpoint = self.load_checkpoint()
        
        # 스레드 안전을 위한 락
        self.stats_lock = threading.Lock()
        self.db_lock = threading.Lock()
        
    def load_accounts(self, accounts_file):
        """계정 정보 로드 - DB 우선, 파일은 fallback"""
        try:
            # 먼저 데이터베이스에서 로드 시도
            accounts = self.load_accounts_from_db()
            if accounts:
                logger.info(f"데이터베이스에서 {len(accounts)}개의 계정 로드")
                return accounts
        except Exception as e:
            logger.warning(f"DB에서 계정 로드 실패: {str(e)}")
            
        # DB에서 못 가져왔으면 파일에서 로드
        accounts_path = os.path.join(os.path.dirname(__file__), accounts_file)
        if os.path.exists(accounts_path):
            with open(accounts_path, 'r') as f:
                accounts = json.load(f)
                
            active_accounts = [acc for acc in accounts if acc.get('is_active', True)]
            logger.info(f"파일에서 {len(active_accounts)}개의 활성 계정 로드")
            return active_accounts
            
        raise Exception("계정 정보를 찾을 수 없습니다 (DB 및 파일 모두 실패)")
        
    def load_accounts_from_db(self):
        """데이터베이스에서 계정 정보 로드"""
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sc.api_key,
                        sc.api_secret,
                        s.name || '_' || sc.id as name,
                        sc.collection_enabled,
                        sc.api_endpoint
                    FROM supplier_configs sc
                    JOIN suppliers s ON sc.supplier_id = s.id
                    WHERE s.name = '오너클랜'
                    AND sc.api_key IS NOT NULL
                    AND sc.api_secret IS NOT NULL
                    AND sc.collection_enabled = true
                """)
                
                accounts = []
                for row in cursor.fetchall():
                    accounts.append({
                        'name': row['name'],
                        'api_key': row['api_key'],
                        'api_secret': row['api_secret'],
                        'is_active': True,
                        'api_endpoint': row.get('api_endpoint', self.api_url)
                    })
                    
                return accounts
                
        finally:
            conn.close()
            
    def load_checkpoint(self):
        """체크포인트 로드"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            'last_offset': 0,
            'total_collected': 0,
            'account_offsets': {}  # 계정별 offset
        }
        
    def save_checkpoint(self):
        """체크포인트 저장"""
        with self.stats_lock:
            checkpoint = {
                'last_offset': self.checkpoint['last_offset'],
                'total_collected': self.stats['total_products'],
                'account_offsets': self.checkpoint.get('account_offsets', {}),
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
            
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
    def get_db_connection(self):
        """데이터베이스 연결 가져오기"""
        with self.db_lock:
            if self.conn_pool:
                return self.conn_pool.pop()
        
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        return conn
        
    def return_db_connection(self, conn):
        """데이터베이스 연결 반환"""
        with self.db_lock:
            if len(self.conn_pool) < self.max_connections:
                self.conn_pool.append(conn)
            else:
                conn.close()
                
    def authenticate_account(self, account):
        """특정 계정 인증"""
        try:
            account_name = account['name']
            
            # 토큰이 아직 유효한지 확인
            if (account_name in self.account_tokens and 
                account_name in self.account_expires and 
                datetime.now() < self.account_expires[account_name]):
                return True
                
            # JWT 토큰 요청
            auth_data = {
                'username': account['api_key'],
                'password': account['api_secret']
            }
            
            response = requests.post(self.auth_url, json=auth_data)
            
            if response.status_code != 200:
                logger.error(f"{account_name} 인증 실패: {response.status_code}")
                return False
                
            token_data = response.json()
            token = token_data.get('token')
            
            if not token:
                logger.error(f"{account_name} 토큰을 받지 못했습니다")
                return False
                
            # 토큰 저장
            self.account_tokens[account_name] = token
            self.account_expires[account_name] = datetime.now() + timedelta(hours=1)
            
            logger.info(f"{account_name} 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"{account['name']} 인증 오류: {str(e)}")
            return False
            
    def authenticate_all_accounts(self):
        """모든 계정 인증"""
        success_count = 0
        
        for account in self.accounts:
            if self.authenticate_account(account):
                success_count += 1
            else:
                logger.warning(f"{account['name']} 인증 실패 - 이 계정은 사용하지 않습니다")
                
        if success_count == 0:
            raise Exception("사용 가능한 계정이 없습니다")
            
        logger.info(f"{success_count}개 계정 인증 완료")
        return success_count
        
    def get_headers_for_account(self, account_name):
        """특정 계정의 헤더 생성"""
        if account_name not in self.account_tokens:
            # 재인증 시도
            account = next((acc for acc in self.accounts if acc['name'] == account_name), None)
            if account and not self.authenticate_account(account):
                raise Exception(f"{account_name} 재인증 실패")
                
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.account_tokens[account_name]}'
        }
        
    def get_products_query(self, limit=1000, offset=0):
        """상품 목록 조회 GraphQL 쿼리"""
        return """
        query GetProducts($limit: Int!, $offset: Int!) {
            products(limit: $limit, offset: $offset) {
                totalCount
                items {
                    id
                    name
                    code
                    barcode
                    brandName
                    manufacturerName
                    originCountry
                    stock
                    price
                    costPrice
                    weight
                    status
                    createdAt
                    updatedAt
                    category {
                        id
                        name
                        fullPath
                    }
                    options {
                        id
                        name
                        values
                    }
                    images {
                        url
                        isMain
                    }
                }
            }
        }
        """
        
    def collect_batch_for_account(self, account, offset, limit):
        """특정 계정으로 배치 수집"""
        try:
            account_name = account['name']
            
            # GraphQL 요청
            response = requests.post(
                self.api_url,
                headers=self.get_headers_for_account(account_name),
                json={
                    'query': self.get_products_query(limit, offset),
                    'variables': {
                        'limit': limit,
                        'offset': offset
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"{account_name} API 요청 실패 (offset: {offset}): {response.status_code}")
                return None
                
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"{account_name} GraphQL 에러 (offset: {offset}): {data['errors']}")
                return None
                
            batch_data = data.get('data', {}).get('products', {})
            
            # 계정 정보 추가
            if batch_data:
                batch_data['account_name'] = account_name
                
            return batch_data
            
        except Exception as e:
            logger.error(f"{account['name']} 배치 수집 오류 (offset: {offset}): {str(e)}")
            return None
            
    def save_products_batch(self, products, account_name):
        """상품 배치 저장"""
        if not products:
            return {'new': 0, 'updated': 0, 'failed': 0}
            
        conn = self.get_db_connection()
        stats = {'new': 0, 'updated': 0, 'failed': 0}
        
        try:
            with conn.cursor() as cursor:
                # 기존 상품 키 조회
                product_keys = [f"W{p['id']}" for p in products]
                cursor.execute("""
                    SELECT product_key FROM products 
                    WHERE product_key = ANY(%s)
                """, (product_keys,))
                
                existing_keys = {row[0] for row in cursor.fetchall()}
                
                # 신규/업데이트 분리
                new_products = []
                update_products = []
                
                for product in products:
                    product_key = f"W{product['id']}"
                    
                    # 수집 계정 정보 추가
                    product['collected_by'] = account_name
                    
                    # 데이터 준비
                    product_data = {
                        'product_key': product_key,
                        'name': product['name'],
                        'brand': product.get('brandName'),
                        'price': product.get('price', 0),
                        'base_price': product.get('price', 0),
                        'cost_price': product.get('costPrice', 0),
                        'stock_quantity': product.get('stock', 0),
                        'stock_status': 'in_stock' if product.get('stock', 0) > 0 else 'out_of_stock',
                        'status': 'active' if product.get('status') == 'ACTIVE' else 'inactive',
                        'weight_kg': product.get('weight', 0) / 1000.0 if product.get('weight') else 0,
                        'barcode': product.get('barcode'),
                        'manufacturer': product.get('manufacturerName'),
                        'metadata': Json(product),
                        'updated_at': datetime.now(),
                        'last_stock_check': datetime.now()
                    }
                    
                    if product_key in existing_keys:
                        update_products.append(product_data)
                    else:
                        product_data['created_at'] = datetime.now()
                        product_data['stock_sync_enabled'] = True
                        new_products.append(product_data)
                
                # 배치 삽입
                if new_products:
                    execute_batch(cursor, """
                        INSERT INTO products (
                            product_key, name, brand, price, base_price, cost_price,
                            stock_quantity, stock_status, status, weight_kg, barcode,
                            manufacturer, metadata, created_at, updated_at,
                            last_stock_check, stock_sync_enabled
                        ) VALUES (
                            %(product_key)s, %(name)s, %(brand)s, %(price)s, %(base_price)s,
                            %(cost_price)s, %(stock_quantity)s, %(stock_status)s, %(status)s,
                            %(weight_kg)s, %(barcode)s, %(manufacturer)s, %(metadata)s,
                            %(created_at)s, %(updated_at)s, %(last_stock_check)s,
                            %(stock_sync_enabled)s
                        )
                    """, new_products, page_size=500)
                    stats['new'] = len(new_products)
                
                # 배치 업데이트
                if update_products:
                    execute_batch(cursor, """
                        UPDATE products SET
                            name = %(name)s,
                            brand = %(brand)s,
                            price = %(price)s,
                            base_price = %(base_price)s,
                            cost_price = %(cost_price)s,
                            stock_quantity = %(stock_quantity)s,
                            stock_status = %(stock_status)s,
                            status = %(status)s,
                            weight_kg = %(weight_kg)s,
                            barcode = %(barcode)s,
                            manufacturer = %(manufacturer)s,
                            metadata = %(metadata)s,
                            updated_at = %(updated_at)s,
                            last_stock_check = %(last_stock_check)s
                        WHERE product_key = %(product_key)s
                    """, update_products, page_size=500)
                    stats['updated'] = len(update_products)
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"배치 저장 오류: {str(e)}")
            stats['failed'] = len(products)
        finally:
            self.return_db_connection(conn)
            
        return stats
        
    def worker_thread(self, worker_id, account):
        """워커 스레드 - 특정 계정으로 작업 처리"""
        account_name = account['name']
        logger.info(f"워커 {worker_id} 시작 ({account_name})")
        
        while True:
            try:
                # 작업 큐에서 가져오기
                work_item = self.work_queue.get(timeout=5)
                if work_item is None:  # 종료 신호
                    break
                    
                offset, limit = work_item
                
                # 배치 수집
                batch_data = self.collect_batch_for_account(account, offset, limit)
                if not batch_data:
                    continue
                    
                items = batch_data.get('items', [])
                if not items:
                    continue
                    
                # 배치 저장
                stats = self.save_products_batch(items, account_name)
                
                # 통계 업데이트
                with self.stats_lock:
                    self.stats['total_products'] += len(items)
                    self.stats['new_products'] += stats['new']
                    self.stats['updated_products'] += stats['updated']
                    self.stats['failed_products'] += stats['failed']
                    
                    # 계정별 통계
                    acc_stats = self.stats['account_stats'][account_name]
                    acc_stats['collected'] += len(items)
                    acc_stats['new'] += stats['new']
                    acc_stats['updated'] += stats['updated']
                    acc_stats['failed'] += stats['failed']
                    
                logger.debug(f"워커 {worker_id} 완료: offset {offset}, {len(items)}개 처리")
                
            except Exception as e:
                logger.error(f"워커 {worker_id} 오류: {str(e)}")
            finally:
                self.work_queue.task_done()
                
    def collect_all_products(self, batch_size=1000, workers_per_account=3):
        """전체 상품 수집 (멀티 계정 병렬 처리)"""
        try:
            # 모든 계정 인증
            active_accounts = self.authenticate_all_accounts()
            
            logger.info(f"오너클랜 멀티 계정 수집 시작")
            logger.info(f"- 활성 계정: {active_accounts}개")
            logger.info(f"- 배치 크기: {batch_size}")
            logger.info(f"- 계정당 워커: {workers_per_account}")
            
            # 첫 번째 요청으로 전체 개수 확인
            first_account = self.accounts[0]
            initial_batch = self.collect_batch_for_account(first_account, 0, 1)
            if not initial_batch:
                logger.error("초기 요청 실패")
                return
                
            total_count = initial_batch.get('totalCount', 0)
            logger.info(f"전체 상품 수: {total_count:,}개")
            
            # 워커 스레드 시작
            threads = []
            for i, account in enumerate(self.accounts):
                for j in range(workers_per_account):
                    worker_id = f"{account['name']}_worker_{j}"
                    thread = threading.Thread(
                        target=self.worker_thread,
                        args=(worker_id, account)
                    )
                    thread.start()
                    threads.append(thread)
                    
            # 작업 분배
            offset = self.checkpoint.get('last_offset', 0)
            batch_count = 0
            
            while offset < total_count:
                # 계정 수 * 워커 수만큼 작업 생성
                for _ in range(len(self.accounts) * workers_per_account):
                    if offset < total_count:
                        self.work_queue.put((offset, batch_size))
                        offset += batch_size
                        batch_count += 1
                        
                # 주기적으로 체크포인트 저장 및 통계 출력
                if batch_count % 100 == 0:
                    self.checkpoint['last_offset'] = offset
                    self.save_checkpoint()
                    self.print_progress(total_count)
                    
                # 큐가 너무 커지지 않도록 대기
                while self.work_queue.qsize() > 100:
                    time.sleep(1)
                    
            # 모든 작업 완료 대기
            self.work_queue.join()
            
            # 워커 종료
            for _ in threads:
                self.work_queue.put(None)
                
            for thread in threads:
                thread.join()
                
            # 최종 통계
            self.print_final_stats()
            
            # 체크포인트 파일 삭제 (완료)
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                
        except Exception as e:
            logger.error(f"전체 수집 오류: {str(e)}")
        finally:
            # 연결 풀 정리
            for conn in self.conn_pool:
                conn.close()
                
    def print_progress(self, total_count):
        """진행 상황 출력"""
        with self.stats_lock:
            total_collected = self.stats['total_products']
            progress = (total_collected / total_count) * 100 if total_count > 0 else 0
            elapsed = datetime.now() - self.stats['start_time']
            rate = total_collected / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            eta = timedelta(seconds=(total_count - total_collected) / rate) if rate > 0 else timedelta(0)
            
            logger.info(f"""
========================================
진행 상황: {total_collected:,} / {total_count:,} ({progress:.2f}%)
----------------------------------------
전체 통계:
- 신규: {self.stats['new_products']:,}
- 업데이트: {self.stats['updated_products']:,}
- 실패: {self.stats['failed_products']:,}
- 속도: {rate:.2f} 상품/초
- 남은 시간: {eta}
----------------------------------------
계정별 통계:""")
            
            for account_name, acc_stats in self.stats['account_stats'].items():
                logger.info(f"  {account_name}: {acc_stats['collected']:,}개 (신규: {acc_stats['new']:,}, 업데이트: {acc_stats['updated']:,})")
                
            logger.info("========================================")
            
    def print_final_stats(self):
        """최종 통계 출력"""
        elapsed = datetime.now() - self.stats['start_time']
        
        logger.info(f"""
========================================
오너클랜 멀티 계정 수집 완료!
========================================
총 상품 수: {self.stats['total_products']:,}
신규 추가: {self.stats['new_products']:,}
업데이트: {self.stats['updated_products']:,}
실패: {self.stats['failed_products']:,}
소요 시간: {elapsed}
평균 속도: {self.stats['total_products'] / elapsed.total_seconds():.2f} 상품/초
----------------------------------------
계정별 성과:""")
        
        for account_name, acc_stats in self.stats['account_stats'].items():
            logger.info(f"""
{account_name}:
  - 수집: {acc_stats['collected']:,}개
  - 신규: {acc_stats['new']:,}개
  - 업데이트: {acc_stats['updated']:,}개
  - 실패: {acc_stats['failed']:,}개""")
            
        logger.info("========================================")

def main():
    parser = argparse.ArgumentParser(description='오너클랜 멀티 계정 대량 상품 수집')
    parser.add_argument('--batch-size', type=int, default=1000, help='배치 크기 (기본: 1000)')
    parser.add_argument('--workers', type=int, default=3, help='계정당 워커 수 (기본: 3)')
    parser.add_argument('--accounts', default='accounts.json', help='계정 파일 경로')
    parser.add_argument('--resume', action='store_true', help='체크포인트에서 재개')
    
    args = parser.parse_args()
    
    collector = OwnerClanMultiAccountCollector(accounts_file=args.accounts)
    collector.collect_all_products(
        batch_size=args.batch_size,
        workers_per_account=args.workers
    )

if __name__ == "__main__":
    main()