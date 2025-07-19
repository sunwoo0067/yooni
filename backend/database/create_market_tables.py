#!/usr/bin/env python3
"""
마켓 공통 테이블 생성 스크립트
"""
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def create_market_tables():
    """마켓 공통 테이블 생성"""
    
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
        
        # SQL 파일 읽기
        schema_path = Path(__file__).parent / 'schema' / 'market_common_tables.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 자동 커밋 모드로 변경
        conn.autocommit = True
        
        # SQL 문을 세미콜론으로 분리하여 개별 실행
        sql_statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(sql_statements):
            try:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement + ';')
                    success_count += 1
            except psycopg2.Error as e:
                error_count += 1
                error_msg = str(e)
                # 이미 존재하는 테이블/인덱스는 무시
                if 'already exists' in error_msg:
                    print(f"  ℹ️  Already exists (statement {i})")
                # ON CONFLICT 에러도 무시
                elif 'no unique or exclusion constraint' in error_msg:
                    # markets 테이블에 대한 INSERT를 수동으로 처리
                    if 'INSERT INTO markets' in statement:
                        try:
                            cursor.execute("""
                                INSERT INTO markets (code, name, description) 
                                SELECT 'coupang', '쿠팡', '쿠팡 파트너스 마켓플레이스'
                                WHERE NOT EXISTS (SELECT 1 FROM markets WHERE code = 'coupang')
                            """)
                            cursor.execute("""
                                INSERT INTO markets (code, name, description) 
                                SELECT 'naver', '네이버 스마트스토어', '네이버 커머스 플랫폼'
                                WHERE NOT EXISTS (SELECT 1 FROM markets WHERE code = 'naver')
                            """)
                            cursor.execute("""
                                INSERT INTO markets (code, name, description) 
                                SELECT '11st', '11번가', '11번가 오픈마켓'
                                WHERE NOT EXISTS (SELECT 1 FROM markets WHERE code = '11st')
                            """)
                            success_count += 1
                        except:
                            pass
                else:
                    print(f"  ❌ Statement {i} error: {error_msg[:100]}...")
        
        print(f"\n실행 결과: 성공 {success_count}개, 스킵 {error_count}개")
        
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
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_market_tables()