#!/usr/bin/env python3
"""
캐시 서비스 API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cache import RedisClient, CacheManager
from core import get_logger

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Cache Management API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 클라이언트 초기화
redis_client = RedisClient()
cache_manager = CacheManager(redis_client)

# Request/Response 모델
class CacheSetRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = 3600
    tags: Optional[List[str]] = None


class CacheGetRequest(BaseModel):
    keys: List[str]


class CacheInvalidateRequest(BaseModel):
    pattern: Optional[str] = None
    tag: Optional[str] = None
    keys: Optional[List[str]] = None


class CacheWarmRequest(BaseModel):
    configs: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """API 서버 시작 시 실행"""
    logger.info("캐시 관리 API 시작")
    
    # Redis 연결 확인
    if not redis_client.ping():
        logger.error("Redis 연결 실패")
    else:
        logger.info("Redis 연결 성공")


@app.on_event("shutdown")
async def shutdown_event():
    """API 서버 종료 시 실행"""
    redis_client.close()
    logger.info("캐시 관리 API 종료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    redis_status = "healthy" if redis_client.ping() else "unhealthy"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }


# 캐시 기본 작업
@app.get("/cache/{key}")
async def get_cache(key: str):
    """캐시 조회"""
    value = redis_client.get(key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {
        "key": key,
        "value": value,
        "ttl": redis_client.ttl(key)
    }


@app.post("/cache")
async def set_cache(request: CacheSetRequest):
    """캐시 설정"""
    try:
        if request.tags:
            cache_manager.set_with_tags(
                key=request.key,
                value=request.value,
                tags=request.tags,
                ttl=request.ttl
            )
        else:
            redis_client.set(request.key, request.value, ttl=request.ttl)
        
        return {
            "success": True,
            "key": request.key,
            "ttl": request.ttl
        }
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/{key}")
async def delete_cache(key: str):
    """캐시 삭제"""
    deleted = redis_client.delete(key)
    return {
        "success": deleted > 0,
        "deleted_count": deleted
    }


@app.post("/cache/mget")
async def mget_cache(request: CacheGetRequest):
    """다중 캐시 조회"""
    result = cache_manager.mget(request.keys)
    return {
        "result": result,
        "found_count": len([v for v in result.values() if v is not None])
    }


# 캐시 무효화
@app.post("/cache/invalidate")
async def invalidate_cache(request: CacheInvalidateRequest):
    """캐시 무효화"""
    deleted_count = 0
    
    try:
        if request.pattern:
            # 패턴 기반 삭제
            keys = redis_client.keys(request.pattern)
            if keys:
                deleted_count = redis_client.delete(*keys)
                
        elif request.tag:
            # 태그 기반 삭제
            deleted_count = cache_manager.invalidate_by_tag(request.tag)
            
        elif request.keys:
            # 특정 키 삭제
            deleted_count = redis_client.delete(*request.keys)
        
        return {
            "success": True,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 캐시 통계
@app.get("/cache/stats")
async def get_cache_stats(pattern: Optional[str] = None):
    """캐시 통계 조회"""
    stats = cache_manager.get_stats(pattern)
    
    # 전체 통계 계산
    total_hits = sum(s['hits'] for s in stats.values())
    total_misses = sum(s['misses'] for s in stats.values())
    total_sets = sum(s['sets'] for s in stats.values())
    
    hit_rate = 0.0
    if total_hits + total_misses > 0:
        hit_rate = total_hits / (total_hits + total_misses)
    
    return {
        "stats": stats,
        "summary": {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_sets": total_sets,
            "hit_rate": hit_rate,
            "key_count": len(stats)
        }
    }


@app.post("/cache/stats/reset")
async def reset_cache_stats():
    """캐시 통계 초기화"""
    cache_manager.reset_stats()
    return {"success": True}


# 캐시 메모리 관리
@app.get("/cache/memory")
async def get_memory_usage(pattern: str = '*'):
    """메모리 사용량 조회"""
    try:
        usage = cache_manager.get_memory_usage(pattern)
        return usage
    except Exception as e:
        logger.error(f"Memory usage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/evict")
async def evict_cache(pattern: str, keep_count: int = 0):
    """캐시 제거"""
    try:
        evicted = cache_manager.evict_by_pattern(pattern, keep_count)
        return {
            "success": True,
            "evicted_count": evicted
        }
    except Exception as e:
        logger.error(f"Cache eviction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 캐시 워밍
@app.post("/cache/warm")
async def warm_cache(request: CacheWarmRequest):
    """캐시 워밍"""
    try:
        # 실제 구현에서는 loader 함수를 동적으로 매핑
        warmed_count = 0
        
        for config in request.configs:
            # 예시: 특정 타입별 로더 매핑
            if config.get('type') == 'products':
                # 제품 데이터 로드
                pass
            elif config.get('type') == 'users':
                # 사용자 데이터 로드
                pass
            
            warmed_count += 1
        
        return {
            "success": True,
            "warmed_count": warmed_count
        }
    except Exception as e:
        logger.error(f"Cache warming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 캐시 정보
@app.get("/cache/info")
async def get_cache_info():
    """캐시 서버 정보"""
    try:
        info = redis_client.client.info()
        
        return {
            "server": {
                "version": info.get('redis_version'),
                "uptime_seconds": info.get('uptime_in_seconds'),
                "connected_clients": info.get('connected_clients')
            },
            "memory": {
                "used_memory": info.get('used_memory'),
                "used_memory_human": info.get('used_memory_human'),
                "used_memory_peak": info.get('used_memory_peak'),
                "used_memory_peak_human": info.get('used_memory_peak_human')
            },
            "stats": {
                "total_connections_received": info.get('total_connections_received'),
                "total_commands_processed": info.get('total_commands_processed'),
                "instantaneous_ops_per_sec": info.get('instantaneous_ops_per_sec'),
                "keyspace_hits": info.get('keyspace_hits'),
                "keyspace_misses": info.get('keyspace_misses')
            }
        }
    except Exception as e:
        logger.error(f"Cache info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/keys")
async def list_keys(pattern: str = '*', cursor: int = 0, count: int = 100):
    """키 목록 조회"""
    try:
        new_cursor, keys = redis_client.scan(cursor, match=pattern, count=count)
        
        return {
            "cursor": new_cursor,
            "keys": keys,
            "count": len(keys),
            "has_more": new_cursor != 0
        }
    except Exception as e:
        logger.error(f"Key listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cache_service:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    )