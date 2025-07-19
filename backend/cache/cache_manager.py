#!/usr/bin/env python3
"""
캐시 매니저
"""
import time
import json
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import logging
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """
    고급 캐시 관리 기능을 제공하는 매니저
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self._stats = defaultdict(lambda: {'hits': 0, 'misses': 0, 'sets': 0})
        self._lock = threading.Lock()
    
    # 캐시 워밍
    def warm_cache(self, cache_configs: List[Dict[str, Any]]):
        """
        캐시 사전 로딩 (워밍)
        
        Args:
            cache_configs: 캐시 설정 목록
                [
                    {
                        'key': 'products:all',
                        'loader': callable,
                        'ttl': 3600,
                        'args': [],
                        'kwargs': {}
                    }
                ]
        """
        warmed_count = 0
        
        for config in cache_configs:
            try:
                key = config['key']
                loader = config['loader']
                ttl = config.get('ttl', 3600)
                args = config.get('args', [])
                kwargs = config.get('kwargs', {})
                
                # 데이터 로드
                data = loader(*args, **kwargs)
                
                # 캐시 저장
                if data is not None:
                    self.redis.set(key, data, ttl=ttl)
                    warmed_count += 1
                    logger.info(f"Cache warmed: {key}")
                    
            except Exception as e:
                logger.error(f"Cache warming error for {config.get('key')}: {e}")
        
        return warmed_count
    
    # 다단계 캐시
    def get_multi_level(self, key: str, loaders: List[Callable], 
                       ttls: Optional[List[int]] = None) -> Any:
        """
        다단계 캐시 조회
        
        Args:
            key: 캐시 키
            loaders: 데이터 로더 함수 목록 (빠른 것부터 느린 순서)
            ttls: 각 레벨의 TTL
        
        Example:
            value = cache_manager.get_multi_level(
                key="user:123",
                loaders=[
                    lambda: get_from_memory_cache(123),
                    lambda: get_from_redis(123),
                    lambda: get_from_database(123)
                ],
                ttls=[60, 3600, 86400]
            )
        """
        if ttls is None:
            ttls = [3600] * len(loaders)
        
        # Redis에서 먼저 확인
        value = self.redis.get(key)
        if value is not None:
            self._record_hit(key)
            return value
        
        # 각 로더 실행
        for i, loader in enumerate(loaders):
            try:
                value = loader()
                if value is not None:
                    # 캐시 저장
                    ttl = ttls[i] if i < len(ttls) else 3600
                    self.redis.set(key, value, ttl=ttl)
                    self._record_miss(key)
                    self._record_set(key)
                    return value
            except Exception as e:
                logger.error(f"Multi-level cache loader {i} error: {e}")
                continue
        
        self._record_miss(key)
        return None
    
    # 태그 기반 캐싱
    def set_with_tags(self, key: str, value: Any, tags: List[str], ttl: int = 3600):
        """
        태그와 함께 캐시 저장
        
        Args:
            key: 캐시 키
            value: 캐시 값
            tags: 태그 목록
            ttl: TTL
        """
        # 값 저장
        self.redis.set(key, value, ttl=ttl)
        
        # 태그 인덱스 업데이트
        for tag in tags:
            tag_key = f"tag:{tag}"
            self.redis.sadd(tag_key, key)
            self.redis.expire(tag_key, ttl + 60)  # 태그는 조금 더 오래 유지
        
        self._record_set(key)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        태그로 캐시 무효화
        
        Args:
            tag: 태그
            
        Returns:
            삭제된 키 개수
        """
        tag_key = f"tag:{tag}"
        keys = list(self.redis.smembers(tag_key))
        
        if keys:
            deleted = self.redis.delete(*keys)
            self.redis.delete(tag_key)
            logger.info(f"Invalidated {deleted} keys with tag: {tag}")
            return deleted
        
        return 0
    
    def get_keys_by_tag(self, tag: str) -> List[str]:
        """태그로 키 목록 조회"""
        tag_key = f"tag:{tag}"
        return list(self.redis.smembers(tag_key))
    
    # 캐시 통계
    def get_stats(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        캐시 통계 조회
        
        Args:
            pattern: 키 패턴
        """
        with self._lock:
            if pattern:
                # 패턴 매칭 통계
                stats = {}
                for key, data in self._stats.items():
                    if self._match_pattern(key, pattern):
                        stats[key] = data
                return stats
            else:
                return dict(self._stats)
    
    def get_hit_rate(self, key: Optional[str] = None) -> float:
        """캐시 히트율 계산"""
        with self._lock:
            if key:
                stats = self._stats.get(key, {'hits': 0, 'misses': 0})
            else:
                # 전체 통계
                stats = {'hits': 0, 'misses': 0}
                for data in self._stats.values():
                    stats['hits'] += data['hits']
                    stats['misses'] += data['misses']
            
            total = stats['hits'] + stats['misses']
            if total == 0:
                return 0.0
            
            return stats['hits'] / total
    
    def reset_stats(self):
        """통계 초기화"""
        with self._lock:
            self._stats.clear()
    
    # 캐시 만료 정책
    def set_with_sliding_expiration(self, key: str, value: Any, ttl: int = 3600):
        """
        슬라이딩 만료 정책으로 캐시 저장
        (접근할 때마다 TTL 갱신)
        """
        self.redis.set(key, value, ttl=ttl)
        # 메타데이터 저장
        meta_key = f"meta:{key}"
        self.redis.hset(meta_key, "sliding_ttl", str(ttl))
        self.redis.expire(meta_key, ttl)
    
    def get_with_sliding_expiration(self, key: str) -> Any:
        """슬라이딩 만료 정책으로 캐시 조회"""
        value = self.redis.get(key)
        
        if value is not None:
            # TTL 갱신
            meta_key = f"meta:{key}"
            sliding_ttl = self.redis.hget(meta_key, "sliding_ttl")
            if sliding_ttl:
                ttl = int(sliding_ttl)
                self.redis.expire(key, ttl)
                self.redis.expire(meta_key, ttl)
            
            self._record_hit(key)
        else:
            self._record_miss(key)
        
        return value
    
    # 캐시 크기 관리
    def evict_by_pattern(self, pattern: str, keep_count: int = 0) -> int:
        """
        패턴에 맞는 키 중 오래된 것부터 삭제
        
        Args:
            pattern: 키 패턴
            keep_count: 유지할 키 개수
        """
        keys = self.redis.keys(pattern)
        
        if len(keys) <= keep_count:
            return 0
        
        # TTL 기준 정렬
        key_ttls = []
        for key in keys:
            ttl = self.redis.ttl(key)
            if ttl > 0:
                key_ttls.append((key, ttl))
        
        # TTL이 적은 순서로 정렬
        key_ttls.sort(key=lambda x: x[1])
        
        # 삭제
        delete_count = len(keys) - keep_count
        keys_to_delete = [k[0] for k in key_ttls[:delete_count]]
        
        if keys_to_delete:
            deleted = self.redis.delete(*keys_to_delete)
            logger.info(f"Evicted {deleted} keys matching pattern: {pattern}")
            return deleted
        
        return 0
    
    def get_memory_usage(self, pattern: str = '*') -> Dict[str, Any]:
        """
        메모리 사용량 추정
        
        Args:
            pattern: 키 패턴
        """
        keys = self.redis.keys(pattern)
        total_size = 0
        key_count = len(keys)
        
        # 샘플링 (최대 100개)
        sample_size = min(100, key_count)
        sample_keys = keys[:sample_size] if sample_size > 0 else []
        
        sample_total = 0
        for key in sample_keys:
            try:
                # 메모리 사용량 추정 (Redis 4.0+)
                pipe = self.redis.pipeline()
                pipe.memory_usage(key)
                results = pipe.execute()
                if results[0]:
                    sample_total += results[0]
            except:
                # 대략적인 추정
                value = self.redis.get(key)
                if value:
                    sample_total += len(str(value))
        
        # 전체 추정
        if sample_size > 0:
            avg_size = sample_total / sample_size
            total_size = int(avg_size * key_count)
        
        return {
            'pattern': pattern,
            'key_count': key_count,
            'estimated_memory': total_size,
            'average_key_size': int(total_size / key_count) if key_count > 0 else 0,
            'sample_size': sample_size
        }
    
    # 배치 작업
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """다중 키 조회"""
        values = self.redis.mget(keys)
        result = {}
        
        for key, value in zip(keys, values):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except:
                    result[key] = value
                self._record_hit(key)
            else:
                self._record_miss(key)
        
        return result
    
    def mset(self, mapping: Dict[str, Any], ttl: int = 3600) -> bool:
        """다중 키 설정"""
        # 값 직렬화
        serialized = {}
        for key, value in mapping.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value, ensure_ascii=False)
            else:
                serialized[key] = str(value)
            self._record_set(key)
        
        # 파이프라인으로 설정
        pipe = self.redis.pipeline()
        for key, value in serialized.items():
            pipe.set(key, value, ex=ttl)
        
        results = pipe.execute()
        return all(results)
    
    # Lock 기반 캐싱
    def get_or_set_with_lock(self, key: str, loader: Callable, 
                           ttl: int = 3600, lock_timeout: int = 10) -> Any:
        """
        Lock을 사용한 캐시 설정 (thundering herd 방지)
        
        Args:
            key: 캐시 키
            loader: 데이터 로더 함수
            ttl: 캐시 TTL
            lock_timeout: Lock 타임아웃
        """
        # 캐시 확인
        value = self.redis.get(key)
        if value is not None:
            self._record_hit(key)
            return value
        
        # Lock 획득
        lock_key = f"lock:{key}"
        lock_value = str(time.time())
        
        # Lock 획득 시도
        if self.redis.set(lock_key, lock_value, nx=True, ex=lock_timeout):
            try:
                # 다시 한번 캐시 확인 (다른 프로세스가 설정했을 수 있음)
                value = self.redis.get(key)
                if value is not None:
                    self._record_hit(key)
                    return value
                
                # 데이터 로드
                value = loader()
                if value is not None:
                    self.redis.set(key, value, ttl=ttl)
                    self._record_set(key)
                
                self._record_miss(key)
                return value
                
            finally:
                # Lock 해제
                stored_value = self.redis.get(lock_key)
                if stored_value and stored_value.decode() == lock_value:
                    self.redis.delete(lock_key)
        else:
            # Lock 대기
            max_wait = lock_timeout
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                value = self.redis.get(key)
                if value is not None:
                    self._record_hit(key)
                    return value
                time.sleep(0.1)
            
            # 타임아웃 - 직접 로드
            value = loader()
            self._record_miss(key)
            return value
    
    # 유틸리티 메서드
    def _record_hit(self, key: str):
        """히트 기록"""
        with self._lock:
            self._stats[key]['hits'] += 1
    
    def _record_miss(self, key: str):
        """미스 기록"""
        with self._lock:
            self._stats[key]['misses'] += 1
    
    def _record_set(self, key: str):
        """설정 기록"""
        with self._lock:
            self._stats[key]['sets'] += 1
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """패턴 매칭"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)