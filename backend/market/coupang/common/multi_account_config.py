#!/usr/bin/env python3
"""
쿠팡 파트너스 API 멀티 계정 설정 관리 (DB 기반)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class CoupangAccount:
    """쿠팡 계정 정보"""
    id: int                           # DB ID
    account_name: str                 # 계정 별칭 (alias)
    access_key: str                   # 액세스 키
    secret_key: str                   # 시크릿 키
    vendor_id: str                    # 벤더 ID
    market_id: Optional[int] = None   # 마켓 ID
    is_active: bool = True            # 활성화 여부
    
    def validate(self) -> bool:
        """계정 정보 유효성 검증"""
        return all([
            self.access_key.strip(),
            self.secret_key.strip(),
            self.vendor_id.strip()
        ])


class MultiAccountConfig:
    """멀티 계정 설정 관리 클래스 (DB 기반)"""
    
    def __init__(self):
        """
        멀티 계정 설정 초기화
        """
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        self.accounts: Dict[str, CoupangAccount] = {}
        self.default_account: Optional[str] = None
        
        # DB에서 계정 로드
        self._load_from_db()
    
    def _load_from_db(self):
        """DB에서 계정 설정 로드"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, alias as account_name, vendor_id, access_key, 
                           secret_key, market_id, is_active
                    FROM coupang
                    WHERE is_active = true
                """)
                
                for row in cursor.fetchall():
                    account = CoupangAccount(
                        id=row['id'],
                        account_name=row['account_name'],
                        vendor_id=row['vendor_id'],
                        access_key=row['access_key'],
                        secret_key=row['secret_key'],
                        market_id=row['market_id'],
                        is_active=row['is_active']
                    )
                    self.accounts[account.account_name] = account
                    
                    # 첫 번째 활성 계정을 기본으로
                    if not self.default_account:
                        self.default_account = account.account_name
                        
        except Exception as e:
            print(f"❌ DB에서 계정 로드 실패: {e}")
    
    def save_to_db(self):
        """변경사항을 DB에 저장"""
        try:
            self.conn.commit()
            print("✅ 계정 설정 DB 저장 완료")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 계정 설정 DB 저장 실패: {e}")
    
    def add_account(self, alias: str, vendor_id: str, access_key: str, 
                   secret_key: str, market_id: int = 1) -> bool:
        """
        계정 추가
        
        Args:
            alias: 계정 별칭
            vendor_id: 벤더 ID
            access_key: 액세스 키
            secret_key: 시크릿 키
            market_id: 마켓 ID
            
        Returns:
            bool: 성공 여부
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO coupang (market_id, alias, vendor_id, access_key, secret_key)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (market_id, alias, vendor_id, access_key, secret_key))
                
                new_id = cursor.fetchone()[0]
                self.conn.commit()
                
                # 새 계정을 메모리에 추가
                account = CoupangAccount(
                    id=new_id,
                    account_name=alias,
                    vendor_id=vendor_id,
                    access_key=access_key,
                    secret_key=secret_key,
                    market_id=market_id
                )
                self.accounts[alias] = account
                
                print(f"✅ 계정 추가 완료: {alias}")
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 계정 추가 실패: {e}")
            return False
    
    def remove_account(self, account_name: str) -> bool:
        """
        계정 제거 (비활성화)
        
        Args:
            account_name: 제거할 계정 이름
            
        Returns:
            bool: 성공 여부
        """
        if account_name not in self.accounts:
            print(f"❌ 존재하지 않는 계정: {account_name}")
            return False
            
        try:
            account = self.accounts[account_name]
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE coupang SET is_active = false
                    WHERE id = %s
                """, (account.id,))
                
                self.conn.commit()
                
                # 메모리에서 제거
                del self.accounts[account_name]
                
                # 기본 계정이 제거된 경우 다른 계정으로 변경
                if self.default_account == account_name:
                    if self.accounts:
                        self.default_account = list(self.accounts.keys())[0]
                        print(f"🔄 기본 계정 변경: {self.default_account}")
                    else:
                        self.default_account = None
                
                print(f"✅ 계정 비활성화 완료: {account_name}")
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 계정 제거 실패: {e}")
            return False
    
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
    
    def toggle_account_status(self, account_name: str) -> bool:
        """
        계정 활성화/비활성화 토글
        
        Args:
            account_name: 계정 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            if account_name in self.accounts:
                account = self.accounts[account_name]
                new_status = not account.is_active
            else:
                # DB에서 비활성 계정도 확인
                with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, is_active FROM coupang
                        WHERE alias = %s
                    """, (account_name,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"❌ 존재하지 않는 계정: {account_name}")
                        return False
                    new_status = not result['is_active']
                    account_id = result['id']
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE coupang SET is_active = %s
                    WHERE alias = %s
                """, (new_status, account_name))
                
                self.conn.commit()
                
                # 메모리 상태 업데이트
                self._load_from_db()
                
                status = "활성화" if new_status else "비활성화"
                print(f"✅ '{account_name}' 계정이 {status}되었습니다.")
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 계정 상태 변경 실패: {e}")
            return False
    
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
        try:
            with self.conn.cursor() as cursor:
                # 전체 계정 수
                cursor.execute("SELECT COUNT(*) FROM coupang")
                total = cursor.fetchone()[0]
                
                # 활성 계정 수
                cursor.execute("SELECT COUNT(*) FROM coupang WHERE is_active = true")
                active = cursor.fetchone()[0]
                
                # 비활성 계정 수
                inactive = total - active
                
                return {
                    'total_accounts': total,
                    'active_accounts': active,
                    'inactive_accounts': inactive,
                    'default_account': self.default_account,
                    'account_names': list(self.accounts.keys())
                }
        except Exception as e:
            print(f"❌ 계정 요약 정보 조회 실패: {e}")
            return {}
    
    def __del__(self):
        """소멸자: DB 연결 종료"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
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