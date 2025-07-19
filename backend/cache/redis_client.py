#!/usr/bin/env python3
"""
Redis 클라이언트
"""
import redis
import json
import pickle
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis 연결 및 기본 작업을 관리하는 클라이언트
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None,
                 decode_responses: bool = False, connection_pool_kwargs: Optional[Dict] = None):
        """
        Redis 클라이언트 초기화
        
        Args:
            host: Redis 호스트
            port: Redis 포트
            db: 데이터베이스 번호
            password: Redis 비밀번호
            decode_responses: 응답 디코딩 여부
            connection_pool_kwargs: 연결 풀 설정
        """
        pool_kwargs = {
            'host': host,
            'port': port,
            'db': db,
            'password': password,
            'decode_responses': decode_responses,
            'max_connections': 50,
            'socket_keepalive': True,
            'socket_keepalive_options': {
                1: 1,  # TCP_KEEPIDLE
                2: 1,  # TCP_KEEPINTVL
                3: 5,  # TCP_KEEPCNT
            }
        }
        
        if connection_pool_kwargs:
            pool_kwargs.update(connection_pool_kwargs)
        
        self.pool = redis.ConnectionPool(**pool_kwargs)
        self._client = None
        self.default_ttl = 3600  # 1시간
        
    @property
    def client(self) -> redis.Redis:
        """Redis 클라이언트 인스턴스 반환"""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self.pool)
        return self._client
    
    def get(self, key: str, default: Any = None) -> Any:
        """키 값 조회"""
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            # JSON 디코딩 시도
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # pickle 디코딩 시도
                try:
                    return pickle.loads(value)
                except:
                    # 문자열로 반환
                    return value.decode('utf-8') if isinstance(value, bytes) else value
                    
        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            nx: bool = False, xx: bool = False) -> bool:
        """
        키 값 설정
        
        Args:
            key: 키
            value: 값
            ttl: TTL (초)
            nx: 키가 존재하지 않을 때만 설정
            xx: 키가 존재할 때만 설정
        """
        try:
            # 값 직렬화
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, str, bool)):
                value = json.dumps(value)
            else:
                value = pickle.dumps(value)
            
            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl
            
            # Redis SET
            return self.client.set(key, value, ex=ttl, nx=nx, xx=xx)
            
        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """키 삭제"""
        try:
            return self.client.delete(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis delete error: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """키 존재 확인"""
        try:
            return self.client.exists(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis exists error: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """키 만료 시간 설정"""
        try:
            return self.client.expire(key, ttl)
        except redis.RedisError as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """키 남은 TTL 조회"""
        try:
            return self.client.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Redis ttl error: {e}")
            return -2
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """값 증가"""
        try:
            return self.client.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis incr error: {e}")
            return None
    
    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """값 감소"""
        try:
            return self.client.decr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis decr error: {e}")
            return None
    
    # Hash 작업
    def hget(self, name: str, key: str) -> Any:
        """해시 필드 값 조회"""
        try:
            value = self.client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except:
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except redis.RedisError as e:
            logger.error(f"Redis hget error: {e}")
            return None
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """해시 필드 값 설정"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            return self.client.hset(name, key, value)
        except redis.RedisError as e:
            logger.error(f"Redis hset error: {e}")
            return 0
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """해시 모든 필드 조회"""
        try:
            data = self.client.hgetall(name)
            result = {}
            for key, value in data.items():
                key = key.decode('utf-8') if isinstance(key, bytes) else key
                try:
                    result[key] = json.loads(value)
                except:
                    result[key] = value.decode('utf-8') if isinstance(value, bytes) else value
            return result
        except redis.RedisError as e:
            logger.error(f"Redis hgetall error: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """해시 필드 삭제"""
        try:
            return self.client.hdel(name, *keys)
        except redis.RedisError as e:
            logger.error(f"Redis hdel error: {e}")
            return 0
    
    # List 작업
    def lpush(self, key: str, *values: Any) -> int:
        """리스트 왼쪽에 추가"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    serialized_values.append(str(value))
            return self.client.lpush(key, *serialized_values)
        except redis.RedisError as e:
            logger.error(f"Redis lpush error: {e}")
            return 0
    
    def rpush(self, key: str, *values: Any) -> int:
        """리스트 오른쪽에 추가"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    serialized_values.append(str(value))
            return self.client.rpush(key, *serialized_values)
        except redis.RedisError as e:
            logger.error(f"Redis rpush error: {e}")
            return 0
    
    def lrange(self, key: str, start: int, stop: int) -> List[Any]:
        """리스트 범위 조회"""
        try:
            values = self.client.lrange(key, start, stop)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except:
                    result.append(value.decode('utf-8') if isinstance(value, bytes) else value)
            return result
        except redis.RedisError as e:
            logger.error(f"Redis lrange error: {e}")
            return []
    
    def llen(self, key: str) -> int:
        """리스트 길이"""
        try:
            return self.client.llen(key)
        except redis.RedisError as e:
            logger.error(f"Redis llen error: {e}")
            return 0
    
    # Set 작업
    def sadd(self, key: str, *values: Any) -> int:
        """셋에 멤버 추가"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    serialized_values.append(str(value))
            return self.client.sadd(key, *serialized_values)
        except redis.RedisError as e:
            logger.error(f"Redis sadd error: {e}")
            return 0
    
    def srem(self, key: str, *values: Any) -> int:
        """셋에서 멤버 제거"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    serialized_values.append(str(value))
            return self.client.srem(key, *serialized_values)
        except redis.RedisError as e:
            logger.error(f"Redis srem error: {e}")
            return 0
    
    def smembers(self, key: str) -> set:
        """셋 모든 멤버 조회"""
        try:
            values = self.client.smembers(key)
            result = set()
            for value in values:
                try:
                    result.add(json.loads(value))
                except:
                    result.add(value.decode('utf-8') if isinstance(value, bytes) else value)
            return result
        except redis.RedisError as e:
            logger.error(f"Redis smembers error: {e}")
            return set()
    
    def sismember(self, key: str, value: Any) -> bool:
        """셋 멤버 확인"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            else:
                value = str(value)
            return self.client.sismember(key, value)
        except redis.RedisError as e:
            logger.error(f"Redis sismember error: {e}")
            return False
    
    # 패턴 매칭
    def keys(self, pattern: str = '*') -> List[str]:
        """패턴과 일치하는 키 목록"""
        try:
            keys = self.client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except redis.RedisError as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    def scan(self, cursor: int = 0, match: Optional[str] = None, 
             count: Optional[int] = None) -> tuple:
        """키 스캔"""
        try:
            cursor, keys = self.client.scan(cursor, match=match, count=count)
            decoded_keys = [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
            return cursor, decoded_keys
        except redis.RedisError as e:
            logger.error(f"Redis scan error: {e}")
            return 0, []
    
    # 트랜잭션
    def pipeline(self, transaction: bool = True) -> redis.client.Pipeline:
        """파이프라인 생성"""
        return self.client.pipeline(transaction=transaction)
    
    # 연결 관리
    def ping(self) -> bool:
        """연결 확인"""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False
    
    def close(self):
        """연결 종료"""
        if self._client:
            self._client.close()
            self._client = None
    
    def flush_db(self):
        """현재 데이터베이스 비우기 (주의!)"""
        try:
            self.client.flushdb()
            logger.warning("Redis database flushed")
        except redis.RedisError as e:
            logger.error(f"Redis flushdb error: {e}")


# 싱글톤 인스턴스
_redis_client = None

def get_redis_client(**kwargs) -> RedisClient:
    """Redis 클라이언트 싱글톤 인스턴스 반환"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(**kwargs)
    return _redis_client