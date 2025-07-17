#!/usr/bin/env python3
"""
쿠팡 파트너스 API 멀티 계정 설정 관리
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv


@dataclass
class CoupangAccount:
    """쿠팡 계정 정보"""
    account_name: str                 # 계정 별칭 (예: "main", "sub1", "fashion_store")
    access_key: str                   # 액세스 키
    secret_key: str                   # 시크릿 키
    vendor_id: str                    # 벤더 ID
    description: str = ""             # 계정 설명
    is_active: bool = True            # 활성화 여부
    tags: List[str] = None            # 태그 (카테고리 분류용)
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def validate(self) -> bool:
        """계정 정보 유효성 검증"""
        return all([
            self.account_name.strip(),
            self.access_key.strip(),
            self.secret_key.strip(),
            self.vendor_id.strip()
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoupangAccount':
        """딕셔너리에서 생성"""
        return cls(**data)


class MultiAccountConfig:
    """멀티 계정 설정 관리 클래스"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        멀티 계정 설정 초기화
        
        Args:
            config_file: 설정 파일 경로 (None이면 기본 경로 사용)
        """
        self.config_file = self._get_config_file_path(config_file)
        self.accounts: Dict[str, CoupangAccount] = {}
        self.default_account: Optional[str] = None
        
        # 설정 로드
        self._load_from_file()
        self._load_from_env()
    
    def _get_config_file_path(self, config_file: Optional[str]) -> Path:
        """설정 파일 경로 결정"""
        if config_file:
            return Path(config_file)
        
        # 기본 경로: market/coupang/accounts.json
        current_path = Path(__file__).resolve()
        default_path = current_path.parent.parent / 'accounts.json'
        return default_path
    
    def _load_from_file(self):
        """파일에서 계정 설정 로드"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 계정 정보 로드
            for account_data in data.get('accounts', []):
                account = CoupangAccount.from_dict(account_data)
                if account.validate():
                    self.accounts[account.account_name] = account
            
            # 기본 계정 설정
            self.default_account = data.get('default_account')
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️ 계정 설정 파일 로드 실패: {e}")
    
    def _load_from_env(self):
        """환경변수에서 기본 계정 로드"""
        # 기존 환경변수 방식 지원 (하위 호환성)
        access_key = os.getenv('COUPANG_ACCESS_KEY')
        secret_key = os.getenv('COUPANG_SECRET_KEY')
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if all([access_key, secret_key, vendor_id]):
            default_account = CoupangAccount(
                account_name="default",
                access_key=access_key,
                secret_key=secret_key,
                vendor_id=vendor_id,
                description="환경변수에서 로드된 기본 계정",
                tags=["default", "env"]
            )
            
            self.accounts["default"] = default_account
            if not self.default_account:
                self.default_account = "default"
    
    def save_to_file(self):
        """설정을 파일에 저장"""
        # 디렉토리 생성
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'default_account': self.default_account,
            'accounts': [account.to_dict() for account in self.accounts.values()]
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ 계정 설정 저장 완료: {self.config_file}")
        except Exception as e:
            print(f"❌ 계정 설정 저장 실패: {e}")
    
    def add_account(self, account: CoupangAccount, set_as_default: bool = False) -> bool:
        """
        계정 추가
        
        Args:
            account: 추가할 계정 정보
            set_as_default: 기본 계정으로 설정 여부
            
        Returns:
            bool: 성공 여부
        """
        if not account.validate():
            print(f"❌ 유효하지 않은 계정 정보: {account.account_name}")
            return False
        
        if account.account_name in self.accounts:
            print(f"⚠️ 이미 존재하는 계정: {account.account_name}")
            return False
        
        self.accounts[account.account_name] = account
        
        # 첫 번째 계정이면 기본 계정으로 설정
        if not self.default_account or set_as_default:
            self.default_account = account.account_name
        
        print(f"✅ 계정 추가 완료: {account.account_name}")
        return True
    
    def remove_account(self, account_name: str) -> bool:
        """
        계정 제거
        
        Args:
            account_name: 제거할 계정 이름
            
        Returns:
            bool: 성공 여부
        """
        if account_name not in self.accounts:
            print(f"❌ 존재하지 않는 계정: {account_name}")
            return False
        
        del self.accounts[account_name]
        
        # 기본 계정이 제거된 경우 다른 계정으로 변경
        if self.default_account == account_name:
            if self.accounts:
                self.default_account = list(self.accounts.keys())[0]
                print(f"🔄 기본 계정 변경: {self.default_account}")
            else:
                self.default_account = None
        
        print(f"✅ 계정 제거 완료: {account_name}")
        return True
    
    def get_account(self, account_name: Optional[str] = None) -> Optional[CoupangAccount]:
        """
        계정 정보 조회
        
        Args:
            account_name: 계정 이름 (None이면 기본 계정)
            
        Returns:
            CoupangAccount: 계정 정보 (없으면 None)
        """
        if account_name is None:
            account_name = self.default_account
        
        if account_name is None:
            return None
        
        return self.accounts.get(account_name)
    
    def set_default_account(self, account_name: str) -> bool:
        """
        기본 계정 설정
        
        Args:
            account_name: 기본으로 설정할 계정 이름
            
        Returns:
            bool: 성공 여부
        """
        if account_name not in self.accounts:
            print(f"❌ 존재하지 않는 계정: {account_name}")
            return False
        
        self.default_account = account_name
        print(f"✅ 기본 계정 설정: {account_name}")
        return True
    
    def list_accounts(self, active_only: bool = True) -> List[CoupangAccount]:
        """
        계정 목록 조회
        
        Args:
            active_only: 활성 계정만 조회 여부
            
        Returns:
            List[CoupangAccount]: 계정 목록
        """
        accounts = list(self.accounts.values())
        if active_only:
            accounts = [acc for acc in accounts if acc.is_active]
        return accounts
    
    def get_accounts_by_tag(self, tag: str) -> List[CoupangAccount]:
        """
        태그로 계정 필터링
        
        Args:
            tag: 필터링할 태그
            
        Returns:
            List[CoupangAccount]: 태그가 일치하는 계정 목록
        """
        return [
            account for account in self.accounts.values()
            if tag in account.tags and account.is_active
        ]
    
    def validate_account(self, account_name: str) -> bool:
        """
        계정 유효성 검증
        
        Args:
            account_name: 검증할 계정 이름
            
        Returns:
            bool: 유효한 계정인지 여부
        """
        account = self.get_account(account_name)
        return account is not None and account.validate()
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        계정 요약 정보
        
        Returns:
            Dict: 계정 요약 정보
        """
        active_accounts = [acc for acc in self.accounts.values() if acc.is_active]
        inactive_accounts = [acc for acc in self.accounts.values() if not acc.is_active]
        
        # 태그별 분류
        all_tags = set()
        for account in self.accounts.values():
            all_tags.update(account.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = len(self.get_accounts_by_tag(tag))
        
        return {
            'total_accounts': len(self.accounts),
            'active_accounts': len(active_accounts),
            'inactive_accounts': len(inactive_accounts),
            'default_account': self.default_account,
            'available_tags': list(all_tags),
            'tag_counts': tag_counts,
            'account_names': list(self.accounts.keys())
        }
    
    def export_accounts(self, file_path: str, include_secrets: bool = False):
        """
        계정 정보 내보내기
        
        Args:
            file_path: 내보낼 파일 경로
            include_secrets: 시크릿 키 포함 여부
        """
        export_data = []
        
        for account in self.accounts.values():
            account_data = account.to_dict()
            if not include_secrets:
                # 보안 정보 마스킹
                account_data['access_key'] = account_data['access_key'][:8] + '...'
                account_data['secret_key'] = '***masked***'
            
            export_data.append(account_data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_timestamp': os.path.getmtime(__file__),
                    'accounts': export_data
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ 계정 정보 내보내기 완료: {file_path}")
        except Exception as e:
            print(f"❌ 계정 정보 내보내기 실패: {e}")
    
    def __str__(self) -> str:
        """문자열 표현"""
        summary = self.get_account_summary()
        return (
            f"MultiAccountConfig("
            f"accounts={summary['total_accounts']}, "
            f"active={summary['active_accounts']}, "
            f"default='{summary['default_account']}')"
        )


# 전역 멀티 계정 설정 인스턴스
multi_config = MultiAccountConfig()


# 편의 함수들
def get_account(account_name: Optional[str] = None) -> Optional[CoupangAccount]:
    """계정 정보 조회 편의 함수"""
    return multi_config.get_account(account_name)


def list_account_names() -> List[str]:
    """계정 이름 목록 조회"""
    return list(multi_config.accounts.keys())


def get_default_account_name() -> Optional[str]:
    """기본 계정 이름 조회"""
    return multi_config.default_account


def validate_account_exists(account_name: str) -> bool:
    """계정 존재 여부 확인"""
    return account_name in multi_config.accounts


def get_active_account_names() -> List[str]:
    """활성 계정 이름 목록"""
    return [
        acc.account_name for acc in multi_config.list_accounts(active_only=True)
    ]