#!/usr/bin/env python3
"""
오너클랜 대량 상품 수집 스크립트
700만개 상품을 효율적으로 수집하기 위한 배치 처리
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
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ownerclan_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OwnerClanBatchCollector:
    def __init__(self):
        self.api_url = "https://api.ownerclan.com/v1/graphql"
        self.auth_url = "https://auth.ownerclan.com/auth"
        self.access_token = None
        self.token_expires = None
        
        # 데이터베이스 연결 풀
        self.conn_pool = []
        self.max_connections = 10
        
        # 수집 통계
        self.stats = {
            'total_products': 0,
            'new_products': 0,
            'updated_products': 0,
            'failed_products': 0,
            'start_time': datetime.now()
        }
        
        # 체크포인트 파일
        self.checkpoint_file = 'ownerclan_checkpoint.json'
        self.checkpoint = self.load_checkpoint()
        
    def load_checkpoint(self):
        """체크포인트 로드"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {'last_offset': 0, 'total_collected': 0}
        
    def save_checkpoint(self, offset, total):
        """체크포인트 저장"""
        self.checkpoint = {
            'last_offset': offset,
            'total_collected': total,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f)
            
    def get_db_connection(self):
        """데이터베이스 연결 가져오기"""
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
        if len(self.conn_pool) < self.max_connections:
            self.conn_pool.append(conn)
        else:
            conn.close()
            
    def authenticate(self):
        """오너클랜 API 인증 (토큰 갱신 포함)"""
        try:
            # 토큰이 아직 유효한지 확인
            if self.access_token and self.token_expires and datetime.now() < self.token_expires:
                return True
                
            conn = self.get_db_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT sc.api_key, sc.api_secret
                        FROM supplier_configs sc
                        JOIN suppliers s ON sc.supplier_id = s.id
                        WHERE s.name = '오너클랜'
                    """)
                    config = cursor.fetchone()
            finally:
                self.return_db_connection(conn)
                
            if not config or not config['api_key'] or not config['api_secret']:
                raise ValueError("오너클랜 인증 정보가 없습니다")
                
            # JWT 토큰 요청
            auth_data = {
                'username': config['api_key'],
                'password': config['api_secret']
            }
            
            response = requests.post(self.auth_url, json=auth_data)
            
            if response.status_code != 200:
                raise Exception(f"인증 실패: {response.status_code} - {response.text}")
                
            token_data = response.json()
            self.access_token = token_data.get('token')
            
            # 토큰 만료 시간 설정 (일반적으로 1시간)
            self.token_expires = datetime.now() + timedelta(hours=1)
            
            logger.info("오너클랜 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"인증 오류: {str(e)}")
            return False
            
    def get_headers(self):
        """API 요청 헤더 생성"""
        if not self.access_token or datetime.now() >= self.token_expires:
            self.authenticate()
            
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
    def get_products_query(self, limit=1000, offset=0):
        """상품 목록 조회 GraphQL 쿼리 (최적화)"""
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
        
    def collect_batch(self, offset, limit):
        """배치 단위로 상품 수집"""
        try:
            # GraphQL 요청
            response = requests.post(
                self.api_url,
                headers=self.get_headers(),
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
                logger.error(f"API 요청 실패 (offset: {offset}): {response.status_code}")
                return None
                
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL 에러 (offset: {offset}): {data['errors']}")
                return None
                
            return data.get('data', {}).get('products', {})
            
        except Exception as e:
            logger.error(f"배치 수집 오류 (offset: {offset}): {str(e)}")
            return None
            
    def save_products_batch(self, products):
        """상품 배치 저장 (최적화)"""
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
        
    def collect_all_products(self, batch_size=1000, max_workers=5):
        """전체 상품 수집 (병렬 처리)"""
        try:
            # 인증
            if not self.authenticate():
                logger.error("인증 실패")
                return
                
            logger.info(f"오너클랜 대량 수집 시작 (배치 크기: {batch_size}, 워커: {max_workers})")
            
            # 시작 offset (체크포인트에서 재개)
            offset = self.checkpoint['last_offset']
            total_collected = self.checkpoint['total_collected']
            
            # 첫 번째 요청으로 전체 개수 확인
            initial_batch = self.collect_batch(0, 1)
            if not initial_batch:
                logger.error("초기 요청 실패")
                return
                
            total_count = initial_batch.get('totalCount', 0)
            logger.info(f"전체 상품 수: {total_count:,}개")
            
            # 병렬 처리를 위한 스레드 풀
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                while offset < total_count:
                    # 배치 작업 제출
                    for i in range(max_workers):
                        if offset + i * batch_size < total_count:
                            future = executor.submit(
                                self.process_batch,
                                offset + i * batch_size,
                                batch_size
                            )
                            futures.append(future)
                    
                    # 결과 수집
                    for future in as_completed(futures):
                        batch_stats = future.result()
                        if batch_stats:
                            self.stats['new_products'] += batch_stats['new']
                            self.stats['updated_products'] += batch_stats['updated']
                            self.stats['failed_products'] += batch_stats['failed']
                            total_collected += batch_stats['total']
                    
                    futures.clear()
                    
                    # 진행 상황 업데이트
                    offset += max_workers * batch_size
                    self.stats['total_products'] = total_collected
                    
                    # 체크포인트 저장
                    self.save_checkpoint(offset, total_collected)
                    
                    # 진행률 표시
                    progress = (total_collected / total_count) * 100
                    elapsed = datetime.now() - self.stats['start_time']
                    rate = total_collected / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                    eta = timedelta(seconds=(total_count - total_collected) / rate) if rate > 0 else timedelta(0)
                    
                    logger.info(f"""
진행 상황: {total_collected:,} / {total_count:,} ({progress:.2f}%)
- 신규: {self.stats['new_products']:,}
- 업데이트: {self.stats['updated_products']:,}
- 실패: {self.stats['failed_products']:,}
- 속도: {rate:.2f} 상품/초
- 남은 시간: {eta}
                    """)
                    
                    # API 부하 방지
                    time.sleep(0.1)
            
            # 최종 통계
            elapsed = datetime.now() - self.stats['start_time']
            logger.info(f"""
========================================
오너클랜 상품 수집 완료!
========================================
총 상품 수: {self.stats['total_products']:,}
신규 추가: {self.stats['new_products']:,}
업데이트: {self.stats['updated_products']:,}
실패: {self.stats['failed_products']:,}
소요 시간: {elapsed}
평균 속도: {self.stats['total_products'] / elapsed.total_seconds():.2f} 상품/초
========================================
            """)
            
            # 체크포인트 파일 삭제 (완료)
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                
        except Exception as e:
            logger.error(f"전체 수집 오류: {str(e)}")
        finally:
            # 연결 풀 정리
            for conn in self.conn_pool:
                conn.close()
                
    def process_batch(self, offset, limit):
        """단일 배치 처리"""
        try:
            # 배치 수집
            batch_data = self.collect_batch(offset, limit)
            if not batch_data:
                return None
                
            items = batch_data.get('items', [])
            if not items:
                return None
                
            # 배치 저장
            stats = self.save_products_batch(items)
            stats['total'] = len(items)
            
            return stats
            
        except Exception as e:
            logger.error(f"배치 처리 오류 (offset: {offset}): {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description='오너클랜 대량 상품 수집')
    parser.add_argument('--batch-size', type=int, default=1000, help='배치 크기 (기본: 1000)')
    parser.add_argument('--workers', type=int, default=5, help='병렬 워커 수 (기본: 5)')
    parser.add_argument('--resume', action='store_true', help='체크포인트에서 재개')
    
    args = parser.parse_args()
    
    collector = OwnerClanBatchCollector()
    collector.collect_all_products(
        batch_size=args.batch_size,
        max_workers=args.workers
    )

if __name__ == "__main__":
    main()