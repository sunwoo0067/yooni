"""
메트릭 수집기
시스템, 비즈니스, 성능 메트릭을 수집하고 저장합니다.
"""
import asyncio
import psutil
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

from ..db.connection_pool import get_database_pool
from ..core.structured_logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """메트릭 수집 및 관리 클래스"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self._collection_task = None
        self._db_pool = None
        
        # 시스템 메트릭 수집 간격 (초)
        self.system_metrics_interval = 60
        
        logger.info("메트릭 수집기 초기화")
    
    def start_collection(self):
        """백그라운드 메트릭 수집 시작"""
        if self._collection_task is None:
            self._collection_task = asyncio.create_task(self._collect_system_metrics())
            logger.info("시스템 메트릭 수집 시작")
    
    def stop_collection(self):
        """메트릭 수집 중지"""
        if self._collection_task:
            self._collection_task.cancel()
            self._collection_task = None
            logger.info("시스템 메트릭 수집 중지")
    
    async def _collect_system_metrics(self):
        """시스템 메트릭 주기적 수집"""
        while True:
            try:
                # CPU 사용률
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_gauge('system.cpu.usage', cpu_percent)
                
                # 메모리 사용률
                memory = psutil.virtual_memory()
                self.record_gauge('system.memory.usage', memory.percent)
                self.record_gauge('system.memory.available', memory.available / (1024 * 1024))  # MB
                
                # 디스크 사용률
                disk = psutil.disk_usage('/')
                self.record_gauge('system.disk.usage', disk.percent)
                self.record_gauge('system.disk.free', disk.free / (1024 * 1024 * 1024))  # GB
                
                # 네트워크 I/O
                net_io = psutil.net_io_counters()
                self.record_counter('system.network.bytes_sent', net_io.bytes_sent)
                self.record_counter('system.network.bytes_recv', net_io.bytes_recv)
                
                # 데이터베이스 연결 풀 상태
                if self._db_pool is None:
                    self._db_pool = get_database_pool()
                
                if self._db_pool:
                    pool_status = self._db_pool.get_pool_status()
                    self.record_gauge('database.pool.available', pool_status['available_connections'])
                    self.record_gauge('database.pool.size', pool_status['current_size'])
                
                # 프로세스 정보
                process = psutil.Process()
                self.record_gauge('process.cpu.percent', process.cpu_percent())
                self.record_gauge('process.memory.rss', process.memory_info().rss / (1024 * 1024))  # MB
                self.record_gauge('process.threads', process.num_threads())
                
                await asyncio.sleep(self.system_metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"시스템 메트릭 수집 오류: {e}")
                await asyncio.sleep(self.system_metrics_interval)
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """카운터 메트릭 기록 (누적값)"""
        key = self._make_key(name, tags)
        self.counters[key] += value
        
        # 타임시리즈 데이터 저장
        self._record_timeseries(name, self.counters[key], 'counter', tags)
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """게이지 메트릭 기록 (현재값)"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
        
        # 타임시리즈 데이터 저장
        self._record_timeseries(name, value, 'gauge', tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """히스토그램 메트릭 기록 (분포)"""
        key = self._make_key(name, tags)
        
        # 최근 1000개 값만 유지
        if len(self.histograms[key]) >= 1000:
            self.histograms[key].pop(0)
        
        self.histograms[key].append(value)
        
        # 통계 계산
        values = self.histograms[key]
        if values:
            stats = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'p50': self._percentile(values, 50),
                'p90': self._percentile(values, 90),
                'p99': self._percentile(values, 99)
            }
            
            # 각 통계를 개별 메트릭으로 저장
            for stat_name, stat_value in stats.items():
                self._record_timeseries(f"{name}.{stat_name}", stat_value, 'histogram', tags)
    
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """실행 시간 측정 컨텍스트 매니저"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # ms
            self.record_histogram(f"{name}.duration", duration, tags)
    
    async def atimer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """비동기 실행 시간 측정"""
        class AsyncTimer:
            def __init__(self, collector, metric_name, metric_tags):
                self.collector = collector
                self.name = metric_name
                self.tags = metric_tags
                self.start_time = None
            
            async def __aenter__(self):
                self.start_time = time.time()
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                duration = (time.time() - self.start_time) * 1000  # ms
                self.collector.record_histogram(f"{self.name}.duration", duration, self.tags)
        
        return AsyncTimer(self, name, tags)
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, 
                          duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """API 요청 메트릭 기록"""
        base_tags = {
            'method': method,
            'endpoint': endpoint,
            'status': str(status_code),
            'status_group': f"{status_code // 100}xx"
        }
        
        if tags:
            base_tags.update(tags)
        
        # 요청 수
        self.record_counter('api.requests', tags=base_tags)
        
        # 응답 시간
        self.record_histogram('api.response_time', duration_ms, tags=base_tags)
        
        # 에러율
        if status_code >= 400:
            self.record_counter('api.errors', tags=base_tags)
    
    def record_business_metric(self, name: str, value: float, metric_type: str = 'gauge',
                             tags: Optional[Dict[str, str]] = None):
        """비즈니스 메트릭 기록"""
        business_tags = {'type': 'business'}
        if tags:
            business_tags.update(tags)
        
        if metric_type == 'counter':
            self.record_counter(f"business.{name}", value, business_tags)
        elif metric_type == 'gauge':
            self.record_gauge(f"business.{name}", value, business_tags)
        elif metric_type == 'histogram':
            self.record_histogram(f"business.{name}", value, business_tags)
    
    def get_metrics_summary(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """메트릭 요약 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)
        summary = {
            'counters': {},
            'gauges': {},
            'histograms': {},
            'timeseries': {}
        }
        
        # 카운터 요약
        for key, value in self.counters.items():
            name, tags = self._parse_key(key)
            if name not in summary['counters']:
                summary['counters'][name] = []
            summary['counters'][name].append({
                'value': value,
                'tags': tags
            })
        
        # 게이지 요약
        for key, value in self.gauges.items():
            name, tags = self._parse_key(key)
            if name not in summary['gauges']:
                summary['gauges'][name] = []
            summary['gauges'][name].append({
                'value': value,
                'tags': tags
            })
        
        # 히스토그램 요약
        for key, values in self.histograms.items():
            if values:
                name, tags = self._parse_key(key)
                if name not in summary['histograms']:
                    summary['histograms'][name] = []
                
                summary['histograms'][name].append({
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 50),
                    'p90': self._percentile(values, 90),
                    'p99': self._percentile(values, 99),
                    'tags': tags
                })
        
        # 타임시리즈 데이터
        for metric_name, datapoints in self.metrics_buffer.items():
            recent_points = [
                point for point in datapoints
                if datetime.fromisoformat(point['timestamp']) > cutoff_time
            ]
            if recent_points:
                summary['timeseries'][metric_name] = recent_points
        
        return summary
    
    def get_metric_timeseries(self, metric_name: str, 
                            time_range_minutes: int = 60) -> List[Dict[str, Any]]:
        """특정 메트릭의 시계열 데이터 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)
        
        datapoints = self.metrics_buffer.get(metric_name, [])
        return [
            point for point in datapoints
            if datetime.fromisoformat(point['timestamp']) > cutoff_time
        ]
    
    def _record_timeseries(self, name: str, value: float, metric_type: str, 
                          tags: Optional[Dict[str, str]] = None):
        """타임시리즈 데이터 저장"""
        datapoint = {
            'timestamp': datetime.now().isoformat(),
            'value': value,
            'type': metric_type
        }
        
        if tags:
            datapoint['tags'] = tags
        
        key = self._make_key(name, tags)
        self.metrics_buffer[key].append(datapoint)
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """메트릭 키 생성"""
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"
    
    def _parse_key(self, key: str) -> tuple:
        """메트릭 키 파싱"""
        parts = key.split(',', 1)
        name = parts[0]
        
        tags = {}
        if len(parts) > 1:
            for tag_pair in parts[1].split(','):
                k, v = tag_pair.split('=', 1)
                tags[k] = v
        
        return name, tags
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """백분위수 계산"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * (percentile / 100)
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[lower]
        
        return sorted_values[lower] * (upper - index) + sorted_values[upper] * (index - lower)
    
    async def persist_metrics(self):
        """메트릭을 데이터베이스에 저장"""
        if not self._db_pool:
            self._db_pool = get_database_pool()
        
        try:
            # 메트릭 요약 생성
            summary = self.get_metrics_summary(time_range_minutes=5)
            
            # JSON으로 직렬화
            metrics_json = json.dumps(summary)
            
            # 데이터베이스에 저장
            await self._db_pool.execute_query("""
                INSERT INTO metrics_snapshots (timestamp, metrics_data)
                VALUES (NOW(), %s)
            """, (metrics_json,))
            
            logger.info("메트릭 데이터 저장 완료")
            
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")


# 싱글톤 인스턴스
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """메트릭 수집기 인스턴스 반환"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector