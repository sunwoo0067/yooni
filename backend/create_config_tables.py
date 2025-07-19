#!/usr/bin/env python3
"""
시스템 설정 테이블 생성 스크립트
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_config_tables():
    """시스템 설정 테이블 생성"""
    
    # DB 연결
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5434),
        database=os.getenv('DB_NAME', 'yoonni'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '1234')
    )
    conn.autocommit = True
    
    try:
        # SQL 파일 읽기
        with open('database/schema/system_config_tables.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 실행
        with conn.cursor() as cursor:
            cursor.execute(sql)
        
        print("시스템 설정 테이블 생성 완료!")
        
        # 테이블 확인
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'system_config%'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            print("\n생성된 테이블:")
            for table in tables:
                print(f"  - {table[0]}")
    
    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_config_tables()