"""
데이터베이스 통합 테스트
"""
import pytest
import psycopg2
from datetime import datetime, timedelta
import json


class TestDatabaseOperations:
    """데이터베이스 작업 통합 테스트"""
    
    @pytest.mark.db
    def test_product_crud_operations(self, db_cursor):
        """상품 CRUD 작업 테스트"""
        # CREATE - 상품 생성
        product_data = {
            'market_product_id': 'TEST_PROD_001',
            'product_name': '통합 테스트 상품',
            'brand': 'TEST BRAND',
            'category_name': 'TEST CATEGORY',
            'sale_price': 25000,
            'cost_price': 15000,
            'stock_quantity': 50,
            'status': 'active',
            'market_code': 'coupang'
        }
        
        db_cursor.execute("""
            INSERT INTO unified_products (
                market_product_id, product_name, brand, category_name,
                sale_price, cost_price, stock_quantity, status, market_code
            ) VALUES (
                %(market_product_id)s, %(product_name)s, %(brand)s, %(category_name)s,
                %(sale_price)s, %(cost_price)s, %(stock_quantity)s, %(status)s, %(market_code)s
            ) RETURNING id
        """, product_data)
        
        product_id = db_cursor.fetchone()[0]
        db_cursor.connection.commit()
        
        assert product_id is not None
        
        # READ - 상품 조회
        db_cursor.execute("""
            SELECT * FROM unified_products WHERE id = %s
        """, (product_id,))
        
        product = db_cursor.fetchone()
        assert product is not None
        assert product[1] == 'TEST_PROD_001'  # market_product_id
        assert product[2] == '통합 테스트 상품'  # product_name
        
        # UPDATE - 상품 수정
        new_price = 30000
        db_cursor.execute("""
            UPDATE unified_products 
            SET sale_price = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_price, product_id))
        db_cursor.connection.commit()
        
        db_cursor.execute("""
            SELECT sale_price FROM unified_products WHERE id = %s
        """, (product_id,))
        
        updated_price = db_cursor.fetchone()[0]
        assert updated_price == new_price
        
        # DELETE - 상품 삭제
        db_cursor.execute("""
            DELETE FROM unified_products WHERE id = %s
        """, (product_id,))
        db_cursor.connection.commit()
        
        db_cursor.execute("""
            SELECT COUNT(*) FROM unified_products WHERE id = %s
        """, (product_id,))
        
        count = db_cursor.fetchone()[0]
        assert count == 0
    
    @pytest.mark.db
    def test_order_with_items(self, db_cursor):
        """주문 및 주문 항목 통합 테스트"""
        # 테스트용 상품 생성
        db_cursor.execute("""
            INSERT INTO unified_products (
                market_product_id, product_name, sale_price, stock_quantity, market_code
            ) VALUES 
            ('PROD_001', '상품1', 10000, 100, 'coupang'),
            ('PROD_002', '상품2', 20000, 50, 'coupang')
            RETURNING id
        """)
        product_ids = [row[0] for row in db_cursor.fetchall()]
        
        # 주문 생성
        order_data = {
            'market_order_id': 'TEST_ORDER_001',
            'order_date': datetime.now(),
            'buyer_name': '테스트 구매자',
            'buyer_email': 'test@example.com',
            'buyer_phone': '010-1234-5678',
            'total_price': 40000,
            'order_status': 'pending',
            'payment_method': '신용카드',
            'shipping_address': '서울시 테스트구 샘플로 123',
            'market_code': 'coupang',
            'raw_data': json.dumps({'test': 'data'})
        }
        
        db_cursor.execute("""
            INSERT INTO market_orders (
                market_order_id, order_date, buyer_name, buyer_email, buyer_phone,
                total_price, order_status, payment_method, shipping_address, 
                market_code, raw_data
            ) VALUES (
                %(market_order_id)s, %(order_date)s, %(buyer_name)s, %(buyer_email)s, 
                %(buyer_phone)s, %(total_price)s, %(order_status)s, %(payment_method)s,
                %(shipping_address)s, %(market_code)s, %(raw_data)s
            ) RETURNING id
        """, order_data)
        
        order_id = db_cursor.fetchone()[0]
        
        # 주문 항목 생성
        order_items = [
            {
                'order_id': order_id,
                'product_id': product_ids[0],
                'quantity': 2,
                'unit_price': 10000,
                'total_price': 20000
            },
            {
                'order_id': order_id,
                'product_id': product_ids[1],
                'quantity': 1,
                'unit_price': 20000,
                'total_price': 20000
            }
        ]
        
        for item in order_items:
            db_cursor.execute("""
                INSERT INTO order_items (
                    order_id, product_id, quantity, unit_price, total_price
                ) VALUES (
                    %(order_id)s, %(product_id)s, %(quantity)s, %(unit_price)s, %(total_price)s
                )
            """, item)
        
        db_cursor.connection.commit()
        
        # 주문 및 항목 조회
        db_cursor.execute("""
            SELECT 
                o.market_order_id,
                o.total_price,
                COUNT(oi.id) as item_count,
                SUM(oi.quantity) as total_quantity
            FROM market_orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = %s
            GROUP BY o.id, o.market_order_id, o.total_price
        """, (order_id,))
        
        result = db_cursor.fetchone()
        assert result[0] == 'TEST_ORDER_001'
        assert result[1] == 40000
        assert result[2] == 2  # 2개 항목
        assert result[3] == 3  # 총 3개 수량
    
    @pytest.mark.db
    def test_inventory_tracking(self, db_cursor):
        """재고 추적 테스트"""
        # 상품 생성
        db_cursor.execute("""
            INSERT INTO unified_products (
                market_product_id, product_name, stock_quantity, market_code
            ) VALUES ('INV_TEST_001', '재고 테스트 상품', 100, 'coupang')
            RETURNING id, stock_quantity
        """)
        product_id, initial_stock = db_cursor.fetchone()
        
        # 재고 이력 테이블 생성 (없으면)
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_history (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES unified_products(id),
                change_type VARCHAR(50),
                change_quantity INTEGER,
                before_quantity INTEGER,
                after_quantity INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 재고 감소 (주문)
        order_quantity = 10
        db_cursor.execute("""
            UPDATE unified_products 
            SET stock_quantity = stock_quantity - %s
            WHERE id = %s AND stock_quantity >= %s
            RETURNING stock_quantity
        """, (order_quantity, product_id, order_quantity))
        
        new_stock = db_cursor.fetchone()[0]
        
        # 재고 이력 기록
        db_cursor.execute("""
            INSERT INTO inventory_history (
                product_id, change_type, change_quantity,
                before_quantity, after_quantity, reason
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (product_id, 'order', -order_quantity, initial_stock, new_stock, '주문 처리'))
        
        # 재고 증가 (입고)
        receive_quantity = 50
        db_cursor.execute("""
            UPDATE unified_products 
            SET stock_quantity = stock_quantity + %s
            WHERE id = %s
            RETURNING stock_quantity
        """, (receive_quantity, product_id))
        
        final_stock = db_cursor.fetchone()[0]
        
        db_cursor.execute("""
            INSERT INTO inventory_history (
                product_id, change_type, change_quantity,
                before_quantity, after_quantity, reason
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (product_id, 'receive', receive_quantity, new_stock, final_stock, '상품 입고'))
        
        db_cursor.connection.commit()
        
        # 재고 이력 확인
        db_cursor.execute("""
            SELECT 
                SUM(change_quantity) as total_change,
                COUNT(*) as change_count
            FROM inventory_history
            WHERE product_id = %s
        """, (product_id,))
        
        total_change, change_count = db_cursor.fetchone()
        
        assert final_stock == initial_stock - order_quantity + receive_quantity
        assert total_change == -order_quantity + receive_quantity
        assert change_count == 2
    
    @pytest.mark.db
    def test_market_raw_data_storage(self, db_cursor):
        """마켓 원본 데이터 저장 테스트"""
        raw_data = {
            'orderId': 'COUPANG-12345',
            'orderDate': '2024-01-15T10:00:00',
            'items': [
                {'productId': 'P001', 'quantity': 2, 'price': 10000},
                {'productId': 'P002', 'quantity': 1, 'price': 20000}
            ],
            'buyer': {
                'name': '구매자',
                'phone': '010-1234-5678',
                'email': 'buyer@example.com'
            }
        }
        
        db_cursor.execute("""
            INSERT INTO market_raw_data (
                market_code, data_type, raw_data, created_at
            ) VALUES (%s, %s, %s, %s)
            RETURNING id
        """, ('coupang', 'order', json.dumps(raw_data), datetime.now()))
        
        raw_data_id = db_cursor.fetchone()[0]
        db_cursor.connection.commit()
        
        # JSONB 쿼리 테스트
        db_cursor.execute("""
            SELECT 
                raw_data->>'orderId' as order_id,
                raw_data->'buyer'->>'name' as buyer_name,
                jsonb_array_length(raw_data->'items') as item_count
            FROM market_raw_data
            WHERE id = %s
        """, (raw_data_id,))
        
        result = db_cursor.fetchone()
        assert result[0] == 'COUPANG-12345'
        assert result[1] == '구매자'
        assert result[2] == 2
        
        # JSONB 인덱스를 사용한 검색
        db_cursor.execute("""
            SELECT COUNT(*)
            FROM market_raw_data
            WHERE market_code = 'coupang'
            AND raw_data @> %s
        """, (json.dumps({'orderId': 'COUPANG-12345'}),))
        
        count = db_cursor.fetchone()[0]
        assert count == 1
    
    @pytest.mark.db
    @pytest.mark.slow
    def test_concurrent_stock_update(self, db_connection):
        """동시 재고 업데이트 테스트"""
        import threading
        import time
        
        # 상품 생성
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO unified_products (
                market_product_id, product_name, stock_quantity, market_code
            ) VALUES ('CONCURRENT_TEST', '동시성 테스트 상품', 100, 'coupang')
            RETURNING id
        """)
        product_id = cursor.fetchone()[0]
        db_connection.commit()
        cursor.close()
        
        results = {'success': 0, 'failure': 0}
        
        def update_stock(thread_id):
            """재고 업데이트 함수"""
            conn = psycopg2.connect(**TEST_DB_CONFIG)
            cur = conn.cursor()
            
            try:
                # 재고 차감 시도
                cur.execute("""
                    UPDATE unified_products 
                    SET stock_quantity = stock_quantity - 1
                    WHERE id = %s AND stock_quantity > 0
                    RETURNING stock_quantity
                """, (product_id,))
                
                if cur.rowcount > 0:
                    results['success'] += 1
                else:
                    results['failure'] += 1
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                results['failure'] += 1
            finally:
                cur.close()
                conn.close()
        
        # 10개 스레드로 동시 업데이트
        threads = []
        for i in range(10):
            thread = threading.Thread(target=update_stock, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 최종 재고 확인
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT stock_quantity FROM unified_products WHERE id = %s
        """, (product_id,))
        final_stock = cursor.fetchone()[0]
        cursor.close()
        
        assert results['success'] == 10
        assert results['failure'] == 0
        assert final_stock == 90  # 100 - 10