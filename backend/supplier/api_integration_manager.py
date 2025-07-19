#!/usr/bin/env python3
"""
실제 API 연동 통합 매니저
- 오너클랜, 젠트레이드 등 실제 API 연동
- 토큰 관리, 율 제한, 오류 처리
- 데이터 검증 및 변환
"""

import os
import sys
import json
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Any, Optional
import hashlib
import hmac
import base64
from dataclasses import dataclass
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class APICredentials:
    """API 인증 정보"""
    api_key: str
    api_secret: str
    api_endpoint: str
    api_type: str  # 'graphql', 'rest'
    vendor_id: Optional[str] = None

@dataclass
class CollectionResult:
    """수집 결과"""
    success: bool
    total_products: int
    new_products: int
    updated_products: int
    failed_products: int
    errors: List[str]
    duration_seconds: float

class RateLimiter:
    """API 요청 율 제한기"""
    
    def __init__(self, max_requests_per_second: float = 5.0):
        self.max_requests = max_requests_per_second
        self.requests = []
        
    async def wait_if_needed(self):
        """필요시 대기"""
        now = time.time()
        
        # 1초 이내 요청들만 유지
        self.requests = [req_time for req_time in self.requests if now - req_time < 1.0]
        
        if len(self.requests) >= self.max_requests:
            # 가장 오래된 요청이 1초가 지날 때까지 대기
            wait_time = 1.0 - (now - self.requests[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
        self.requests.append(now)

class APIIntegrationManager:
    """API 연동 통합 매니저"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        self.rate_limiters = {}
        
    def get_supplier_credentials(self, supplier_name: str) -> Optional[APICredentials]:
        """공급사 인증 정보 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT sc.api_type, sc.api_endpoint, sc.api_key, 
                           sc.api_secret, sc.settings
                    FROM supplier_configs sc
                    JOIN suppliers s ON sc.supplier_id = s.id
                    WHERE s.name = %s AND sc.collection_enabled = true
                """, (supplier_name,))
                
                config = cursor.fetchone()
                if not config:
                    logger.error(f"활성 설정을 찾을 수 없습니다: {supplier_name}")
                    return None
                    
                settings = config.get('settings', {}) or {}
                rate_limit = float(settings.get('rate_limit_per_second', 5.0))
                
                # 율 제한기 설정
                if supplier_name not in self.rate_limiters:
                    self.rate_limiters[supplier_name] = RateLimiter(rate_limit)
                
                return APICredentials(
                    api_key=config['api_key'],
                    api_secret=config['api_secret'],
                    api_endpoint=config['api_endpoint'],
                    api_type=config['api_type'],
                    vendor_id=settings.get('vendor_id')
                )
                
        except Exception as e:
            logger.error(f"인증 정보 조회 실패 ({supplier_name}): {e}")
            return None
    
    async def collect_ownerclan_products(self, credentials: APICredentials) -> CollectionResult:
        """오너클랜 상품 수집"""
        start_time = time.time()
        result = CollectionResult(
            success=False, total_products=0, new_products=0, 
            updated_products=0, failed_products=0, errors=[], duration_seconds=0
        )
        
        try:
            logger.info("🏪 오너클랜 실제 API 연동 시작")
            
            # 1. 인증 토큰 획득
            auth_token = await self._authenticate_ownerclan(credentials)
            if not auth_token:
                result.errors.append("인증 실패")
                return result
            
            # 2. 상품 목록 조회 (페이지네이션)
            total_collected = 0
            page_offset = 0
            page_limit = 100
            
            while True:
                await self.rate_limiters['오너클랜'].wait_if_needed()
                
                products_data = await self._fetch_ownerclan_products(
                    credentials, auth_token, page_limit, page_offset
                )
                
                if not products_data or not products_data.get('items'):
                    break
                    
                # 3. 상품 데이터 저장
                items = products_data['items']
                total_count = products_data.get('totalCount', 0)
                
                logger.info(f"📦 페이지 처리: {page_offset + 1}-{page_offset + len(items)} / {total_count}")
                
                for product in items:
                    try:
                        save_result = self._save_product('오너클랜', product)
                        if save_result == 'new':
                            result.new_products += 1
                        elif save_result == 'updated':
                            result.updated_products += 1
                        total_collected += 1
                    except Exception as e:
                        logger.error(f"상품 저장 실패: {e}")
                        result.failed_products += 1
                        result.errors.append(f"상품 저장 실패: {product.get('id', 'unknown')}")
                
                page_offset += page_limit
                
                # 모든 상품 수집 완료
                if page_offset >= total_count:
                    break
                    
                # API 부하 방지
                await asyncio.sleep(0.2)
            
            result.total_products = total_collected
            result.success = True
            self.conn.commit()
            
            logger.info(f"✅ 오너클랜 수집 완료: {total_collected}개 상품")
            
        except Exception as e:
            logger.error(f"❌ 오너클랜 수집 실패: {e}")
            result.errors.append(str(e))
            self.conn.rollback()
            
        finally:
            result.duration_seconds = time.time() - start_time
            
        return result
    
    async def _authenticate_ownerclan(self, credentials: APICredentials) -> Optional[str]:
        """오너클랜 인증"""
        try:
            auth_url = "https://auth.ownerclan.com/auth"
            
            auth_data = {
                'username': credentials.api_key,
                'password': credentials.api_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, json=auth_data) as response:
                    if response.status != 200:
                        logger.error(f"인증 실패: {response.status}")
                        return None
                        
                    data = await response.json()
                    token = data.get('token')
                    
                    if token:
                        logger.info("✅ 오너클랜 인증 성공")
                        return token
                    else:
                        logger.error("토큰을 받지 못했습니다")
                        return None
                        
        except Exception as e:
            logger.error(f"인증 오류: {e}")
            return None
    
    async def _fetch_ownerclan_products(self, credentials: APICredentials, 
                                      token: str, limit: int, offset: int) -> Optional[Dict]:
        """오너클랜 상품 목록 조회"""
        try:
            query = """
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
                        description
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
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            payload = {
                'query': query,
                'variables': {
                    'limit': limit,
                    'offset': offset
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(credentials.api_endpoint, 
                                      json=payload, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"API 요청 실패: {response.status}")
                        return None
                        
                    data = await response.json()
                    
                    if 'errors' in data:
                        logger.error(f"GraphQL 오류: {data['errors']}")
                        return None
                        
                    return data.get('data', {}).get('products', {})
                    
        except Exception as e:
            logger.error(f"상품 조회 오류: {e}")
            return None
    
    async def collect_zentrade_products(self, credentials: APICredentials) -> CollectionResult:
        """젠트레이드 상품 수집"""
        start_time = time.time()
        result = CollectionResult(
            success=False, total_products=0, new_products=0, 
            updated_products=0, failed_products=0, errors=[], duration_seconds=0
        )
        
        try:
            logger.info("🏪 젠트레이드 실제 API 연동 시작")
            
            # REST API 방식으로 수집
            page = 1
            per_page = 50
            total_collected = 0
            
            while True:
                await self.rate_limiters.get('젠트레이드', RateLimiter()).wait_if_needed()
                
                products_data = await self._fetch_zentrade_products(
                    credentials, page, per_page
                )
                
                if not products_data or not products_data.get('data'):
                    break
                    
                items = products_data['data']
                total_count = products_data.get('total', 0)
                
                logger.info(f"📦 젠트레이드 페이지 {page}: {len(items)}개 상품")
                
                for product in items:
                    try:
                        save_result = self._save_product('젠트레이드', product)
                        if save_result == 'new':
                            result.new_products += 1
                        elif save_result == 'updated':
                            result.updated_products += 1
                        total_collected += 1
                    except Exception as e:
                        logger.error(f"젠트레이드 상품 저장 실패: {e}")
                        result.failed_products += 1
                        result.errors.append(f"상품 저장 실패: {product.get('id', 'unknown')}")
                
                # 다음 페이지로
                if len(items) < per_page:
                    break
                    
                page += 1
                await asyncio.sleep(0.1)  # API 부하 방지
            
            result.total_products = total_collected
            result.success = True
            self.conn.commit()
            
            logger.info(f"✅ 젠트레이드 수집 완료: {total_collected}개 상품")
            
        except Exception as e:
            logger.error(f"❌ 젠트레이드 수집 실패: {e}")
            result.errors.append(str(e))
            self.conn.rollback()
            
        finally:
            result.duration_seconds = time.time() - start_time
            
        return result
    
    async def _fetch_zentrade_products(self, credentials: APICredentials, 
                                     page: int, per_page: int) -> Optional[Dict]:
        """젠트레이드 상품 목록 조회"""
        try:
            url = f"{credentials.api_endpoint}/products"
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': credentials.api_key,
                'X-API-Secret': credentials.api_secret
            }
            
            params = {
                'page': page,
                'per_page': per_page,
                'status': 'active'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"젠트레이드 API 요청 실패: {response.status}")
                        return None
                        
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"젠트레이드 조회 오류: {e}")
            return None
    
    def _save_product(self, supplier_name: str, product_data: Dict) -> str:
        """상품 데이터 저장"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 공급사 ID 조회
                cursor.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
                supplier = cursor.fetchone()
                
                if not supplier:
                    raise ValueError(f"공급사를 찾을 수 없습니다: {supplier_name}")
                    
                supplier_id = supplier['id']
                
                # 기존 상품 확인
                product_id = str(product_data.get('id', product_data.get('product_id', '')))
                cursor.execute("""
                    SELECT id FROM supplier_products 
                    WHERE supplier_id = %s AND supplier_product_id = %s
                """, (supplier_id, product_id))
                
                existing = cursor.fetchone()
                
                # 상품 데이터 변환
                product_record = {
                    'supplier_id': supplier_id,
                    'supplier_product_id': product_id,
                    'product_name': product_data.get('name', ''),
                    'product_code': product_data.get('code'),
                    'barcode': product_data.get('barcode'),
                    'brand': product_data.get('brandName', product_data.get('brand')),
                    'manufacturer': product_data.get('manufacturerName', product_data.get('manufacturer')),
                    'origin': product_data.get('originCountry', product_data.get('origin')),
                    'description': product_data.get('description'),
                    'category': self._extract_category(product_data),
                    'price': float(product_data.get('price', 0)),
                    'cost_price': float(product_data.get('costPrice', product_data.get('cost_price', 0))),
                    'stock_quantity': int(product_data.get('stock', product_data.get('stock_quantity', 0))),
                    'weight': float(product_data.get('weight', 0)),
                    'status': 'active' if product_data.get('status') == 'ACTIVE' else 'inactive',
                    'image_url': self._extract_main_image(product_data),
                    'raw_data': Json(product_data),
                    'collected_at': datetime.now()
                }
                
                if existing:
                    # 업데이트
                    update_fields = [f"{k} = %({k})s" for k in product_record.keys() if k != 'supplier_id']
                    update_query = f"""
                        UPDATE supplier_products SET
                            {', '.join(update_fields)},
                            updated_at = NOW()
                        WHERE id = %(existing_id)s
                    """
                    product_record['existing_id'] = existing['id']
                    cursor.execute(update_query, product_record)
                    return 'updated'
                else:
                    # 신규 생성
                    fields = list(product_record.keys())
                    placeholders = [f"%({field})s" for field in fields]
                    insert_query = f"""
                        INSERT INTO supplier_products ({', '.join(fields)}) 
                        VALUES ({', '.join(placeholders)})
                    """
                    cursor.execute(insert_query, product_record)
                    return 'new'
                    
        except Exception as e:
            logger.error(f"상품 저장 오류: {e}")
            raise
    
    def _extract_category(self, product_data: Dict) -> Optional[str]:
        """카테고리 정보 추출"""
        category = product_data.get('category', {})
        if isinstance(category, dict):
            return category.get('fullPath', category.get('name'))
        return str(category) if category else None
    
    def _extract_main_image(self, product_data: Dict) -> Optional[str]:
        """메인 이미지 URL 추출"""
        images = product_data.get('images', [])
        if images:
            # 메인 이미지 찾기
            main_image = next((img.get('url') for img in images if img.get('isMain')), None)
            return main_image or images[0].get('url')
        return None
    
    async def collect_all_suppliers(self) -> Dict[str, CollectionResult]:
        """모든 활성 공급사의 상품 수집"""
        results = {}
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT DISTINCT s.name 
                    FROM suppliers s
                    JOIN supplier_configs sc ON s.id = sc.supplier_id
                    WHERE sc.collection_enabled = true
                    ORDER BY s.name
                """)
                
                suppliers = [row['name'] for row in cursor.fetchall()]
                
            logger.info(f"🚀 활성 공급사 {len(suppliers)}개 수집 시작: {suppliers}")
            
            for supplier_name in suppliers:
                logger.info(f"📡 {supplier_name} 수집 중...")
                
                credentials = self.get_supplier_credentials(supplier_name)
                if not credentials:
                    results[supplier_name] = CollectionResult(
                        success=False, total_products=0, new_products=0,
                        updated_products=0, failed_products=0,
                        errors=[f"인증 정보 없음: {supplier_name}"], duration_seconds=0
                    )
                    continue
                
                # 공급사별 수집 메서드 호출
                if supplier_name == '오너클랜':
                    result = await self.collect_ownerclan_products(credentials)
                elif supplier_name == '젠트레이드':
                    result = await self.collect_zentrade_products(credentials)
                else:
                    result = CollectionResult(
                        success=False, total_products=0, new_products=0,
                        updated_products=0, failed_products=0,
                        errors=[f"지원되지 않는 공급사: {supplier_name}"], duration_seconds=0
                    )
                
                results[supplier_name] = result
                
                # 수집 로그 기록
                self._log_collection_result(supplier_name, result)
                
                # 공급사 간 간격
                await asyncio.sleep(1.0)
                
        except Exception as e:
            logger.error(f"전체 수집 오류: {e}")
            
        return results
    
    def _log_collection_result(self, supplier_name: str, result: CollectionResult):
        """수집 결과 로그 기록"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 공급사 ID 조회
                cursor.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
                supplier = cursor.fetchone()
                
                if not supplier:
                    return
                    
                cursor.execute("""
                    INSERT INTO supplier_collection_logs 
                    (supplier_id, collection_type, status, total_items, new_items, 
                     updated_items, failed_items, error_message, started_at, 
                     completed_at, duration_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    supplier['id'],
                    'products',
                    'success' if result.success else 'failed',
                    result.total_products,
                    result.new_products,
                    result.updated_products,
                    result.failed_products,
                    '; '.join(result.errors) if result.errors else None,
                    datetime.now() - timedelta(seconds=result.duration_seconds),
                    datetime.now(),
                    int(result.duration_seconds)
                ))
                
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"로그 기록 실패: {e}")
    
    def close(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()

async def main():
    """메인 실행 함수"""
    print("🚀 실제 API 연동 시스템 시작")
    print("=" * 60)
    
    manager = APIIntegrationManager()
    
    try:
        # 모든 공급사 수집
        results = await manager.collect_all_suppliers()
        
        # 결과 출력
        print("\n📊 수집 결과 요약:")
        total_products = 0
        total_new = 0
        total_updated = 0
        total_failed = 0
        
        for supplier_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"\n{status} {supplier_name}:")
            print(f"   📦 총 상품: {result.total_products}개")
            print(f"   🆕 신규: {result.new_products}개")
            print(f"   🔄 업데이트: {result.updated_products}개")
            print(f"   ❌ 실패: {result.failed_products}개")
            print(f"   ⏱️ 소요시간: {result.duration_seconds:.1f}초")
            
            if result.errors:
                print(f"   🚨 오류: {', '.join(result.errors[:3])}")
                
            total_products += result.total_products
            total_new += result.new_products
            total_updated += result.updated_products
            total_failed += result.failed_products
        
        print("\n" + "=" * 60)
        print(f"🎯 전체 요약:")
        print(f"   총 수집: {total_products}개 상품")
        print(f"   신규: {total_new}개, 업데이트: {total_updated}개, 실패: {total_failed}개")
        
    except Exception as e:
        logger.error(f"실행 오류: {e}")
        traceback.print_exc()
        
    finally:
        manager.close()

if __name__ == "__main__":
    asyncio.run(main())