#!/usr/bin/env python3
"""
성능 모니터링 시스템
- 실시간 메트릭 수집
- 성능 병목 지점 감지
- 리소스 사용량 추적
"""

import psutil
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import statistics
from collections import deque
from dataclasses import dataclass, asdict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    query_count: int
    avg_query_time_ms: float
    slow_queries: int
    collection_rate: float  # 상품/초
    error_rate: float

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 메트릭 저장용 큐 (최근 5분 데이터)
        self.metrics_queue = deque(maxlen=300)  # 1초마다 수집, 5분 = 300개
        
        # 이전 측정값 (델타 계산용)
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_net_io = psutil.net_io_counters()
        self.prev_query_count = 0
        
        # 모니터링 플래그
        self.monitoring = False
        self.monitor_thread = None
        
    def get_database_metrics(self) -> Dict[str, Any]:
        """데이터베이스 성능 메트릭 수집"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 활성 연결 수
                cursor.execute("""
                    SELECT COUNT(*) as active_connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_conn = cursor.fetchone()['active_connections']
                
                # 쿼리 통계
                cursor.execute("""
                    SELECT 
                        COUNT(*) as query_count,
                        AVG(mean_exec_time) as avg_query_time,
                        COUNT(CASE WHEN mean_exec_time > 1000 THEN 1 END) as slow_queries
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat%'
                """)
                query_stats = cursor.fetchone()
                
                # 최근 수집 속도
                cursor.execute("""
                    SELECT 
                        AVG(collected_count / NULLIF(processing_time_seconds, 0)) as collection_rate
                    FROM supplier_collection_logs
                    WHERE completed_at > NOW() - INTERVAL '5 minutes'
                    AND status = 'completed'
                """)
                collection_rate = cursor.fetchone()['collection_rate'] or 0
                
                # 오류율
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / 
                        NULLIF(COUNT(*), 0) * 100 as error_rate
                    FROM supplier_collection_logs
                    WHERE started_at > NOW() - INTERVAL '1 hour'
                """)
                error_rate = cursor.fetchone()['error_rate'] or 0
                
                return {
                    'active_connections': active_conn,
                    'query_count': query_stats['query_count'] or 0,
                    'avg_query_time_ms': float(query_stats['avg_query_time'] or 0),
                    'slow_queries': query_stats['slow_queries'] or 0,
                    'collection_rate': float(collection_rate),
                    'error_rate': float(error_rate)
                }
                
        except Exception as e:
            logger.error(f"데이터베이스 메트릭 수집 실패: {e}")
            return {
                'active_connections': 0,
                'query_count': 0,
                'avg_query_time_ms': 0,
                'slow_queries': 0,
                'collection_rate': 0,
                'error_rate': 0
            }
    
    def collect_metrics(self) -> PerformanceMetrics:
        """시스템 및 애플리케이션 메트릭 수집"""
        # CPU 및 메모리
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # 디스크 I/O (델타)
        current_disk = psutil.disk_io_counters()
        disk_read_mb = (current_disk.read_bytes - self.prev_disk_io.read_bytes) / 1024 / 1024
        disk_write_mb = (current_disk.write_bytes - self.prev_disk_io.write_bytes) / 1024 / 1024
        self.prev_disk_io = current_disk
        
        # 네트워크 I/O (델타)
        current_net = psutil.net_io_counters()
        net_sent_mb = (current_net.bytes_sent - self.prev_net_io.bytes_sent) / 1024 / 1024
        net_recv_mb = (current_net.bytes_recv - self.prev_net_io.bytes_recv) / 1024 / 1024
        self.prev_net_io = current_net
        
        # 데이터베이스 메트릭
        db_metrics = self.get_database_metrics()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / 1024 / 1024,
            disk_io_read_mb=max(0, disk_read_mb),
            disk_io_write_mb=max(0, disk_write_mb),
            network_sent_mb=max(0, net_sent_mb),
            network_recv_mb=max(0, net_recv_mb),
            **db_metrics
        )
    
    def analyze_performance(self) -> Dict[str, Any]:
        """성능 분석 및 병목 지점 감지"""
        if len(self.metrics_queue) < 10:
            return {"status": "insufficient_data"}
        
        recent_metrics = list(self.metrics_queue)[-60:]  # 최근 1분
        
        # 평균 계산
        avg_cpu = statistics.mean(m.cpu_percent for m in recent_metrics)
        avg_memory = statistics.mean(m.memory_percent for m in recent_metrics)
        avg_query_time = statistics.mean(m.avg_query_time_ms for m in recent_metrics)
        avg_collection_rate = statistics.mean(m.collection_rate for m in recent_metrics)
        
        # 병목 지점 감지
        bottlenecks = []
        recommendations = []
        
        # CPU 병목
        if avg_cpu > 80:
            bottlenecks.append("CPU")
            recommendations.append("CPU 사용률이 높습니다. 병렬 처리 또는 스케일 아웃을 고려하세요.")
        
        # 메모리 병목
        if avg_memory > 85:
            bottlenecks.append("Memory")
            recommendations.append("메모리 사용률이 높습니다. 배치 크기를 줄이거나 메모리를 증설하세요.")
        
        # 데이터베이스 병목
        if avg_query_time > 100:
            bottlenecks.append("Database")
            recommendations.append("쿼리 실행 시간이 깁니다. 인덱스 최적화나 쿼리 튜닝이 필요합니다.")
        
        # 수집 속도 저하
        if avg_collection_rate < 50 and avg_collection_rate > 0:
            bottlenecks.append("Collection")
            recommendations.append("수집 속도가 느립니다. API 연결 상태나 네트워크를 확인하세요.")
        
        # 성능 점수 계산 (0-100)
        performance_score = 100
        performance_score -= max(0, avg_cpu - 50) * 0.5  # CPU 50% 이상시 감점
        performance_score -= max(0, avg_memory - 50) * 0.3  # 메모리 50% 이상시 감점
        performance_score -= max(0, avg_query_time - 50) * 0.2  # 쿼리 50ms 이상시 감점
        performance_score = max(0, min(100, performance_score))
        
        return {
            "status": "analyzed",
            "performance_score": round(performance_score, 1),
            "metrics": {
                "avg_cpu_percent": round(avg_cpu, 1),
                "avg_memory_percent": round(avg_memory, 1),
                "avg_query_time_ms": round(avg_query_time, 1),
                "avg_collection_rate": round(avg_collection_rate, 1)
            },
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def save_metrics_to_db(self, metrics: PerformanceMetrics):
        """메트릭을 데이터베이스에 저장"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, metrics_data, performance_score)
                    VALUES (%s, %s, %s)
                """, (
                    metrics.timestamp,
                    json.dumps(asdict(metrics), default=str),
                    self.analyze_performance().get('performance_score', 0)
                ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")
            self.conn.rollback()
    
    def monitor_loop(self):
        """모니터링 루프"""
        logger.info("🚀 성능 모니터링 시작")
        
        while self.monitoring:
            try:
                # 메트릭 수집
                metrics = self.collect_metrics()
                self.metrics_queue.append(metrics)
                
                # 10초마다 DB 저장
                if len(self.metrics_queue) % 10 == 0:
                    self.save_metrics_to_db(metrics)
                
                # 성능 저하 감지
                analysis = self.analyze_performance()
                if analysis.get('performance_score', 100) < 70:
                    logger.warning(f"⚠️ 성능 저하 감지: {analysis['performance_score']}점")
                    logger.warning(f"   병목: {', '.join(analysis['bottlenecks'])}")
                
                time.sleep(1)  # 1초 대기
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(5)
    
    def start(self):
        """모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("✅ 성능 모니터링 시작됨")
    
    def stop(self):
        """모니터링 중지"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
            logger.info("🛑 성능 모니터링 중지됨")
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭 조회"""
        if not self.metrics_queue:
            return {"error": "No metrics available"}
        
        latest = self.metrics_queue[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_mb": round(latest.memory_mb, 1),
            "disk_io": {
                "read_mb_s": round(latest.disk_io_read_mb, 2),
                "write_mb_s": round(latest.disk_io_write_mb, 2)
            },
            "network": {
                "sent_mb_s": round(latest.network_sent_mb, 2),
                "recv_mb_s": round(latest.network_recv_mb, 2)
            },
            "database": {
                "active_connections": latest.active_connections,
                "avg_query_time_ms": round(latest.avg_query_time_ms, 1),
                "slow_queries": latest.slow_queries
            },
            "application": {
                "collection_rate": round(latest.collection_rate, 1),
                "error_rate": round(latest.error_rate, 1)
            }
        }

def main():
    """테스트 실행"""
    monitor = PerformanceMonitor()
    monitor.start()
    
    try:
        # 30초 동안 모니터링
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                metrics = monitor.get_realtime_metrics()
                print(f"\n📊 실시간 메트릭:")
                print(f"   CPU: {metrics['cpu_percent']}%")
                print(f"   Memory: {metrics['memory_percent']}%")
                print(f"   Collection Rate: {metrics['application']['collection_rate']} items/sec")
                
                if i == 15:
                    analysis = monitor.analyze_performance()
                    print(f"\n🎯 성능 분석:")
                    print(f"   점수: {analysis.get('performance_score', 'N/A')}점")
                    if 'bottlenecks' in analysis:
                        print(f"   병목: {', '.join(analysis['bottlenecks'])}")
                
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()