"""
워크플로우 스케줄러 - 시간 기반 워크플로우 실행
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from croniter import croniter
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

sys.path.append('/home/sunwoo/yooni/backend')
from core import get_logger
from workflow.engine import WorkflowEngine

logger = get_logger(__name__)


class WorkflowScheduler:
    """워크플로우 스케줄러"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.workflow_engine = WorkflowEngine(db_config)
        self._running = False
        self._scheduled_jobs = {}
        
    async def start(self):
        """스케줄러 시작"""
        if not self._running:
            self._running = True
            await self._load_scheduled_workflows()
            asyncio.create_task(self._scheduler_loop())
            logger.info("워크플로우 스케줄러 시작됨")
    
    def stop(self):
        """스케줄러 중지"""
        self._running = False
        self._scheduled_jobs.clear()
        logger.info("워크플로우 스케줄러 중지됨")
    
    async def _load_scheduled_workflows(self):
        """스케줄된 워크플로우 로드"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM workflow_definitions
            WHERE trigger_type = 'schedule'
            AND is_active = true
        """)
        
        workflows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for workflow in workflows:
            self._schedule_workflow(dict(workflow))
        
        logger.info(f"{len(workflows)}개의 스케줄된 워크플로우 로드됨")
    
    def _schedule_workflow(self, workflow: Dict[str, Any]):
        """워크플로우 스케줄링"""
        config = workflow.get('config', {})
        cron_expression = config.get('cron')
        
        if not cron_expression:
            logger.warning(f"워크플로우 {workflow['id']}에 cron 표현식이 없습니다")
            return
        
        try:
            # cron 표현식 검증
            cron = croniter(cron_expression, datetime.now())
            next_run = cron.get_next(datetime)
            
            self._scheduled_jobs[workflow['id']] = {
                'workflow': workflow,
                'cron': cron_expression,
                'next_run': next_run
            }
            
            logger.info(f"워크플로우 스케줄됨: {workflow['name']} - 다음 실행: {next_run}")
            
        except Exception as e:
            logger.error(f"워크플로우 스케줄링 실패: {workflow['id']} - {e}")
    
    async def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        while self._running:
            try:
                now = datetime.now()
                
                # 실행할 워크플로우 확인
                for job_id, job in list(self._scheduled_jobs.items()):
                    if job['next_run'] <= now:
                        # 워크플로우 실행
                        asyncio.create_task(self._execute_scheduled_workflow(job_id, job))
                        
                        # 다음 실행 시간 계산
                        cron = croniter(job['cron'], now)
                        job['next_run'] = cron.get_next(datetime)
                        
                        logger.info(f"스케줄된 워크플로우 실행: {job['workflow']['name']}")
                
                # 1초 대기
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"스케줄러 루프 오류: {e}")
                await asyncio.sleep(5)
    
    async def _execute_scheduled_workflow(self, job_id: int, job: Dict[str, Any]):
        """스케줄된 워크플로우 실행"""
        try:
            workflow = job['workflow']
            
            # 트리거 데이터 구성
            trigger_data = {
                'source': 'scheduler',
                'trigger_type': 'schedule',
                'scheduled_time': job['next_run'].isoformat(),
                'cron': job['cron']
            }
            
            # 워크플로우 실행
            result = await self.workflow_engine.execute_workflow(
                workflow['id'],
                trigger_data
            )
            
            # 실행 기록 업데이트
            self._update_last_run(workflow['id'])
            
        except Exception as e:
            logger.error(f"스케줄된 워크플로우 실행 실패: {job_id} - {e}")
    
    def _update_last_run(self, workflow_id: int):
        """마지막 실행 시간 업데이트"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflow_definitions
            SET updated_at = NOW()
            WHERE id = %s
        """, (workflow_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    async def add_scheduled_workflow(self, workflow_id: int, cron_expression: str):
        """스케줄된 워크플로우 추가"""
        # 워크플로우 로드
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            UPDATE workflow_definitions
            SET trigger_type = 'schedule',
                config = jsonb_set(config, '{cron}', %s::jsonb)
            WHERE id = %s
            RETURNING *
        """, (json.dumps(cron_expression), workflow_id))
        
        workflow = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if workflow:
            self._schedule_workflow(dict(workflow))
            logger.info(f"스케줄된 워크플로우 추가됨: {workflow_id}")
    
    async def remove_scheduled_workflow(self, workflow_id: int):
        """스케줄된 워크플로우 제거"""
        if workflow_id in self._scheduled_jobs:
            del self._scheduled_jobs[workflow_id]
            logger.info(f"스케줄된 워크플로우 제거됨: {workflow_id}")
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """스케줄된 작업 목록 조회"""
        jobs = []
        
        for job_id, job in self._scheduled_jobs.items():
            jobs.append({
                'workflow_id': job_id,
                'workflow_name': job['workflow']['name'],
                'cron': job['cron'],
                'next_run': job['next_run'].isoformat()
            })
        
        return sorted(jobs, key=lambda x: x['next_run'])