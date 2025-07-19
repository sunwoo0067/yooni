"""
데이터베이스 설정 관리
ConfigManager를 사용하여 DB 연결 정보를 DB에서 관리
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    
    def __init__(self, config_manager=None):
        """
        Args:
            config_manager: ConfigManager 인스턴스 (순환 참조 방지)
        """
        self.config_manager = config_manager
        
        # 초기 연결 정보는 환경변수에서 (부트스트랩)
        self._bootstrap_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5434)),
            'database': os.getenv('DB_NAME', 'yoonni'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '1234')
        }
    
    def get_connection_config(self, use_db_config: bool = True) -> Dict:
        """데이터베이스 연결 설정 반환
        
        Args:
            use_db_config: DB에서 설정을 읽을지 여부
            
        Returns:
            연결 설정 딕셔너리
        """
        if not use_db_config or not self.config_manager:
            return self._bootstrap_config
        
        try:
            # DB에서 설정 읽기
            db_config = self.config_manager.get_category('database')
            
            return {
                'host': db_config.get('DB_HOST', self._bootstrap_config['host']),
                'port': int(db_config.get('DB_PORT', self._bootstrap_config['port'])),
                'database': db_config.get('DB_NAME', self._bootstrap_config['database']),
                'user': db_config.get('DB_USER', self._bootstrap_config['user']),
                'password': db_config.get('DB_PASSWORD', self._bootstrap_config['password'])
            }
        except:
            # DB 읽기 실패 시 부트스트랩 설정 사용
            return self._bootstrap_config
    
    def get_pool_config(self) -> Dict:
        """연결 풀 설정 반환"""
        if not self.config_manager:
            return {
                'minconn': 1,
                'maxconn': 20,
                'connect_timeout': 10
            }
        
        try:
            pool_size = self.config_manager.get('database', 'DB_CONNECTION_POOL_SIZE', 20)
            return {
                'minconn': 1,
                'maxconn': pool_size,
                'connect_timeout': 10
            }
        except:
            return {
                'minconn': 1,
                'maxconn': 20,
                'connect_timeout': 10
            }
    
    def get_market_db_config(self, market_code: str) -> Dict:
        """특정 마켓의 DB 설정 반환
        
        Args:
            market_code: 마켓 코드 (coupang, naver, 11st 등)
            
        Returns:
            마켓별 DB 설정 (없으면 기본 설정)
        """
        if not self.config_manager:
            return self.get_connection_config(use_db_config=False)
        
        # 마켓별 설정이 있는지 확인
        market_host = self.config_manager.get('database', f'{market_code.upper()}_DB_HOST')
        
        if market_host:
            return {
                'host': market_host,
                'port': int(self.config_manager.get('database', f'{market_code.upper()}_DB_PORT', self._bootstrap_config['port'])),
                'database': self.config_manager.get('database', f'{market_code.upper()}_DB_NAME', self._bootstrap_config['database']),
                'user': self.config_manager.get('database', f'{market_code.upper()}_DB_USER', self._bootstrap_config['user']),
                'password': self.config_manager.get('database', f'{market_code.upper()}_DB_PASSWORD', self._bootstrap_config['password'])
            }
        
        # 마켓별 설정이 없으면 기본 설정 사용
        return self.get_connection_config()
    
    @property
    def host(self) -> str:
        """데이터베이스 호스트"""
        return self.get_connection_config()['host']
    
    @property
    def port(self) -> int:
        """데이터베이스 포트"""
        return self.get_connection_config()['port']
    
    @property
    def database(self) -> str:
        """데이터베이스 이름"""
        return self.get_connection_config()['database']
    
    @property
    def user(self) -> str:
        """데이터베이스 사용자"""
        return self.get_connection_config()['user']
    
    @property
    def password(self) -> str:
        """데이터베이스 비밀번호"""
        return self.get_connection_config()['password']
    
    @property
    def connection_string(self) -> str:
        """PostgreSQL 연결 문자열"""
        config = self.get_connection_config()
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    def __str__(self) -> str:
        """문자열 표현"""
        config = self.get_connection_config()
        return f"DatabaseConfig(host={config['host']}, port={config['port']}, database={config['database']}, user={config['user']})"