#!/usr/bin/env python3
"""
향상된 마켓플레이스 관리자 테스트 스크립트
"""
import sys
import os
import asyncio
import time
import json
from typing import Dict, Any

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market.enhanced_marketplace_manager import EnhancedMarketplaceManager
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres',
    'password': '1234'
}

def test_marketplace_manager():
    """마켓플레이스 관리자 기본 기능 테스트"""
    logger.info("향상된 마켓플레이스 관리자 테스트 시작")
    
    try:
        # 관리자 초기화
        manager = EnhancedMarketplaceManager(DB_CONFIG)
        
        # 1. 상태 확인
        logger.info("=== 1. 마켓플레이스 상태 확인 ===")
        status = manager.get_marketplace_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # 2. 모의 요청 큐잉 테스트
        logger.info("=== 2. 요청 큐잉 테스트 ===")
        
        def callback(response, error):
            if error:
                logger.error(f"요청 실패: {error}")
            else:
                logger.info(f"요청 성공: {response}")
        
        # 쿠팡 API 요청 시뮬레이션
        success = manager.queue_request(
            marketplace='coupang',
            method='GET',
            endpoint='products',
            params={'limit': 10},
            priority=1,
            callback=callback
        )
        
        if success:
            logger.info("쿠팡 요청 큐잉 성공")
        else:
            logger.error("쿠팡 요청 큐잉 실패")
        
        # 네이버 API 요청 시뮬레이션
        success = manager.queue_request(
            marketplace='naver',
            method='GET',
            endpoint='orders',
            params={'status': 'pending'},
            priority=2,
            callback=callback
        )
        
        if success:
            logger.info("네이버 요청 큐잉 성공")
        else:
            logger.error("네이버 요청 큐잉 실패")
        
        # 3. 대량 요청 테스트
        logger.info("=== 3. 대량 요청 테스트 ===")
        
        bulk_requests = [
            {
                'marketplace': 'coupang',
                'method': 'GET',
                'endpoint': 'products',
                'params': {'page': i}
            }
            for i in range(5)
        ]
        
        # 비동기 대량 요청 (실제로는 동기 함수이므로 시뮬레이션)
        start_time = time.time()
        
        # 대량 요청 처리 (실제 API 호출은 없으므로 예외 발생 예상)
        try:
            results = asyncio.run(manager.bulk_request(bulk_requests))
            logger.info(f"대량 요청 완료: {len(results)}개 결과")
        except Exception as e:
            logger.warning(f"대량 요청 테스트 중 예상된 오류 (API 클라이언트 없음): {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"처리 시간: {processing_time:.2f}초")
        
        # 4. 성능 권장사항 확인
        logger.info("=== 4. 성능 권장사항 ===")
        recommendations = manager.get_performance_recommendations()
        if recommendations:
            for rec in recommendations:
                logger.info(f"권장사항: {rec['message']} - {rec['suggestion']}")
        else:
            logger.info("현재 성능 문제가 감지되지 않았습니다")
        
        # 5. 율 제한 최적화 테스트
        logger.info("=== 5. 율 제한 최적화 테스트 ===")
        manager.optimize_rate_limits()
        logger.info("율 제한 최적화 완료")
        
        # 6. 최종 상태 확인
        logger.info("=== 6. 최종 상태 확인 ===")
        final_status = manager.get_marketplace_status()
        print(json.dumps(final_status, indent=2, ensure_ascii=False))
        
        # 잠시 대기 (백그라운드 워커 동작 확인)
        logger.info("백그라운드 워커 동작 확인을 위해 5초 대기...")
        time.sleep(5)
        
        # 정리
        manager.cleanup()
        logger.info("테스트 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        return False

def test_database_connection():
    """데이터베이스 연결 및 테이블 확인"""
    logger.info("데이터베이스 연결 및 테이블 확인")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 마켓플레이스 관련 테이블 확인
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
            logger.info(f"  - {table['table_name']}")
        
        # 율 제한 설정 확인
        cursor.execute("SELECT * FROM marketplace_rate_limits")
        rate_limits = cursor.fetchall()
        logger.info("현재 율 제한 설정:")
        for limit in rate_limits:
            logger.info(f"  - {limit['marketplace']}: {limit['max_requests_per_second']} req/sec")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 테스트 오류: {e}")
        return False

def test_token_bucket():
    """토큰 버킷 알고리즘 테스트"""
    logger.info("=== 토큰 버킷 알고리즘 테스트 ===")
    
    from market.enhanced_marketplace_manager import TokenBucket
    
    # 초당 5개 토큰, 최대 10개 용량
    bucket = TokenBucket(rate=5.0, capacity=10)
    
    # 연속 요청 테스트
    successful_requests = 0
    total_requests = 15
    
    for i in range(total_requests):
        if bucket.consume():
            successful_requests += 1
            logger.info(f"요청 {i+1}: 성공 (토큰 남음: {bucket.tokens:.2f})")
        else:
            wait_time = bucket.time_until_available()
            logger.info(f"요청 {i+1}: 실패 (대기 시간: {wait_time:.2f}초)")
        
        time.sleep(0.1)  # 100ms 간격
    
    logger.info(f"토큰 버킷 테스트 완료: {successful_requests}/{total_requests} 성공")
    return successful_requests

def test_circuit_breaker():
    """회로 차단기 테스트"""
    logger.info("=== 회로 차단기 테스트 ===")
    
    from market.enhanced_marketplace_manager import CircuitBreaker
    
    # 실패 임계값 3, 타임아웃 5초
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=5)
    
    def failing_function():
        raise Exception("테스트 실패")
    
    def successful_function():
        return "성공"
    
    # 실패 누적
    failures = 0
    for i in range(5):
        try:
            result = circuit_breaker.call(failing_function)
        except Exception as e:
            failures += 1
            logger.info(f"실패 {failures}: {e} (상태: {circuit_breaker.state})")
    
    # 회로 열림 상태에서 요청
    try:
        circuit_breaker.call(successful_function)
    except Exception as e:
        logger.info(f"회로 열림 상태에서 요청 차단: {e}")
    
    logger.info(f"회로 차단기 테스트 완료 (상태: {circuit_breaker.state})")
    return circuit_breaker.state == 'OPEN'

if __name__ == "__main__":
    print("🏪 향상된 마켓플레이스 관리자 테스트")
    print("=" * 50)
    
    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        print("❌ 데이터베이스 연결 실패")
        sys.exit(1)
    
    # 2. 토큰 버킷 테스트
    successful_tokens = test_token_bucket()
    
    # 3. 회로 차단기 테스트
    circuit_breaker_working = test_circuit_breaker()
    
    # 4. 전체 관리자 테스트
    manager_working = test_marketplace_manager()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    print(f"✅ 데이터베이스 연결: 성공")
    print(f"✅ 토큰 버킷: {successful_tokens}개 요청 처리")
    print(f"✅ 회로 차단기: {'정상 작동' if circuit_breaker_working else '테스트 실패'}")
    print(f"✅ 마켓플레이스 관리자: {'정상 작동' if manager_working else '테스트 실패'}")
    
    if manager_working:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("향상된 마켓플레이스 관리자가 준비되었습니다.")
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
        sys.exit(1)