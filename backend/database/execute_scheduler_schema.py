#!/usr/bin/env python3
"""
스케줄러 테이블 생성 스크립트
"""
import psycopg2
import sys
from pathlib import Path

# DB 연결 정보
db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres', 
    'password': '1234'
}

def execute_sql_file(filename):
    """SQL 파일 실행"""
    sql_file = Path(__file__).parent / 'schema' / filename
    
    if not sql_file.exists():
        print(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
        return False
        
    try:
        # DB 연결
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        # SQL 파일 읽기
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # SQL 실행
        cur.execute(sql_content)
        
        print(f"✓ {filename} 실행 완료")
        
        # 생성된 테이블 확인
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'schedule_%' OR table_name LIKE 'job_%'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        print("\n생성된 테이블:")
        for table in tables:
            print(f"  - {table[0]}")
            
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("스케줄러 테이블 생성 시작...")
    
    if execute_sql_file('scheduler_tables.sql'):
        print("\n스케줄러 테이블 생성 완료!")
    else:
        print("\n스케줄러 테이블 생성 실패!")
        sys.exit(1)