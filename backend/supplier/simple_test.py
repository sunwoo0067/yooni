#!/usr/bin/env python3
"""
간단한 상품수집 테스트
"""
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_supplier_collection():
    """간단한 상품수집 테스트"""
    
    # 1. 데이터베이스 연결 (Docker 컨테이너 내부 방식)
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'  # Docker 컨테이너 비밀번호
        )
        logger.info("✅ 데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 2. 공급사 확인
            cursor.execute("SELECT id, name FROM suppliers WHERE name = '오너클랜'")
            supplier = cursor.fetchone()
            
            if not supplier:
                logger.error("❌ 오너클랜 공급사를 찾을 수 없습니다")
                return False
                
            supplier_id = supplier['id']
            logger.info(f"✅ 공급사 확인: {supplier['name']} (ID: {supplier_id})")
            
            # 3. 테스트 상품 데이터 생성
            test_products = []
            for i in range(1, 6):  # 5개 상품만 테스트
                product = {
                    'id': f'TEST{i:03d}',
                    'name': f'테스트 상품 {i}',
                    'code': f'TC{i:03d}',
                    'price': 10000 + (i * 1000),
                    'stock': 100 + i * 10,
                    'status': 'ACTIVE'
                }
                test_products.append(product)
            
            logger.info(f"✅ 테스트 상품 {len(test_products)}개 생성")
            
            # 4. 상품 저장 테스트
            saved_count = 0
            for product in test_products:
                try:
                    # 기존 상품 확인
                    cursor.execute("""
                        SELECT id FROM supplier_products 
                        WHERE supplier_id = %s AND supplier_product_id = %s
                    """, (supplier_id, product['id']))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 업데이트
                        cursor.execute("""
                            UPDATE supplier_products SET
                                product_name = %s,
                                price = %s,
                                stock_quantity = %s,
                                status = %s,
                                raw_data = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            product['name'],
                            product['price'],
                            product['stock'],
                            'active' if product['status'] == 'ACTIVE' else 'inactive',
                            Json(product),
                            existing['id']
                        ))
                        logger.info(f"🔄 상품 업데이트: {product['name']}")
                    else:
                        # 신규 생성
                        cursor.execute("""
                            INSERT INTO supplier_products (
                                supplier_id, supplier_product_id, product_name,
                                price, stock_quantity, status, raw_data
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            supplier_id,
                            product['id'],
                            product['name'],
                            product['price'],
                            product['stock'],
                            'active' if product['status'] == 'ACTIVE' else 'inactive',
                            Json(product)
                        ))
                        logger.info(f"🆕 신규 상품 생성: {product['name']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 상품 저장 실패 ({product['id']}): {e}")
            
            # 5. 커밋
            conn.commit()
            logger.info(f"✅ {saved_count}개 상품 저장 완료")
            
            # 6. 저장된 상품 확인
            cursor.execute("""
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
                FROM supplier_products sp
                JOIN suppliers s ON sp.supplier_id = s.id
                WHERE s.name = '오너클랜'
            """)
            
            result = cursor.fetchone()
            logger.info(f"📊 총 상품: {result['total_count']}개, 활성: {result['active_count']}개")
            
            # 7. 수집 로그 기록
            cursor.execute("""
                INSERT INTO supplier_collection_logs 
                (supplier_id, collection_type, status, total_items, new_items, 
                 started_at, completed_at, duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                supplier_id, 'products', 'success', saved_count, saved_count,
                datetime.now(), datetime.now(), 1
            ))
            
            conn.commit()
            logger.info("✅ 수집 로그 기록 완료")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏪 간단한 상품수집 테스트 시작")
    print("=" * 50)
    
    success = test_supplier_collection()
    
    print("=" * 50)
    if success:
        print("🎉 상품수집 테스트 성공!")
    else:
        print("💥 상품수집 테스트 실패!")
    
    exit(0 if success else 1)