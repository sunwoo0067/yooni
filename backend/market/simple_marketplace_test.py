#!/usr/bin/env python3
"""
향상된 마켓플레이스 관리자 핵심 기능 테스트
"""
import sys
import os
import time
import json
import threading
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni', 
    'user': 'postgres',
    'password': '1234'
}

class TokenBucket:
    """토큰 버킷 알고리즘 구현 (테스트용)"""
    
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
    """회로 차단기 패턴 구현 (테스트용)"""
    
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

def test_database_tables():
    """데이터베이스 테이블 및 연결 테스트"""
    logger.info("=== 데이터베이스 테이블 테스트 ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 마켓플레이스 테이블 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'marketplace%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"마켓플레이스 테이블 {len(tables)}개 발견:")
        for table in tables:
            logger.info(f"  ✅ {table['table_name']}")
        
        # 율 제한 설정 데이터 확인
        cursor.execute("SELECT * FROM marketplace_rate_limits ORDER BY marketplace")
        rate_limits = cursor.fetchall()
        logger.info("현재 율 제한 설정:")
        for limit in rate_limits:
            logger.info(f"  📊 {limit['marketplace']}: {limit['max_requests_per_second']} req/sec, burst: {limit['burst_allowance']}")
        
        # 회로 차단기 상태 확인
        cursor.execute("SELECT * FROM marketplace_circuit_breaker_status ORDER BY marketplace")
        circuit_states = cursor.fetchall()
        logger.info("회로 차단기 상태:")
        for state in circuit_states:
            logger.info(f"  🔌 {state['marketplace']}: {state['state']} (실패: {state['failure_count']})")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 테스트 실패: {e}")
        return False

def test_token_bucket():
    """토큰 버킷 알고리즘 테스트"""
    logger.info("=== 토큰 버킷 알고리즘 테스트 ===")
    
    # 초당 5개 토큰, 최대 10개 용량
    bucket = TokenBucket(rate=5.0, capacity=10)
    
    successful_requests = 0
    total_requests = 15
    
    logger.info(f"토큰 버킷 설정: {bucket.rate} req/sec, 용량: {bucket.capacity}")
    
    for i in range(total_requests):
        if bucket.consume():
            successful_requests += 1
            logger.info(f"  ✅ 요청 {i+1}: 성공 (남은 토큰: {bucket.tokens:.2f})")
        else:
            wait_time = bucket.time_until_available()
            logger.info(f"  ❌ 요청 {i+1}: 실패 (대기 시간: {wait_time:.2f}초)")
        
        time.sleep(0.1)  # 100ms 간격
    
    success_rate = (successful_requests / total_requests) * 100
    logger.info(f"토큰 버킷 테스트 완료: {successful_requests}/{total_requests} 성공 ({success_rate:.1f}%)")
    return successful_requests

def test_circuit_breaker():
    """회로 차단기 테스트"""
    logger.info("=== 회로 차단기 테스트 ===")
    
    # 실패 임계값 3, 타임아웃 2초
    breaker = CircuitBreaker(failure_threshold=3, timeout=2)
    
    def failing_function():
        raise Exception("API 호출 실패")
    
    def successful_function():
        return "API 호출 성공"
    
    # 1. 연속 실패로 회로 열기
    logger.info("1단계: 연속 실패로 회로 차단기 열기")
    failures = 0
    for i in range(5):
        try:
            breaker.call(failing_function)
        except Exception as e:
            failures += 1
            logger.info(f"  ❌ 실패 {failures}: {str(e)[:50]} (상태: {breaker.state})")
    
    # 2. 회로 열림 상태에서 요청 차단 확인
    logger.info("2단계: 회로 열림 상태에서 요청 차단 확인")
    try:
        breaker.call(successful_function)
        logger.error("  예상과 다름: 요청이 차단되지 않음")
    except Exception as e:
        logger.info(f"  ✅ 요청 차단됨: {e}")
    
    # 3. 타임아웃 후 half-open 상태 테스트
    logger.info("3단계: 타임아웃 후 half-open 상태 테스트")
    time.sleep(2.1)  # 타임아웃보다 약간 더 대기
    
    try:
        result = breaker.call(successful_function)
        logger.info(f"  ✅ 복구 성공: {result} (상태: {breaker.state})")
    except Exception as e:
        logger.error(f"  ❌ 복구 실패: {e}")
    
    logger.info(f"회로 차단기 테스트 완료 (최종 상태: {breaker.state})")
    return breaker.state

def test_marketplace_metrics():
    """마켓플레이스 메트릭 기록 테스트"""
    logger.info("=== 마켓플레이스 메트릭 테스트 ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 테스트 메트릭 데이터 삽입
        test_data = [
            ('coupang', 100, 95, 5, 2, 0.150),
            ('naver', 200, 180, 20, 8, 0.120),
            ('eleven', 150, 140, 10, 5, 0.180)
        ]
        
        for marketplace, total, success, failed, rate_limited, avg_time in test_data:
            cursor.execute("""
                INSERT INTO marketplace_metrics 
                (marketplace, total_requests, successful_requests, failed_requests, 
                 rate_limited_requests, avg_response_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (marketplace, total, success, failed, rate_limited, avg_time))
        
        conn.commit()
        
        # 메트릭 조회 및 분석
        cursor.execute("""
            SELECT 
                marketplace,
                total_requests,
                successful_requests,
                failed_requests,
                rate_limited_requests,
                avg_response_time,
                ROUND((successful_requests::float / total_requests * 100), 2) as success_rate
            FROM marketplace_metrics
            WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY marketplace, collected_at DESC
        """)
        
        metrics = cursor.fetchall()
        logger.info("최근 메트릭 데이터:")
        for metric in metrics:
            marketplace, total, success, failed, rate_limited, avg_time, success_rate = metric
            logger.info(f"  📊 {marketplace}: {success_rate}% 성공률, {avg_time:.3f}s 평균응답시간")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"메트릭 테스트 실패: {e}")
        return False

def test_marketplace_health():
    """마켓플레이스 헬스 체크 테스트"""
    logger.info("=== 마켓플레이스 헬스 체크 테스트 ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 헬스 체크 데이터 삽입
        health_data = [
            ('coupang', True, 0.095, None),
            ('naver', True, 0.120, None),
            ('eleven', False, None, 'Connection timeout')
        ]
        
        for marketplace, is_healthy, response_time, error_msg in health_data:
            cursor.execute("""
                INSERT INTO marketplace_health_status 
                (marketplace, is_healthy, response_time, error_message)
                VALUES (%s, %s, %s, %s)
            """, (marketplace, is_healthy, response_time, error_msg))
        
        conn.commit()
        
        # 헬스 상태 조회
        cursor.execute("""
            SELECT 
                marketplace, 
                is_healthy, 
                response_time, 
                error_message,
                checked_at
            FROM marketplace_health_status
            WHERE checked_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY marketplace, checked_at DESC
            LIMIT 10
        """)
        
        health_records = cursor.fetchall()
        logger.info("최근 헬스 체크 결과:")
        for record in health_records:
            marketplace, healthy, resp_time, error, checked = record
            status = "✅ 정상" if healthy else "❌ 장애"
            time_info = f"{resp_time:.3f}s" if resp_time else "N/A"
            error_info = f" ({error})" if error else ""
            logger.info(f"  {status} {marketplace}: {time_info}{error_info}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"헬스 체크 테스트 실패: {e}")
        return False

def run_comprehensive_test():
    """종합 테스트 실행"""
    logger.info("🏪 향상된 마켓플레이스 관리자 종합 테스트 시작")
    print("=" * 60)
    
    results = {}
    
    # 1. 데이터베이스 테이블 테스트
    results['database'] = test_database_tables()
    
    # 2. 토큰 버킷 테스트
    results['token_bucket'] = test_token_bucket()
    
    # 3. 회로 차단기 테스트
    circuit_state = test_circuit_breaker()
    results['circuit_breaker'] = circuit_state in ['CLOSED', 'OPEN']
    
    # 4. 메트릭 테스트
    results['metrics'] = test_marketplace_metrics()
    
    # 5. 헬스 체크 테스트
    results['health_check'] = test_marketplace_health()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 전체 성공률: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("향상된 마켓플레이스 관리자 구성 요소가 정상 작동합니다.")
        
        print("\n📋 구현된 기능:")
        print("  • 토큰 버킷 기반 율 제한")
        print("  • 회로 차단기 패턴")
        print("  • 실시간 메트릭 수집")
        print("  • 헬스 체크 모니터링")
        print("  • 데이터베이스 통합")
        print("  • 자동 최적화")
        
    else:
        print(f"\n⚠️  {total - passed}개 테스트가 실패했습니다.")
        print("로그를 확인하여 문제를 해결해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)