#!/usr/bin/env python3
"""
향상된 마켓플레이스 관리 API
- FastAPI 기반 REST API
- 마켓플레이스 상태 모니터링
- 성능 메트릭 조회
- 율 제한 최적화
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time
import json

# 로깅 설정
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres', 
    'password': '1234'
}

# Pydantic 모델
class MarketplaceStatus(BaseModel):
    marketplace: str
    is_healthy: bool
    response_time: Optional[float]
    success_rate: float
    total_requests: int
    circuit_breaker_state: str
    available_tokens: int
    last_check: Optional[str]

class MetricsRequest(BaseModel):
    marketplace: Optional[str] = None
    hours: int = 24

class RateLimitUpdate(BaseModel):
    marketplace: str
    max_requests_per_second: float
    burst_allowance: int

# FastAPI 앱 생성
app = FastAPI(
    title="향상된 마켓플레이스 관리 API",
    description="마켓플레이스 통합 관리, 모니터링 및 최적화 API",
    version="1.0.0"
)

def get_db_connection():
    """데이터베이스 연결"""
    try:
        # Docker 내부 연결 시도
        docker_config = DB_CONFIG.copy()
        docker_config['password'] = 'postgres'  # Docker 내부 비밀번호
        
        conn = psycopg2.connect(**docker_config)
        return conn
    except:
        # 외부 연결 시도
        conn = psycopg2.connect(**DB_CONFIG)
        return conn

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "향상된 마켓플레이스 관리 API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "marketplace_status": "/marketplace/status",
            "metrics": "/marketplace/metrics",
            "health": "/marketplace/health",
            "rate_limits": "/marketplace/rate-limits"
        }
    }

@app.get("/marketplace/status", response_model=List[MarketplaceStatus])
async def get_marketplace_status():
    """전체 마켓플레이스 상태 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 마켓플레이스별 최신 상태 조회
        cursor.execute("""
            WITH latest_health AS (
                SELECT DISTINCT ON (marketplace) 
                    marketplace, is_healthy, response_time, checked_at
                FROM marketplace_health_status 
                ORDER BY marketplace, checked_at DESC
            ),
            latest_metrics AS (
                SELECT DISTINCT ON (marketplace)
                    marketplace, 
                    total_requests, 
                    successful_requests, 
                    failed_requests,
                    collected_at
                FROM marketplace_metrics 
                ORDER BY marketplace, collected_at DESC
            ),
            circuit_status AS (
                SELECT marketplace, state, failure_count 
                FROM marketplace_circuit_breaker_status
            ),
            rate_config AS (
                SELECT marketplace, max_requests_per_second, burst_allowance
                FROM marketplace_rate_limits
            )
            SELECT 
                rl.marketplace,
                COALESCE(lh.is_healthy, true) as is_healthy,
                lh.response_time,
                COALESCE(lm.total_requests, 0) as total_requests,
                COALESCE(lm.successful_requests, 0) as successful_requests,
                COALESCE(lm.failed_requests, 0) as failed_requests,
                cs.state as circuit_breaker_state,
                cs.failure_count,
                rl.max_requests_per_second,
                rl.burst_allowance,
                lh.checked_at,
                lm.collected_at
            FROM rate_config rl
            LEFT JOIN latest_health lh ON rl.marketplace = lh.marketplace
            LEFT JOIN latest_metrics lm ON rl.marketplace = lm.marketplace  
            LEFT JOIN circuit_status cs ON rl.marketplace = cs.marketplace
            ORDER BY rl.marketplace
        """)
        
        results = cursor.fetchall()
        
        status_list = []
        for row in results:
            # 성공률 계산
            success_rate = 0.0
            if row['total_requests'] > 0:
                success_rate = (row['successful_requests'] / row['total_requests']) * 100
            
            # 가용 토큰 시뮬레이션 (실제로는 메모리에서 관리)
            available_tokens = row['burst_allowance']
            
            status = MarketplaceStatus(
                marketplace=row['marketplace'],
                is_healthy=row['is_healthy'],
                response_time=row['response_time'],
                success_rate=round(success_rate, 1),
                total_requests=row['total_requests'],
                circuit_breaker_state=row['circuit_breaker_state'] or 'CLOSED',
                available_tokens=available_tokens,
                last_check=row['checked_at'].isoformat() if row['checked_at'] else None
            )
            status_list.append(status)
        
        conn.close()
        return status_list
        
    except Exception as e:
        logger.error(f"마켓플레이스 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/marketplace/metrics")
async def get_marketplace_metrics(marketplace: Optional[str] = None, hours: int = 24):
    """마켓플레이스 메트릭 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 시간 필터링
        time_filter = f"collected_at >= CURRENT_TIMESTAMP - INTERVAL '{hours} hours'"
        marketplace_filter = ""
        params = []
        
        if marketplace:
            marketplace_filter = "AND marketplace = %s"
            params.append(marketplace)
        
        # 시간별 메트릭 조회
        query = f"""
            SELECT 
                marketplace,
                DATE_TRUNC('hour', collected_at) as hour,
                SUM(total_requests) as total_requests,
                SUM(successful_requests) as successful_requests,
                SUM(failed_requests) as failed_requests,
                SUM(rate_limited_requests) as rate_limited_requests,
                AVG(avg_response_time) as avg_response_time,
                COUNT(*) as data_points
            FROM marketplace_metrics 
            WHERE {time_filter} {marketplace_filter}
            GROUP BY marketplace, DATE_TRUNC('hour', collected_at)
            ORDER BY marketplace, hour DESC
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 데이터 구조화
        metrics = {}
        for row in results:
            mp = row['marketplace']
            if mp not in metrics:
                metrics[mp] = {
                    'marketplace': mp,
                    'timespan_hours': hours,
                    'hourly_data': [],
                    'summary': {
                        'total_requests': 0,
                        'total_successes': 0, 
                        'total_failures': 0,
                        'total_rate_limited': 0,
                        'avg_response_time': 0,
                        'success_rate': 0
                    }
                }
            
            # 시간별 데이터
            hourly_data = {
                'hour': row['hour'].isoformat(),
                'requests': row['total_requests'],
                'successes': row['successful_requests'],
                'failures': row['failed_requests'],
                'rate_limited': row['rate_limited_requests'],
                'avg_response_time': round(row['avg_response_time'], 3),
                'success_rate': round((row['successful_requests'] / max(1, row['total_requests'])) * 100, 1)
            }
            metrics[mp]['hourly_data'].append(hourly_data)
            
            # 요약 통계 누적
            summary = metrics[mp]['summary']
            summary['total_requests'] += row['total_requests']
            summary['total_successes'] += row['successful_requests']
            summary['total_failures'] += row['failed_requests']
            summary['total_rate_limited'] += row['rate_limited_requests']
        
        # 요약 통계 계산
        for mp_data in metrics.values():
            summary = mp_data['summary']
            if summary['total_requests'] > 0:
                summary['success_rate'] = round((summary['total_successes'] / summary['total_requests']) * 100, 1)
            
            # 평균 응답시간 계산 (가중 평균)
            total_response_time = 0
            total_weight = 0
            for hourly in mp_data['hourly_data']:
                weight = hourly['requests']
                total_response_time += hourly['avg_response_time'] * weight
                total_weight += weight
            
            if total_weight > 0:
                summary['avg_response_time'] = round(total_response_time / total_weight, 3)
        
        conn.close()
        
        if marketplace:
            return metrics.get(marketplace, {})
        else:
            return list(metrics.values())
        
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/marketplace/health")
async def get_marketplace_health():
    """마켓플레이스 헬스 체크 상태"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 최근 24시간 헬스 체크 이력
        cursor.execute("""
            SELECT 
                marketplace,
                is_healthy,
                response_time,
                error_message,
                checked_at
            FROM marketplace_health_status 
            WHERE checked_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY marketplace, checked_at DESC
        """)
        
        results = cursor.fetchall()
        
        # 마켓플레이스별 그룹화
        health_data = {}
        for row in results:
            mp = row['marketplace']
            if mp not in health_data:
                health_data[mp] = {
                    'marketplace': mp,
                    'current_status': row['is_healthy'],
                    'last_check': row['checked_at'].isoformat(),
                    'recent_checks': [],
                    'uptime_24h': 0,
                    'avg_response_time': 0
                }
            
            # 최근 체크 이력
            check_data = {
                'timestamp': row['checked_at'].isoformat(),
                'is_healthy': row['is_healthy'],
                'response_time': row['response_time'],
                'error_message': row['error_message']
            }
            health_data[mp]['recent_checks'].append(check_data)
        
        # 가동률 및 평균 응답시간 계산
        for mp_data in health_data.values():
            checks = mp_data['recent_checks']
            if checks:
                healthy_count = sum(1 for check in checks if check['is_healthy'])
                mp_data['uptime_24h'] = round((healthy_count / len(checks)) * 100, 1)
                
                # 응답시간 평균 (정상 상태만)
                response_times = [check['response_time'] for check in checks 
                                if check['is_healthy'] and check['response_time']]
                if response_times:
                    mp_data['avg_response_time'] = round(sum(response_times) / len(response_times), 3)
        
        conn.close()
        return list(health_data.values())
        
    except Exception as e:
        logger.error(f"헬스 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/marketplace/rate-limits")
async def get_rate_limits():
    """현재 율 제한 설정 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                marketplace,
                max_requests_per_second,
                max_requests_per_minute, 
                max_requests_per_hour,
                burst_allowance,
                current_rate,
                last_optimized_at,
                optimization_count
            FROM marketplace_rate_limits
            ORDER BY marketplace
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"율 제한 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/marketplace/rate-limits")
async def update_rate_limits(update: RateLimitUpdate):
    """율 제한 설정 업데이트"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE marketplace_rate_limits 
            SET 
                max_requests_per_second = %s,
                current_rate = %s,
                burst_allowance = %s,
                last_optimized_at = CURRENT_TIMESTAMP,
                optimization_count = optimization_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE marketplace = %s
        """, (
            update.max_requests_per_second,
            update.max_requests_per_second,
            update.burst_allowance,
            update.marketplace
        ))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"마켓플레이스 '{update.marketplace}'를 찾을 수 없습니다")
        
        conn.commit()
        conn.close()
        
        return {"message": f"{update.marketplace} 율 제한 설정이 업데이트되었습니다"}
        
    except Exception as e:
        logger.error(f"율 제한 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/marketplace/simulate-requests")
async def simulate_requests(background_tasks: BackgroundTasks, 
                          marketplace: str, count: int = 10):
    """요청 시뮬레이션 (테스트용)"""
    
    def simulate_background(mp: str, request_count: int):
        """백그라운드에서 요청 시뮬레이션"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 메트릭 데이터 생성
            successful = max(1, int(request_count * 0.9))  # 90% 성공률
            failed = request_count - successful
            rate_limited = max(0, int(request_count * 0.05))  # 5% 율 제한
            avg_response = 0.100 + (0.050 * (request_count / 10))  # 요청 수에 따른 응답시간
            
            cursor.execute("""
                INSERT INTO marketplace_metrics 
                (marketplace, total_requests, successful_requests, failed_requests, 
                 rate_limited_requests, avg_response_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (mp, request_count, successful, failed, rate_limited, avg_response))
            
            # 헬스 상태 업데이트
            is_healthy = failed < (request_count * 0.2)  # 실패율 20% 미만이면 정상
            response_time = avg_response if is_healthy else None
            error_msg = "높은 실패율" if not is_healthy else None
            
            cursor.execute("""
                INSERT INTO marketplace_health_status 
                (marketplace, is_healthy, response_time, error_message)
                VALUES (%s, %s, %s, %s)
            """, (mp, is_healthy, response_time, error_msg))
            
            conn.commit()
            conn.close()
            
            logger.info(f"{mp} 요청 시뮬레이션 완료: {request_count}개 요청 처리")
            
        except Exception as e:
            logger.error(f"요청 시뮬레이션 오류: {e}")
    
    # 유효한 마켓플레이스 확인
    valid_marketplaces = ['coupang', 'naver', 'eleven']
    if marketplace not in valid_marketplaces:
        raise HTTPException(status_code=400, 
                          detail=f"유효하지 않은 마켓플레이스. 허용된 값: {valid_marketplaces}")
    
    if count < 1 or count > 1000:
        raise HTTPException(status_code=400, 
                          detail="요청 수는 1~1000 사이여야 합니다")
    
    # 백그라운드 작업으로 시뮬레이션 실행
    background_tasks.add_task(simulate_background, marketplace, count)
    
    return {
        "message": f"{marketplace}에 대한 {count}개 요청 시뮬레이션이 백그라운드에서 시작되었습니다",
        "marketplace": marketplace,
        "request_count": count
    }

@app.get("/marketplace/recommendations")
async def get_performance_recommendations():
    """성능 개선 권장사항"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 최근 메트릭 기반 분석
        cursor.execute("""
            SELECT 
                marketplace,
                SUM(total_requests) as total_requests,
                SUM(successful_requests) as successful_requests,
                SUM(failed_requests) as failed_requests,
                SUM(rate_limited_requests) as rate_limited_requests,
                AVG(avg_response_time) as avg_response_time
            FROM marketplace_metrics 
            WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            GROUP BY marketplace
        """)
        
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            mp = row['marketplace']
            total = row['total_requests']
            
            if total == 0:
                continue
            
            # 실패율 분석
            failure_rate = row['failed_requests'] / total
            if failure_rate > 0.1:  # 10% 이상
                recommendations.append({
                    'marketplace': mp,
                    'type': 'high_failure_rate',
                    'severity': 'high' if failure_rate > 0.2 else 'medium',
                    'message': f"{mp} 실패율이 {failure_rate:.1%}로 높습니다",
                    'suggestion': "회로 차단기 설정 조정 또는 재시도 로직 개선을 고려하세요",
                    'metric_value': failure_rate
                })
            
            # 율 제한 분석
            rate_limit_rate = row['rate_limited_requests'] / total
            if rate_limit_rate > 0.05:  # 5% 이상
                recommendations.append({
                    'marketplace': mp,
                    'type': 'high_rate_limiting',
                    'severity': 'medium',
                    'message': f"{mp} 율 제한이 {rate_limit_rate:.1%}로 높습니다",
                    'suggestion': "요청 빈도를 낮추거나 더 낮은 우선순위로 처리하세요",
                    'metric_value': rate_limit_rate
                })
            
            # 응답시간 분석
            if row['avg_response_time'] > 5.0:  # 5초 이상
                recommendations.append({
                    'marketplace': mp,
                    'type': 'slow_response',
                    'severity': 'low',
                    'message': f"{mp} 평균 응답시간이 {row['avg_response_time']:.1f}초로 느립니다",
                    'suggestion': "타임아웃 설정 조정 또는 요청 최적화를 고려하세요",
                    'metric_value': row['avg_response_time']
                })
        
        conn.close()
        
        # 우선순위 정렬
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
        
        return {
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"권장사항 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")