#!/usr/bin/env python3
"""
데이터베이스 테이블 분석 스크립트
파티셔닝이 필요한 테이블 식별
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import sys

# DB 연결 정보
db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres', 
    'password': '1234'
}

def analyze_tables():
    """테이블 크기 및 레코드 수 분석"""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 테이블별 크기 및 레코드 수 조회
        query = """
        WITH table_sizes AS (
            SELECT 
                n.nspname AS schemaname,
                c.relname AS tablename,
                pg_total_relation_size(c.oid) AS total_size,
                pg_relation_size(c.oid) AS table_size,
                pg_total_relation_size(c.oid) - pg_relation_size(c.oid) AS indexes_size
            FROM pg_class c
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')  -- regular tables and partitioned tables
            AND n.nspname = 'public'
        )
        SELECT 
            ts.schemaname,
            ts.tablename,
            pg_size_pretty(ts.total_size) AS total_size,
            pg_size_pretty(ts.table_size) AS table_size,
            pg_size_pretty(ts.indexes_size) AS indexes_size,
            COALESCE(s.n_live_tup, 0) as row_count,
            COALESCE(s.n_dead_tup, 0) as dead_rows,
            s.last_autovacuum,
            CASE 
                WHEN COALESCE(s.n_live_tup, 0) > 1000000 THEN 'HIGH'
                WHEN COALESCE(s.n_live_tup, 0) > 100000 THEN 'MEDIUM'
                ELSE 'LOW'
            END as partition_priority
        FROM table_sizes ts
        LEFT JOIN pg_stat_user_tables s ON s.schemaname = ts.schemaname AND s.relname = ts.tablename
        ORDER BY ts.total_size DESC;
        """
        
        cur.execute(query)
        tables = cur.fetchall()
        
        print("="*100)
        print("데이터베이스 테이블 분석 보고서")
        print(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        print()
        
        # 파티셔닝 필요 테이블
        high_priority_tables = []
        medium_priority_tables = []
        
        print("## 테이블 크기 분석")
        print("-"*100)
        print(f"{'테이블명':<30} {'전체크기':>12} {'테이블크기':>12} {'인덱스크기':>12} {'레코드수':>12} {'우선순위':>10}")
        print("-"*100)
        
        for table in tables:
            print(f"{table['tablename']:<30} {table['total_size']:>12} {table['table_size']:>12} {table['indexes_size']:>12} {table['row_count']:>12,} {table['partition_priority']:>10}")
            
            if table['partition_priority'] == 'HIGH':
                high_priority_tables.append(table)
            elif table['partition_priority'] == 'MEDIUM':
                medium_priority_tables.append(table)
        
        print()
        print("## 파티셔닝 권장 사항")
        print("-"*100)
        
        if high_priority_tables:
            print("\n### 즉시 파티셔닝 필요 (100만 레코드 이상):")
            for table in high_priority_tables:
                print(f"  - {table['tablename']}: {table['row_count']:,} 레코드, {table['total_size']}")
                
                # 테이블별 파티셔닝 전략 제안
                if 'orders' in table['tablename']:
                    print(f"    → 권장: 월별 범위 파티셔닝 (order_date 기준)")
                elif 'products' in table['tablename']:
                    print(f"    → 권장: 마켓별 리스트 파티셔닝 (market_code 기준)")
                elif 'raw_data' in table['tablename']:
                    print(f"    → 권장: 월별 범위 파티셔닝 (created_at 기준)")
                elif 'executions' in table['tablename'] or 'logs' in table['tablename']:
                    print(f"    → 권장: 월별 범위 파티셔닝 (created_at 기준)")
        
        if medium_priority_tables:
            print("\n### 파티셔닝 고려 대상 (10만 레코드 이상):")
            for table in medium_priority_tables:
                print(f"  - {table['tablename']}: {table['row_count']:,} 레코드, {table['total_size']}")
        
        # 날짜 컬럼 분석
        print("\n## 파티셔닝 키 후보 분석")
        print("-"*100)
        
        for table in high_priority_tables + medium_priority_tables:
            print(f"\n### {table['tablename']} 테이블:")
            
            # 컬럼 정보 조회
            column_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = %s
            AND (
                data_type IN ('timestamp', 'timestamp with time zone', 'date') OR
                column_name LIKE '%_date' OR 
                column_name LIKE '%_at' OR
                column_name IN ('market_code', 'market_id', 'status', 'job_type')
            )
            ORDER BY ordinal_position;
            """
            
            cur.execute(column_query, (table['tablename'],))
            columns = cur.fetchall()
            
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")
        
        # 기존 인덱스 분석
        print("\n## 기존 인덱스 분석")
        print("-"*100)
        
        index_query = """
        SELECT 
            t.tablename,
            i.indexname,
            i.indexdef,
            pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size
        FROM pg_indexes i
        JOIN pg_stat_user_indexes ui ON i.indexname = ui.indexrelname
        JOIN pg_stat_user_tables t ON ui.relid = t.relid
        WHERE i.schemaname = 'public'
        AND t.relname IN %s
        ORDER BY t.tablename, i.indexname;
        """
        
        target_tables = [t['tablename'] for t in high_priority_tables + medium_priority_tables]
        if target_tables:
            cur.execute(index_query, (tuple(target_tables),))
            indexes = cur.fetchall()
            
            current_table = None
            for idx in indexes:
                if current_table != idx['tablename']:
                    current_table = idx['tablename']
                    print(f"\n{current_table}:")
                print(f"  - {idx['indexname']} ({idx['index_size']})")
        
        cur.close()
        conn.close()
        
        return high_priority_tables
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return []

if __name__ == "__main__":
    high_priority_tables = analyze_tables()
    
    if high_priority_tables:
        print("\n" + "="*100)
        print("파티셔닝 구현이 필요합니다!")
        print("="*100)