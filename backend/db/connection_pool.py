#!/usr/bin/env python3
"""
데이터베이스 연결 풀 관리
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import time
import logging
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)


class DatabasePool:
    """스레드 안전한 데이터베이스 연결 풀"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any]):
        if hasattr(self, '_initialized'):
            return
            
        self.config = config
        self._pool = None
        self._create_pool()
        self._initialized = True
        
    def _create_pool(self):
        """연결 풀 생성"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.get('min_connections', 2),
                maxconn=self.config.get('max_connections', 20),
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                connect_timeout=self.config.get('connect_timeout', 10),
                options='-c statement_timeout=30000'  # 30초 쿼리 타임아웃
            )
            logger.info("데이터베이스 연결 풀 생성 완료")
        except Exception as e:
            logger.error(f"연결 풀 생성 실패: {e}")
            raise
    
    @contextmanager
    def get_connection(self, retry_count: int = 3):
        """연결 풀에서 연결 가져오기"""
        connection = None
        attempt = 0
        
        while attempt < retry_count:
            try:
                connection = self._pool.getconn()
                yield connection
                break
            except psycopg2.pool.PoolError as e:
                attempt += 1
                if attempt >= retry_count:
                    logger.error(f"연결 풀에서 연결 획득 실패: {e}")
                    raise
                time.sleep(0.5 * attempt)  # 지수 백오프
            except Exception as e:
                logger.error(f"데이터베이스 연결 오류: {e}")
                if connection:
                    self._pool.putconn(connection, close=True)
                raise
            finally:
                if connection:
                    self._pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """커서 컨텍스트 매니저"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"쿼리 실행 오류: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = True):
        """쿼리 실행 헬퍼"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            
            if cursor.description is None:  # INSERT, UPDATE, DELETE
                return cursor.rowcount
            elif fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor
    
    def close_all_connections(self):
        """모든 연결 종료"""
        if self._pool:
            self._pool.closeall()
            logger.info("모든 데이터베이스 연결 종료")
    
    def get_pool_status(self) -> Dict[str, int]:
        """연결 풀 상태 조회"""
        if not self._pool:
            return {"error": "Pool not initialized"}
            
        return {
            "min_connections": self._pool.minconn,
            "max_connections": self._pool.maxconn,
            "closed_connections": len(self._pool._closed),
            "used_connections": len(self._pool._used),
            "available_connections": len(self._pool._pool)
        }


# 싱글톤 인스턴스
_db_pool: Optional[DatabasePool] = None


def init_database_pool(config: Dict[str, Any]) -> DatabasePool:
    """데이터베이스 풀 초기화"""
    global _db_pool
    if not _db_pool:
        _db_pool = DatabasePool(config)
    return _db_pool


def get_database_pool() -> DatabasePool:
    """데이터베이스 풀 가져오기"""
    if not _db_pool:
        raise RuntimeError("데이터베이스 풀이 초기화되지 않았습니다.")
    return _db_pool