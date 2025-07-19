"""
스케줄러 매니저 - 자동화된 작업 실행 관리
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
import psycopg2
from psycopg2.extras import RealDictCursor
import threading
import time
import os
from pathlib import Path
import json
import traceback

from ..config.config_manager import ConfigManager
from .models import ScheduleJob, JobStatus, JobType, ScheduleInterval, JobExecution


class SchedulerManager:
    """스케줄러 매니저"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.db_config = {
            'host': self.config_manager.get('database', 'host', 'localhost'),
            'port': self.config_manager.get('database', 'port', 5434),
            'database': self.config_manager.get('database', 'name', 'yoonni'),
            'user': self.config_manager.get('database', 'user', 'postgres'),
            'password': self.config_manager.get('database', 'password', '1234')
        }
        
        self.logger = self._setup_logger()
        self.running = False
        self.jobs: Dict[int, ScheduleJob] = {}
        self.job_handlers: Dict[JobType, Callable] = {}
        self.worker_threads: List[threading.Thread] = []
        self.lock = threading.Lock()
        
        # 작업 핸들러 등록
        self._register_default_handlers()
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('scheduler')
        logger.setLevel(logging.INFO)
        
        # 로그 디렉토리 생성
        log_dir = Path(__file__).parent.parent / 'logs' / 'scheduler'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 핸들러
        log_file = log_dir / f'scheduler_{datetime.now().strftime("%Y%m%d")}.log'
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
        
    def _register_default_handlers(self):
        """기본 작업 핸들러 등록"""
        self.register_handler(JobType.PRODUCT_COLLECTION, self._handle_product_collection)
        self.register_handler(JobType.ORDER_COLLECTION, self._handle_order_collection)
        self.register_handler(JobType.INVENTORY_SYNC, self._handle_inventory_sync)
        self.register_handler(JobType.PRICE_UPDATE, self._handle_price_update)
        self.register_handler(JobType.DATABASE_BACKUP, self._handle_database_backup)
        self.register_handler(JobType.REPORT_GENERATION, self._handle_report_generation)
        
    def register_handler(self, job_type: JobType, handler: Callable):
        """작업 핸들러 등록"""
        self.job_handlers[job_type] = handler
        self.logger.info(f"핸들러 등록: {job_type.value}")
        
    def start(self):
        """스케줄러 시작"""
        self.logger.info("스케줄러 시작")
        self.running = True
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 메인 루프 시작
        self._main_loop()
        
    def stop(self):
        """스케줄러 중지"""
        self.logger.info("스케줄러 중지 요청")
        self.running = False
        
        # 모든 워커 스레드 종료 대기
        for thread in self.worker_threads:
            thread.join(timeout=30)
            
        self.logger.info("스케줄러 중지 완료")
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.logger.info(f"시그널 수신: {signum}")
        self.stop()
        sys.exit(0)
        
    def _main_loop(self):
        """메인 실행 루프"""
        while self.running:
            try:
                # 활성 작업 로드
                self._load_active_jobs()
                
                # 실행할 작업 확인
                jobs_to_run = self._get_jobs_to_run()
                
                # 작업 실행
                for job in jobs_to_run:
                    if not self.running:
                        break
                    self._execute_job(job)
                    
                # 다음 실행 시간 업데이트
                self._update_next_run_times()
                
                # 대기
                time.sleep(10)  # 10초마다 확인
                
            except Exception as e:
                self.logger.error(f"메인 루프 오류: {str(e)}")
                self.logger.error(traceback.format_exc())
                time.sleep(30)  # 오류 발생 시 30초 대기
                
    def _load_active_jobs(self):
        """활성 작업 로드"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM schedule_jobs 
                    WHERE is_active = true AND status = 'active'
                    ORDER BY priority DESC
                """)
                rows = cur.fetchall()
                
                with self.lock:
                    self.jobs.clear()
                    for row in rows:
                        job = self._row_to_job(row)
                        self.jobs[job.id] = job
                        
            conn.close()
            
        except Exception as e:
            self.logger.error(f"작업 로드 오류: {str(e)}")
            
    def _row_to_job(self, row: dict) -> ScheduleJob:
        """DB 행을 작업 객체로 변환"""
        return ScheduleJob(
            id=row['id'],
            name=row['name'],
            job_type=JobType(row['job_type']),
            status=JobStatus(row['status']),
            interval=ScheduleInterval(row['interval']) if row['interval'] else None,
            cron_expression=row['cron_expression'],
            specific_times=row['specific_times'] or [],
            market_codes=row['market_codes'] or [],
            account_ids=row['account_ids'] or [],
            parameters=row['parameters'] or {},
            max_retries=row['max_retries'],
            timeout_minutes=row['timeout_minutes'],
            priority=row['priority'],
            last_run_at=row['last_run_at'],
            next_run_at=row['next_run_at'],
            last_success_at=row['last_success_at'],
            last_error=row['last_error'],
            run_count=row['run_count'],
            success_count=row['success_count'],
            error_count=row['error_count']
        )
        
    def _get_jobs_to_run(self) -> List[ScheduleJob]:
        """실행할 작업 목록 반환"""
        jobs_to_run = []
        current_time = datetime.now()
        
        with self.lock:
            for job in self.jobs.values():
                if self._should_run_job(job, current_time):
                    # 잠금 확인
                    if not self._is_job_locked(job.id):
                        jobs_to_run.append(job)
                        
        return jobs_to_run
        
    def _should_run_job(self, job: ScheduleJob, current_time: datetime) -> bool:
        """작업 실행 여부 확인"""
        # next_run_at이 설정되어 있고 현재 시간이 지났으면 실행
        if job.next_run_at and current_time >= job.next_run_at:
            return True
            
        # 첫 실행인 경우
        if not job.last_run_at:
            return True
            
        # 특정 시간 실행 확인
        if job.specific_times:
            for specific_time in job.specific_times:
                # 오늘 해당 시간이 지났는지 확인
                run_time = datetime.combine(current_time.date(), specific_time)
                if job.last_run_at < run_time <= current_time:
                    return True
                    
        return False
        
    def _is_job_locked(self, job_id: int) -> bool:
        """작업 잠금 상태 확인"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM schedule_locks 
                    WHERE job_id = %s AND expires_at > CURRENT_TIMESTAMP
                """, (job_id,))
                return cur.fetchone() is not None
        except:
            return False
        finally:
            conn.close()
            
    def _execute_job(self, job: ScheduleJob):
        """작업 실행"""
        # 워커 스레드에서 실행
        thread = threading.Thread(
            target=self._execute_job_worker,
            args=(job,),
            name=f"job-{job.id}-{job.name}"
        )
        thread.start()
        self.worker_threads.append(thread)
        
        # 완료된 스레드 정리
        self.worker_threads = [t for t in self.worker_threads if t.is_alive()]
        
    def _execute_job_worker(self, job: ScheduleJob):
        """작업 실행 워커"""
        execution = JobExecution(job_id=job.id, parameters=job.parameters)
        
        try:
            self.logger.info(f"작업 시작: {job.name} (ID: {job.id})")
            
            # 잠금 획득
            if not self._acquire_lock(job):
                self.logger.warning(f"잠금 획득 실패: {job.name}")
                return
                
            # 실행 기록 시작
            execution_id = self._start_execution(execution)
            execution.id = execution_id
            
            # 핸들러 실행
            handler = self.job_handlers.get(job.job_type)
            if handler:
                result = handler(job, execution)
                execution.result_summary = result
                execution.status = JobStatus.COMPLETED
                self._update_job_success(job)
            else:
                raise Exception(f"핸들러 없음: {job.job_type.value}")
                
        except Exception as e:
            self.logger.error(f"작업 실행 오류: {job.name} - {str(e)}")
            self.logger.error(traceback.format_exc())
            execution.status = JobStatus.FAILED
            execution.error_message = str(e)
            self._update_job_failure(job, str(e))
            
        finally:
            # 실행 완료
            execution.completed_at = datetime.now()
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )
            self._complete_execution(execution)
            
            # 잠금 해제
            self._release_lock(job.id)
            
            self.logger.info(
                f"작업 완료: {job.name} - 상태: {execution.status.value}, "
                f"소요시간: {execution.duration_seconds}초"
            )
            
    def _acquire_lock(self, job: ScheduleJob) -> bool:
        """작업 잠금 획득"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            
            with conn.cursor() as cur:
                expires_at = datetime.now() + timedelta(minutes=job.timeout_minutes)
                cur.execute("""
                    INSERT INTO schedule_locks (job_id, locked_by, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (job_id) DO NOTHING
                """, (job.id, f"scheduler-{os.getpid()}", expires_at))
                
                return cur.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"잠금 획득 오류: {str(e)}")
            return False
        finally:
            conn.close()
            
    def _release_lock(self, job_id: int):
        """작업 잠금 해제"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            
            with conn.cursor() as cur:
                cur.execute("DELETE FROM schedule_locks WHERE job_id = %s", (job_id,))
                
        except Exception as e:
            self.logger.error(f"잠금 해제 오류: {str(e)}")
        finally:
            conn.close()
            
    def _start_execution(self, execution: JobExecution) -> int:
        """실행 기록 시작"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO job_executions 
                    (job_id, status, started_at, parameters)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    execution.job_id,
                    execution.status.value,
                    execution.started_at,
                    json.dumps(execution.parameters)
                ))
                execution_id = cur.fetchone()[0]
                conn.commit()
                return execution_id
                
        except Exception as e:
            self.logger.error(f"실행 기록 시작 오류: {str(e)}")
            return 0
        finally:
            conn.close()
            
    def _complete_execution(self, execution: JobExecution):
        """실행 기록 완료"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE job_executions
                    SET status = %s, completed_at = %s, duration_seconds = %s,
                        records_processed = %s, error_message = %s, 
                        result_summary = %s
                    WHERE id = %s
                """, (
                    execution.status.value,
                    execution.completed_at,
                    execution.duration_seconds,
                    execution.records_processed,
                    execution.error_message,
                    json.dumps(execution.result_summary),
                    execution.id
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"실행 기록 완료 오류: {str(e)}")
        finally:
            conn.close()
            
    def _update_job_success(self, job: ScheduleJob):
        """작업 성공 업데이트"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE schedule_jobs
                    SET last_run_at = CURRENT_TIMESTAMP,
                        last_success_at = CURRENT_TIMESTAMP,
                        run_count = run_count + 1,
                        success_count = success_count + 1,
                        last_error = NULL
                    WHERE id = %s
                """, (job.id,))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"작업 성공 업데이트 오류: {str(e)}")
        finally:
            conn.close()
            
    def _update_job_failure(self, job: ScheduleJob, error: str):
        """작업 실패 업데이트"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE schedule_jobs
                    SET last_run_at = CURRENT_TIMESTAMP,
                        run_count = run_count + 1,
                        error_count = error_count + 1,
                        last_error = %s
                    WHERE id = %s
                """, (error[:500], job.id))  # 에러 메시지 길이 제한
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"작업 실패 업데이트 오류: {str(e)}")
        finally:
            conn.close()
            
    def _update_next_run_times(self):
        """다음 실행 시간 업데이트"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # 간격 기반 스케줄
                cur.execute("""
                    UPDATE schedule_jobs
                    SET next_run_at = CASE
                        WHEN interval = '5m' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '5 minutes'
                        WHEN interval = '10m' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '10 minutes'
                        WHEN interval = '15m' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '15 minutes'
                        WHEN interval = '30m' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '30 minutes'
                        WHEN interval = '1h' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '1 hour'
                        WHEN interval = '2h' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '2 hours'
                        WHEN interval = '4h' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '4 hours'
                        WHEN interval = '6h' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '6 hours'
                        WHEN interval = '12h' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '12 hours'
                        WHEN interval = '1d' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '1 day'
                        WHEN interval = '1w' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '1 week'
                        WHEN interval = '1M' THEN COALESCE(last_run_at, CURRENT_TIMESTAMP) + INTERVAL '1 month'
                    END
                    WHERE interval IS NOT NULL AND is_active = true
                """)
                
                # 특정 시간 스케줄은 별도 로직으로 처리
                # TODO: 특정 시간 스케줄 next_run_at 계산 구현
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"다음 실행 시간 업데이트 오류: {str(e)}")
        finally:
            conn.close()
            
    # 작업 핸들러 구현
    def _handle_product_collection(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """상품 수집 작업 처리"""
        result = {
            'markets': {},
            'total_products': 0,
            'errors': []
        }
        
        try:
            for market_code in job.market_codes:
                self.logger.info(f"상품 수집 시작: {market_code}")
                
                if market_code == 'coupang':
                    # 쿠팡 상품 수집 실행
                    from ..market.coupang.collect_products_unified import main as collect_coupang
                    count = collect_coupang()
                    result['markets'][market_code] = count
                    result['total_products'] += count
                    
                elif market_code == 'naver':
                    # 네이버 상품 수집 실행
                    from ..market.naver.collect_products import collect_all_products
                    count = collect_all_products()
                    result['markets'][market_code] = count
                    result['total_products'] += count
                    
                elif market_code == 'eleven':
                    # 11번가 상품 수집 실행
                    from ..market.eleven.collect_products import collect_all_products
                    count = collect_all_products()
                    result['markets'][market_code] = count
                    result['total_products'] += count
                    
            execution.records_processed = result['total_products']
            
        except Exception as e:
            error_msg = f"상품 수집 오류: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            raise
            
        return result
        
    def _handle_order_collection(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """주문 수집 작업 처리"""
        result = {
            'markets': {},
            'total_orders': 0,
            'errors': []
        }
        
        try:
            days_back = job.parameters.get('days_back', 1)
            
            for market_code in job.market_codes:
                self.logger.info(f"주문 수집 시작: {market_code}")
                
                if market_code == 'coupang':
                    # 쿠팡 주문 수집
                    from ..market.coupang.collect_orders_jsonb import main as collect_orders
                    count = collect_orders(days_back=days_back)
                    result['markets'][market_code] = count
                    result['total_orders'] += count
                    
                # TODO: 네이버, 11번가 주문 수집 구현
                
            execution.records_processed = result['total_orders']
            
        except Exception as e:
            error_msg = f"주문 수집 오류: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            raise
            
        return result
        
    def _handle_inventory_sync(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """재고 동기화 작업 처리"""
        # TODO: 재고 동기화 로직 구현
        return {'status': 'not_implemented'}
        
    def _handle_price_update(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """가격 업데이트 작업 처리"""
        # TODO: 가격 업데이트 로직 구현
        return {'status': 'not_implemented'}
        
    def _handle_database_backup(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """데이터베이스 백업 작업 처리"""
        result = {
            'backup_file': '',
            'size_mb': 0,
            'tables_backed_up': 0
        }
        
        try:
            backup_type = job.parameters.get('backup_type', 'full')
            retention_days = job.parameters.get('retention_days', 30)
            
            # 백업 디렉토리 생성
            backup_dir = Path(__file__).parent.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # 백업 파일명
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"yoonni_backup_{timestamp}.sql"
            
            # pg_dump 실행
            import subprocess
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '-f', str(backup_file),
                '--verbose'
            ]
            
            # PGPASSWORD 환경변수 설정
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            process = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if process.returncode == 0:
                # 백업 성공
                file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                result['backup_file'] = str(backup_file)
                result['size_mb'] = round(file_size, 2)
                
                # 오래된 백업 삭제
                self._cleanup_old_backups(backup_dir, retention_days)
                
                self.logger.info(f"데이터베이스 백업 완료: {backup_file} ({file_size:.2f} MB)")
            else:
                raise Exception(f"pg_dump 실패: {process.stderr}")
                
        except Exception as e:
            error_msg = f"데이터베이스 백업 오류: {str(e)}"
            self.logger.error(error_msg)
            raise
            
        return result
        
    def _handle_report_generation(self, job: ScheduleJob, execution: JobExecution) -> dict:
        """보고서 생성 작업 처리"""
        # TODO: 보고서 생성 로직 구현
        return {'status': 'not_implemented'}
        
    def _cleanup_old_backups(self, backup_dir: Path, retention_days: int):
        """오래된 백업 파일 삭제"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for backup_file in backup_dir.glob("yoonni_backup_*.sql"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                self.logger.info(f"오래된 백업 삭제: {backup_file}")


if __name__ == "__main__":
    # 스케줄러 실행
    scheduler = SchedulerManager()
    scheduler.start()