"""
중앙 집중식 로깅 시스템
"""
import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback
from functools import wraps

class JSONFormatter(logging.Formatter):
    """JSON 형식의 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
        }
        
        # 추가 필드 포함
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'market_code'):
            log_data['market_code'] = record.market_code
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
            
        # 에러 정보 포함
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)


class DatabaseLogHandler(logging.Handler):
    """데이터베이스 로그 핸들러"""
    
    def __init__(self, db_config: Dict[str, Any]):
        super().__init__()
        self.db_config = db_config
        self._connection = None
        self._init_table()
    
    def _init_table(self):
        """로그 테이블 초기화"""
        import psycopg2
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level VARCHAR(20),
                    logger VARCHAR(100),
                    message TEXT,
                    module VARCHAR(100),
                    function VARCHAR(100),
                    line INTEGER,
                    user_id VARCHAR(50),
                    market_code VARCHAR(20),
                    request_id VARCHAR(50),
                    execution_time FLOAT,
                    exception_type VARCHAR(100),
                    exception_message TEXT,
                    traceback TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
                CREATE INDEX IF NOT EXISTS idx_logs_logger ON system_logs(logger);
                CREATE INDEX IF NOT EXISTS idx_logs_market ON system_logs(market_code);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"로그 테이블 초기화 실패: {e}")
    
    def emit(self, record: logging.LogRecord):
        """로그 레코드를 데이터베이스에 저장"""
        import psycopg2
        from psycopg2.extras import Json
        
        try:
            if not self._connection or self._connection.closed:
                self._connection = psycopg2.connect(**self.db_config)
            
            cursor = self._connection.cursor()
            
            # 메타데이터 수집
            metadata = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 
                               'funcName', 'levelname', 'levelno', 'lineno', 
                               'module', 'exc_info', 'exc_text', 'stack_info',
                               'pathname', 'process', 'processName', 'thread',
                               'threadName', 'getMessage']:
                    metadata[key] = value
            
            # 예외 정보 처리
            exception_type = None
            exception_message = None
            traceback_text = None
            
            if record.exc_info:
                exception_type = record.exc_info[0].__name__
                exception_message = str(record.exc_info[1])
                traceback_text = ''.join(traceback.format_exception(*record.exc_info))
            
            cursor.execute("""
                INSERT INTO system_logs (
                    timestamp, level, logger, message, module, function, line,
                    user_id, market_code, request_id, execution_time,
                    exception_type, exception_message, traceback, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                datetime.fromtimestamp(record.created),
                record.levelname,
                record.name,
                record.getMessage(),
                record.module,
                record.funcName,
                record.lineno,
                getattr(record, 'user_id', None),
                getattr(record, 'market_code', None),
                getattr(record, 'request_id', None),
                getattr(record, 'execution_time', None),
                exception_type,
                exception_message,
                traceback_text,
                Json(metadata) if metadata else None
            ))
            
            self._connection.commit()
            
        except Exception as e:
            self.handleError(record)


class LoggerManager:
    """로거 관리자 싱글톤"""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """루트 로거 설정"""
        # 로그 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        root_logger.addHandler(console_handler)
        
        # 파일 핸들러 (일별 로테이션)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir / 'app.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
        # 에러 전용 파일 핸들러
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / 'error.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str, **kwargs) -> logging.Logger:
        """
        로거 인스턴스 반환
        
        Args:
            name: 로거 이름
            **kwargs: 추가 설정 (market_code, user_id 등)
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            
            # 추가 속성 설정
            for key, value in kwargs.items():
                setattr(logger, key, value)
            
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def add_database_handler(self, db_config: Dict[str, Any]):
        """데이터베이스 핸들러 추가"""
        db_handler = DatabaseLogHandler(db_config)
        db_handler.setLevel(logging.WARNING)  # WARNING 이상만 DB에 저장
        db_handler.setFormatter(JSONFormatter())
        
        root_logger = logging.getLogger()
        root_logger.addHandler(db_handler)


# 편의 함수
def get_logger(name: str, **kwargs) -> logging.Logger:
    """로거 인스턴스 반환"""
    manager = LoggerManager()
    return manager.get_logger(name, **kwargs)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """함수 실행 시간 로깅 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            _logger = logger or get_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                _logger.info(
                    f"{func.__name__} 실행 완료",
                    extra={'execution_time': execution_time}
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                _logger.error(
                    f"{func.__name__} 실행 중 오류 발생",
                    exc_info=True,
                    extra={'execution_time': execution_time}
                )
                raise
        
        return wrapper
    return decorator


def log_api_call(market_code: str):
    """API 호출 로깅 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__, market_code=market_code)
            
            # 요청 ID 생성
            import uuid
            request_id = str(uuid.uuid4())
            
            logger.info(
                f"API 호출 시작: {func.__name__}",
                extra={
                    'request_id': request_id,
                    'market_code': market_code,
                    'args': str(args)[:200],  # 인자 일부만 로깅
                    'kwargs': str(kwargs)[:200]
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(
                    f"API 호출 성공: {func.__name__}",
                    extra={
                        'request_id': request_id,
                        'market_code': market_code
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(
                    f"API 호출 실패: {func.__name__}",
                    exc_info=True,
                    extra={
                        'request_id': request_id,
                        'market_code': market_code
                    }
                )
                raise
        
        return wrapper
    return decorator