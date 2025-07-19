#!/usr/bin/env python3
"""
오너클랜 상품 수집 스크립트
GraphQL API를 사용하여 상품 정보를 수집하고 DB에 저장
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

class OwnerClanCollector:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OWNERCLAN_API_KEY', '')
        self.api_url = "https://api.ownerclan.com/v1/graphql"
        self.auth_url = "https://auth.ownerclan.com/auth"
        self.access_token = None
        
        # 데이터베이스 연결
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
    def authenticate(self):
        """오너클랜 API 인증"""
        try:
            # supplier_configs에서 인증 정보 가져오기
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT sc.api_key, sc.api_secret
                    FROM supplier_configs sc
                    JOIN suppliers s ON sc.supplier_id = s.id
                    WHERE s.name = '오너클랜'
                """)
                config = cursor.fetchone()
                
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
            
            if not self.access_token:
                raise Exception("토큰을 받지 못했습니다")
                
            logger.info("오너클랜 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"인증 오류: {str(e)}")
            return False
    
    def get_headers(self):
        """API 요청 헤더 생성"""
        if not self.access_token:
            self.authenticate()
            
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
    def get_products_query(self, limit=100, offset=0):
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
        
    def collect_products(self):
        """오너클랜 상품 수집"""
        try:
            logger.info("오너클랜 상품 수집 시작...")
            
            # 인증 먼저 수행
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
            limit = 100
            offset = 0
            
            while True:
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
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"API 요청 실패: {response.status_code} - {response.text}")
                        break
                        
                    data = response.json()
                    
                    if 'errors' in data:
                        logger.error(f"GraphQL 에러: {data['errors']}")
                        break
                        
                    products = data.get('data', {}).get('products', {})
                    items = products.get('items', [])
                    total_count = products.get('totalCount', 0)
                    
                    if not items:
                        break
                        
                    logger.info(f"수집 중... {offset + 1}-{offset + len(items)} / {total_count}")
                    
                    # 각 상품 저장
                    for product in items:
                        try:
                            saved = self.save_product(product)
                            if saved == 'new':
                                new_products += 1
                            elif saved == 'updated':
                                updated_products += 1
                            total_collected += 1
                        except Exception as e:
                            logger.error(f"상품 저장 실패 ({product.get('id')}): {str(e)}")
                            failed_products += 1
                            
                    offset += limit
                    
                    # API 부하 방지
                    time.sleep(0.5)
                    
                    # 모든 상품 수집 완료
                    if offset >= total_count:
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
            
    def save_product(self, product):
        """상품 정보를 DB에 저장"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # supplier_id 가져오기 (오너클랜 = 1)
            cursor.execute("SELECT id FROM suppliers WHERE name = '오너클랜'")
            supplier = cursor.fetchone()
            supplier_id = supplier['id'] if supplier else 1
            
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
                'product_code': product.get('code'),
                'barcode': product.get('barcode'),
                'brand': product.get('brandName'),
                'manufacturer': product.get('manufacturerName'),
                'origin': product.get('originCountry'),
                'description': product.get('description'),
                'category': product.get('category', {}).get('fullPath'),
                'price': product.get('price', 0),
                'cost_price': product.get('costPrice', 0),
                'stock_quantity': product.get('stock', 0),
                'weight': product.get('weight', 0),
                'status': 'active' if product.get('status') == 'ACTIVE' else 'inactive',
                'raw_data': Json(product),
                'collected_at': datetime.now()
            }
            
            # 이미지 URL 추출
            images = product.get('images', [])
            if images:
                main_image = next((img['url'] for img in images if img.get('isMain')), None)
                product_data['image_url'] = main_image or images[0].get('url')
                
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
    collector = OwnerClanCollector()
    result = collector.collect_products()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()