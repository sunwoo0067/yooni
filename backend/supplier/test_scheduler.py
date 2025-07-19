#!/usr/bin/env python3
"""
스케줄러 테스트 스크립트
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import SupplierCollectionScheduler, manual_collect
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scheduler():
    """스케줄러 기능 테스트"""
    print("🚀 스케줄러 테스트 시작")
    print("=" * 60)
    
    # 1. 스케줄러 초기화 테스트
    print("\n1️⃣ 스케줄러 초기화 테스트")
    scheduler = SupplierCollectionScheduler()
    print("✅ 스케줄러 생성 성공")
    
    # 2. 설정 확인
    print("\n2️⃣ 공급사 설정 확인")
    for supplier, config in scheduler.supplier_configs.items():
        print(f"  📋 {supplier}:")
        print(f"     스케줄: {config['schedule']}")
        print(f"     간격: {config['interval_hours']}시간")
        print(f"     활성화: {config['enabled']}")
    
    # 3. 수동 수집 테스트 (오너클랜)
    print("\n3️⃣ 오너클랜 수동 수집 테스트")
    try:
        await scheduler.collect_supplier_products('오너클랜')
        print("✅ 오너클랜 수집 완료")
    except Exception as e:
        print(f"❌ 오너클랜 수집 실패: {e}")
    
    # 4. 상태 확인
    print("\n4️⃣ 수집 상태 확인")
    await scheduler.check_system_health()
    
    # 5. 스케줄 등록 확인
    print("\n5️⃣ 스케줄 등록 테스트")
    scheduler.setup_schedules()
    
    jobs = scheduler.scheduler.get_jobs()
    print(f"✅ 등록된 작업: {len(jobs)}개")
    for job in jobs:
        print(f"  ⏰ {job.name}")
        print(f"     ID: {job.id}")
        print(f"     트리거: {job.trigger}")
        # APScheduler 3.x에서는 next_run_time이 다른 방식으로 접근
        try:
            next_run = job.trigger.get_next_fire_time(None, datetime.now())
            print(f"     다음 실행: {next_run}")
        except:
            print(f"     다음 실행: N/A")
    
    # 6. 통계 확인
    print("\n6️⃣ 수집 통계 확인")
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    conn = psycopg2.connect(
        host='localhost',
        port=5434,
        database='yoonni',
        user='postgres',
        password='postgres'
    )
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM supplier_collection_stats")
        stats = cursor.fetchall()
        
        print("📊 공급사별 통계:")
        for stat in stats:
            print(f"  📦 {stat['supplier_name']}:")
            print(f"     총 상품: {stat['total_products']}개")
            print(f"     활성 상품: {stat['active_products']}개")
            print(f"     평균 수집시간: {stat['avg_duration_seconds']:.1f}초" if stat['avg_duration_seconds'] else "     평균 수집시간: N/A")
            print(f"     성공/실패: {stat['success_count']}/{stat['fail_count']}")
    
    conn.close()
    scheduler.shutdown()
    
    print("\n" + "=" * 60)
    print("✅ 스케줄러 테스트 완료!")
    
    return True

async def test_manual_collection():
    """수동 수집 테스트"""
    print("\n🔧 수동 수집 테스트")
    print("=" * 60)
    
    # 특정 공급사 수집
    print("\n젠트레이드 수동 수집 실행...")
    await manual_collect('젠트레이드')
    
    print("\n✅ 수동 수집 테스트 완료!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual', action='store_true', help='수동 수집 테스트')
    args = parser.parse_args()
    
    if args.manual:
        asyncio.run(test_manual_collection())
    else:
        asyncio.run(test_scheduler())