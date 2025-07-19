#!/usr/bin/env python3
"""
상품 테이블 생성 스크립트
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_products_table():
    """상품 테이블 생성"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                supplier_product_id VARCHAR(100) UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                brand VARCHAR(200),
                category_name VARCHAR(200),
                sale_price DECIMAL(12, 2),
                cost_price DECIMAL(12, 2),
                stock_quantity INTEGER DEFAULT 0,
                status VARCHAR(50),
                weight INTEGER,
                barcode VARCHAR(100),
                supplier_code VARCHAR(50),
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_supplier_code ON products(supplier_code);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_name);")
        
        conn.commit()
        logger.info("상품 테이블 생성 완료")
        
        # 테이블 정보 확인
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info("상품 테이블 컬럼:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"테이블 생성 실패: {str(e)}")

if __name__ == "__main__":
    create_products_table()