#!/usr/bin/env python3
"""
젠트레이드 상품 수집 스크립트
REST API를 사용하여 상품 정보를 수집하고 DB에 저장
"""

import os
import sys
import json
import requests
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import logging
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZentradeCollector:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('ZENTRADE_API_KEY', '')
        self.base_url = "https://api.zentrade.co.kr/v1"
        self.session = requests.Session()
        
        # 데이터베이스 연결
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
    def authenticate(self):
        """API 인증"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={
                    'apiKey': self.api_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session.headers.update({
                    'Authorization': f"Bearer {data.get('token')}"
                })
                return True
            else:
                logger.error(f"인증 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"인증 오류: {str(e)}")
            return False
            
    def collect_products(self):
        """젠트레이드 상품 수집"""
        try:
            logger.info("젠트레이드 상품 수집 시작...")
            
            # 인증
            if not self.authenticate():
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "total_products": 0,
                    "new_products": 0,
                    "updated_products": 0,
                    "failed_products": 0
                }
            
            total_collected = 0
            new_products = 0
            updated_products = 0
            failed_products = 0
            
            # 페이지네이션으로 모든 상품 수집
            page = 1
            page_size = 100
            
            while True:
                try:
                    # API 요청
                    response = self.session.get(
                        f"{self.base_url}/products",
                        params={
                            'page': page,
                            'pageSize': page_size,
                            'status': 'all'
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"API 요청 실패: {response.status_code} - {response.text}")
                        break
                        
                    data = response.json()
                    items = data.get('data', [])
                    total_count = data.get('totalCount', 0)
                    
                    if not items:
                        break
                        
                    logger.info(f"수집 중... 페이지 {page} ({len(items)}개 상품)")
                    
                    # 각 상품 저장
                    for product in items:
                        try:
                            # 상세 정보 조회
                            detail = self.get_product_detail(product['id'])
                            if detail:
                                saved = self.save_product(detail)
                                if saved == 'new':
                                    new_products += 1
                                elif saved == 'updated':
                                    updated_products += 1
                                total_collected += 1
                        except Exception as e:
                            logger.error(f"상품 저장 실패 ({product.get('id')}): {str(e)}")
                            failed_products += 1
                            
                    page += 1
                    
                    # API 부하 방지
                    time.sleep(0.5)
                    
                    # 마지막 페이지 확인
                    if total_collected >= total_count:
                        break
                        
                except Exception as e:
                    logger.error(f"페이지 수집 오류: {str(e)}")
                    break
                    
            self.conn.commit()
            
            result = {
                "success": True,
                "total_products": total_collected,
                "new_products": new_products,
                "updated_products": updated_products,
                "failed_products": failed_products
            }
            
            logger.info(f"수집 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"수집 실패: {str(e)}")
            self.conn.rollback()
            return {
                "success": False,
                "error": str(e),
                "total_products": 0,
                "new_products": 0,
                "updated_products": 0,
                "failed_products": 0
            }
        finally:
            self.conn.close()
            
    def get_product_detail(self, product_id):
        """상품 상세 정보 조회"""
        try:
            response = self.session.get(f"{self.base_url}/products/{product_id}")
            if response.status_code == 200:
                return response.json().get('data')
            else:
                logger.error(f"상품 상세 조회 실패: {product_id}")
                return None
        except Exception as e:
            logger.error(f"상품 상세 조회 오류: {str(e)}")
            return None
            
    def save_product(self, product):
        """상품 정보를 DB에 저장"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # supplier_id 가져오기 (젠트레이드 = 2)
            cursor.execute("SELECT id FROM suppliers WHERE name = '젠트레이드'")
            supplier = cursor.fetchone()
            supplier_id = supplier['id'] if supplier else 2
            
            # 기존 상품 확인
            cursor.execute("""
                SELECT id FROM supplier_products 
                WHERE supplier_id = %s AND supplier_product_id = %s
            """, (supplier_id, str(product['id'])))
            
            existing = cursor.fetchone()
            
            # 상품 데이터 준비
            product_data = {
                'supplier_id': supplier_id,
                'supplier_product_id': str(product['id']),
                'product_name': product['name'],
                'product_code': product.get('productCode'),
                'barcode': product.get('barcode'),
                'brand': product.get('brand'),
                'manufacturer': product.get('manufacturer'),
                'origin': product.get('origin', 'KR'),
                'description': product.get('description'),
                'category': product.get('category'),
                'price': product.get('price', 0),
                'cost_price': product.get('costPrice', 0),
                'stock_quantity': product.get('stockQuantity', 0),
                'weight': product.get('weight', 0),
                'status': 'active' if product.get('isActive', True) else 'inactive',
                'image_url': product.get('mainImage'),
                'raw_data': Json(product),
                'collected_at': datetime.now()
            }
            
            if existing:
                # 업데이트
                update_query = """
                    UPDATE supplier_products SET
                        product_name = %(product_name)s,
                        product_code = %(product_code)s,
                        barcode = %(barcode)s,
                        brand = %(brand)s,
                        manufacturer = %(manufacturer)s,
                        origin = %(origin)s,
                        description = %(description)s,
                        category = %(category)s,
                        price = %(price)s,
                        cost_price = %(cost_price)s,
                        stock_quantity = %(stock_quantity)s,
                        weight = %(weight)s,
                        status = %(status)s,
                        image_url = %(image_url)s,
                        raw_data = %(raw_data)s,
                        collected_at = %(collected_at)s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                cursor.execute(update_query, {**product_data, 'id': existing['id']})
                return 'updated'
            else:
                # 신규 생성
                insert_query = """
                    INSERT INTO supplier_products (
                        supplier_id, supplier_product_id, product_name, product_code,
                        barcode, brand, manufacturer, origin, description,
                        category, price, cost_price, stock_quantity, weight,
                        status, image_url, raw_data, collected_at
                    ) VALUES (
                        %(supplier_id)s, %(supplier_product_id)s, %(product_name)s, %(product_code)s,
                        %(barcode)s, %(brand)s, %(manufacturer)s, %(origin)s, %(description)s,
                        %(category)s, %(price)s, %(cost_price)s, %(stock_quantity)s, %(weight)s,
                        %(status)s, %(image_url)s, %(raw_data)s, %(collected_at)s
                    )
                """
                cursor.execute(insert_query, product_data)
                return 'new'

def main():
    """메인 실행 함수"""
    collector = ZentradeCollector()
    result = collector.collect_products()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()