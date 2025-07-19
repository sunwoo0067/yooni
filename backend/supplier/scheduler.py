#!/usr/bin/env python3
"""
상품 수집 스케줄러
APScheduler를 사용하여 주기적으로 상품 정보를 수집하고 업데이트
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, List, Any, Optional

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_integration_manager import APIIntegrationManager, CollectionResult

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supplier_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SupplierCollectionScheduler:
    """상품 수집 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.api_manager = APIIntegrationManager()
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 스케줄 설정 로드
        self.load_schedule_config()
        
    def load_schedule_config(self):
        """스케줄 설정 로드"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        s.id, s.name, 
                        sc.settings->>'collection_schedule' as schedule,
                        sc.settings->>'collection_interval_hours' as interval_hours,
                        sc.settings->>'collection_enabled' as enabled
                    FROM suppliers s
                    JOIN supplier_configs sc ON s.id = sc.supplier_id
                    WHERE sc.collection_enabled = true
                """)
                
                self.supplier_configs = {
                    row['name']: {
                        'id': row['id'],
                        'schedule': row['schedule'] or '0 3 * * *',  # 기본값: 매일 새벽 3시
                        'interval_hours': int(row['interval_hours'] or '24'),
                        'enabled': row['enabled'] != 'false'
                    }
                    for row in cursor.fetchall()
                }
                
                logger.info(f"스케줄 설정 로드 완료: {list(self.supplier_configs.keys())}")
                
        except Exception as e:
            logger.error(f"스케줄 설정 로드 실패: {e}")
            # 기본 설정 사용
            self.supplier_configs = {
                '오너클랜': {'schedule': '0 3 * * *', 'interval_hours': 24, 'enabled': True},
                '젠트레이드': {'schedule': '0 4 * * *', 'interval_hours': 24, 'enabled': True}
            }
    
    async def collect_supplier_products(self, supplier_name: str):
        """개별 공급사 상품 수집"""
        try:
            logger.info(f"🏪 {supplier_name} 정기 수집 시작")
            
            # 수집 상태 확인 (중복 실행 방지)
            if not await self.check_collection_status(supplier_name):
                logger.warning(f"{supplier_name} 수집이 이미 진행 중입니다")
                return
            
            # 수집 시작 기록
            await self.update_collection_status(supplier_name, 'running')
            
            # API 연동 매니저로 수집
            credentials = self.api_manager.get_supplier_credentials(supplier_name)
            if not credentials:
                logger.error(f"{supplier_name} 인증 정보 없음")
                await self.update_collection_status(supplier_name, 'failed')
                return
            
            # 공급사별 수집 실행
            if supplier_name == '오너클랜':
                result = await self.api_manager.collect_ownerclan_products(credentials)
            elif supplier_name == '젠트레이드':
                result = await self.api_manager.collect_zentrade_products(credentials)
            else:
                logger.error(f"지원되지 않는 공급사: {supplier_name}")
                await self.update_collection_status(supplier_name, 'failed')
                return
            
            # 결과 로깅
            if result.success:
                logger.info(f"✅ {supplier_name} 수집 완료: {result.total_products}개 상품")
                await self.update_collection_status(supplier_name, 'completed', result)
            else:
                logger.error(f"❌ {supplier_name} 수집 실패: {result.errors}")
                await self.update_collection_status(supplier_name, 'failed', result)
            
            # 알림 발송 (중요 이벤트)
            if result.failed_products > 10 or not result.success:
                await self.send_notification(supplier_name, result)
                
        except Exception as e:
            logger.error(f"{supplier_name} 수집 중 오류: {e}")
            await self.update_collection_status(supplier_name, 'failed')
    
    async def check_collection_status(self, supplier_name: str) -> bool:
        """수집 상태 확인 (중복 실행 방지)"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT status, started_at 
                    FROM supplier_collection_status
                    WHERE supplier_name = %s
                """, (supplier_name,))
                
                status = cursor.fetchone()
                
                if status and status['status'] == 'running':
                    # 6시간 이상 running 상태면 강제 재시작 허용
                    started_at = status['started_at']
                    if datetime.now() - started_at < timedelta(hours=6):
                        return False
                        
                return True
                
        except Exception as e:
            logger.error(f"상태 확인 오류: {e}")
            return True
    
    async def update_collection_status(self, supplier_name: str, status: str, 
                                     result: Optional[CollectionResult] = None):
        """수집 상태 업데이트"""
        try:
            with self.conn.cursor() as cursor:
                if status == 'running':
                    cursor.execute("""
                        INSERT INTO supplier_collection_status 
                        (supplier_name, status, started_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (supplier_name) 
                        DO UPDATE SET status = EXCLUDED.status, 
                                    started_at = EXCLUDED.started_at
                    """, (supplier_name, status, datetime.now()))
                    
                elif status in ['completed', 'failed']:
                    cursor.execute("""
                        UPDATE supplier_collection_status 
                        SET status = %s, 
                            completed_at = %s,
                            last_result = %s
                        WHERE supplier_name = %s
                    """, (
                        status, 
                        datetime.now(),
                        json.dumps({
                            'total_products': result.total_products if result else 0,
                            'new_products': result.new_products if result else 0,
                            'updated_products': result.updated_products if result else 0,
                            'failed_products': result.failed_products if result else 0,
                            'errors': result.errors if result else []
                        }) if result else None,
                        supplier_name
                    ))
                    
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"상태 업데이트 오류: {e}")
            self.conn.rollback()
    
    async def send_notification(self, supplier_name: str, result: CollectionResult):
        """알림 발송 (Slack, Email 등)"""
        try:
            message = f"""
🚨 상품 수집 알림 - {supplier_name}

상태: {'실패' if not result.success else '경고'}
총 상품: {result.total_products}개
실패: {result.failed_products}개
오류: {', '.join(result.errors[:3]) if result.errors else '없음'}

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            logger.warning(message)
            
            # TODO: Slack webhook 또는 이메일 발송 구현
            # await send_slack_message(message)
            # await send_email(subject, message)
            
        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")
    
    async def collect_all_suppliers(self):
        """모든 공급사 수집 (전체 수집용)"""
        logger.info("🚀 전체 공급사 수집 시작")
        
        results = await self.api_manager.collect_all_suppliers()
        
        # 결과 요약
        total_success = sum(1 for r in results.values() if r.success)
        total_products = sum(r.total_products for r in results.values())
        
        logger.info(f"""
📊 전체 수집 완료:
- 성공: {total_success}/{len(results)}개 공급사
- 총 상품: {total_products}개
- 소요시간: {sum(r.duration_seconds for r in results.values()):.1f}초
""")
        
        # 실패한 공급사가 있으면 알림
        failed_suppliers = [name for name, r in results.items() if not r.success]
        if failed_suppliers:
            await self.send_notification(
                f"전체 수집 ({', '.join(failed_suppliers)} 실패)",
                CollectionResult(
                    success=False,
                    total_products=total_products,
                    new_products=sum(r.new_products for r in results.values()),
                    updated_products=sum(r.updated_products for r in results.values()),
                    failed_products=sum(r.failed_products for r in results.values()),
                    errors=[f"{name} 실패" for name in failed_suppliers],
                    duration_seconds=0
                )
            )
    
    def setup_schedules(self):
        """스케줄 설정"""
        # 개별 공급사 스케줄
        for supplier_name, config in self.supplier_configs.items():
            if config.get('enabled', True):
                # Cron 스케줄 (매일 특정 시간)
                self.scheduler.add_job(
                    self.collect_supplier_products,
                    CronTrigger.from_crontab(config['schedule']),
                    args=[supplier_name],
                    id=f'collect_{supplier_name}_cron',
                    name=f'{supplier_name} 정기 수집',
                    replace_existing=True
                )
                
                logger.info(f"✅ {supplier_name} 스케줄 등록: {config['schedule']}")
        
        # 전체 수집 스케줄 (매주 일요일 새벽 2시)
        self.scheduler.add_job(
            self.collect_all_suppliers,
            CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='collect_all_weekly',
            name='전체 공급사 주간 수집',
            replace_existing=True
        )
        
        # 상태 모니터링 (30분마다)
        self.scheduler.add_job(
            self.check_system_health,
            IntervalTrigger(minutes=30),
            id='health_check',
            name='시스템 상태 확인',
            replace_existing=True
        )
    
    async def check_system_health(self):
        """시스템 상태 확인"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 최근 수집 상태 확인
                cursor.execute("""
                    SELECT 
                        supplier_name,
                        status,
                        started_at,
                        completed_at,
                        last_result
                    FROM supplier_collection_status
                    WHERE started_at > NOW() - INTERVAL '24 hours'
                    ORDER BY started_at DESC
                """)
                
                recent_collections = cursor.fetchall()
                
                # 장시간 실행 중인 작업 확인
                stuck_jobs = [
                    job for job in recent_collections
                    if job['status'] == 'running' and 
                    datetime.now() - job['started_at'] > timedelta(hours=2)
                ]
                
                if stuck_jobs:
                    logger.warning(f"🚨 장시간 실행 중인 작업: {[j['supplier_name'] for j in stuck_jobs]}")
                
                # 연속 실패 확인
                cursor.execute("""
                    SELECT supplier_name, COUNT(*) as fail_count
                    FROM supplier_collection_logs
                    WHERE status = 'failed' 
                    AND started_at > NOW() - INTERVAL '7 days'
                    GROUP BY supplier_name
                    HAVING COUNT(*) > 3
                """)
                
                frequent_failures = cursor.fetchall()
                if frequent_failures:
                    logger.warning(f"🚨 빈번한 실패 발생: {frequent_failures}")
                    
        except Exception as e:
            logger.error(f"상태 확인 오류: {e}")
    
    def start(self):
        """스케줄러 시작"""
        try:
            # 스케줄 설정
            self.setup_schedules()
            
            # 스케줄러 시작
            self.scheduler.start()
            logger.info("✅ 스케줄러 시작됨")
            
            # 등록된 작업 목록 출력
            jobs = self.scheduler.get_jobs()
            logger.info(f"📋 등록된 작업: {len(jobs)}개")
            for job in jobs:
                logger.info(f"  - {job.name}: {job.trigger}")
            
            # 이벤트 루프 실행
            asyncio.get_event_loop().run_forever()
            
        except (KeyboardInterrupt, SystemExit):
            logger.info("스케줄러 종료 중...")
            self.shutdown()
            
    def shutdown(self):
        """스케줄러 종료"""
        self.scheduler.shutdown()
        self.api_manager.close()
        self.conn.close()
        logger.info("✅ 스케줄러 종료됨")

async def manual_collect(supplier_name: Optional[str] = None):
    """수동 수집 실행"""
    scheduler = SupplierCollectionScheduler()
    
    try:
        if supplier_name:
            # 특정 공급사만 수집
            await scheduler.collect_supplier_products(supplier_name)
        else:
            # 전체 수집
            await scheduler.collect_all_suppliers()
    finally:
        scheduler.shutdown()

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='상품 수집 스케줄러')
    parser.add_argument('--daemon', action='store_true', help='데몬 모드로 실행')
    parser.add_argument('--collect', type=str, help='특정 공급사 즉시 수집')
    parser.add_argument('--collect-all', action='store_true', help='전체 공급사 즉시 수집')
    
    args = parser.parse_args()
    
    if args.collect:
        # 특정 공급사 수집
        asyncio.run(manual_collect(args.collect))
    elif args.collect_all:
        # 전체 수집
        asyncio.run(manual_collect())
    else:
        # 스케줄러 실행
        scheduler = SupplierCollectionScheduler()
        scheduler.start()

if __name__ == "__main__":
    main()