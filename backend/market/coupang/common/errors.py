#!/usr/bin/env python3
"""
쿠팡 API 에러 핸들링 및 로깅 시스템
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime


class CoupangAPIError(Exception):
    """쿠팡 API 오류 기본 클래스"""
    
    def __init__(self, message: str, error_code: Optional[int] = None, 
                 response_data: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.response_data = response_data or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)


class CoupangAuthError(CoupangAPIError):
    """쿠팡 API 인증 오류"""
    pass


class CoupangValidationError(CoupangAPIError):
    """쿠팡 API 파라미터 검증 오류"""
    pass


class CoupangNetworkError(CoupangAPIError):
    """쿠팡 API 네트워크 오류"""
    pass


class ErrorHandler:
    """통합 에러 핸들러"""
    
    def __init__(self, logger_name: str = "coupang_api"):
        self.logger = self._setup_logger(logger_name)
    
    def _setup_logger(self, name: str) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(name)
        
        # 이미 설정된 경우 재사용
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def handle_api_success(self, response: Dict[str, Any], 
                          default_message: str = "API 호출 성공",
                          **extra_data) -> Dict[str, Any]:
        """API 성공 응답 처리"""
        result = {
            "success": True,
            "message": default_message,
            "timestamp": datetime.now().isoformat(),
            "data": response.get("data", []),
            **extra_data
        }
        
        # 민감 정보 제거 후 로깅
        safe_result = self._sanitize_for_logging(result)
        self.logger.info(f"✅ {default_message}: {safe_result.get('message', '')}")
        
        return result
    
    def handle_api_error(self, response: Dict[str, Any], 
                        custom_message: Optional[str] = None) -> Dict[str, Any]:
        """API 오류 응답 처리"""
        error_code = response.get("code", 0)
        error_message = response.get("message", "알 수 없는 오류")
        
        if custom_message:
            display_message = custom_message
        else:
            display_message = error_message
        
        result = {
            "success": False,
            "error": display_message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat(),
            "raw_response": response
        }
        
        # 오류 로깅
        self.logger.error(f"❌ API 오류 (코드: {error_code}): {display_message}")
        
        return result
    
    def handle_exception_error(self, exception: Exception, 
                             context: str = "API 호출") -> Dict[str, Any]:
        """예외 오류 처리"""
        error_message = f"{context} 중 오류: {str(exception)}"
        
        result = {
            "success": False,
            "error": error_message,
            "exception_type": type(exception).__name__,
            "timestamp": datetime.now().isoformat()
        }
        
        # 예외 로깅 (스택 트레이스 포함)
        self.logger.error(f"💥 {error_message}")
        self.logger.debug(f"스택 트레이스: {traceback.format_exc()}")
        
        return result
    
    def _sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """로깅용 민감 정보 제거"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        sensitive_keys = {
            'access_key', 'secret_key', 'password', 'token', 
            'authorization', 'signature', 'key'
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_for_logging(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_for_logging(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_api_request(self, method: str, url: str, params: Optional[Dict] = None):
        """API 요청 로깅"""
        safe_params = self._sanitize_for_logging(params or {})
        self.logger.info(f"🔄 {method} 요청: {url}")
        if safe_params:
            self.logger.debug(f"파라미터: {safe_params}")
    
    def log_performance(self, operation: str, duration: float):
        """성능 로깅"""
        self.logger.info(f"⏱️  {operation} 완료: {duration:.2f}초")


# 전역 에러 핸들러 인스턴스
error_handler = ErrorHandler()