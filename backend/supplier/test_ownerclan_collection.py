#!/usr/bin/env python3
"""
오너클랜 상품수집 테스트 스크립트
실제 API 대신 모의 데이터로 수집 프로세스 테스트
"""

import sys
import os
import json
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres',
    'password': '1234'
}

class MockOwnerClanCollector:
    """오너클랜 수집 시뮬레이터"""
    
    def __init__(self):
        # 간단한 연결 (이미 확인된 방법)
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        logger.info("데이터베이스 연결 성공")
    
    def generate_mock_products(self, count=50):
        """모의 상품 데이터 생성"""
        mock_products = []
        
        categories = [
            "가전/디지털/컴퓨터",
            "패션/의류/액세서리", 
            "뷰티/건강/헬스케어",
            "생활용품/가구/인테리어",
            "스포츠/레저/자동차",
            "식품/건강기능식품",
            "출산/육아/완구",
            "도서/문구/취미"
        ]
        
        brands = ["삼성", "LG", "애플", "나이키", "아디다스", "언더아머", "코카콜라", "농심"]
        origins = ["대한민국", "미국", "중국", "일본", "독일", "베트남"]
        
        for i in range(1, count + 1):
            product = {
                "id": f"OC{i:06d}",
                "name": f"테스트 상품 {i}번",
                "code": f"TC{i:06d}",
                "barcode": f"880123{i:06d}",
                "brandName": brands[i % len(brands)],
                "manufacturerName": f"{brands[i % len(brands)]} 제조",
                "originCountry": origins[i % len(origins)],
                "description": f"고품질 테스트 상품입니다. 상품번호: {i}",
                "stock": 100 + (i * 10) % 500,
                "price": 10000 + (i * 1000) % 100000,
                "costPrice": 5000 + (i * 500) % 50000,
                "weight": 0.1 + (i * 0.05) % 5.0,
                "status": "ACTIVE" if i % 10 != 0 else "INACTIVE",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": datetime.now().isoformat(),
                "category": {
                    "id": f"CAT{(i % len(categories)) + 1}",
                    "name": categories[i % len(categories)],
                    "fullPath": f"대분류 > {categories[i % len(categories)]}"
                },
                "options": [
                    {
                        "id": f"OPT{i}_1",
                        "name": "색상",
                        "values": ["빨강", "파랑", "초록"]
                    },
                    {
                        "id": f"OPT{i}_2", 
                        "name": "크기",
                        "values": ["S", "M", "L", "XL"]
                    }
                ],
                "images": [
                    {
                        "url": f"https://cdn.ownerclan.com/products/{i}_main.jpg",
                        "isMain": True
                    },
                    {
                        "url": f"https://cdn.ownerclan.com/products/{i}_detail.jpg",
                        "isMain": False
                    }
                ]
            }
            mock_products.append(product)
            
        return mock_products
    
    def simulate_collection(self, product_count=50):
        """상품 수집 시뮬레이션"""
        logger.info(f"오너클랜 상품수집 시뮬레이션 시작 ({product_count}개 상품)")
        
        start_time = datetime.now()
        
        try:
            # 공급사 ID 확인
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id FROM suppliers WHERE name = '오너클랜'")
                supplier = cursor.fetchone()
                
                if not supplier:
                    raise ValueError("오너클랜 공급사를 찾을 수 없습니다")
                    
                supplier_id = supplier['id']
                logger.info(f"공급사 ID: {supplier_id}")
            
            # 모의 상품 데이터 생성
            mock_products = self.generate_mock_products(product_count)
            logger.info(f"모의 상품 {len(mock_products)}개 생성 완료")
            
            # 상품 저장 통계
            total_collected = 0
            new_products = 0
            updated_products = 0
            failed_products = 0
            
            # 배치 처리로 성능 향상
            batch_size = 10
            for i in range(0, len(mock_products), batch_size):
                batch = mock_products[i:i + batch_size]
                
                for product in batch:
                    try:
                        result = self.save_product(supplier_id, product)
                        if result == 'new':
                            new_products += 1
                        elif result == 'updated':
                            updated_products += 1
                        total_collected += 1
                        
                    except Exception as e:
                        logger.error(f"상품 저장 실패 ({product['id']}): {e}")
                        failed_products += 1
                
                # 진행률 표시
                progress = min(100, (i + batch_size) / len(mock_products) * 100)
                logger.info(f"진행률: {progress:.1f}% ({i + batch_size}/{len(mock_products)})")
                
                # API 부하 시뮬레이션
                time.sleep(0.1)
            
            # 커밋
            self.conn.commit()
            
            # 수집 로그 기록
            duration = (datetime.now() - start_time).total_seconds()
            self.log_collection_result(supplier_id, 'products', 'success', 
                                     total_collected, new_products, updated_products, 
                                     failed_products, None, start_time, duration)
            
            result = {
                "success": True,
                "total_products": total_collected,
                "new_products": new_products,
                "updated_products": updated_products,
                "failed_products": failed_products,
                "duration_seconds": duration,
                "products_per_second": total_collected / duration if duration > 0 else 0
            }
            
            logger.info(f"수집 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"수집 실패: {e}")
            self.conn.rollback()
            
            # 실패 로그 기록
            duration = (datetime.now() - start_time).total_seconds()
            self.log_collection_result(supplier_id, 'products', 'failed', 
                                     0, 0, 0, 0, str(e), start_time, duration)
            
            return {
                "success": False,
                "error": str(e),
                "total_products": 0,
                "new_products": 0,
                "updated_products": 0,
                "failed_products": 0
            }
    
    def save_product(self, supplier_id, product):
        """상품 저장"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
                'price': float(product.get('price', 0)),
                'cost_price': float(product.get('costPrice', 0)),
                'stock_quantity': int(product.get('stock', 0)),
                'weight': float(product.get('weight', 0)),
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
                update_fields = [f"{k} = %({k})s" for k in product_data.keys() if k != 'supplier_id']
                update_query = f"""
                    UPDATE supplier_products SET
                        {', '.join(update_fields)},
                        updated_at = NOW()
                    WHERE id = %(existing_id)s
                """
                product_data['existing_id'] = existing['id']
                cursor.execute(update_query, product_data)
                return 'updated'
            else:
                # 신규 생성
                fields = list(product_data.keys())
                placeholders = [f"%({field})s" for field in fields]
                insert_query = f"""
                    INSERT INTO supplier_products ({', '.join(fields)}) 
                    VALUES ({', '.join(placeholders)})
                """
                cursor.execute(insert_query, product_data)
                return 'new'
    
    def log_collection_result(self, supplier_id, collection_type, status, 
                            total_items, new_items, updated_items, failed_items,
                            error_message, started_at, duration):
        """수집 결과 로그 기록"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO supplier_collection_logs 
                (supplier_id, collection_type, status, total_items, new_items, 
                 updated_items, failed_items, error_message, started_at, 
                 completed_at, duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                supplier_id, collection_type, status, total_items, new_items,
                updated_items, failed_items, error_message, started_at,
                datetime.now(), int(duration)
            ))
    
    def get_collection_stats(self):
        """수집 통계 조회"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 전체 상품 수
            cursor.execute("""
                SELECT 
                    s.name as supplier_name,
                    COUNT(sp.id) as total_products,
                    COUNT(CASE WHEN sp.status = 'active' THEN 1 END) as active_products,
                    MAX(sp.collected_at) as last_collected
                FROM suppliers s
                LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
                WHERE s.name IN ('오너클랜', '젠트레이드')
                GROUP BY s.id, s.name
                ORDER BY s.name
            """)
            
            product_stats = cursor.fetchall()
            
            # 최근 수집 로그
            cursor.execute("""
                SELECT 
                    s.name as supplier_name,
                    scl.collection_type,
                    scl.status,
                    scl.total_items,
                    scl.new_items,
                    scl.updated_items,
                    scl.failed_items,
                    scl.duration_seconds,
                    scl.started_at
                FROM supplier_collection_logs scl
                JOIN suppliers s ON scl.supplier_id = s.id
                WHERE s.name IN ('오너클랜', '젠트레이드')
                ORDER BY scl.started_at DESC
                LIMIT 10
            """)
            
            recent_logs = cursor.fetchall()
            
            return {
                'product_stats': [dict(row) for row in product_stats],
                'recent_logs': [dict(row) for row in recent_logs]
            }
    
    def close(self):
        """연결 종료"""
        self.conn.close()

def run_collection_test():
    """상품수집 테스트 실행"""
    logger.info("🏪 오너클랜 상품수집 테스트 시작")
    print("=" * 60)
    
    collector = MockOwnerClanCollector()
    
    try:
        # 1. 기존 통계 확인
        logger.info("=== 1. 현재 상태 확인 ===")
        before_stats = collector.get_collection_stats()
        
        print("수집 전 상품 통계:")
        for stat in before_stats['product_stats']:
            print(f"  📊 {stat['supplier_name']}: {stat['total_products']}개 상품 ({stat['active_products']}개 활성)")
        
        # 2. 상품 수집 시뮬레이션
        logger.info("=== 2. 상품 수집 시뮬레이션 ===")
        result = collector.simulate_collection(product_count=100)
        
        if result['success']:
            print(f"✅ 수집 성공!")
            print(f"  📦 총 상품: {result['total_products']}개")
            print(f"  🆕 신규: {result['new_products']}개")
            print(f"  🔄 업데이트: {result['updated_products']}개")
            print(f"  ❌ 실패: {result['failed_products']}개")
            print(f"  ⏱️ 소요시간: {result['duration_seconds']:.1f}초")
            print(f"  📈 처리속도: {result['products_per_second']:.1f}개/초")
        else:
            print(f"❌ 수집 실패: {result['error']}")
            
        # 3. 수집 후 통계 확인
        logger.info("=== 3. 수집 후 상태 확인 ===")
        after_stats = collector.get_collection_stats()
        
        print("수집 후 상품 통계:")
        for stat in after_stats['product_stats']:
            print(f"  📊 {stat['supplier_name']}: {stat['total_products']}개 상품 ({stat['active_products']}개 활성)")
            if stat['last_collected']:
                print(f"      마지막 수집: {stat['last_collected']}")
        
        print("\n최근 수집 로그:")
        for log in after_stats['recent_logs'][:3]:
            status_icon = "✅" if log['status'] == 'success' else "❌"
            print(f"  {status_icon} {log['supplier_name']}: {log['total_items']}개 처리 ({log['duration_seconds']}초)")
        
        # 4. 데이터베이스 검증
        logger.info("=== 4. 데이터 검증 ===")
        with collector.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 샘플 상품 조회
            cursor.execute("""
                SELECT 
                    product_name, brand, category, price, stock_quantity, status
                FROM supplier_products sp
                JOIN suppliers s ON sp.supplier_id = s.id
                WHERE s.name = '오너클랜'
                ORDER BY sp.id DESC
                LIMIT 5
            """)
            
            sample_products = cursor.fetchall()
            
            print("샘플 상품 데이터:")
            for product in sample_products:
                print(f"  🛍️ {product['product_name']}")
                print(f"     브랜드: {product['brand']}, 가격: {product['price']:,}원")
                print(f"     카테고리: {product['category']}, 재고: {product['stock_quantity']}개")
        
        print("\n" + "=" * 60)
        print("🎉 상품수집 테스트 완료!")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"테스트 중 오류: {e}")
        return False
        
    finally:
        collector.close()

if __name__ == "__main__":
    success = run_collection_test()
    sys.exit(0 if success else 1)