#!/usr/bin/env python3
"""
쿠팡 판매 상품 수집 - 통합 상품 스키마 버전 (개선된 에러 처리)
모든 계정의 상품을 수집하여 통합 테이블에 저장
"""

import sys
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.append('/home/sunwoo/yooni/backend')
sys.path.append('/home/sunwoo/yooni/module/market/coupang')

from core import (
    get_logger, log_execution_time, log_api_call,
    APIException, APITimeoutException, APIRateLimitException,
    DatabaseException, MarketException,
    retry_on_error, handle_error
)
from auth.coupang_auth import CoupangAuth
import psycopg2
from psycopg2.extras import Json, RealDictCursor


class UnifiedCoupangProductCollector:
    def __init__(self):
        self.logger = get_logger(__name__, market_code='coupang')
        self._init_database()
        self._init_ssl_context()
        self._init_market()
        
    def _init_database(self):
        """데이터베이스 연결 초기화"""
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                port=5434,
                database="yoonni",
                user="postgres",
                password="1234"
            )
            self.logger.info("데이터베이스 연결 성공")
        except psycopg2.Error as e:
            raise DatabaseException(
                "데이터베이스 연결 실패",
                details={'error': str(e)},
                cause=e
            )
    
    def _init_ssl_context(self):
        """SSL 컨텍스트 초기화"""
        import ssl
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def _init_market(self):
        """쿠팡 마켓 정보 초기화"""
        try:
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
                    self.logger.info("쿠팡 마켓 정보 생성")
        except psycopg2.Error as e:
            raise DatabaseException(
                "마켓 정보 초기화 실패",
                details={'market': '쿠팡'},
                cause=e
            )
    
    @log_api_call('coupang')
    @retry_on_error(max_attempts=3, delay=2.0, exceptions=(APIException,))
    def get_products_page(self, auth: CoupangAuth, next_token: Optional[str] = None, 
                         status_type: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """상품 페이지 조회 (API 호출)"""
        base_url = "https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        params = {
            'vendorId': auth.vendor_id,
            'nextToken': next_token,
            'maxPerPage': limit,
            'statusType': status_type
        }
        
        # None 값 제거
        params = {k: v for k, v in params.items() if v is not None}
        
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        
        # 인증 헤더 생성
        auth_header = auth.generate_auth_header(url, "GET")
        
        # 요청 생성
        request = urllib.request.Request(url, headers=auth_header)
        
        try:
            # 타임아웃 설정과 함께 요청
            response = urllib.request.urlopen(request, context=self.ssl_context, timeout=30)
            response_data = json.loads(response.read().decode('utf-8'))
            
            # API 응답 검증
            if response_data.get('code') != 'SUCCESS':
                raise APIException(
                    f"API 오류: {response_data.get('message', 'Unknown error')}",
                    status_code=response.getcode(),
                    response_data=response_data
                )
            
            return response_data
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            
            # Rate limit 체크
            if e.code == 429:
                raise APIRateLimitException(
                    "API 요청 한도 초과",
                    retry_after=int(e.headers.get('Retry-After', 60))
                )
            
            raise APIException(
                f"HTTP 오류: {e.code}",
                status_code=e.code,
                response_data=error_body,
                cause=e
            )
            
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise APITimeoutException(
                    "API 요청 시간 초과",
                    timeout=30,
                    cause=e
                )
            raise APIException(
                f"네트워크 오류: {str(e.reason)}",
                cause=e
            )
    
    @log_execution_time()
    def upsert_product(self, product_data: Dict[str, Any]) -> bool:
        """상품 정보 upsert (insert or update)"""
        try:
            cursor = self.conn.cursor()
            
            # 필수 필드 추출
            market_product_id = str(product_data.get('sellerProductId', ''))
            
            # 옵션 상품인 경우 첫 번째 아이템의 정보 사용
            items = product_data.get('items', [])
            if items:
                first_item = items[0]
                sale_price = first_item.get('salePrice', 0)
                original_price = first_item.get('originalPrice', sale_price)
                cost_price = None  # API에서 제공하지 않음
                stock_quantity = first_item.get('maximumBuyableQuantity', 0)
            else:
                sale_price = original_price = cost_price = stock_quantity = 0
            
            # 상태 매핑
            status_map = {
                'APPROVED': 'active',
                'REJECTED': 'inactive',
                'PARTIAL_APPROVED': 'partial',
                'PENDING': 'pending',
                'PROHIBITED': 'prohibited'
            }
            status = status_map.get(product_data.get('statusName'), 'unknown')
            
            # UPSERT 쿼리
            cursor.execute("""
                INSERT INTO unified_products (
                    market_product_id, product_name, brand, manufacturer,
                    category_name, description, barcode, model_number,
                    sale_price, original_price, cost_price, discount_rate,
                    stock_quantity, min_order_quantity, max_order_quantity,
                    status, weight, shipping_type, shipping_fee,
                    is_free_shipping, tags, attributes, options,
                    images, thumbnail_url, detail_images, market_url,
                    market_code, market_data, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, NOW(), NOW()
                )
                ON CONFLICT (market_product_id, market_code) 
                DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    brand = EXCLUDED.brand,
                    sale_price = EXCLUDED.sale_price,
                    original_price = EXCLUDED.original_price,
                    stock_quantity = EXCLUDED.stock_quantity,
                    status = EXCLUDED.status,
                    market_data = EXCLUDED.market_data,
                    updated_at = NOW()
                RETURNING id
            """, (
                market_product_id,
                product_data.get('productName'),
                product_data.get('brand'),
                product_data.get('manufacture'),
                product_data.get('displayCategoryName'),
                None,  # description
                product_data.get('barcode'),
                product_data.get('modelNo'),
                sale_price,
                original_price,
                cost_price,
                None,  # discount_rate
                stock_quantity,
                1,  # min_order_quantity
                product_data.get('maximumBuyCount'),
                status,
                None,  # weight
                product_data.get('deliveryMethod'),
                product_data.get('deliveryCompanyCode'),
                product_data.get('freeShipOverAmount') is not None,
                [],  # tags
                Json(product_data.get('attributes', {})),
                Json(items),  # options
                [img.get('imageUrl') for img in product_data.get('images', []) if img.get('imageType') == 'MAIN'],
                next((img.get('imageUrl') for img in product_data.get('images', []) if img.get('imageType') == 'MAIN'), None),
                [img.get('imageUrl') for img in product_data.get('images', []) if img.get('imageType') == 'DETAIL'],
                f"https://www.coupang.com/vp/products/{market_product_id}",
                'coupang',
                Json(product_data)
            ))
            
            product_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            
            self.logger.debug(f"상품 저장 완료: {market_product_id}")
            return True
            
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseException(
                f"상품 저장 실패: {market_product_id}",
                details={'product_id': market_product_id, 'error': str(e)},
                cause=e
            )
        finally:
            if cursor:
                cursor.close()
    
    @log_execution_time()
    def collect_products_for_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """특정 계정의 상품 수집"""
        auth = CoupangAuth(
            access_key=account['access_key'],
            secret_key=account['secret_key'],
            vendor_id=account['vendor_id']
        )
        
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        next_token = None
        page = 1
        
        self.logger.info(f"계정 {account['name']} 상품 수집 시작")
        
        while True:
            try:
                # API 호출
                response = self.get_products_page(auth, next_token)
                
                products = response.get('data', [])
                if not products:
                    break
                
                # 상품 저장
                for product in products:
                    stats['total'] += 1
                    try:
                        self.upsert_product(product)
                        stats['success'] += 1
                    except Exception as e:
                        stats['failed'] += 1
                        error_info = handle_error(e, {
                            'product_id': product.get('sellerProductId'),
                            'account': account['name']
                        })
                        stats['errors'].append(error_info)
                
                self.logger.info(
                    f"페이지 {page} 처리 완료: {len(products)}개 상품",
                    extra={'account': account['name'], 'page': page}
                )
                
                # 다음 페이지
                next_token = response.get('nextToken')
                if not next_token:
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limit 방지
                
            except APIRateLimitException as e:
                self.logger.warning(
                    f"Rate limit 도달, {e.details.get('retry_after', 60)}초 대기",
                    extra={'account': account['name']}
                )
                time.sleep(e.details.get('retry_after', 60))
                continue
                
            except Exception as e:
                error_info = handle_error(e, {'account': account['name'], 'page': page})
                stats['errors'].append(error_info)
                self.logger.error(
                    f"페이지 {page} 처리 실패",
                    extra={'account': account['name'], 'error': error_info}
                )
                break
        
        return stats
    
    @log_execution_time()
    def run(self):
        """전체 상품 수집 실행"""
        try:
            # 계정 정보 로드
            with open('/home/sunwoo/yooni/module/market/coupang/accounts.json', 'r') as f:
                accounts_data = json.load(f)
            
            total_stats = {
                'accounts_processed': 0,
                'total_products': 0,
                'total_success': 0,
                'total_failed': 0,
                'account_stats': {}
            }
            
            # 각 계정별로 수집
            for account in accounts_data['accounts']:
                if not account.get('active', True):
                    continue
                
                self.logger.info(f"계정 처리 시작: {account['name']}")
                
                try:
                    stats = self.collect_products_for_account(account)
                    
                    total_stats['accounts_processed'] += 1
                    total_stats['total_products'] += stats['total']
                    total_stats['total_success'] += stats['success']
                    total_stats['total_failed'] += stats['failed']
                    total_stats['account_stats'][account['name']] = stats
                    
                    self.logger.info(
                        f"계정 처리 완료: {account['name']}",
                        extra={'stats': stats}
                    )
                    
                except Exception as e:
                    error_info = handle_error(e, {'account': account['name']})
                    total_stats['account_stats'][account['name']] = {
                        'error': error_info
                    }
                    self.logger.error(
                        f"계정 처리 실패: {account['name']}",
                        extra={'error': error_info}
                    )
            
            # 최종 통계 출력
            self.logger.info("전체 수집 완료", extra={'stats': total_stats})
            
            print("\n=== 쿠팡 상품 수집 완료 ===")
            print(f"처리된 계정: {total_stats['accounts_processed']}개")
            print(f"전체 상품: {total_stats['total_products']}개")
            print(f"성공: {total_stats['total_success']}개")
            print(f"실패: {total_stats['total_failed']}개")
            
            return total_stats
            
        except Exception as e:
            self.logger.error("상품 수집 중 치명적 오류", exc_info=True)
            raise
        finally:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.logger.info("데이터베이스 연결 종료")


def main():
    """메인 함수"""
    # 로거 설정
    from core.logger import LoggerManager
    logger_manager = LoggerManager()
    
    # DB 핸들러 추가
    logger_manager.add_database_handler({
        'host': 'localhost',
        'port': 5434,
        'database': 'yoonni',
        'user': 'postgres',
        'password': '1234'
    })
    
    collector = UnifiedCoupangProductCollector()
    return collector.run()


if __name__ == "__main__":
    main()