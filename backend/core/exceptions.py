"""
중앙 집중식 예외 처리 시스템
"""
from typing import Optional, Dict, Any
from datetime import datetime
import traceback
from enum import Enum


class ErrorCode(Enum):
    """표준화된 에러 코드"""
    # 일반 에러 (1000번대)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    PERMISSION_DENIED = 1002
    NOT_FOUND = 1003
    ALREADY_EXISTS = 1004
    
    # 데이터베이스 에러 (2000번대)
    DB_CONNECTION_ERROR = 2001
    DB_QUERY_ERROR = 2002
    DB_INTEGRITY_ERROR = 2003
    DB_TRANSACTION_ERROR = 2004
    
    # API 에러 (3000번대)
    API_CONNECTION_ERROR = 3001
    API_TIMEOUT_ERROR = 3002
    API_AUTHENTICATION_ERROR = 3003
    API_RATE_LIMIT_ERROR = 3004
    API_INVALID_RESPONSE = 3005
    
    # 마켓 관련 에러 (4000번대)
    MARKET_PRODUCT_NOT_FOUND = 4001
    MARKET_ORDER_NOT_FOUND = 4002
    MARKET_INVALID_STATUS = 4003
    MARKET_SYNC_ERROR = 4004
    
    # 비즈니스 로직 에러 (5000번대)
    INSUFFICIENT_STOCK = 5001
    INVALID_PRICE = 5002
    ORDER_ALREADY_PROCESSED = 5003
    INVALID_BUSINESS_RULE = 5004


class BaseException(Exception):
    """기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        
        # 스택 트레이스 저장
        self.stack_trace = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        result = {
            'error_code': self.error_code.value,
            'error_name': self.error_code.name,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }
        
        if self.cause:
            result['cause'] = {
                'type': type(self.cause).__name__,
                'message': str(self.cause)
            }
        
        return result
    
    def __str__(self):
        return f"[{self.error_code.name}] {self.message}"


# 데이터베이스 관련 예외
class DatabaseException(BaseException):
    """데이터베이스 예외"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_QUERY_ERROR,
            details=details,
            cause=cause
        )


class DatabaseConnectionException(DatabaseException):
    """데이터베이스 연결 예외"""
    
    def __init__(self, message: str = "데이터베이스 연결 실패", **kwargs):
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.DB_CONNECTION_ERROR


class DatabaseIntegrityException(DatabaseException):
    """데이터베이스 무결성 예외"""
    
    def __init__(self, message: str = "데이터 무결성 제약 위반", **kwargs):
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.DB_INTEGRITY_ERROR


# API 관련 예외
class APIException(BaseException):
    """API 예외"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'status_code': status_code,
            'response_data': response_data
        })
        kwargs['details'] = details
        
        super().__init__(
            message=message,
            error_code=ErrorCode.API_CONNECTION_ERROR,
            **kwargs
        )


class APITimeoutException(APIException):
    """API 타임아웃 예외"""
    
    def __init__(self, message: str = "API 요청 시간 초과", timeout: Optional[float] = None, **kwargs):
        if timeout:
            details = kwargs.get('details', {})
            details['timeout'] = timeout
            kwargs['details'] = details
        
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.API_TIMEOUT_ERROR


class APIAuthenticationException(APIException):
    """API 인증 예외"""
    
    def __init__(self, message: str = "API 인증 실패", **kwargs):
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.API_AUTHENTICATION_ERROR


class APIRateLimitException(APIException):
    """API 속도 제한 예외"""
    
    def __init__(
        self,
        message: str = "API 요청 한도 초과",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        if retry_after:
            details = kwargs.get('details', {})
            details['retry_after'] = retry_after
            kwargs['details'] = details
        
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.API_RATE_LIMIT_ERROR


# 마켓 관련 예외
class MarketException(BaseException):
    """마켓 관련 예외"""
    
    def __init__(self, message: str, market_code: str, **kwargs):
        details = kwargs.get('details', {})
        details['market_code'] = market_code
        kwargs['details'] = details
        
        super().__init__(
            message=message,
            error_code=ErrorCode.MARKET_SYNC_ERROR,
            **kwargs
        )


class ProductNotFoundException(MarketException):
    """상품을 찾을 수 없음"""
    
    def __init__(self, product_id: str, market_code: str, **kwargs):
        message = f"상품을 찾을 수 없습니다: {product_id}"
        details = kwargs.get('details', {})
        details['product_id'] = product_id
        kwargs['details'] = details
        
        super().__init__(message=message, market_code=market_code, **kwargs)
        self.error_code = ErrorCode.MARKET_PRODUCT_NOT_FOUND


class OrderNotFoundException(MarketException):
    """주문을 찾을 수 없음"""
    
    def __init__(self, order_id: str, market_code: str, **kwargs):
        message = f"주문을 찾을 수 없습니다: {order_id}"
        details = kwargs.get('details', {})
        details['order_id'] = order_id
        kwargs['details'] = details
        
        super().__init__(message=message, market_code=market_code, **kwargs)
        self.error_code = ErrorCode.MARKET_ORDER_NOT_FOUND


# 비즈니스 로직 예외
class BusinessLogicException(BaseException):
    """비즈니스 로직 예외"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_BUSINESS_RULE,
            **kwargs
        )


class InsufficientStockException(BusinessLogicException):
    """재고 부족 예외"""
    
    def __init__(
        self,
        product_id: str,
        requested_quantity: int,
        available_quantity: int,
        **kwargs
    ):
        message = f"재고 부족: 요청 수량 {requested_quantity}, 가용 수량 {available_quantity}"
        details = kwargs.get('details', {})
        details.update({
            'product_id': product_id,
            'requested_quantity': requested_quantity,
            'available_quantity': available_quantity
        })
        kwargs['details'] = details
        
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.INSUFFICIENT_STOCK


class InvalidPriceException(BusinessLogicException):
    """잘못된 가격 예외"""
    
    def __init__(self, price: float, reason: str, **kwargs):
        message = f"잘못된 가격: {price} ({reason})"
        details = kwargs.get('details', {})
        details.update({
            'price': price,
            'reason': reason
        })
        kwargs['details'] = details
        
        super().__init__(message=message, **kwargs)
        self.error_code = ErrorCode.INVALID_PRICE


# 유효성 검사 예외
class ValidationException(BaseException):
    """유효성 검사 예외"""
    
    def __init__(self, field: str, value: Any, constraint: str, **kwargs):
        message = f"유효성 검사 실패: {field} = {value} ({constraint})"
        details = kwargs.get('details', {})
        details.update({
            'field': field,
            'value': value,
            'constraint': constraint
        })
        kwargs['details'] = details
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            **kwargs
        )