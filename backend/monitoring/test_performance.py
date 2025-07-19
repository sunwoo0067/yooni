#!/usr/bin/env python3
"""
성능 모니터링 및 최적화 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.performance_monitor import PerformanceMonitor
from optimization.database_optimizer import DatabaseOptimizer
from optimization.cache_manager import ProductCacheManager
import time
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_performance_monitor():
    """성능 모니터 테스트"""
    print("\n🔍 성능 모니터 테스트")
    print("=" * 60)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    try:
        # 10초 동안 모니터링
        for i in range(10):
            time.sleep(1)
            
            if i % 3 == 0:
                metrics = monitor.get_realtime_metrics()
                print(f"\n📊 실시간 메트릭 (T+{i}초):")
                print(f"   CPU: {metrics['cpu_percent']}%")
                print(f"   Memory: {metrics['memory_percent']}% ({metrics['memory_mb']}MB)")
                print(f"   DB 연결: {metrics['database']['active_connections']}")
                print(f"   평균 쿼리시간: {metrics['database']['avg_query_time_ms']}ms")
                print(f"   수집 속도: {metrics['application']['collection_rate']} items/sec")
        
        # 성능 분석
        analysis = monitor.analyze_performance()
        print(f"\n🎯 성능 분석:")
        print(f"   성능 점수: {analysis.get('performance_score', 'N/A')}점")
        
        if 'bottlenecks' in analysis and analysis['bottlenecks']:
            print(f"   병목 지점: {', '.join(analysis['bottlenecks'])}")
            print("\n   권장사항:")
            for rec in analysis.get('recommendations', []):
                print(f"   - {rec}")
        else:
            print("   병목 지점: 없음")
        
    finally:
        monitor.stop()
        print("\n✅ 성능 모니터 테스트 완료")

def test_database_optimizer():
    """데이터베이스 최적화 테스트"""
    print("\n🔧 데이터베이스 최적화 테스트")
    print("=" * 60)
    
    optimizer = DatabaseOptimizer()
    
    # 1. 최적화 보고서
    report = optimizer.get_optimization_report()
    print(f"\n📊 최적화 보고서:")
    print(f"   DB 크기: {report['database_size']}")
    print(f"   캐시 히트율: {report['cache_hit_ratio']:.1f}%")
    print(f"   총 인덱스: {report['index_usage']['total_indexes']}")
    print(f"   미사용 인덱스: {report['index_usage']['unused_indexes']}")
    
    # 2. 테이블 크기 분석
    print(f"\n📈 상위 5개 테이블:")
    for table in report['table_sizes'][:5]:
        print(f"   {table['tablename']}: {table['size']} (행: {table['row_count']:,})")
    
    # 3. 권장사항
    if report['recommendations']:
        print(f"\n💡 권장사항:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    # 4. 느린 쿼리 분석
    slow_queries = optimizer.analyze_slow_queries()
    if slow_queries:
        print(f"\n🐌 느린 쿼리 TOP 3:")
        for i, query in enumerate(slow_queries[:3], 1):
            print(f"   {i}. 평균 {query['mean_exec_time']:.1f}ms (호출: {query['calls']}회)")
    
    print("\n✅ 데이터베이스 최적화 테스트 완료")

def test_cache_manager():
    """캐시 매니저 테스트"""
    print("\n💾 캐시 매니저 테스트")
    print("=" * 60)
    
    cache = ProductCacheManager()
    
    # 1. 기본 캐시 동작 테스트
    print("\n1️⃣ 기본 캐시 동작:")
    
    # 캐시 저장
    test_data = {"products": [{"id": 1, "name": "테스트상품"}], "count": 1}
    cache.set("test", "products:1", test_data, layer='hot')
    print("   ✅ 데이터 캐시 저장")
    
    # 캐시 조회
    cached_data = cache.get("test", "products:1")
    if cached_data:
        print(f"   ✅ 캐시 히트: {cached_data['count']}개 상품")
    
    # 2. 데코레이터 테스트
    print("\n2️⃣ 캐시 데코레이터 테스트:")
    
    @cache.cache_decorator('analysis', layer='warm')
    def slow_analysis(product_id: int):
        # 시뮬레이션: 느린 작업
        time.sleep(1)
        return {"product_id": product_id, "score": 85.5, "timestamp": time.time()}
    
    # 첫 호출 (캐시 미스)
    start = time.time()
    result1 = slow_analysis(12345)
    elapsed1 = time.time() - start
    print(f"   첫 호출: {elapsed1:.2f}초 소요")
    
    # 두 번째 호출 (캐시 히트)
    start = time.time()
    result2 = slow_analysis(12345)
    elapsed2 = time.time() - start
    print(f"   캐시 호출: {elapsed2:.2f}초 소요 (속도 향상: {elapsed1/elapsed2:.1f}배)")
    
    # 3. 캐시 통계
    stats = cache.get_stats()
    print(f"\n3️⃣ 캐시 통계:")
    print(f"   히트: {stats['hits']}")
    print(f"   미스: {stats['misses']}")
    print(f"   히트율: {stats['hit_rate']}")
    print(f"   메모리 사용: {stats['memory_usage_mb']}MB")
    print(f"   총 키: {stats['total_keys']}")
    
    # 4. 캐시 무효화
    invalidated = cache.invalidate_namespace("test")
    print(f"\n4️⃣ 캐시 무효화: {invalidated}개 삭제")
    
    print("\n✅ 캐시 매니저 테스트 완료")

async def test_integration():
    """통합 테스트"""
    print("\n🔗 통합 성능 테스트")
    print("=" * 60)
    
    # 동시에 여러 컴포넌트 실행
    monitor = PerformanceMonitor()
    cache = ProductCacheManager()
    optimizer = DatabaseOptimizer()
    
    monitor.start()
    
    try:
        # 캐시 예열
        print("\n🔥 캐시 예열 중...")
        for i in range(5):
            cache.set("products", f"list:{i}", [{"id": j} for j in range(100)], layer='warm')
        
        # 성능 측정
        await asyncio.sleep(3)
        
        # 결과 분석
        perf_metrics = monitor.get_realtime_metrics()
        perf_analysis = monitor.analyze_performance()
        cache_stats = cache.get_stats()
        db_report = optimizer.get_optimization_report()
        
        print("\n📊 통합 성능 리포트:")
        print(f"   성능 점수: {perf_analysis.get('performance_score', 'N/A')}점")
        print(f"   캐시 히트율: {cache_stats['hit_rate']}")
        print(f"   DB 캐시 히트율: {db_report['cache_hit_ratio']:.1f}%")
        print(f"   활성 DB 연결: {perf_metrics['database']['active_connections']}")
        
    finally:
        monitor.stop()
        print("\n✅ 통합 테스트 완료")

def main():
    """메인 실행 함수"""
    print("🚀 Yooni 성능 모니터링 및 최적화 테스트")
    print("=" * 60)
    
    # 각 컴포넌트 테스트
    test_performance_monitor()
    test_database_optimizer()
    test_cache_manager()
    
    # 통합 테스트
    asyncio.run(test_integration())
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")

if __name__ == "__main__":
    main()