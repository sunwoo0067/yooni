#!/usr/bin/env python3
"""
향상된 마켓플레이스 통합 관리자
- 율 제한 최적화
- 연결 안정성 개선  
- 실시간 모니터링
- 자동 failover
"""
import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import queue
import sys
import os

# 기존 마켓플레이스 클라이언트 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from coupang.coupang_client import CoupangClient
from naver.naver_client import NaverClient  
from eleven.eleven_client import ElevenClient

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """율 제한 설정"""
    max_requests_per_second: float
    max_requests_per_minute: int
    max_requests_per_hour: int
    burst_allowance: int = 5
    backoff_base: float = 1.0
    max_backoff: float = 60.0


@dataclass
class MarketplaceEndpoint:
    """마켓플레이스 엔드포인트 정보"""
    name: str
    url: str
    rate_limit: RateLimitConfig
    priority: int = 1
    health_check_interval: int = 300  # 5분


@dataclass
class RequestMetrics:
    """요청 메트릭"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None


class TokenBucket:
    """토큰 버킷 알고리즘 구현"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # 초당 토큰 추가율
        self.capacity = capacity  # 최대 토큰 수
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """토큰 소비 시도"""
        with self.lock:
            now = time.time()
            # 토큰 추가
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            # 토큰 소비 가능 여부 확인
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """토큰이 사용 가능해질 때까지의 시간"""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.rate


class CircuitBreaker:
    """회로 차단기 패턴 구현"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """회로 차단기를 통한 함수 호출"""
        with self.lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                
                raise e


class EnhancedMarketplaceManager:
    """향상된 마켓플레이스 통합 관리자"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        
        # 율 제한 설정
        self.rate_limits = {
            'coupang': RateLimitConfig(
                max_requests_per_second=10.0,
                max_requests_per_minute=500,
                max_requests_per_hour=10000,
                burst_allowance=15
            ),
            'naver': RateLimitConfig(
                max_requests_per_second=20.0,
                max_requests_per_minute=1000,
                max_requests_per_hour=20000,
                burst_allowance=30
            ),
            'eleven': RateLimitConfig(
                max_requests_per_second=15.0,
                max_requests_per_minute=800,
                max_requests_per_hour=15000,
                burst_allowance=20
            )
        }
        
        # 토큰 버킷 초기화
        self.token_buckets = {
            marketplace: TokenBucket(
                rate=config.max_requests_per_second,
                capacity=config.burst_allowance
            )
            for marketplace, config in self.rate_limits.items()
        }
        
        # 회로 차단기 초기화
        self.circuit_breakers = {
            marketplace: CircuitBreaker(failure_threshold=5, timeout=60)
            for marketplace in self.rate_limits.keys()
        }
        
        # 메트릭 추적
        self.metrics = {
            marketplace: RequestMetrics()
            for marketplace in self.rate_limits.keys()
        }
        
        # 클라이언트 초기화
        self.clients = {}
        self._init_clients()
        
        # 요청 큐
        self.request_queues = {
            marketplace: queue.PriorityQueue()
            for marketplace in self.rate_limits.keys()
        }
        
        # 워커 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 백그라운드 작업 시작
        self._start_background_workers()
        
        logger.info("향상된 마켓플레이스 관리자 초기화 완료")
    
    def _init_clients(self):
        """마켓플레이스 클라이언트 초기화"""
        try:
            # 세션 설정 (연결 풀링, 재시도 등)
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 환경변수에서 인증 정보 로드 (실제 환경에서는 설정)
            self.clients = {
                'coupang': CoupangClient(session=session),
                'naver': NaverClient(session=session),
                'eleven': ElevenClient(session=session)
            }
            
            logger.info("마켓플레이스 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"클라이언트 초기화 실패: {e}")
    
    def _start_background_workers(self):
        """백그라운드 워커 시작"""
        # 요청 처리 워커
        for marketplace in self.rate_limits.keys():
            threading.Thread(
                target=self._request_worker,
                args=(marketplace,),
                daemon=True
            ).start()
        
        # 헬스 체크 워커
        threading.Thread(target=self._health_check_worker, daemon=True).start()
        
        # 메트릭 수집 워커
        threading.Thread(target=self._metrics_collector_worker, daemon=True).start()
    
    def _request_worker(self, marketplace: str):
        """마켓플레이스별 요청 처리 워커"""
        request_queue = self.request_queues[marketplace]
        token_bucket = self.token_buckets[marketplace]
        
        while True:
            try:
                # 우선순위 큐에서 요청 가져오기
                priority, request_data = request_queue.get(timeout=1)
                
                # 토큰 버킷에서 토큰 소비 대기
                while not token_bucket.consume():
                    wait_time = token_bucket.time_until_available()
                    time.sleep(min(wait_time, 0.1))
                
                # 요청 처리
                self._execute_request(marketplace, request_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"{marketplace} 요청 워커 오류: {e}")
    
    def _execute_request(self, marketplace: str, request_data: Dict[str, Any]):
        """실제 요청 실행"""
        start_time = time.time()
        metrics = self.metrics[marketplace]
        circuit_breaker = self.circuit_breakers[marketplace]
        
        try:
            # 회로 차단기를 통한 요청 실행
            response = circuit_breaker.call(
                self._make_api_request,
                marketplace,
                request_data
            )
            
            # 성공 메트릭 업데이트
            response_time = time.time() - start_time
            metrics.successful_requests += 1
            metrics.avg_response_time = (
                (metrics.avg_response_time * (metrics.successful_requests - 1) + response_time) /
                metrics.successful_requests
            )
            
            # 결과 콜백 호출
            if 'callback' in request_data:
                request_data['callback'](response, None)
                
        except Exception as e:
            # 실패 메트릭 업데이트
            metrics.failed_requests += 1
            
            if '429' in str(e) or 'rate limit' in str(e).lower():
                metrics.rate_limited_requests += 1
            
            # 오류 콜백 호출
            if 'callback' in request_data:
                request_data['callback'](None, e)
            
            logger.error(f"{marketplace} API 요청 실패: {e}")
        
        finally:
            metrics.total_requests += 1
            metrics.last_request_time = datetime.now()
    
    def _make_api_request(self, marketplace: str, request_data: Dict[str, Any]) -> Any:
        """실제 API 요청 수행"""
        client = self.clients[marketplace]
        method = request_data['method']
        endpoint = request_data['endpoint']
        params = request_data.get('params', {})
        data = request_data.get('data', {})
        
        # 마켓플레이스별 API 호출
        if marketplace == 'coupang':
            return self._call_coupang_api(client, method, endpoint, params, data)
        elif marketplace == 'naver':
            return self._call_naver_api(client, method, endpoint, params, data)
        elif marketplace == 'eleven':
            return self._call_eleven_api(client, method, endpoint, params, data)
        else:
            raise ValueError(f"지원되지 않는 마켓플레이스: {marketplace}")
    
    def _call_coupang_api(self, client, method: str, endpoint: str, params: Dict, data: Dict) -> Any:
        """쿠팡 API 호출"""
        if method == 'GET':
            if 'products' in endpoint:
                return client.get_products(**params)
            elif 'orders' in endpoint:
                return client.get_orders(**params)
            # 추가 엔드포인트 처리
        elif method == 'POST':
            if 'products' in endpoint:
                return client.create_product(data)
            elif 'orders' in endpoint:
                return client.update_order(data)
        
        raise ValueError(f"지원되지 않는 쿠팡 API: {method} {endpoint}")
    
    def _call_naver_api(self, client, method: str, endpoint: str, params: Dict, data: Dict) -> Any:
        """네이버 API 호출"""
        if method == 'GET':
            if 'products' in endpoint:
                return client.get_products(**params)
            elif 'orders' in endpoint:
                return client.get_orders(**params)
        elif method == 'POST':
            if 'products' in endpoint:
                return client.create_product(data)
        
        raise ValueError(f"지원되지 않는 네이버 API: {method} {endpoint}")
    
    def _call_eleven_api(self, client, method: str, endpoint: str, params: Dict, data: Dict) -> Any:
        """11번가 API 호출"""
        if method == 'GET':
            if 'products' in endpoint:
                return client.get_products(**params)
            elif 'orders' in endpoint:
                return client.get_orders(**params)
        elif method == 'POST':
            if 'products' in endpoint:
                return client.create_product(data)
        
        raise ValueError(f"지원되지 않는 11번가 API: {method} {endpoint}")
    
    def _health_check_worker(self):
        """헬스 체크 워커"""
        while True:
            try:
                for marketplace in self.rate_limits.keys():
                    self._check_marketplace_health(marketplace)
                
                time.sleep(300)  # 5분마다 체크
                
            except Exception as e:
                logger.error(f"헬스 체크 오류: {e}")
                time.sleep(60)
    
    def _check_marketplace_health(self, marketplace: str):
        """마켓플레이스 헬스 체크"""
        try:
            # 간단한 API 호출로 헬스 체크
            request_data = {
                'method': 'GET',
                'endpoint': 'health',
                'params': {},
                'priority': 0  # 최고 우선순위
            }
            
            start_time = time.time()
            response = self._make_api_request(marketplace, request_data)
            response_time = time.time() - start_time
            
            # 헬스 상태 기록
            self._record_health_status(marketplace, True, response_time)
            
        except Exception as e:
            logger.warning(f"{marketplace} 헬스 체크 실패: {e}")
            self._record_health_status(marketplace, False, None)
    
    def _record_health_status(self, marketplace: str, is_healthy: bool, response_time: Optional[float]):
        """헬스 상태 기록"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO marketplace_health_status 
                (marketplace, is_healthy, response_time, checked_at)
                VALUES (%s, %s, %s, %s)
            """, (marketplace, is_healthy, response_time, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"헬스 상태 기록 실패: {e}")
    
    def _metrics_collector_worker(self):
        """메트릭 수집 워커"""
        while True:
            try:
                self._collect_and_store_metrics()
                time.sleep(60)  # 1분마다 수집
                
            except Exception as e:
                logger.error(f"메트릭 수집 오류: {e}")
                time.sleep(60)
    
    def _collect_and_store_metrics(self):
        """메트릭 수집 및 저장"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            for marketplace, metrics in self.metrics.items():
                cursor.execute("""
                    INSERT INTO marketplace_metrics 
                    (marketplace, total_requests, successful_requests, failed_requests,
                     rate_limited_requests, avg_response_time, collected_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    marketplace,
                    metrics.total_requests,
                    metrics.successful_requests, 
                    metrics.failed_requests,
                    metrics.rate_limited_requests,
                    metrics.avg_response_time,
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")
    
    def queue_request(self, marketplace: str, method: str, endpoint: str, 
                     params: Optional[Dict] = None, data: Optional[Dict] = None,
                     priority: int = 5, callback: Optional[callable] = None) -> bool:
        """요청을 큐에 추가"""
        try:
            request_data = {
                'method': method,
                'endpoint': endpoint,
                'params': params or {},
                'data': data or {},
                'callback': callback,
                'queued_at': datetime.now()
            }
            
            self.request_queues[marketplace].put((priority, request_data))
            return True
            
        except Exception as e:
            logger.error(f"요청 큐 추가 실패: {e}")
            return False
    
    async def bulk_request(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """대량 요청 처리"""
        results = []
        futures = []
        
        for request in requests:
            marketplace = request['marketplace']
            
            # 우선순위 기반 큐잉
            future = self.executor.submit(
                self._process_single_request,
                marketplace,
                request
            )
            futures.append(future)
        
        # 모든 요청 완료 대기
        for future in as_completed(futures):
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    def _process_single_request(self, marketplace: str, request: Dict[str, Any]) -> Any:
        """단일 요청 처리"""
        token_bucket = self.token_buckets[marketplace]
        
        # 토큰 소비 대기
        while not token_bucket.consume():
            wait_time = token_bucket.time_until_available()
            time.sleep(min(wait_time, 0.1))
        
        # 요청 실행
        return self._make_api_request(marketplace, request)
    
    def get_marketplace_status(self) -> Dict[str, Any]:
        """마켓플레이스 상태 조회"""
        status = {}
        
        for marketplace in self.rate_limits.keys():
            metrics = self.metrics[marketplace]
            circuit_breaker = self.circuit_breakers[marketplace]
            token_bucket = self.token_buckets[marketplace]
            
            success_rate = (
                metrics.successful_requests / max(1, metrics.total_requests) * 100
                if metrics.total_requests > 0 else 0
            )
            
            status[marketplace] = {
                'circuit_breaker_state': circuit_breaker.state,
                'available_tokens': int(token_bucket.tokens),
                'success_rate': f"{success_rate:.1f}%",
                'total_requests': metrics.total_requests,
                'avg_response_time': f"{metrics.avg_response_time:.3f}s",
                'rate_limited_count': metrics.rate_limited_requests,
                'last_request': metrics.last_request_time.isoformat() if metrics.last_request_time else None
            }
        
        return status
    
    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """성능 개선 권장사항"""
        recommendations = []
        
        for marketplace, metrics in self.metrics.items():
            if metrics.total_requests == 0:
                continue
            
            # 높은 실패율
            failure_rate = metrics.failed_requests / metrics.total_requests
            if failure_rate > 0.1:  # 10% 이상
                recommendations.append({
                    'marketplace': marketplace,
                    'type': 'high_failure_rate',
                    'message': f"{marketplace} 실패율이 {failure_rate:.1%}로 높습니다",
                    'suggestion': "회로 차단기 설정 조정 또는 재시도 로직 개선을 고려하세요"
                })
            
            # 높은 율 제한
            rate_limit_rate = metrics.rate_limited_requests / metrics.total_requests
            if rate_limit_rate > 0.05:  # 5% 이상
                recommendations.append({
                    'marketplace': marketplace,
                    'type': 'high_rate_limiting',
                    'message': f"{marketplace} 율 제한이 {rate_limit_rate:.1%}로 높습니다",
                    'suggestion': "요청 빈도를 낮추거나 더 낮은 우선순위로 처리하세요"
                })
            
            # 느린 응답시간
            if metrics.avg_response_time > 5.0:  # 5초 이상
                recommendations.append({
                    'marketplace': marketplace,
                    'type': 'slow_response',
                    'message': f"{marketplace} 평균 응답시간이 {metrics.avg_response_time:.1f}초로 느립니다",
                    'suggestion': "타임아웃 설정 조정 또는 요청 최적화를 고려하세요"
                })
        
        return recommendations
    
    def optimize_rate_limits(self):
        """율 제한 자동 최적화"""
        for marketplace, metrics in self.metrics.items():
            if metrics.total_requests < 100:  # 충분한 데이터가 없으면 건너뛰기
                continue
            
            rate_limit_config = self.rate_limits[marketplace]
            
            # 율 제한 빈도가 높으면 요청 속도 감소
            rate_limit_rate = metrics.rate_limited_requests / metrics.total_requests
            if rate_limit_rate > 0.1:
                new_rate = rate_limit_config.max_requests_per_second * 0.8
                rate_limit_config.max_requests_per_second = max(1.0, new_rate)
                
                # 토큰 버킷 업데이트
                self.token_buckets[marketplace] = TokenBucket(
                    rate=new_rate,
                    capacity=rate_limit_config.burst_allowance
                )
                
                logger.info(f"{marketplace} 율 제한 최적화: {new_rate:.1f} req/sec")
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        logger.info("마켓플레이스 관리자 정리 완료")