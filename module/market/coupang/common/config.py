#!/usr/bin/env python3
"""
쿠팡 마켓플레이스 통합 설정 관리
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """통합 설정 관리 클래스 (싱글톤)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._setup_project_path()
            Config._initialized = True
    
    def _load_environment(self):
        """환경변수 로드"""
        # 프로젝트 루트에서 .env 파일 찾기
        current_path = Path(__file__).resolve()
        project_root = None
        
        # 상위 디렉토리를 순회하며 .env 파일 찾기
        for parent in current_path.parents:
            env_file = parent / 'market' / 'coupang' / '.env'
            if env_file.exists():
                project_root = parent
                load_dotenv(env_file)
                break
        
        if project_root is None:
            # 기본 경로 시도
            default_env = Path(__file__).parent.parent / '.env'
            if default_env.exists():
                load_dotenv(default_env)
    
    def _setup_project_path(self):
        """프로젝트 경로 설정"""
        # 프로젝트 루트를 sys.path에 추가 (중복 방지)
        current_path = Path(__file__).resolve()
        project_root = current_path.parent.parent.parent.parent  # yooni_02까지
        
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
    
    @property
    def coupang_access_key(self) -> Optional[str]:
        """쿠팡 액세스 키"""
        return os.getenv('COUPANG_ACCESS_KEY')
    
    @property
    def coupang_secret_key(self) -> Optional[str]:
        """쿠팡 시크릿 키"""
        return os.getenv('COUPANG_SECRET_KEY')
    
    @property
    def coupang_vendor_id(self) -> Optional[str]:
        """쿠팡 벤더 ID"""
        return os.getenv('COUPANG_VENDOR_ID')
    
    @property
    def database_url(self) -> Optional[str]:
        """데이터베이스 URL"""
        return os.getenv('DATABASE_URL')
    
    @property
    def db_host(self) -> str:
        """데이터베이스 호스트"""
        return os.getenv('DB_HOST', 'localhost')
    
    @property
    def db_port(self) -> int:
        """데이터베이스 포트"""
        return int(os.getenv('DB_PORT', '5433'))
    
    @property
    def db_name(self) -> str:
        """데이터베이스 이름"""
        return os.getenv('DB_NAME', 'yooni_02')
    
    @property
    def db_user(self) -> str:
        """데이터베이스 사용자"""
        return os.getenv('DB_USER', 'consignai_user')
    
    @property
    def db_password(self) -> Optional[str]:
        """데이터베이스 비밀번호"""
        return os.getenv('DB_PASSWORD')
    
    def validate_coupang_credentials(self) -> bool:
        """쿠팡 API 인증 정보 유효성 검사"""
        return all([
            self.coupang_access_key,
            self.coupang_secret_key,
            self.coupang_vendor_id
        ])
    
    def get_env_or_default(self, key: str, default: str, description: str = "") -> str:
        """환경변수 조회 (기본값 포함)"""
        value = os.getenv(key, default)
        if value == default and description:
            print(f"⚠️  {key} 환경변수가 설정되지 않아 기본값 사용: {default} ({description})")
        return value


# 전역 설정 인스턴스
config = Config()