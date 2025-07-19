#!/usr/bin/env python3
"""
에러 핸들러 통합 테스트
"""
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.error_handlers import (
    global_exception_handler,
    retry_on_exception,
    CircuitBreaker,
    APIError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    DatabaseError
)


class TestErrorHandlers:
    """에러 핸들러 테스트"""
    
    @pytest.fixture
    def test_app(self):
        """테스트용 FastAPI 앱"""
        app = FastAPI()
        app.add_exception_handler(Exception, global_exception_handler)
        
        @app.get("/test/api-error")
        async def raise_api_error():
            raise APIError("테스트 API 에러", status_code=400, error_code="TEST_ERROR")
        
        @app.get("/test/validation-error")
        async def raise_validation_error():
            raise ValidationError("필드 검증 실패", field="test_field")
        
        @app.get("/test/not-found")
        async def raise_not_found():
            raise NotFoundError("Product", "12345")
        
        @app.get("/test/rate-limit")
        async def raise_rate_limit():
            raise RateLimitError(retry_after=60)
        
        @app.get("/test/database-error")
        async def raise_database_error():
            raise DatabaseError("연결 실패")
        
        @app.get("/test/http-exception")
        async def raise_http_exception():
            raise HTTPException(status_code=403, detail="접근 거부")
        
        @app.get("/test/unexpected-error")
        async def raise_unexpected_error():
            raise RuntimeError("예상치 못한 에러")
        
        return app
    
    def test_api_error_handling(self, test_app):
        """API 에러 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/api-error")
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "테스트 API 에러"
        assert "timestamp" in data["error"]
        assert data["error"]["path"] == "http://testserver/test/api-error"
    
    def test_validation_error_handling(self, test_app):
        """검증 에러 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/validation-error")
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "필드 검증 실패" in data["error"]["message"]
    
    def test_not_found_error_handling(self, test_app):
        """Not Found 에러 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/not-found")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "Product not found: 12345" in data["error"]["message"]
    
    def test_rate_limit_error_handling(self, test_app):
        """Rate Limit 에러 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/rate-limit")
        assert response.status_code == 429
        
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT"
        assert "60 seconds" in data["error"]["message"]
    
    def test_http_exception_handling(self, test_app):
        """HTTP 예외 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/http-exception")
        assert response.status_code == 403
        
        data = response.json()
        assert data["error"]["code"] == "HTTP_ERROR"
        assert data["error"]["message"] == "접근 거부"
    
    def test_unexpected_error_handling(self, test_app):
        """예상치 못한 에러 처리 테스트"""
        client = TestClient(test_app)
        
        response = client.get("/test/unexpected-error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "Internal server error occurred"


class TestRetryDecorator:
    """재시도 데코레이터 테스트"""
    
    def test_sync_retry_success(self):
        """동기 함수 재시도 성공 테스트"""
        call_count = 0
        
        @retry_on_exception(max_attempts=3, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("일시적 오류")
            return "성공"
        
        result = flaky_function()
        assert result == "성공"
        assert call_count == 3
    
    def test_sync_retry_failure(self):
        """동기 함수 재시도 실패 테스트"""
        call_count = 0
        
        @retry_on_exception(max_attempts=3, delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("항상 실패")
        
        with pytest.raises(ValueError, match="항상 실패"):
            always_fails()
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """비동기 함수 재시도 성공 테스트"""
        call_count = 0
        
        @retry_on_exception(max_attempts=3, delay=0.1)
        async def async_flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("일시적 오류")
            return "비동기 성공"
        
        result = await async_flaky_function()
        assert result == "비동기 성공"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_with_backoff(self):
        """지수 백오프 테스트"""
        call_times = []
        
        @retry_on_exception(max_attempts=3, delay=0.1, backoff_factor=2.0)
        async def timed_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("재시도 필요")
            return "완료"
        
        start_time = time.time()
        result = await timed_function()
        
        assert result == "완료"
        assert len(call_times) == 3
        
        # 백오프 지연 확인
        # 첫 재시도: 0.1초, 두 번째 재시도: 0.2초
        assert call_times[1] - call_times[0] >= 0.1
        assert call_times[2] - call_times[1] >= 0.2


class TestCircuitBreaker:
    """서킷 브레이커 테스트"""
    
    def test_circuit_breaker_opens(self):
        """서킷 브레이커 열림 테스트"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        call_count = 0
        
        @breaker
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("실패")
        
        # 3번 실패하면 서킷이 열림
        for i in range(3):
            with pytest.raises(ValueError):
                failing_function()
        
        assert call_count == 3
        assert breaker.state == "open"
        
        # 서킷이 열린 상태에서는 함수가 호출되지 않음
        with pytest.raises(APIError, match="Service temporarily unavailable"):
            failing_function()
        
        assert call_count == 3  # 호출 횟수 증가하지 않음
    
    def test_circuit_breaker_half_open_recovery(self):
        """서킷 브레이커 복구 테스트"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        call_count = 0
        success = False
        
        @breaker
        def sometimes_working():
            nonlocal call_count
            call_count += 1
            if success:
                return "성공"
            raise ValueError("실패")
        
        # 서킷 열기
        for _ in range(2):
            with pytest.raises(ValueError):
                sometimes_working()
        
        assert breaker.state == "open"
        
        # 복구 타임아웃 대기
        time.sleep(0.6)
        
        # 이제 성공하도록 설정
        success = True
        
        # Half-open 상태에서 성공하면 다시 closed로
        result = sometimes_working()
        assert result == "성공"
        assert breaker.state == "closed"
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """비동기 서킷 브레이커 테스트"""
        breaker = CircuitBreaker(failure_threshold=2)
        
        @breaker
        async def async_failing():
            raise ValueError("비동기 실패")
        
        # 서킷 열기
        for _ in range(2):
            with pytest.raises(ValueError):
                await async_failing()
        
        # 서킷이 열린 상태 확인
        with pytest.raises(APIError, match="Service temporarily unavailable"):
            await async_failing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])