"""
스케줄러 모델 정의
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, time
from dataclasses import dataclass, field


class JobType(Enum):
    """작업 유형"""
    PRODUCT_COLLECTION = "product_collection"
    ORDER_COLLECTION = "order_collection"
    INVENTORY_SYNC = "inventory_sync"
    PRICE_UPDATE = "price_update"
    SHIPMENT_SYNC = "shipment_sync"
    RETURN_SYNC = "return_sync"
    DATABASE_BACKUP = "database_backup"
    REPORT_GENERATION = "report_generation"


class JobStatus(Enum):
    """작업 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleInterval(Enum):
    """스케줄 간격"""
    EVERY_5_MINUTES = "5m"
    EVERY_10_MINUTES = "10m"
    EVERY_15_MINUTES = "15m"
    EVERY_30_MINUTES = "30m"
    HOURLY = "1h"
    EVERY_2_HOURS = "2h"
    EVERY_4_HOURS = "4h"
    EVERY_6_HOURS = "6h"
    EVERY_12_HOURS = "12h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


@dataclass
class ScheduleJob:
    """스케줄 작업 정의"""
    id: Optional[int] = None
    name: str = ""
    job_type: JobType = JobType.PRODUCT_COLLECTION
    status: JobStatus = JobStatus.ACTIVE
    interval: Optional[ScheduleInterval] = None
    cron_expression: Optional[str] = None
    specific_times: list[time] = field(default_factory=list)
    market_codes: list[str] = field(default_factory=list)
    account_ids: list[int] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    timeout_minutes: int = 30
    priority: int = 5
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.job_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


@dataclass
class JobExecution:
    """작업 실행 기록"""
    id: Optional[int] = None
    job_id: int = 0
    status: JobStatus = JobStatus.RUNNING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    records_processed: int = 0
    error_message: Optional[str] = None
    log_file_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result_summary: Dict[str, Any] = field(default_factory=dict)