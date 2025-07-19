#!/usr/bin/env python3
"""
데이터베이스 연결 풀 통합 테스트
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import psycopg2
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.connection_pool import DatabasePool, init_database_pool, get_database_pool


class TestDatabasePool:
    """데이터베이스 풀 테스트"""
    
    @pytest.fixture
    def db_config(self):
        """테스트용 DB 설정"""
        return {
            'host': 'localhost',
            'port': 5434,
            'database': 'yoonni',
            'user': 'postgres',
            'password': '1234',
            'min_connections': 2,
            'max_connections': 5
        }
    
    @pytest.fixture
    def db_pool(self, db_config):
        """데이터베이스 풀 픽스처"""
        pool = DatabasePool(db_config)
        yield pool
        pool.close_all_connections()
    
    def test_singleton_pattern(self, db_config):
        """싱글톤 패턴 테스트"""
        pool1 = init_database_pool(db_config)
        pool2 = init_database_pool(db_config)
        
        assert pool1 is pool2
        assert get_database_pool() is pool1
    
    def test_connection_acquisition(self, db_pool):
        """연결 획득 테스트"""
        with db_pool.get_connection() as conn:
            assert conn is not None
            assert not conn.closed
            
            # 간단한 쿼리 실행
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            cursor.close()
    
    def test_concurrent_connections(self, db_pool):
        """동시 연결 테스트"""
        results = []
        
        def execute_query(pool, query_id):
            try:
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT %s, pg_sleep(0.1)", (query_id,))
                    result = cursor.fetchone()
                    cursor.close()
                    results.append((query_id, result[0]))
                    return True
            except Exception as e:
                print(f"Query {query_id} failed: {e}")
                return False
        
        # 최대 연결 수보다 많은 동시 요청
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(execute_query, db_pool, i)
                futures.append(future)
            
            # 모든 작업 완료 대기
            for future in futures:
                assert future.result() is True
        
        # 모든 쿼리가 성공했는지 확인
        assert len(results) == 10
        assert all(query_id == result for query_id, result in results)
    
    def test_connection_retry(self, db_pool):
        """연결 재시도 테스트"""
        # 연결 풀 소진 시뮬레이션
        connections = []
        
        # 모든 연결 획득
        for _ in range(db_pool._pool.maxconn):
            conn = db_pool._pool.getconn()
            connections.append(conn)
        
        # 추가 연결 시도 (재시도 로직 테스트)
        start_time = time.time()
        
        try:
            with db_pool.get_connection(retry_count=2) as conn:
                # 이 부분은 실행되지 않아야 함
                assert False, "연결이 획득되면 안됨"
        except psycopg2.pool.PoolError:
            # 예상된 에러
            elapsed = time.time() - start_time
            # 재시도로 인한 지연 확인 (최소 0.5초)
            assert elapsed >= 0.5
        
        # 연결 반환
        for conn in connections:
            db_pool._pool.putconn(conn)
    
    def test_query_execution_helpers(self, db_pool):
        """쿼리 실행 헬퍼 테스트"""
        # SELECT 쿼리 - fetch_all
        result = db_pool.execute_query(
            "SELECT * FROM generate_series(1, 3) as num",
            fetch_all=True
        )
        assert len(result) == 3
        assert result[0][0] == 1
        
        # SELECT 쿼리 - fetch_one
        result = db_pool.execute_query(
            "SELECT 42 as answer",
            fetch_one=True
        )
        assert result[0] == 42
        
        # INSERT/UPDATE 시뮬레이션 (실제로는 테이블 생성 필요)
        # 여기서는 rowcount 테스트를 위해 임시 테이블 사용
        db_pool.execute_query("""
            CREATE TEMP TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """)
        
        rowcount = db_pool.execute_query(
            "INSERT INTO test_table (value) VALUES (%s), (%s)",
            ('test1', 'test2')
        )
        assert rowcount == 2
    
    def test_transaction_rollback(self, db_pool):
        """트랜잭션 롤백 테스트"""
        # 임시 테이블 생성
        db_pool.execute_query("""
            CREATE TEMP TABLE IF NOT EXISTS test_rollback (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # 실패하는 트랜잭션
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute("INSERT INTO test_rollback (value) VALUES (%s)", ('test',))
                # NULL 제약 조건 위반
                cursor.execute("INSERT INTO test_rollback (value) VALUES (%s)", (None,))
        except Exception:
            # 예상된 에러
            pass
        
        # 롤백 확인
        result = db_pool.execute_query(
            "SELECT COUNT(*) FROM test_rollback",
            fetch_one=True
        )
        assert result[0] == 0  # 롤백되어 데이터 없음
    
    def test_pool_status(self, db_pool):
        """풀 상태 조회 테스트"""
        status = db_pool.get_pool_status()
        
        assert 'min_connections' in status
        assert 'max_connections' in status
        assert 'available_connections' in status
        assert status['min_connections'] == 2
        assert status['max_connections'] == 5


@pytest.mark.asyncio
class TestDatabasePoolAsync:
    """비동기 환경에서의 데이터베이스 풀 테스트"""
    
    @pytest.fixture
    def db_config(self):
        return {
            'host': 'localhost',
            'port': 5434,
            'database': 'yoonni',
            'user': 'postgres',
            'password': '1234',
            'min_connections': 2,
            'max_connections': 5
        }
    
    async def test_async_concurrent_access(self, db_config):
        """비동기 동시 접근 테스트"""
        pool = DatabasePool(db_config)
        
        async def async_query(query_id):
            # 동기 작업을 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            
            def sync_work():
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT %s, pg_sleep(0.05)", (query_id,))
                    result = cursor.fetchone()
                    cursor.close()
                    return result[0]
            
            result = await loop.run_in_executor(None, sync_work)
            return result
        
        # 동시에 여러 쿼리 실행
        tasks = [async_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(i == results[i] for i in range(10))
        
        pool.close_all_connections()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])