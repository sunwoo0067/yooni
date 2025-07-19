#!/usr/bin/env python3
"""
공급사 관리 API 엔드포인트
프론트엔드 관리 인터페이스를 위한 RESTful API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
import asyncio
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 공급사 관련 모듈 임포트
from supplier.api_integration_manager import APIIntegrationManager, APICredentials
from supplier.scheduler import SupplierCollectionScheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitoring.performance_monitor import PerformanceMonitor
from optimization.database_optimizer import DatabaseOptimizer
from optimization.cache_manager import ProductCacheManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Supplier Management API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 연결
def get_db():
    return psycopg2.connect(
        host='localhost',
        port=5434,
        database='yoonni',
        user='postgres',
        password='postgres'
    )

# Pydantic 모델
class CollectionTrigger(BaseModel):
    supplier_name: str
    force: bool = False

class ScheduleUpdate(BaseModel):
    supplier_name: str
    cron_expression: str
    enabled: bool = True

class SupplierStatus(BaseModel):
    id: int
    name: str
    status: str
    last_collection: Optional[datetime]
    next_collection: Optional[datetime]
    total_products: int
    active_products: int
    success_rate: float
    avg_collection_time: float

# 전역 인스턴스
scheduler = None
performance_monitor = None
cache_manager = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global scheduler, performance_monitor, cache_manager
    
    # 스케줄러 초기화
    scheduler = SupplierCollectionScheduler()
    scheduler.scheduler.start()
    
    # 성능 모니터 초기화
    performance_monitor = PerformanceMonitor()
    performance_monitor.start()
    
    # 캐시 매니저 초기화
    cache_manager = ProductCacheManager()
    
    logger.info("✅ Supplier Management API 시작됨")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    global scheduler, performance_monitor
    
    if scheduler:
        scheduler.shutdown()
    
    if performance_monitor:
        performance_monitor.stop()
    
    logger.info("🛑 Supplier Management API 종료됨")

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "service": "Supplier Management API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "suppliers": "/api/suppliers",
            "collection_status": "/api/collection/status",
            "collection_logs": "/api/collection/logs",
            "ai_insights": "/api/ai/insights",
            "schedules": "/api/schedules"
        }
    }

@app.get("/api/suppliers", response_model=List[SupplierStatus])
async def get_suppliers():
    """모든 공급사 상태 조회"""
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    s.id,
                    s.name,
                    COALESCE(cs.status, 'idle') as status,
                    cs.last_run_at as last_collection,
                    -- 다음 실행 시간 계산 (간단히 24시간 후로 가정)
                    CASE 
                        WHEN cs.last_run_at IS NOT NULL 
                        THEN cs.last_run_at + INTERVAL '24 hours'
                        ELSE NULL
                    END as next_collection,
                    COUNT(sp.id) as total_products,
                    COUNT(CASE WHEN sp.status = 'active' THEN 1 END) as active_products,
                    COALESCE(stats.success_rate, 0) as success_rate,
                    COALESCE(stats.avg_duration_seconds, 0) as avg_collection_time
                FROM suppliers s
                LEFT JOIN supplier_collection_status cs ON s.id = cs.supplier_id
                LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
                LEFT JOIN supplier_collection_stats stats ON s.name = stats.supplier_name
                WHERE s.is_active = true
                GROUP BY s.id, s.name, cs.status, cs.last_run_at, 
                         stats.success_rate, stats.avg_duration_seconds
                ORDER BY s.name
            """)
            
            suppliers = cursor.fetchall()
            return suppliers
            
    except Exception as e:
        logger.error(f"공급사 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/collection/status")
async def get_collection_status():
    """현재 수집 상태 조회"""
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 현재 실행 중인 작업
            cursor.execute("""
                SELECT 
                    cs.id,
                    s.name as supplier_name,
                    cs.status,
                    cs.started_at,
                    cs.last_run_at,
                    cs.error_message,
                    EXTRACT(EPOCH FROM (NOW() - cs.started_at))::int as duration_seconds
                FROM supplier_collection_status cs
                JOIN suppliers s ON cs.supplier_id = s.id
                WHERE cs.status = 'running'
                ORDER BY cs.started_at DESC
            """)
            
            running_jobs = cursor.fetchall()
            
            # 최근 완료된 작업
            cursor.execute("""
                SELECT 
                    h.id,
                    h.supplier_name,
                    h.status,
                    h.started_at,
                    h.completed_at,
                    h.duration_seconds,
                    h.collected_count,
                    h.failed_count,
                    h.error_details
                FROM scheduler_execution_history h
                WHERE h.completed_at > NOW() - INTERVAL '24 hours'
                ORDER BY h.completed_at DESC
                LIMIT 10
            """)
            
            recent_jobs = cursor.fetchall()
            
            return {
                "running_jobs": running_jobs,
                "recent_jobs": recent_jobs,
                "scheduler_status": "running" if scheduler and scheduler.scheduler.running else "stopped"
            }
            
    except Exception as e:
        logger.error(f"수집 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/collection/logs")
async def get_collection_logs(
    supplier_name: Optional[str] = None,
    days: int = 7,
    limit: int = 100
):
    """수집 로그 조회"""
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT 
                    l.id,
                    s.name as supplier_name,
                    l.status,
                    l.started_at,
                    l.completed_at,
                    l.collected_count,
                    l.failed_count,
                    l.error_count,
                    l.processing_time_seconds,
                    l.error_details
                FROM supplier_collection_logs l
                JOIN suppliers s ON l.supplier_id = s.id
                WHERE l.started_at > NOW() - INTERVAL '%s days'
            """
            
            params = [days]
            
            if supplier_name:
                query += " AND s.name = %s"
                params.append(supplier_name)
            
            query += " ORDER BY l.started_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            return logs
            
    except Exception as e:
        logger.error(f"로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/collection/trigger")
async def trigger_collection(
    trigger: CollectionTrigger,
    background_tasks: BackgroundTasks
):
    """수동 수집 트리거"""
    try:
        # 중복 실행 확인
        if not trigger.force:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM supplier_collection_status cs
                    JOIN suppliers s ON cs.supplier_id = s.id
                    WHERE s.name = %s AND cs.status = 'running'
                """, (trigger.supplier_name,))
                
                if cursor.fetchone():
                    conn.close()
                    raise HTTPException(
                        status_code=409,
                        detail=f"{trigger.supplier_name} 수집이 이미 실행 중입니다"
                    )
            conn.close()
        
        # 백그라운드에서 수집 실행
        background_tasks.add_task(
            run_collection_task,
            trigger.supplier_name
        )
        
        return {
            "status": "triggered",
            "supplier": trigger.supplier_name,
            "message": f"{trigger.supplier_name} 수집이 시작되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수집 트리거 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/insights")
async def get_ai_insights(
    supplier_name: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20
):
    """AI 분석 인사이트 조회"""
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT 
                    pai.*,
                    CAST(pai.predicted_price AS FLOAT) - sp.price as price_diff,
                    CASE 
                        WHEN CAST(pai.demand_grade AS CHAR) IN ('A', 'B') THEN 'high'
                        WHEN CAST(pai.demand_grade AS CHAR) = 'C' THEN 'medium'
                        ELSE 'low'
                    END as demand_level_group
                FROM product_ai_insights pai
                JOIN supplier_products sp ON pai.product_id = sp.id
                WHERE 1=1
            """
            
            params = []
            
            if supplier_name:
                query += " AND pai.supplier_name = %s"
                params.append(supplier_name)
            
            if category:
                query += " AND pai.category = %s"
                params.append(category)
            
            query += """ 
                ORDER BY 
                    CAST(pai.demand_score AS FLOAT) DESC,
                    ABS(CAST(pai.predicted_price AS FLOAT) - sp.price) DESC
                LIMIT %s
            """
            params.append(limit)
            
            cursor.execute(query, params)
            insights = cursor.fetchall()
            
            # 카테고리별 통계
            cursor.execute("""
                SELECT * FROM category_ai_insights
                ORDER BY avg_demand_score DESC
                LIMIT 10
            """)
            
            category_stats = cursor.fetchall()
            
            return {
                "product_insights": insights,
                "category_stats": category_stats
            }
            
    except Exception as e:
        logger.error(f"AI 인사이트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/schedules")
async def get_schedules():
    """스케줄 설정 조회"""
    try:
        if not scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않음")
        
        jobs = []
        for job in scheduler.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
                "args": job.args,
                "kwargs": job.kwargs
            })
        
        return {
            "scheduler_running": scheduler.scheduler.running,
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"스케줄 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/schedules")
async def update_schedule(schedule: ScheduleUpdate):
    """스케줄 설정 업데이트"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # supplier_configs 업데이트
            cursor.execute("""
                UPDATE supplier_configs 
                SET settings = settings || jsonb_build_object(
                    'collection_schedule', %s,
                    'collection_enabled', %s
                )
                WHERE supplier_id = (
                    SELECT id FROM suppliers WHERE name = %s
                )
            """, (schedule.cron_expression, schedule.enabled, schedule.supplier_name))
            
            conn.commit()
        
        # 스케줄러 재시작
        if scheduler:
            scheduler.reload_schedules()
        
        return {
            "status": "updated",
            "supplier": schedule.supplier_name,
            "cron": schedule.cron_expression,
            "enabled": schedule.enabled
        }
        
    except Exception as e:
        logger.error(f"스케줄 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """대시보드 통계"""
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 전체 통계
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s.id) as total_suppliers,
                    COUNT(DISTINCT sp.id) as total_products,
                    COUNT(DISTINCT CASE WHEN sp.status = 'active' THEN sp.id END) as active_products,
                    COUNT(DISTINCT CASE WHEN spa.id IS NOT NULL THEN sp.id END) as analyzed_products,
                    AVG(CASE WHEN spa.analysis_result->>'demand_score' IS NOT NULL 
                        THEN CAST(spa.analysis_result->>'demand_score' AS FLOAT) END) as avg_demand_score
                FROM suppliers s
                LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
                LEFT JOIN supplier_product_analysis spa ON sp.id = spa.product_id
                WHERE s.is_active = true
            """)
            
            overall_stats = cursor.fetchone()
            
            # 최근 24시간 수집 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as collections_24h,
                    SUM(collected_count) as products_collected_24h,
                    AVG(processing_time_seconds) as avg_processing_time,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_collections
                FROM supplier_collection_logs
                WHERE started_at > NOW() - INTERVAL '24 hours'
            """)
            
            recent_stats = cursor.fetchone()
            
            return {
                "overall": overall_stats,
                "recent_24h": recent_stats,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# 백그라운드 태스크 함수
async def run_collection_task(supplier_name: str):
    """백그라운드에서 수집 실행"""
    try:
        logger.info(f"🚀 {supplier_name} 수집 시작 (백그라운드)")
        
        # APIIntegrationManager를 사용하여 수집
        manager = APIIntegrationManager()
        
        if supplier_name.lower() == 'all':
            results = await manager.collect_all_suppliers()
        else:
            # 개별 공급사 수집
            conn = get_db()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sc.supplier_id,
                        sc.api_endpoint,
                        sc.auth_type,
                        sc.credentials,
                        sc.settings
                    FROM supplier_configs sc
                    JOIN suppliers s ON sc.supplier_id = s.id
                    WHERE s.name = %s AND s.is_active = true
                """, (supplier_name,))
                
                config = cursor.fetchone()
                conn.close()
                
                if not config:
                    raise ValueError(f"공급사 설정을 찾을 수 없음: {supplier_name}")
                
                credentials = APICredentials(
                    api_key=config['credentials'].get('api_key'),
                    api_secret=config['credentials'].get('api_secret'),
                    vendor_id=config['credentials'].get('vendor_id'),
                    username=config['credentials'].get('username'),
                    password=config['credentials'].get('password')
                )
                
                if supplier_name == '오너클랜':
                    result = await manager.collect_ownerclan_products(credentials)
                elif supplier_name == '젠트레이드':
                    result = await manager.collect_zentrade_products(credentials)
                else:
                    raise ValueError(f"지원하지 않는 공급사: {supplier_name}")
                
                results = {supplier_name: result}
        
        logger.info(f"✅ {supplier_name} 수집 완료")
        
    except Exception as e:
        logger.error(f"❌ {supplier_name} 수집 실패: {e}")

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """실시간 성능 메트릭 조회"""
    try:
        if not performance_monitor:
            raise HTTPException(status_code=503, detail="성능 모니터가 초기화되지 않음")
        
        metrics = performance_monitor.get_realtime_metrics()
        analysis = performance_monitor.analyze_performance()
        
        return {
            "metrics": metrics,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"성능 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance/optimization")
async def get_optimization_report():
    """데이터베이스 최적화 보고서"""
    try:
        optimizer = DatabaseOptimizer()
        report = optimizer.get_optimization_report()
        
        return report
        
    except Exception as e:
        logger.error(f"최적화 보고서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/optimize")
async def run_optimization(
    optimization_type: str = "index"  # index, vacuum, analyze
):
    """최적화 실행"""
    try:
        optimizer = DatabaseOptimizer()
        
        if optimization_type == "index":
            optimizer.optimize_indexes()
            message = "인덱스 최적화 완료"
        elif optimization_type == "vacuum":
            optimizer.vacuum_and_analyze()
            message = "VACUUM 및 ANALYZE 완료"
        elif optimization_type == "analyze":
            slow_queries = optimizer.analyze_slow_queries()
            message = f"느린 쿼리 {len(slow_queries)}개 분석 완료"
        else:
            raise HTTPException(status_code=400, detail="잘못된 최적화 타입")
        
        return {
            "status": "completed",
            "type": optimization_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"최적화 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cache/stats")
async def get_cache_stats():
    """캐시 통계 조회"""
    try:
        if not cache_manager:
            raise HTTPException(status_code=503, detail="캐시 매니저가 초기화되지 않음")
        
        stats = cache_manager.get_stats()
        
        return {
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/invalidate")
async def invalidate_cache(
    namespace: Optional[str] = None,
    supplier_id: Optional[int] = None
):
    """캐시 무효화"""
    try:
        if not cache_manager:
            raise HTTPException(status_code=503, detail="캐시 매니저가 초기화되지 않음")
        
        invalidated = 0
        
        if namespace:
            invalidated = cache_manager.invalidate_namespace(namespace)
        elif supplier_id:
            invalidated = cache_manager.invalidate_supplier_cache(supplier_id)
        else:
            raise HTTPException(status_code=400, detail="namespace 또는 supplier_id 필요")
        
        return {
            "status": "invalidated",
            "count": invalidated,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"캐시 무효화 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)