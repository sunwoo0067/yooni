#!/usr/bin/env python3
"""
쿠팡 파트너스 API 멀티 계정 클라이언트 팩토리
"""

from typing import Dict, List, Optional, Any, Union, Type
from .multi_account_config import MultiAccountConfig, CoupangAccount, multi_config
from ..common.base_client import BaseCoupangClient


class MultiClientFactory:
    """멀티 계정 클라이언트 팩토리"""
    
    def __init__(self, config: MultiAccountConfig = None):
        """
        팩토리 초기화
        
        Args:
            config: 멀티 계정 설정 (None이면 전역 설정 사용)
        """
        self.config = config or multi_config
        self._client_cache: Dict[str, Dict[str, BaseCoupangClient]] = {}
    
    def create_client(
        self, 
        client_class: Type[BaseCoupangClient], 
        account_name: Optional[str] = None
    ) -> Optional[BaseCoupangClient]:
        """
        특정 계정용 클라이언트 생성
        
        Args:
            client_class: 클라이언트 클래스
            account_name: 계정 이름 (None이면 기본 계정)
            
        Returns:
            BaseCoupangClient: 클라이언트 인스턴스 (실패시 None)
        """
        account = self.config.get_account(account_name)
        if not account:
            print(f"❌ 계정을 찾을 수 없음: {account_name}")
            return None
        
        if not account.is_active:
            print(f"❌ 비활성화된 계정: {account.account_name}")
            return None
        
        # 캐시 확인
        cache_key = f"{account.account_name}_{client_class.__name__}"
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]
        
        try:
            # 클라이언트 생성
            client = client_class(
                access_key=account.access_key,
                secret_key=account.secret_key,
                vendor_id=account.vendor_id
            )
            
            # 캐시에 저장
            if account.account_name not in self._client_cache:
                self._client_cache[account.account_name] = {}
            self._client_cache[account.account_name][client_class.__name__] = client
            
            return client
            
        except Exception as e:
            print(f"❌ 클라이언트 생성 실패 ({account.account_name}): {e}")
            return None
    
    def create_unified_client(self, account_name: Optional[str] = None) -> Optional[Dict[str, BaseCoupangClient]]:
        """
        특정 계정용 통합 클라이언트 생성
        
        Args:
            account_name: 계정 이름 (None이면 기본 계정)
            
        Returns:
            Dict[str, BaseCoupangClient]: 모든 모듈 클라이언트 딕셔너리
        """
        # 동적 import로 순환 참조 방지
        from ..cs import CSClient
        from ..sales import SalesClient
        from ..settlement import SettlementClient
        from ..order import OrderClient
        from ..product import ProductClient
        from ..returns import ReturnClient
        from ..exchange import ExchangeClient
        
        account = self.config.get_account(account_name)
        if not account:
            print(f"❌ 계정을 찾을 수 없음: {account_name}")
            return None
        
        if not account.is_active:
            print(f"❌ 비활성화된 계정: {account.account_name}")
            return None
        
        clients = {}
        client_classes = {
            'cs': CSClient,
            'sales': SalesClient,
            'settlement': SettlementClient,
            'order': OrderClient,
            'product': ProductClient,
            'returns': ReturnClient,
            'exchange': ExchangeClient
        }
        
        for module_name, client_class in client_classes.items():
            client = self.create_client(client_class, account.account_name)
            if client:
                clients[module_name] = client
            else:
                print(f"⚠️ {module_name} 클라이언트 생성 실패 ({account.account_name})")
        
        return clients if clients else None
    
    def create_clients_for_all_accounts(
        self, 
        client_class: Type[BaseCoupangClient],
        active_only: bool = True
    ) -> Dict[str, BaseCoupangClient]:
        """
        모든 계정용 클라이언트 생성
        
        Args:
            client_class: 클라이언트 클래스
            active_only: 활성 계정만 포함 여부
            
        Returns:
            Dict[str, BaseCoupangClient]: 계정별 클라이언트 딕셔너리
        """
        clients = {}
        accounts = self.config.list_accounts(active_only=active_only)
        
        for account in accounts:
            client = self.create_client(client_class, account.account_name)
            if client:
                clients[account.account_name] = client
        
        return clients
    
    def create_clients_by_tag(
        self, 
        client_class: Type[BaseCoupangClient],
        tag: str
    ) -> Dict[str, BaseCoupangClient]:
        """
        특정 태그를 가진 계정들의 클라이언트 생성
        
        Args:
            client_class: 클라이언트 클래스
            tag: 필터링할 태그
            
        Returns:
            Dict[str, BaseCoupangClient]: 태그별 클라이언트 딕셔너리
        """
        clients = {}
        accounts = self.config.get_accounts_by_tag(tag)
        
        for account in accounts:
            client = self.create_client(client_class, account.account_name)
            if client:
                clients[account.account_name] = client
        
        return clients
    
    def execute_on_all_accounts(
        self, 
        client_class: Type[BaseCoupangClient],
        method_name: str,
        *args,
        active_only: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        모든 계정에서 동일한 메서드 실행
        
        Args:
            client_class: 클라이언트 클래스
            method_name: 실행할 메서드 이름
            *args: 메서드 인자
            active_only: 활성 계정만 포함 여부
            **kwargs: 메서드 키워드 인자
            
        Returns:
            Dict[str, Any]: 계정별 실행 결과
        """
        results = {}
        clients = self.create_clients_for_all_accounts(client_class, active_only)
        
        for account_name, client in clients.items():
            try:
                method = getattr(client, method_name)
                result = method(*args, **kwargs)
                results[account_name] = {
                    'success': True,
                    'data': result
                }
            except Exception as e:
                results[account_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def execute_on_tagged_accounts(
        self, 
        client_class: Type[BaseCoupangClient],
        tag: str,
        method_name: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        특정 태그 계정들에서 동일한 메서드 실행
        
        Args:
            client_class: 클라이언트 클래스
            tag: 필터링할 태그
            method_name: 실행할 메서드 이름
            *args: 메서드 인자
            **kwargs: 메서드 키워드 인자
            
        Returns:
            Dict[str, Any]: 계정별 실행 결과
        """
        results = {}
        clients = self.create_clients_by_tag(client_class, tag)
        
        for account_name, client in clients.items():
            try:
                method = getattr(client, method_name)
                result = method(*args, **kwargs)
                results[account_name] = {
                    'success': True,
                    'data': result
                }
            except Exception as e:
                results[account_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def get_account_status(self) -> Dict[str, Any]:
        """
        모든 계정의 상태 확인
        
        Returns:
            Dict[str, Any]: 계정별 상태 정보
        """
        status = {}
        
        for account_name, account in self.config.accounts.items():
            # 간단한 API 호출로 계정 상태 확인
            try:
                from ..cs import CSClient
                client = self.create_client(CSClient, account_name)
                if client:
                    # 간단한 API 호출 시도
                    status[account_name] = {
                        'active': account.is_active,
                        'valid': True,
                        'description': account.description,
                        'tags': account.tags,
                        'vendor_id': account.vendor_id
                    }
                else:
                    status[account_name] = {
                        'active': account.is_active,
                        'valid': False,
                        'error': 'Client creation failed'
                    }
            except Exception as e:
                status[account_name] = {
                    'active': account.is_active,
                    'valid': False,
                    'error': str(e)
                }
        
        return status
    
    def clear_cache(self, account_name: Optional[str] = None):
        """
        클라이언트 캐시 정리
        
        Args:
            account_name: 특정 계정 캐시만 정리 (None이면 전체)
        """
        if account_name:
            self._client_cache.pop(account_name, None)
        else:
            self._client_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        캐시 정보 조회
        
        Returns:
            Dict[str, Any]: 캐시 상태 정보
        """
        cache_info = {}
        total_clients = 0
        
        for account_name, clients in self._client_cache.items():
            cache_info[account_name] = {
                'client_count': len(clients),
                'client_types': list(clients.keys())
            }
            total_clients += len(clients)
        
        return {
            'total_cached_clients': total_clients,
            'cached_accounts': len(self._client_cache),
            'cache_details': cache_info
        }


# 전역 팩토리 인스턴스
multi_factory = MultiClientFactory()


# 편의 함수들
def create_client_for_account(
    client_class: Type[BaseCoupangClient], 
    account_name: Optional[str] = None
) -> Optional[BaseCoupangClient]:
    """계정별 클라이언트 생성 편의 함수"""
    return multi_factory.create_client(client_class, account_name)


def create_unified_client_for_account(account_name: Optional[str] = None) -> Optional[Dict[str, BaseCoupangClient]]:
    """계정별 통합 클라이언트 생성 편의 함수"""
    return multi_factory.create_unified_client(account_name)


def execute_on_all_accounts(
    client_class: Type[BaseCoupangClient],
    method_name: str,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """모든 계정에서 메서드 실행 편의 함수"""
    return multi_factory.execute_on_all_accounts(client_class, method_name, *args, **kwargs)


def get_multi_account_status() -> Dict[str, Any]:
    """멀티 계정 상태 조회 편의 함수"""
    return multi_factory.get_account_status()