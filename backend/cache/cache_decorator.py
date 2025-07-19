#!/usr/bin/env python3
"""
캐시 데코레이터
"""
import functools
import hashlib
import json
import inspect
from typing import Any, Callable, Optional, Union, List
from datetime import timedelta
import logging
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, func: Callable, args: tuple, kwargs: dict, 
                      key_builder: Optional[Callable] = None) -> str:
    """
    캐시 키 생성
    
    Args:
        prefix: 키 접두사
        func: 함수
        args: 위치 인자
        kwargs: 키워드 인자
        key_builder: 커스텀 키 빌더 함수
    """
    if key_builder:
        return f"{prefix}:{key_builder(*args, **kwargs)}"
    
    # 기본 키 생성
    key_parts = [prefix, func.__module__, func.__name__]
    
    # 함수 시그니처 파싱
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    
    # self/cls 제외
    params = {}
    for name, value in bound_args.arguments.items():
        if name not in ('self', 'cls'):
            params[name] = value
    
    # 파라미터 해시
    if params:
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        key_parts.append(params_hash)
    
    return ":".join(key_parts)


def cache(prefix: str = "cache", ttl: Union[int, timedelta] = 3600,
          key_builder: Optional[Callable] = None,
          condition: Optional[Callable] = None,
          skip_on_error: bool = True):
    """
    함수 결과를 캐싱하는 데코레이터
    
    Args:
        prefix: 캐시 키 접두사
        ttl: 캐시 만료 시간 (초 또는 timedelta)
        key_builder: 커스텀 캐시 키 생성 함수
        condition: 캐싱 조건 함수 (True 반환 시 캐싱)
        skip_on_error: Redis 오류 시 함수 실행 여부
    
    Examples:
        @cache(prefix="products", ttl=3600)
        def get_product(product_id: int):
            return db.query(...)
        
        @cache(prefix="user", ttl=timedelta(hours=1), 
               key_builder=lambda user_id: f"profile:{user_id}")
        def get_user_profile(user_id: int):
            return db.query(...)
        
        @cache(prefix="search", ttl=300,
               condition=lambda query: len(query) > 2)
        def search_products(query: str):
            return db.search(...)
    """
    # TTL 변환
    if isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐싱 조건 확인
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Redis 클라이언트
            redis_client = get_redis_client()
            
            # 캐시 키 생성
            cache_key = generate_cache_key(prefix, func, args, kwargs, key_builder)
            
            try:
                # 캐시 조회
                cached_value = redis_client.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
                
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 결과 캐싱
                if result is not None:
                    redis_client.set(cache_key, result, ttl=ttl)
                    logger.debug(f"Cache set: {cache_key}")
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error: {e}")
                if skip_on_error:
                    return func(*args, **kwargs)
                raise
        
        # 캐시 관련 메타데이터 추가
        wrapper._cache_prefix = prefix
        wrapper._cache_ttl = ttl
        wrapper._cache_key_builder = key_builder
        
        return wrapper
    
    return decorator


def cache_invalidate(prefix: str = "cache", key_builder: Optional[Callable] = None,
                    patterns: Optional[List[str]] = None):
    """
    캐시 무효화 데코레이터
    
    Args:
        prefix: 캐시 키 접두사
        key_builder: 커스텀 캐시 키 생성 함수
        patterns: 삭제할 키 패턴 목록
    
    Examples:
        @cache_invalidate(prefix="products", 
                         key_builder=lambda product_id: f"detail:{product_id}")
        def update_product(product_id: int, data: dict):
            return db.update(...)
        
        @cache_invalidate(patterns=["products:*", "search:*"])
        def bulk_update_products():
            return db.bulk_update(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 함수 실행
            result = func(*args, **kwargs)
            
            # Redis 클라이언트
            redis_client = get_redis_client()
            
            try:
                # 패턴 기반 삭제
                if patterns:
                    for pattern in patterns:
                        keys = redis_client.keys(pattern)
                        if keys:
                            redis_client.delete(*keys)
                            logger.debug(f"Cache invalidated by pattern: {pattern} ({len(keys)} keys)")
                
                # 특정 키 삭제
                else:
                    cache_key = generate_cache_key(prefix, func, args, kwargs, key_builder)
                    deleted = redis_client.delete(cache_key)
                    if deleted:
                        logger.debug(f"Cache invalidated: {cache_key}")
                
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")
            
            return result
        
        return wrapper
    
    return decorator


def cached_property(ttl: Union[int, timedelta] = 3600):
    """
    프로퍼티 캐싱 데코레이터
    
    Args:
        ttl: 캐시 만료 시간
    
    Example:
        class Product:
            def __init__(self, product_id: int):
                self.product_id = product_id
            
            @cached_property(ttl=3600)
            def reviews(self):
                return fetch_product_reviews(self.product_id)
    """
    if isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())
    
    def decorator(func: Callable) -> property:
        attr_name = f'_cached_{func.__name__}'
        
        @functools.wraps(func)
        def getter(self):
            redis_client = get_redis_client()
            
            # 캐시 키 생성
            cache_key = f"property:{self.__class__.__name__}:{id(self)}:{func.__name__}"
            
            try:
                # 캐시 조회
                cached_value = redis_client.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 프로퍼티 계산
                value = func(self)
                
                # 캐싱
                if value is not None:
                    redis_client.set(cache_key, value, ttl=ttl)
                
                return value
                
            except Exception as e:
                logger.error(f"Cached property error: {e}")
                return func(self)
        
        return property(getter)
    
    return decorator


class CacheContext:
    """
    컨텍스트 매니저를 통한 캐시 제어
    
    Example:
        with CacheContext(prefix="temp", ttl=60) as cache:
            # 임시 캐시 사용
            cache.set("key", "value")
            value = cache.get("key")
    """
    
    def __init__(self, prefix: str = "context", ttl: int = 3600):
        self.prefix = prefix
        self.ttl = ttl
        self.redis_client = get_redis_client()
        self.keys = set()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 컨텍스트 종료 시 모든 키 삭제 (선택적)
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        full_key = f"{self.prefix}:{key}"
        return self.redis_client.get(full_key, default)
    
    def set(self, key: str, value: Any) -> bool:
        full_key = f"{self.prefix}:{key}"
        self.keys.add(full_key)
        return self.redis_client.set(full_key, value, ttl=self.ttl)
    
    def delete(self, key: str) -> int:
        full_key = f"{self.prefix}:{key}"
        self.keys.discard(full_key)
        return self.redis_client.delete(full_key)
    
    def clear(self):
        """컨텍스트의 모든 키 삭제"""
        if self.keys:
            self.redis_client.delete(*self.keys)
            self.keys.clear()