"""
전역 에러 핸들러
"""
import sys
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
import json

from .exceptions import (
    BaseException, DatabaseException, APIException, 
    MarketException, BusinessLogicException, ErrorCode
)
from .logger import get_logger


class ErrorHandler:
    """중앙 집중식 에러 핸들러"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._error_callbacks: Dict[type, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """기본 에러 핸들러 설정"""
        # 기본 예외 핸들러
        self.register_handler(BaseException, self._handle_base_exception)
        self.register_handler(DatabaseException, self._handle_database_exception)
        self.register_handler(APIException, self._handle_api_exception)
        self.register_handler(MarketException, self._handle_market_exception)
        self.register_handler(BusinessLogicException, self._handle_business_exception)
        
        # 시스템 예외 핸들러
        self.register_handler(KeyError, self._handle_key_error)
        self.register_handler(ValueError, self._handle_value_error)
        self.register_handler(TypeError, self._handle_type_error)
        self.register_handler(Exception, self._handle_generic_exception)
    
    def register_handler(self, exception_type: type, handler: Callable):
        """예외 타입별 핸들러 등록"""
        self._error_callbacks[exception_type] = handler
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """에러 처리"""
        context = context or {}
        
        # 적절한 핸들러 찾기
        handler = None
        for exc_type in type(error).__mro__:
            if exc_type in self._error_callbacks:
                handler = self._error_callbacks[exc_type]
                break
        
        if handler:
            return handler(error, context)
        else:
            return self._handle_generic_exception(error, context)
    
    def _handle_base_exception(self, error: BaseException, context: Dict[str, Any]) -> Dict[str, Any]:
        """BaseException 처리"""
        self.logger.error(
            f"Application error: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'error_name': error.error_code.name,
                'details': error.details,
                'context': context
            },
            exc_info=True
        )
        
        return {
            'success': False,
            'error': error.to_dict(),
            'context': context
        }
    
    def _handle_database_exception(self, error: DatabaseException, context: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 예외 처리"""
        self.logger.error(
            f"Database error: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'query': context.get('query'),
                'params': context.get('params'),
                'details': error.details
            },
            exc_info=True
        )
        
        # 알림 발송 (중요한 DB 오류의 경우)
        if error.error_code in [ErrorCode.DB_CONNECTION_ERROR, ErrorCode.DB_TRANSACTION_ERROR]:
            self._send_alert(error, context)
        
        return {
            'success': False,
            'error': error.to_dict(),
            'retry_available': error.error_code != ErrorCode.DB_INTEGRITY_ERROR
        }
    
    def _handle_api_exception(self, error: APIException, context: Dict[str, Any]) -> Dict[str, Any]:
        """API 예외 처리"""
        self.logger.error(
            f"API error: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'url': context.get('url'),
                'method': context.get('method'),
                'status_code': error.details.get('status_code'),
                'market_code': context.get('market_code')
            },
            exc_info=True
        )
        
        # 재시도 정보 추가
        retry_info = {}
        if error.error_code == ErrorCode.API_RATE_LIMIT_ERROR:
            retry_info['retry_after'] = error.details.get('retry_after', 60)
        elif error.error_code == ErrorCode.API_TIMEOUT_ERROR:
            retry_info['retry_after'] = 5
        
        return {
            'success': False,
            'error': error.to_dict(),
            'retry_info': retry_info
        }
    
    def _handle_market_exception(self, error: MarketException, context: Dict[str, Any]) -> Dict[str, Any]:
        """마켓 예외 처리"""
        self.logger.error(
            f"Market error: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'market_code': error.details.get('market_code'),
                'operation': context.get('operation'),
                'details': error.details
            },
            exc_info=True
        )
        
        return {
            'success': False,
            'error': error.to_dict(),
            'market_code': error.details.get('market_code')
        }
    
    def _handle_business_exception(self, error: BusinessLogicException, context: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 로직 예외 처리"""
        self.logger.warning(  # 비즈니스 예외는 WARNING 레벨
            f"Business rule violation: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'details': error.details,
                'context': context
            }
        )
        
        return {
            'success': False,
            'error': error.to_dict(),
            'user_message': self._get_user_friendly_message(error)
        }
    
    def _handle_key_error(self, error: KeyError, context: Dict[str, Any]) -> Dict[str, Any]:
        """KeyError 처리"""
        self.logger.error(
            f"Key error: {str(error)}",
            extra={'context': context},
            exc_info=True
        )
        
        return {
            'success': False,
            'error': {
                'error_code': ErrorCode.VALIDATION_ERROR.value,
                'message': f"필수 키가 누락되었습니다: {str(error)}",
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _handle_value_error(self, error: ValueError, context: Dict[str, Any]) -> Dict[str, Any]:
        """ValueError 처리"""
        self.logger.error(
            f"Value error: {str(error)}",
            extra={'context': context},
            exc_info=True
        )
        
        return {
            'success': False,
            'error': {
                'error_code': ErrorCode.VALIDATION_ERROR.value,
                'message': f"잘못된 값: {str(error)}",
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _handle_type_error(self, error: TypeError, context: Dict[str, Any]) -> Dict[str, Any]:
        """TypeError 처리"""
        self.logger.error(
            f"Type error: {str(error)}",
            extra={'context': context},
            exc_info=True
        )
        
        return {
            'success': False,
            'error': {
                'error_code': ErrorCode.VALIDATION_ERROR.value,
                'message': f"타입 오류: {str(error)}",
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _handle_generic_exception(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """일반 예외 처리"""
        self.logger.error(
            f"Unexpected error: {str(error)}",
            extra={'context': context},
            exc_info=True
        )
        
        return {
            'success': False,
            'error': {
                'error_code': ErrorCode.UNKNOWN_ERROR.value,
                'message': "예상치 못한 오류가 발생했습니다",
                'details': str(error),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _get_user_friendly_message(self, error: BaseException) -> str:
        """사용자 친화적인 메시지 생성"""
        messages = {
            ErrorCode.INSUFFICIENT_STOCK: "재고가 부족합니다. 수량을 확인해주세요.",
            ErrorCode.INVALID_PRICE: "가격 정보가 올바르지 않습니다.",
            ErrorCode.ORDER_ALREADY_PROCESSED: "이미 처리된 주문입니다.",
            ErrorCode.MARKET_PRODUCT_NOT_FOUND: "상품을 찾을 수 없습니다.",
            ErrorCode.API_RATE_LIMIT_ERROR: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.DB_CONNECTION_ERROR: "데이터베이스 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요."
        }
        
        return messages.get(error.error_code, error.message)
    
    def _send_alert(self, error: BaseException, context: Dict[str, Any]):
        """중요한 에러에 대한 알림 발송"""
        # TODO: 실제 알림 시스템 연동 (Slack, Email 등)
        alert_message = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_code': error.error_code.name,
            'message': error.message,
            'context': context
        }
        
        self.logger.critical(
            f"ALERT: {error.error_code.name}",
            extra={'alert': alert_message}
        )


# 전역 에러 핸들러 인스턴스
_error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """전역 에러 처리 함수"""
    return _error_handler.handle_error(error, context)


def safe_execute(func: Callable, context: Optional[Dict[str, Any]] = None):
    """안전한 함수 실행 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return handle_error(e, context or {
                'function': func.__name__,
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200]
            })
    
    return wrapper


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (APIException, DatabaseException)
):
    """에러 발생 시 재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger = get_logger(func.__module__)
                        logger.warning(
                            f"{func.__name__} 실행 실패 (시도 {attempt + 1}/{max_attempts}), "
                            f"{current_delay}초 후 재시도",
                            extra={'error': str(e)}
                        )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # 마지막 시도 실패
                        raise
            
            # 이론적으로 여기 도달하지 않음
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator