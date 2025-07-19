#!/usr/bin/env python3
"""
캐싱 시스템 관리자
- Redis 기반 다층 캐싱
- 자동 캐시 무효화
- 캐시 히트율 모니터링
"""

import redis
import json
import pickle
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import asyncio
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """캐시 통계"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage_mb: float = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0

class CacheManager:
    """캐시 관리자"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=1):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False  # 바이너리 데이터 저장을 위해
        )
        
        # 캐시 레이어별 TTL 설정 (초)
        self.ttl_config = {
            'hot': 300,      # 5분 - 자주 접근하는 데이터
            'warm': 3600,    # 1시간 - 주기적 접근 데이터
            'cold': 86400,   # 24시간 - 가끔 접근하는 데이터
            'static': 604800 # 7일 - 거의 변하지 않는 데이터
        }
        
        # 통계 추적
        self.stats = CacheStats()
        
    def _generate_key(self, namespace: str, key: str) -> str:
        """캐시 키 생성"""
        return f"yooni:{namespace}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """복잡한 데이터를 해시키로 변환"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get(self, namespace: str, key: str, 
            deserializer: Optional[Callable] = None) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            data = self.redis_client.get(cache_key)
            
            if data is None:
                self.stats.misses += 1
                return None
            
            self.stats.hits += 1
            
            # 역직렬화
            if deserializer:
                return deserializer(data)
            else:
                # 기본 pickle 역직렬화
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"캐시 읽기 오류: {e}")
            self.stats.misses += 1
            return None
    
    def set(self, namespace: str, key: str, value: Any,
            layer: str = 'warm',
            serializer: Optional[Callable] = None) -> bool:
        """캐시에 데이터 저장"""
        cache_key = self._generate_key(namespace, key)
        ttl = self.ttl_config.get(layer, 3600)
        
        try:
            # 직렬화
            if serializer:
                data = serializer(value)
            else:
                # 기본 pickle 직렬화
                data = pickle.dumps(value)
            
            # 저장
            self.redis_client.setex(cache_key, ttl, data)
            
            # 레이어 태그 추가 (캐시 무효화용)
            layer_key = f"yooni:layer:{layer}"
            self.redis_client.sadd(layer_key, cache_key)
            self.redis_client.expire(layer_key, ttl + 3600)  # 레이어 키는 더 오래 유지
            
            return True
            
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """캐시 삭제"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            result = self.redis_client.delete(cache_key)
            if result > 0:
                self.stats.evictions += 1
            return result > 0
            
        except Exception as e:
            logger.error(f"캐시 삭제 오류: {e}")
            return False
    
    def invalidate_namespace(self, namespace: str) -> int:
        """네임스페이스 전체 무효화"""
        pattern = self._generate_key(namespace, "*")
        
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.evictions += deleted
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"네임스페이스 무효화 오류: {e}")
            return 0
    
    def invalidate_layer(self, layer: str) -> int:
        """캐시 레이어 전체 무효화"""
        layer_key = f"yooni:layer:{layer}"
        
        try:
            keys = self.redis_client.smembers(layer_key)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.redis_client.delete(layer_key)
                self.stats.evictions += deleted
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"레이어 무효화 오류: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        # Redis 정보
        info = self.redis_client.info()
        
        # 메모리 사용량
        memory_usage_mb = info.get('used_memory', 0) / 1024 / 1024
        self.stats.memory_usage_mb = memory_usage_mb
        
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": f"{self.stats.hit_rate:.1f}%",
            "evictions": self.stats.evictions,
            "memory_usage_mb": f"{memory_usage_mb:.1f}",
            "total_keys": self.redis_client.dbsize(),
            "connected_clients": info.get('connected_clients', 0)
        }
    
    def cache_decorator(self, namespace: str, layer: str = 'warm', 
                       key_generator: Optional[Callable] = None):
        """함수 결과 캐싱 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 캐시 키 생성
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    # 기본 키 생성 (함수명 + 인자 해시)
                    key_data = {'args': args, 'kwargs': kwargs}
                    cache_key = f"{func.__name__}:{self._hash_key(key_data)}"
                
                # 캐시 확인
                cached = self.get(namespace, cache_key)
                if cached is not None:
                    logger.debug(f"캐시 히트: {namespace}:{cache_key}")
                    return cached
                
                # 함수 실행
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 캐시 저장
                self.set(namespace, cache_key, result, layer)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 동기 함수용 래퍼
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    key_data = {'args': args, 'kwargs': kwargs}
                    cache_key = f"{func.__name__}:{self._hash_key(key_data)}"
                
                cached = self.get(namespace, cache_key)
                if cached is not None:
                    logger.debug(f"캐시 히트: {namespace}:{cache_key}")
                    return cached
                
                result = func(*args, **kwargs)
                self.set(namespace, cache_key, result, layer)
                
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

class ProductCacheManager(CacheManager):
    """상품 데이터 전용 캐시 관리자"""
    
    def cache_product_list(self, supplier_id: int, products: List[Dict], 
                          filters: Optional[Dict] = None):
        """상품 목록 캐싱"""
        # 필터 해시를 키에 포함
        filter_hash = self._hash_key(filters) if filters else "all"
        key = f"products:{supplier_id}:{filter_hash}"
        
        # 상품 수에 따라 캐시 레이어 결정
        layer = 'hot' if len(products) < 100 else 'warm'
        
        self.set('supplier', key, products, layer)
    
    def get_product_list(self, supplier_id: int, 
                        filters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """캐시된 상품 목록 조회"""
        filter_hash = self._hash_key(filters) if filters else "all"
        key = f"products:{supplier_id}:{filter_hash}"
        
        return self.get('supplier', key)
    
    def invalidate_supplier_cache(self, supplier_id: int):
        """특정 공급사의 모든 캐시 무효화"""
        pattern = f"products:{supplier_id}:*"
        keys = list(self.redis_client.scan_iter(
            match=self._generate_key('supplier', pattern)
        ))
        
        if keys:
            deleted = self.redis_client.delete(*keys)
            logger.info(f"공급사 {supplier_id} 캐시 {deleted}개 무효화")
            return deleted
        return 0
    
    def warm_up_cache(self, supplier_id: int, product_getter: Callable):
        """캐시 예열 (사전 로딩)"""
        logger.info(f"공급사 {supplier_id} 캐시 예열 시작...")
        
        # 인기 필터 조합
        popular_filters = [
            None,  # 전체
            {'status': 'active'},
            {'category': '가전/디지털/컴퓨터'},
            {'price_range': (0, 50000)},
            {'price_range': (50000, 100000)}
        ]
        
        warmed = 0
        for filters in popular_filters:
            try:
                products = product_getter(supplier_id, filters)
                self.cache_product_list(supplier_id, products, filters)
                warmed += 1
            except Exception as e:
                logger.error(f"캐시 예열 실패: {e}")
        
        logger.info(f"캐시 예열 완료: {warmed}개 필터 조합")
        return warmed

# 사용 예제
def example_usage():
    """사용 예제"""
    cache = ProductCacheManager()
    
    # 데코레이터 사용
    @cache.cache_decorator('analysis', layer='warm')
    def expensive_analysis(product_id: int):
        # 시간이 오래 걸리는 분석
        import time
        time.sleep(2)
        return {"product_id": product_id, "score": 95.5}
    
    # 첫 호출 - 캐시 미스
    result1 = expensive_analysis(12345)
    print(f"첫 번째 결과: {result1}")
    
    # 두 번째 호출 - 캐시 히트
    result2 = expensive_analysis(12345)
    print(f"두 번째 결과: {result2}")
    
    # 통계 확인
    stats = cache.get_stats()
    print(f"\n캐시 통계: {stats}")

if __name__ == "__main__":
    example_usage()