#!/usr/bin/env python3
"""
전역 에러 핸들러 및 재시도 로직
"""
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from typing import Callable, Any, Optional, Type
import asyncio
import functools
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API 에러 기본 클래스"""
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"


class ValidationError(APIError):
    """검증 에러"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")
        self.field = field


class NotFoundError(APIError):
    """리소스 찾을 수 없음"""
    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} not found: {resource_id}"
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class RateLimitError(APIError):
    """속도 제한 에러"""
    def __init__(self, retry_after: int = 60):
        message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        super().__init__(message, status_code=429, error_code="RATE_LIMIT")
        self.retry_after = retry_after


class DatabaseError(APIError):
    """데이터베이스 에러"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR")


def create_error_response(
    request: Request,
    status_code: int,
    message: str,
    error_code: str = "ERROR",
    details: Optional[dict] = None
) -> JSONResponse:
    """표준화된 에러 응답 생성"""
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """전역 예외 핸들러"""
    if isinstance(exc, APIError):
        logger.error(f"API Error: {exc.message}", exc_info=True)
        return create_error_response(
            request=request,
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code
        )
    
    elif isinstance(exc, HTTPException):
        return create_error_response(
            request=request,
            status_code=exc.status_code,
            message=exc.detail,
            error_code="HTTP_ERROR"
        )
    
    else:
        # 예상치 못한 에러
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return create_error_response(
            request=request,
            status_code=500,
            message="Internal server error occurred",
            error_code="INTERNAL_ERROR"
        )


def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """재시도 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        if logger:
                            logger.error(
                                f"Max retry attempts ({max_attempts}) reached for {func.__name__}: {str(e)}"
                            )
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    if logger:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {wait_time:.2f}s delay. Error: {str(e)}"
                        )
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        if logger:
                            logger.error(
                                f"Max retry attempts ({max_attempts}) reached for {func.__name__}: {str(e)}"
                            )
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    if logger:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {wait_time:.2f}s delay. Error: {str(e)}"
                        )
                    
                    time.sleep(wait_time)
            
            raise last_exception
        
        # 비동기 함수인지 확인
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """서킷 브레이커 패턴 구현"""
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise APIError(
                        "Service temporarily unavailable",
                        status_code=503,
                        error_code="CIRCUIT_BREAKER_OPEN"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise APIError(
                        "Service temporarily unavailable",
                        status_code=503,
                        error_code="CIRCUIT_BREAKER_OPEN"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")