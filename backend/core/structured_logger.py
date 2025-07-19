#!/usr/bin/env python3
"""
구조화된 로거 - JSON 형식의 로그와 메트릭 수집
"""
import logging
import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager
import functools
from collections import defaultdict
import threading

class StructuredLogger:
    """구조화된 JSON 로거"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # JSON 포맷터 설정
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
        
        # 메트릭 수집
        self.metrics = defaultdict(list)
        self.metrics_lock = threading.Lock()
    
    class JsonFormatter(logging.Formatter):
        """JSON 형식으로 로그 포맷팅"""
        
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # 추가 컨텍스트 정보
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)
            
            # 예외 정보
            if record.exc_info:
                log_data["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": traceback.format_exception(*record.exc_info)
                }
            
            return json.dumps(log_data, ensure_ascii=False)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """컨텍스트 정보와 함께 로그"""
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    @contextmanager
    def timer(self, operation: str, **context):
        """작업 시간 측정 컨텍스트 매니저"""
        start_time = time.time()
        
        self.info(f"{operation} 시작", operation=operation, **context)
        
        try:
            yield
            duration = time.time() - start_time
            
            self.info(
                f"{operation} 완료",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                status="success",
                **context
            )
            
            # 메트릭 수집
            with self.metrics_lock:
                self.metrics[operation].append(duration)
                
        except Exception as e:
            duration = time.time() - start_time
            
            self.error(
                f"{operation} 실패",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                status="failed",
                error=str(e),
                **context
            )
            raise
    
    def log_api_request(self, method: str, url: str, status_code: int, 
                       duration: float, **kwargs):
        """API 요청 로그"""
        self.info(
            "API 요청",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            success=200 <= status_code < 300,
            **kwargs
        )
    
    def log_database_query(self, query: str, duration: float, 
                          rows_affected: Optional[int] = None, **kwargs):
        """데이터베이스 쿼리 로그"""
        # 쿼리 단순화 (긴 쿼리는 처음 100자만)
        simplified_query = query.strip()[:100] + "..." if len(query) > 100 else query.strip()
        
        self.info(
            "데이터베이스 쿼리",
            query=simplified_query,
            duration_ms=round(duration * 1000, 2),
            rows_affected=rows_affected,
            **kwargs
        )
    
    def log_business_metric(self, metric_name: str, value: Any, **tags):
        """비즈니스 메트릭 로그"""
        self.info(
            "비즈니스 메트릭",
            metric_name=metric_name,
            value=value,
            metric_type="business",
            **tags
        )
    
    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """수집된 메트릭 요약"""
        with self.metrics_lock:
            summary = {}
            
            for operation, durations in self.metrics.items():
                if durations:
                    summary[operation] = {
                        "count": len(durations),
                        "total": sum(durations),
                        "avg": sum(durations) / len(durations),
                        "min": min(durations),
                        "max": max(durations)
                    }
            
            return summary


def log_execution_time(logger: StructuredLogger):
    """함수 실행 시간 로깅 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with logger.timer(f"{func.__module__}.{func.__name__}"):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with logger.timer(f"{func.__module__}.{func.__name__}"):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 글로벌 로거 인스턴스
_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """구조화된 로거 가져오기"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]