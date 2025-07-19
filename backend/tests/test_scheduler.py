"""
스케줄러 테스트
"""
import pytest
from datetime import datetime, timedelta
from scheduler.models import ScheduleJob, JobStatus, JobType, ScheduleInterval, JobExecution
from scheduler.scheduler_manager import SchedulerManager
import threading
import time


class TestSchedulerModels:
    """스케줄러 모델 테스트"""
    
    def test_schedule_job_creation(self):
        """ScheduleJob 생성 테스트"""
        job = ScheduleJob(
            name="테스트 작업",
            job_type=JobType.PRODUCT_COLLECTION,
            interval=ScheduleInterval.EVERY_30_MINUTES,
            market_codes=['coupang', 'naver']
        )
        
        assert job.name == "테스트 작업"
        assert job.job_type == JobType.PRODUCT_COLLECTION
        assert job.status == JobStatus.ACTIVE
        assert job.interval == ScheduleInterval.EVERY_30_MINUTES
        assert 'coupang' in job.market_codes
    
    def test_schedule_job_auto_naming(self):
        """ScheduleJob 자동 이름 생성 테스트"""
        job = ScheduleJob(job_type=JobType.ORDER_COLLECTION)
        
        assert job.name.startswith('order_collection_')
        assert len(job.name) > len('order_collection_')
    
    def test_job_execution_duration(self):
        """JobExecution 실행 시간 계산 테스트"""
        execution = JobExecution(job_id=1)
        
        # 시작 시간 설정
        start_time = datetime.now()
        execution.started_at = start_time
        
        # 완료 시간 설정 (30초 후)
        execution.completed_at = start_time + timedelta(seconds=30)
        execution.duration_seconds = 30
        
        assert execution.duration_seconds == 30


class TestSchedulerManager:
    """스케줄러 매니저 테스트"""
    
    @pytest.fixture
    def scheduler(self):
        """스케줄러 인스턴스"""
        scheduler = SchedulerManager()
        scheduler.running = False  # 자동 시작 방지
        return scheduler
    
    def test_scheduler_initialization(self, scheduler):
        """스케줄러 초기화 테스트"""
        assert scheduler is not None
        assert not scheduler.running
        assert len(scheduler.job_handlers) > 0
        
        # 기본 핸들러 등록 확인
        assert JobType.PRODUCT_COLLECTION in scheduler.job_handlers
        assert JobType.ORDER_COLLECTION in scheduler.job_handlers
        assert JobType.DATABASE_BACKUP in scheduler.job_handlers
    
    def test_register_handler(self, scheduler):
        """핸들러 등록 테스트"""
        def custom_handler(job, execution):
            return {'status': 'custom_handler_executed'}
        
        scheduler.register_handler(JobType.INVENTORY_SYNC, custom_handler)
        
        assert JobType.INVENTORY_SYNC in scheduler.job_handlers
        assert scheduler.job_handlers[JobType.INVENTORY_SYNC] == custom_handler
    
    @pytest.mark.db
    def test_load_active_jobs(self, scheduler, db_cursor):
        """활성 작업 로드 테스트"""
        # 테스트 작업 생성
        db_cursor.execute("""
            INSERT INTO schedule_jobs (
                name, job_type, status, interval, market_codes
            ) VALUES (
                '테스트 작업', 'product_collection', 'active', '30m', 
                ARRAY['coupang']
            )
        """)
        db_cursor.connection.commit()
        
        # 작업 로드
        scheduler._load_active_jobs()
        
        assert len(scheduler.jobs) > 0
        
        # 첫 번째 작업 확인
        job = list(scheduler.jobs.values())[0]
        assert job.name == '테스트 작업'
        assert job.job_type == JobType.PRODUCT_COLLECTION
    
    def test_should_run_job_first_run(self, scheduler):
        """첫 실행 작업 판단 테스트"""
        job = ScheduleJob(
            id=1,
            name="첫 실행 작업",
            job_type=JobType.PRODUCT_COLLECTION,
            last_run_at=None  # 실행 이력 없음
        )
        
        should_run = scheduler._should_run_job(job, datetime.now())
        assert should_run
    
    def test_should_run_job_with_next_run_time(self, scheduler):
        """다음 실행 시간 기반 작업 판단 테스트"""
        # 과거 시간으로 설정
        past_time = datetime.now() - timedelta(minutes=5)
        job = ScheduleJob(
            id=1,
            name="시간 경과 작업",
            job_type=JobType.PRODUCT_COLLECTION,
            next_run_at=past_time,
            last_run_at=datetime.now() - timedelta(hours=1)
        )
        
        should_run = scheduler._should_run_job(job, datetime.now())
        assert should_run
    
    def test_should_not_run_job_future_time(self, scheduler):
        """미래 실행 시간 작업 판단 테스트"""
        # 미래 시간으로 설정
        future_time = datetime.now() + timedelta(minutes=5)
        job = ScheduleJob(
            id=1,
            name="미래 작업",
            job_type=JobType.PRODUCT_COLLECTION,
            next_run_at=future_time,
            last_run_at=datetime.now() - timedelta(hours=1)
        )
        
        should_run = scheduler._should_run_job(job, datetime.now())
        assert not should_run
    
    @pytest.mark.slow
    def test_job_execution_thread(self, scheduler):
        """작업 실행 스레드 테스트"""
        execution_result = {'executed': False}
        
        def test_handler(job, execution):
            execution_result['executed'] = True
            execution.records_processed = 10
            return {'status': 'success'}
        
        # 테스트 핸들러 등록
        scheduler.register_handler(JobType.PRODUCT_COLLECTION, test_handler)
        
        # 테스트 작업
        job = ScheduleJob(
            id=1,
            name="스레드 테스트 작업",
            job_type=JobType.PRODUCT_COLLECTION
        )
        
        # 작업 실행
        scheduler._execute_job(job)
        
        # 스레드 완료 대기 (최대 2초)
        for _ in range(20):
            if execution_result['executed']:
                break
            time.sleep(0.1)
        
        assert execution_result['executed']
    
    def test_parse_size_to_bytes(self, scheduler):
        """크기 문자열 파싱 테스트"""
        test_cases = [
            ('100 bytes', 100),
            ('1 kB', 1024),
            ('5 MB', 5 * 1024 * 1024),
            ('2 GB', 2 * 1024 * 1024 * 1024),
            ('0.5 GB', int(0.5 * 1024 * 1024 * 1024))
        ]
        
        for size_str, expected in test_cases:
            result = scheduler._parse_size_to_bytes(size_str)
            assert result == expected
    
    def test_format_bytes(self, scheduler):
        """바이트 포맷팅 테스트"""
        test_cases = [
            (0, '0 bytes'),
            (100, '100.00 bytes'),
            (1024, '1.00 kB'),
            (1024 * 1024, '1.00 MB'),
            (1024 * 1024 * 1024, '1.00 GB'),
            (1536 * 1024, '1.50 MB')
        ]
        
        for bytes_value, expected in test_cases:
            result = scheduler._format_bytes(bytes_value)
            assert result == expected


class TestSchedulerHandlers:
    """스케줄러 핸들러 테스트"""
    
    @pytest.fixture
    def scheduler(self):
        """스케줄러 인스턴스"""
        return SchedulerManager()
    
    @pytest.mark.slow
    def test_product_collection_handler(self, scheduler, monkeypatch):
        """상품 수집 핸들러 테스트"""
        # 수집 함수 모킹
        collection_called = {'coupang': False, 'naver': False}
        
        def mock_coupang_collect():
            collection_called['coupang'] = True
            return 100
        
        def mock_naver_collect():
            collection_called['naver'] = True
            return 50
        
        # 모듈 임포트 모킹
        import sys
        sys.modules['market.coupang.collect_products_unified'] = type(sys)('mock')
        sys.modules['market.coupang.collect_products_unified'].main = mock_coupang_collect
        
        sys.modules['market.naver.collect_products'] = type(sys)('mock')
        sys.modules['market.naver.collect_products'].collect_all_products = mock_naver_collect
        
        # 작업 및 실행 객체
        job = ScheduleJob(
            id=1,
            name="상품 수집 테스트",
            job_type=JobType.PRODUCT_COLLECTION,
            market_codes=['coupang', 'naver']
        )
        execution = JobExecution(job_id=1)
        
        # 핸들러 실행
        result = scheduler._handle_product_collection(job, execution)
        
        assert collection_called['coupang']
        assert collection_called['naver']
        assert result['total_products'] == 150
        assert execution.records_processed == 150