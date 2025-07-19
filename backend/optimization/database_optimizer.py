#!/usr/bin/env python3
"""
데이터베이스 최적화 도구
- 인덱스 최적화
- 파티셔닝 구현
- 쿼리 성능 분석
- 자동 VACUUM 및 ANALYZE
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """데이터베이스 최적화 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        self.conn.autocommit = True
    
    def analyze_table_sizes(self) -> List[Dict[str, Any]]:
        """테이블 크기 분석"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes,
                    n_live_tup AS row_count,
                    n_dead_tup AS dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
            """)
            
            tables = cursor.fetchall()
            
            logger.info("📊 테이블 크기 분석:")
            for table in tables[:10]:
                logger.info(f"   {table['tablename']}: {table['size']} "
                          f"(행: {table['row_count']:,}, 데드: {table['dead_rows']:,})")
            
            return tables
    
    def optimize_indexes(self):
        """인덱스 최적화"""
        logger.info("🔧 인덱스 최적화 시작...")
        
        # 1. 사용되지 않는 인덱스 찾기
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexrelname NOT LIKE 'pg_toast%'
                ORDER BY pg_relation_size(indexrelid) DESC
            """)
            
            unused_indexes = cursor.fetchall()
            
            if unused_indexes:
                logger.warning(f"⚠️ 사용되지 않는 인덱스 {len(unused_indexes)}개 발견:")
                for idx in unused_indexes[:5]:
                    logger.warning(f"   - {idx['indexname']} on {idx['tablename']} ({idx['index_size']})")
            
            # 2. 누락된 인덱스 제안
            self._suggest_missing_indexes()
            
            # 3. 복합 인덱스 최적화
            self._optimize_composite_indexes()
    
    def _suggest_missing_indexes(self):
        """누락된 인덱스 제안"""
        suggestions = []
        
        # supplier_products 테이블 최적화
        suggestions.append(
            "CREATE INDEX IF NOT EXISTS idx_supplier_products_status_category "
            "ON supplier_products(status, category) WHERE status = 'active';"
        )
        
        suggestions.append(
            "CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier_collected "
            "ON supplier_products(supplier_id, collected_at DESC);"
        )
        
        # supplier_collection_logs 최적화
        suggestions.append(
            "CREATE INDEX IF NOT EXISTS idx_collection_logs_supplier_started "
            "ON supplier_collection_logs(supplier_id, started_at DESC);"
        )
        
        # AI 분석 테이블 최적화
        suggestions.append(
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_updated "
            "ON supplier_product_analysis(updated_at DESC) "
            "WHERE analysis_type = 'price_demand';"
        )
        
        logger.info("💡 인덱스 생성 제안:")
        for suggestion in suggestions:
            logger.info(f"   {suggestion[:60]}...")
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(suggestion)
                logger.info("   ✅ 생성 완료")
            except Exception as e:
                logger.error(f"   ❌ 실패: {e}")
    
    def _optimize_composite_indexes(self):
        """복합 인덱스 최적화"""
        # 자주 사용되는 쿼리 패턴에 대한 복합 인덱스
        with self.conn.cursor() as cursor:
            # JSONB 인덱스 최적화
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_supplier_products_jsonb_gin 
                ON supplier_products USING gin (product_data);
            """)
            
            # 부분 인덱스 생성 (활성 상품만)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_active_products_category 
                ON supplier_products(category, price) 
                WHERE status = 'active';
            """)
            
            logger.info("✅ 복합 인덱스 최적화 완료")
    
    def setup_partitioning(self):
        """테이블 파티셔닝 설정"""
        logger.info("📅 파티셔닝 설정 시작...")
        
        # supplier_collection_logs 월별 파티셔닝
        current_month = datetime.now().strftime('%Y_%m')
        next_month = (datetime.now() + timedelta(days=32)).strftime('%Y_%m')
        
        try:
            with self.conn.cursor() as cursor:
                # 파티션 테이블 생성
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS supplier_collection_logs_{current_month} 
                    PARTITION OF supplier_collection_logs
                    FOR VALUES FROM ('{datetime.now().strftime('%Y-%m-01')}') 
                    TO ('{(datetime.now() + timedelta(days=32)).strftime('%Y-%m-01')}');
                """)
                
                # 다음 달 파티션 미리 생성
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS supplier_collection_logs_{next_month} 
                    PARTITION OF supplier_collection_logs
                    FOR VALUES FROM ('{(datetime.now() + timedelta(days=32)).strftime('%Y-%m-01')}') 
                    TO ('{(datetime.now() + timedelta(days=62)).strftime('%Y-%m-01')}');
                """)
                
                logger.info(f"✅ 파티션 생성 완료: {current_month}, {next_month}")
                
        except Exception as e:
            if "is not partitioned" in str(e):
                logger.warning("⚠️ 파티셔닝을 위해서는 테이블 재생성이 필요합니다")
                self._create_partitioned_table_script()
            else:
                logger.error(f"파티셔닝 실패: {e}")
    
    def _create_partitioned_table_script(self):
        """파티션 테이블 생성 스크립트 출력"""
        script = """
-- 파티션 테이블로 마이그레이션 스크립트
-- 주의: 실행 전 백업 필수!

-- 1. 새로운 파티션 테이블 생성
CREATE TABLE supplier_collection_logs_new (
    LIKE supplier_collection_logs INCLUDING ALL
) PARTITION BY RANGE (started_at);

-- 2. 월별 파티션 생성 (최근 6개월)
CREATE TABLE supplier_collection_logs_2025_01 PARTITION OF supplier_collection_logs_new
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE supplier_collection_logs_2025_02 PARTITION OF supplier_collection_logs_new
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- 이전 달들도 동일하게...

-- 3. 데이터 마이그레이션
INSERT INTO supplier_collection_logs_new SELECT * FROM supplier_collection_logs;

-- 4. 테이블 교체
ALTER TABLE supplier_collection_logs RENAME TO supplier_collection_logs_old;
ALTER TABLE supplier_collection_logs_new RENAME TO supplier_collection_logs;

-- 5. 이전 테이블 삭제 (확인 후)
-- DROP TABLE supplier_collection_logs_old;
        """
        
        logger.info("📝 파티션 테이블 마이그레이션 스크립트:")
        print(script)
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """느린 쿼리 분석"""
        logger.info("🐌 느린 쿼리 분석...")
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    stddev_exec_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > 100  -- 100ms 이상
                AND query NOT LIKE '%pg_stat%'
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """)
            
            slow_queries = cursor.fetchall()
            
            if slow_queries:
                logger.warning(f"⚠️ 느린 쿼리 {len(slow_queries)}개 발견:")
                for i, query in enumerate(slow_queries[:5], 1):
                    logger.warning(f"\n{i}. 평균 실행시간: {query['mean_exec_time']:.1f}ms")
                    logger.warning(f"   호출 횟수: {query['calls']}")
                    logger.warning(f"   쿼리: {query['query'][:100]}...")
            
            return slow_queries
    
    def vacuum_and_analyze(self, full_vacuum: bool = False):
        """VACUUM 및 ANALYZE 실행"""
        logger.info("🧹 VACUUM 및 ANALYZE 실행...")
        
        tables = [
            'supplier_products',
            'supplier_collection_logs',
            'supplier_product_analysis',
            'suppliers',
            'supplier_configs'
        ]
        
        for table in tables:
            try:
                with self.conn.cursor() as cursor:
                    if full_vacuum:
                        logger.info(f"   VACUUM FULL {table}...")
                        cursor.execute(f"VACUUM FULL ANALYZE {table}")
                    else:
                        logger.info(f"   VACUUM ANALYZE {table}...")
                        cursor.execute(f"VACUUM ANALYZE {table}")
                    
                logger.info(f"   ✅ {table} 완료")
                
            except Exception as e:
                logger.error(f"   ❌ {table} 실패: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """최적화 보고서 생성"""
        logger.info("📊 최적화 보고서 생성...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_size": self._get_database_size(),
            "table_sizes": self.analyze_table_sizes()[:5],
            "index_usage": self._get_index_usage_stats(),
            "cache_hit_ratio": self._get_cache_hit_ratio(),
            "connection_stats": self._get_connection_stats(),
            "recommendations": []
        }
        
        # 권장사항 생성
        if report['cache_hit_ratio'] < 90:
            report['recommendations'].append(
                "캐시 히트율이 낮습니다. shared_buffers 증가를 고려하세요."
            )
        
        if report['connection_stats']['idle_in_transaction'] > 5:
            report['recommendations'].append(
                "idle in transaction 연결이 많습니다. 트랜잭션 관리를 확인하세요."
            )
        
        # 큰 테이블 확인
        for table in report['table_sizes']:
            if table['dead_rows'] > table['row_count'] * 0.1:
                report['recommendations'].append(
                    f"{table['tablename']} 테이블의 dead rows가 많습니다. VACUUM을 실행하세요."
                )
        
        return report
    
    def _get_database_size(self) -> str:
        """데이터베이스 크기 조회"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT pg_size_pretty(pg_database_size('yoonni'))")
            return cursor.fetchone()[0]
    
    def _get_index_usage_stats(self) -> Dict[str, Any]:
        """인덱스 사용 통계"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_indexes,
                    COUNT(CASE WHEN idx_scan = 0 THEN 1 END) as unused_indexes,
                    AVG(idx_scan) as avg_scans
                FROM pg_stat_user_indexes
            """)
            return cursor.fetchone()
    
    def _get_cache_hit_ratio(self) -> float:
        """캐시 히트율 계산"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 
                    as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            result = cursor.fetchone()
            return float(result['cache_hit_ratio'] or 0)
    
    def _get_connection_stats(self) -> Dict[str, int]:
        """연결 통계"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    state,
                    COUNT(*) as count
                FROM pg_stat_activity
                GROUP BY state
            """)
            
            stats = {row['state']: row['count'] for row in cursor.fetchall() if row['state']}
            stats['total'] = sum(stats.values())
            return stats

def main():
    """메인 실행 함수"""
    optimizer = DatabaseOptimizer()
    
    # 1. 최적화 보고서
    report = optimizer.get_optimization_report()
    print("\n📊 데이터베이스 최적화 보고서")
    print(f"데이터베이스 크기: {report['database_size']}")
    print(f"캐시 히트율: {report['cache_hit_ratio']:.1f}%")
    print(f"총 인덱스: {report['index_usage']['total_indexes']}")
    print(f"미사용 인덱스: {report['index_usage']['unused_indexes']}")
    
    if report['recommendations']:
        print("\n💡 권장사항:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    # 2. 인덱스 최적화
    optimizer.optimize_indexes()
    
    # 3. 느린 쿼리 분석
    optimizer.analyze_slow_queries()
    
    # 4. VACUUM 실행 (필요시)
    # optimizer.vacuum_and_analyze()

if __name__ == "__main__":
    main()