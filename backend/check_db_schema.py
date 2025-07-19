#!/usr/bin/env python3
"""
데이터베이스 스키마 확인
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_schema():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # products 테이블 컬럼 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            logger.info("Products 테이블 구조:")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        else:
            logger.info("Products 테이블이 존재하지 않습니다.")
        
        # 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) as count FROM products")
        count = cursor.fetchone()
        logger.info(f"\n현재 products 테이블의 레코드 수: {count['count']}")
        
        # 공급사별 상품 수 확인
        cursor.execute("""
            SELECT market_code, COUNT(*) as count 
            FROM products 
            GROUP BY market_code
        """)
        
        suppliers = cursor.fetchall()
        if suppliers:
            logger.info("\n공급사별 상품 수:")
            for s in suppliers:
                logger.info(f"  - {s['market_code']}: {s['count']}개")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"스키마 확인 실패: {str(e)}")

if __name__ == "__main__":
    check_schema()