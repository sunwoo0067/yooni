#!/usr/bin/env python3
"""
마켓 테이블 초기화 및 재생성
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def reset_and_create_tables():
    """마켓 테이블 초기화 및 재생성"""
    
    # 데이터베이스 연결
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5434),
        database=os.getenv('DB_NAME', 'yoonni'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '1234')
    )
    
    try:
        cursor = conn.cursor()
        conn.autocommit = True
        
        print("기존 테이블 삭제 중...")
        
        # 기존 테이블 삭제
        cursor.execute("""
            DROP TABLE IF EXISTS 
                market_shipments, 
                market_order_items, 
                market_orders, 
                market_settlements,
                market_products, 
                market_accounts, 
                markets 
            CASCADE
        """)
        
        print("새 테이블 생성 중...")
        
        # 1. 마켓 정의 테이블
        cursor.execute("""
            CREATE TABLE markets (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 기본 마켓 데이터 삽입
        cursor.execute("""
            INSERT INTO markets (code, name, description) VALUES
            ('coupang', '쿠팡', '쿠팡 파트너스 마켓플레이스'),
            ('naver', '네이버 스마트스토어', '네이버 커머스 플랫폼'),
            ('11st', '11번가', '11번가 오픈마켓'),
            ('gmarket', 'G마켓', 'G마켓 오픈마켓'),
            ('auction', '옥션', '옥션 오픈마켓')
        """)
        
        # 2. 마켓 계정 테이블
        cursor.execute("""
            CREATE TABLE market_accounts (
                id SERIAL PRIMARY KEY,
                market_id INTEGER REFERENCES markets(id),
                account_name VARCHAR(200) NOT NULL,
                api_key VARCHAR(500),
                api_secret VARCHAR(500),
                vendor_id VARCHAR(200),
                extra_config JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(market_id, account_name)
            )
        """)
        
        # 3. 마켓 상품 테이블
        cursor.execute("""
            CREATE TABLE market_products (
                id SERIAL PRIMARY KEY,
                market_id INTEGER REFERENCES markets(id),
                market_account_id INTEGER REFERENCES market_accounts(id),
                market_product_id VARCHAR(200) NOT NULL,
                unified_product_id INTEGER,
                product_name VARCHAR(500) NOT NULL,
                brand VARCHAR(200),
                manufacturer VARCHAR(200),
                model_name VARCHAR(200),
                original_price DECIMAL(15, 2),
                sale_price DECIMAL(15, 2),
                discount_rate DECIMAL(5, 2),
                status VARCHAR(50),
                stock_quantity INTEGER DEFAULT 0,
                category_code VARCHAR(100),
                category_name VARCHAR(500),
                category_path TEXT,
                shipping_type VARCHAR(50),
                shipping_fee DECIMAL(10, 2),
                market_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced_at TIMESTAMP,
                UNIQUE(market_account_id, market_product_id)
            )
        """)
        
        # 4. 마켓 주문 테이블
        cursor.execute("""
            CREATE TABLE market_orders (
                id SERIAL PRIMARY KEY,
                market_id INTEGER REFERENCES markets(id),
                market_account_id INTEGER REFERENCES market_accounts(id),
                market_order_id VARCHAR(200) NOT NULL,
                order_date TIMESTAMP NOT NULL,
                payment_date TIMESTAMP,
                buyer_name VARCHAR(100),
                buyer_email VARCHAR(200),
                buyer_phone VARCHAR(50),
                receiver_name VARCHAR(100),
                receiver_phone VARCHAR(50),
                receiver_address TEXT,
                receiver_zipcode VARCHAR(20),
                delivery_message TEXT,
                order_status VARCHAR(50),
                payment_method VARCHAR(50),
                total_price DECIMAL(15, 2),
                product_price DECIMAL(15, 2),
                discount_amount DECIMAL(15, 2),
                shipping_fee DECIMAL(10, 2),
                market_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced_at TIMESTAMP,
                UNIQUE(market_account_id, market_order_id)
            )
        """)
        
        # 5. 마켓 주문 상품 테이블
        cursor.execute("""
            CREATE TABLE market_order_items (
                id SERIAL PRIMARY KEY,
                market_order_id INTEGER REFERENCES market_orders(id),
                market_product_id VARCHAR(200),
                product_name VARCHAR(500),
                option_name VARCHAR(500),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(15, 2),
                total_price DECIMAL(15, 2),
                item_status VARCHAR(50),
                tracking_company VARCHAR(100),
                tracking_number VARCHAR(100),
                shipped_date TIMESTAMP,
                delivered_date TIMESTAMP,
                item_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. 마켓 배송 테이블
        cursor.execute("""
            CREATE TABLE market_shipments (
                id SERIAL PRIMARY KEY,
                market_order_id INTEGER REFERENCES market_orders(id),
                shipment_type VARCHAR(50),
                tracking_company VARCHAR(100),
                tracking_number VARCHAR(100),
                shipment_status VARCHAR(50),
                shipped_date TIMESTAMP,
                estimated_delivery_date DATE,
                delivered_date TIMESTAMP,
                receiver_name VARCHAR(100),
                receiver_phone VARCHAR(50),
                receiver_address TEXT,
                receiver_zipcode VARCHAR(20),
                shipment_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 7. 마켓 정산 테이블
        cursor.execute("""
            CREATE TABLE market_settlements (
                id SERIAL PRIMARY KEY,
                market_id INTEGER REFERENCES markets(id),
                market_account_id INTEGER REFERENCES market_accounts(id),
                settlement_date DATE NOT NULL,
                settlement_amount DECIMAL(15, 2),
                sales_amount DECIMAL(15, 2),
                commission_amount DECIMAL(15, 2),
                shipping_fee_amount DECIMAL(15, 2),
                promotion_amount DECIMAL(15, 2),
                adjustment_amount DECIMAL(15, 2),
                settlement_status VARCHAR(50),
                settlement_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(market_account_id, settlement_date)
            )
        """)
        
        # 인덱스 생성
        print("인덱스 생성 중...")
        
        cursor.execute("CREATE INDEX idx_market_products_market_id ON market_products(market_id)")
        cursor.execute("CREATE INDEX idx_market_products_status ON market_products(status)")
        cursor.execute("CREATE INDEX idx_market_products_unified_id ON market_products(unified_product_id)")
        cursor.execute("CREATE INDEX idx_market_products_updated ON market_products(updated_at)")
        
        cursor.execute("CREATE INDEX idx_market_orders_market_id ON market_orders(market_id)")
        cursor.execute("CREATE INDEX idx_market_orders_order_date ON market_orders(order_date)")
        cursor.execute("CREATE INDEX idx_market_orders_status ON market_orders(order_status)")
        cursor.execute("CREATE INDEX idx_market_orders_buyer_phone ON market_orders(buyer_phone)")
        
        cursor.execute("CREATE INDEX idx_market_order_items_status ON market_order_items(item_status)")
        cursor.execute("CREATE INDEX idx_market_order_items_tracking ON market_order_items(tracking_number)")
        
        cursor.execute("CREATE INDEX idx_market_shipments_status ON market_shipments(shipment_status)")
        cursor.execute("CREATE INDEX idx_market_shipments_tracking ON market_shipments(tracking_number)")
        
        # 트리거 함수 생성
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        # 트리거 생성
        tables_with_updated_at = [
            'market_accounts', 'market_products', 'market_orders', 
            'market_order_items', 'market_shipments'
        ]
        
        for table in tables_with_updated_at:
            cursor.execute(f"""
                CREATE TRIGGER update_{table}_updated_at 
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """)
        
        print("✅ 마켓 공통 테이블 생성 완료!")
        
        # 생성된 테이블 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'market%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\n생성된 테이블 목록:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 마켓 데이터 확인
        cursor.execute("SELECT code, name FROM markets ORDER BY code")
        markets = cursor.fetchall()
        print("\n등록된 마켓:")
        for market in markets:
            print(f"  - {market[0]}: {market[1]}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    reset_and_create_tables()