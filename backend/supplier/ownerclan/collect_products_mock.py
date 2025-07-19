#!/usr/bin/env python3
"""
오너클랜 상품 수집 스크립트 (모의 데이터)
실제 API 대신 모의 데이터를 생성하여 DB에 저장
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import logging
import random
from faker import Faker

# 한국어 Faker 설정
fake = Faker('ko_KR')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OwnerClanMockCollector:
    def __init__(self):
        # 데이터베이스 연결
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
        # 카테고리 목록
        self.categories = [
            "패션의류", "패션잡화", "화장품/미용", "디지털/가전",
            "가구/인테리어", "출산/육아", "식품", "스포츠/레저",
            "생활/건강", "여행/티켓", "도서/음반", "완구/취미",
            "반려동물", "자동차용품"
        ]
        
        # 브랜드 목록
        self.brands = [
            "나이키", "아디다스", "삼성", "LG", "애플",
            "샤넬", "디올", "네이처리퍼블릭", "이니스프리",
            "무인양품", "이케아", "코스트코", "홈플러스"
        ]
        
    def generate_mock_product(self, index):
        """모의 상품 데이터 생성"""
        category = random.choice(self.categories)
        brand = random.choice(self.brands)
        
        # 가격 범위 설정 (카테고리별)
        price_ranges = {
            "패션의류": (10000, 200000),
            "패션잡화": (5000, 150000),
            "화장품/미용": (3000, 100000),
            "디지털/가전": (50000, 2000000),
            "가구/인테리어": (20000, 1000000),
            "출산/육아": (5000, 300000),
            "식품": (1000, 50000),
            "스포츠/레저": (10000, 500000),
            "생활/건강": (3000, 100000),
            "여행/티켓": (10000, 1000000),
            "도서/음반": (5000, 50000),
            "완구/취미": (5000, 200000),
            "반려동물": (3000, 100000),
            "자동차용품": (5000, 300000)
        }
        
        min_price, max_price = price_ranges.get(category, (5000, 100000))
        price = random.randint(min_price, max_price)
        cost_price = int(price * random.uniform(0.5, 0.8))
        
        product = {
            "id": f"OC{index:06d}",
            "name": f"[{brand}] {fake.catch_phrase()} - {category}",
            "code": f"OC-{category[:2]}-{index:06d}",
            "barcode": fake.ean13(),
            "brand_name": brand,
            "manufacturer_name": fake.company(),
            "origin_country": random.choice(["대한민국", "중국", "베트남", "미국", "일본"]),
            "description": fake.text(max_nb_chars=200),
            "stock": random.randint(0, 1000),
            "price": price,
            "cost_price": cost_price,
            "weight": random.randint(100, 5000),  # 그램 단위
            "status": random.choice(["active", "inactive", "soldout"]),
            "category": category,
            "category_id": f"CAT{random.randint(1, 100):03d}",
            "options": self.generate_options(category),
            "images": [
                {
                    "url": f"https://picsum.photos/seed/{index}/800/800",
                    "is_main": True
                }
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return product
    
    def generate_options(self, category):
        """카테고리별 옵션 생성"""
        options = []
        
        if category in ["패션의류", "패션잡화"]:
            # 색상 옵션
            colors = ["블랙", "화이트", "네이비", "그레이", "베이지", "브라운"]
            selected_colors = random.sample(colors, random.randint(2, 4))
            options.append({
                "name": "색상",
                "values": selected_colors
            })
            
            # 사이즈 옵션
            if category == "패션의류":
                sizes = ["S", "M", "L", "XL", "XXL"]
                options.append({
                    "name": "사이즈",
                    "values": sizes
                })
        
        elif category == "디지털/가전":
            # 용량 옵션
            capacities = ["64GB", "128GB", "256GB", "512GB", "1TB"]
            selected_capacities = random.sample(capacities, random.randint(2, 3))
            options.append({
                "name": "용량",
                "values": selected_capacities
            })
        
        return options
    
    def save_product_to_db(self, product):
        """상품 정보를 데이터베이스에 저장"""
        try:
            cursor = self.conn.cursor()
            
            # 기존 상품 확인
            cursor.execute("""
                SELECT id FROM products 
                WHERE product_key = %s
            """, (product['id'],))
            
            existing = cursor.fetchone()
            
            if existing:
                # 기존 상품 업데이트
                cursor.execute("""
                    UPDATE products SET
                        name = %s,
                        brand = %s,
                        price = %s,
                        base_price = %s,
                        cost_price = %s,
                        stock_quantity = %s,
                        stock_status = %s,
                        status = %s,
                        weight_kg = %s,
                        barcode = %s,
                        manufacturer = %s,
                        metadata = %s,
                        updated_at = %s,
                        last_stock_check = %s
                    WHERE product_key = %s
                """, (
                    product['name'],
                    product['brand_name'],
                    product['price'],
                    product['price'],
                    product['cost_price'],
                    product['stock'],
                    'in_stock' if product['stock'] > 0 else 'out_of_stock',
                    product['status'],
                    product['weight'] / 1000.0,  # 그램을 kg로 변환
                    product['barcode'],
                    product['manufacturer_name'],
                    Json(product),
                    datetime.now(),
                    datetime.now(),
                    product['id']
                ))
                logger.info(f"기존 상품 업데이트: {product['id']} - {product['name']}")
                return 'updated'
            else:
                # 신규 상품 추가
                cursor.execute("""
                    INSERT INTO products (
                        product_key,
                        name,
                        brand,
                        price,
                        base_price,
                        cost_price,
                        stock_quantity,
                        stock_status,
                        status,
                        weight_kg,
                        barcode,
                        manufacturer,
                        metadata,
                        created_at,
                        updated_at,
                        last_stock_check,
                        stock_sync_enabled
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    product['id'],
                    product['name'],
                    product['brand_name'],
                    product['price'],
                    product['price'],
                    product['cost_price'],
                    product['stock'],
                    'in_stock' if product['stock'] > 0 else 'out_of_stock',
                    product['status'],
                    product['weight'] / 1000.0,  # 그램을 kg로 변환
                    product['barcode'],
                    product['manufacturer_name'],
                    Json(product),
                    datetime.now(),
                    datetime.now(),
                    datetime.now(),
                    True
                ))
                logger.info(f"신규 상품 추가: {product['id']} - {product['name']}")
                return 'new'
                
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"상품 저장 실패: {str(e)}")
            return 'failed'
    
    def collect_products(self, total_products=1000):
        """오너클랜 모의 상품 수집"""
        try:
            logger.info(f"오너클랜 모의 상품 수집 시작... (총 {total_products}개)")
            
            new_count = 0
            updated_count = 0
            failed_count = 0
            
            for i in range(1, total_products + 1):
                product = self.generate_mock_product(i)
                result = self.save_product_to_db(product)
                
                if result == 'new':
                    new_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    failed_count += 1
                
                # 진행 상황 표시
                if i % 100 == 0:
                    logger.info(f"진행 상황: {i}/{total_products} 완료")
            
            logger.info(f"""
오너클랜 상품 수집 완료:
- 총 상품 수: {total_products}
- 신규 추가: {new_count}
- 업데이트: {updated_count}
- 실패: {failed_count}
            """)
            
            # 통계 조회
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN stock_quantity > 0 THEN 1 ELSE 0 END) as in_stock,
                    AVG(price) as avg_price
                FROM products
                WHERE product_key LIKE 'OC%'
            """)
            
            stats = cursor.fetchone()
            logger.info(f"""
오너클랜 상품 통계:
- 전체 상품: {stats['total']}
- 활성 상품: {stats['active']}
- 재고 있음: {stats['in_stock']}
- 평균 가격: ₩{stats['avg_price']:,.0f}
            """)
            
        except Exception as e:
            logger.error(f"상품 수집 중 오류 발생: {str(e)}")
            self.conn.rollback()
        finally:
            self.conn.close()

if __name__ == "__main__":
    # 수집할 상품 수 (기본값: 1000개)
    total_products = 1000
    if len(sys.argv) > 1:
        try:
            total_products = int(sys.argv[1])
        except ValueError:
            logger.error("잘못된 상품 수입니다. 기본값 1000개로 진행합니다.")
    
    collector = OwnerClanMockCollector()
    collector.collect_products(total_products)