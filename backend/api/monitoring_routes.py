"""
모니터링 API 라우트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from ..monitoring.metrics_collector import get_metrics_collector
from ..core.structured_logger import get_logger

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])
logger = get_logger(__name__)


@router.get("/metrics/summary")
async def get_metrics_summary(
    time_range: int = Query(60, description="Time range in minutes")
):
    """메트릭 요약 조회"""
    try:
        collector = get_metrics_collector()
        summary = collector.get_metrics_summary(time_range_minutes=time_range)
        
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"메트릭 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/timeseries/{metric_name}")
async def get_metric_timeseries(
    metric_name: str,
    time_range: int = Query(60, description="Time range in minutes")
):
    """특정 메트릭의 시계열 데이터 조회"""
    try:
        collector = get_metrics_collector()
        timeseries = collector.get_metric_timeseries(
            metric_name, 
            time_range_minutes=time_range
        )
        
        return {
            "status": "success",
            "metric": metric_name,
            "data": timeseries,
            "count": len(timeseries)
        }
    except Exception as e:
        logger.error(f"시계열 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/record")
async def record_metric(
    name: str,
    value: float,
    metric_type: str = "gauge",
    tags: Optional[dict] = None
):
    """메트릭 기록"""
    try:
        collector = get_metrics_collector()
        
        if metric_type == "counter":
            collector.record_counter(name, int(value), tags)
        elif metric_type == "gauge":
            collector.record_gauge(name, value, tags)
        elif metric_type == "histogram":
            collector.record_histogram(name, value, tags)
        else:
            raise ValueError(f"Invalid metric type: {metric_type}")
        
        return {"status": "success", "metric": name, "value": value}
    except Exception as e:
        logger.error(f"메트릭 기록 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/metrics/api-request")
async def record_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    tags: Optional[dict] = None
):
    """API 요청 메트릭 기록"""
    try:
        collector = get_metrics_collector()
        collector.record_api_request(
            method, endpoint, status_code, duration_ms, tags
        )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"API 메트릭 기록 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/metrics/business")
async def record_business_metric(
    name: str,
    value: float,
    metric_type: str = "gauge",
    tags: Optional[dict] = None
):
    """비즈니스 메트릭 기록"""
    try:
        collector = get_metrics_collector()
        collector.record_business_metric(name, value, metric_type, tags)
        
        return {"status": "success", "metric": f"business.{name}", "value": value}
    except Exception as e:
        logger.error(f"비즈니스 메트릭 기록 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health/detailed")
async def get_detailed_health():
    """상세 헬스 체크"""
    try:
        collector = get_metrics_collector()
        
        # 시스템 메트릭 가져오기
        system_metrics = collector.get_metrics_summary(time_range_minutes=5)
        
        # 최근 메트릭에서 현재 상태 추출
        cpu_usage = 0
        memory_usage = 0
        
        if 'gauges' in system_metrics:
            if 'system.cpu.usage' in system_metrics['gauges']:
                cpu_usage = system_metrics['gauges']['system.cpu.usage'][0]['value']
            if 'system.memory.usage' in system_metrics['gauges']:
                memory_usage = system_metrics['gauges']['system.memory.usage'][0]['value']
        
        # 상태 판단
        status = "healthy"
        issues = []
        
        if cpu_usage > 80:
            status = "warning"
            issues.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        if memory_usage > 85:
            status = "warning"
            issues.append(f"High memory usage: {memory_usage:.1f}%")
        
        if cpu_usage > 95 or memory_usage > 95:
            status = "critical"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage
            },
            "issues": issues,
            "uptime": system_metrics.get('gauges', {}).get('process.uptime', [{}])[0].get('value', 0)
        }
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.post("/metrics/start-collection")
async def start_metrics_collection():
    """시스템 메트릭 수집 시작"""
    try:
        collector = get_metrics_collector()
        collector.start_collection()
        
        return {"status": "success", "message": "Metrics collection started"}
    except Exception as e:
        logger.error(f"메트릭 수집 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/stop-collection")
async def stop_metrics_collection():
    """시스템 메트릭 수집 중지"""
    try:
        collector = get_metrics_collector()
        collector.stop_collection()
        
        return {"status": "success", "message": "Metrics collection stopped"}
    except Exception as e:
        logger.error(f"메트릭 수집 중지 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))