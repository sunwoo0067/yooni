#!/usr/bin/env python3
"""
쿠팡 파트너스 API 멀티 계정 관리 도구
"""

import sys
import json
from pathlib import Path
from typing import List, Optional
from common.multi_account_config import MultiAccountConfig, CoupangAccount


class MultiAccountManager:
    """멀티 계정 관리 CLI 도구"""
    
    def __init__(self):
        self.config = MultiAccountConfig()
    
    def add_account_interactive(self):
        """대화형 계정 추가"""
        print("🔧 새 계정 추가")
        print("=" * 40)
        
        account_name = input("계정 이름: ").strip()
        if not account_name:
            print("❌ 계정 이름은 필수입니다.")
            return
        
        if account_name in self.config.accounts:
            print(f"❌ 이미 존재하는 계정: {account_name}")
            return
        
        access_key = input("액세스 키: ").strip()
        secret_key = input("시크릿 키: ").strip()
        vendor_id = input("벤더 ID: ").strip()
        description = input("설명 (선택사항): ").strip()
        
        if not all([access_key, secret_key, vendor_id]):
            print("❌ 액세스 키, 시크릿 키, 벤더 ID는 필수입니다.")
            return
        
        # 태그 입력
        tags_input = input("태그 (쉼표로 구분, 선택사항): ").strip()
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
        
        # 기본 계정 설정 여부
        set_default = input("기본 계정으로 설정하시겠습니까? (y/N): ").strip().lower() == 'y'
        
        account = CoupangAccount(
            account_name=account_name,
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id,
            description=description,
            tags=tags
        )
        
        if self.config.add_account(account, set_default):
            self.config.save_to_file()
            print("✅ 계정 추가 및 저장 완료")
        else:
            print("❌ 계정 추가 실패")
    
    def list_accounts(self):
        """계정 목록 표시"""
        accounts = self.config.list_accounts(active_only=False)
        
        if not accounts:
            print("📭 등록된 계정이 없습니다.")
            return
        
        print("📋 등록된 계정 목록")
        print("=" * 80)
        print(f"{'계정명':<15} {'벤더ID':<12} {'상태':<8} {'태그':<20} {'설명':<25}")
        print("-" * 80)
        
        for account in accounts:
            status = "🟢 활성" if account.is_active else "🔴 비활성"
            is_default = " (기본)" if account.account_name == self.config.default_account else ""
            tags_str = ", ".join(account.tags[:3])  # 처음 3개만 표시
            if len(account.tags) > 3:
                tags_str += "..."
            
            print(f"{account.account_name + is_default:<15} {account.vendor_id:<12} {status:<8} {tags_str:<20} {account.description[:25]:<25}")
        
        print("-" * 80)
        summary = self.config.get_account_summary()
        print(f"총 {summary['total_accounts']}개 계정 (활성: {summary['active_accounts']}, 비활성: {summary['inactive_accounts']})")
    
    def remove_account_interactive(self):
        """대화형 계정 제거"""
        self.list_accounts()
        
        if not self.config.accounts:
            return
        
        print("\n🗑️ 계정 제거")
        account_name = input("제거할 계정 이름: ").strip()
        
        if account_name not in self.config.accounts:
            print(f"❌ 존재하지 않는 계정: {account_name}")
            return
        
        # 확인
        confirm = input(f"정말로 '{account_name}' 계정을 제거하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 취소되었습니다.")
            return
        
        if self.config.remove_account(account_name):
            self.config.save_to_file()
            print("✅ 계정 제거 및 저장 완료")
        else:
            print("❌ 계정 제거 실패")
    
    def set_default_account_interactive(self):
        """대화형 기본 계정 설정"""
        active_accounts = self.config.list_accounts(active_only=True)
        
        if not active_accounts:
            print("❌ 활성화된 계정이 없습니다.")
            return
        
        print("🎯 기본 계정 설정")
        print("활성 계정 목록:")
        for i, account in enumerate(active_accounts, 1):
            current = " (현재 기본)" if account.account_name == self.config.default_account else ""
            print(f"  {i}. {account.account_name}{current}")
        
        try:
            choice = int(input("선택할 계정 번호: ").strip())
            if 1 <= choice <= len(active_accounts):
                selected_account = active_accounts[choice - 1]
                if self.config.set_default_account(selected_account.account_name):
                    self.config.save_to_file()
                    print("✅ 기본 계정 설정 및 저장 완료")
                else:
                    print("❌ 기본 계정 설정 실패")
            else:
                print("❌ 잘못된 번호입니다.")
        except ValueError:
            print("❌ 올바른 번호를 입력하세요.")
    
    def toggle_account_status(self):
        """계정 활성화/비활성화 토글"""
        self.list_accounts()
        
        if not self.config.accounts:
            return
        
        print("\n🔄 계정 상태 변경")
        account_name = input("상태를 변경할 계정 이름: ").strip()
        
        if account_name not in self.config.accounts:
            print(f"❌ 존재하지 않는 계정: {account_name}")
            return
        
        account = self.config.accounts[account_name]
        account.is_active = not account.is_active
        
        status = "활성화" if account.is_active else "비활성화"
        print(f"✅ '{account_name}' 계정이 {status}되었습니다.")
        
        self.config.save_to_file()
        print("✅ 변경사항 저장 완료")
    
    def test_account_connection(self):
        """계정 연결 테스트"""
        self.list_accounts()
        
        if not self.config.accounts:
            return
        
        print("\n🔍 계정 연결 테스트")
        account_name = input("테스트할 계정 이름 (전체 테스트: all): ").strip()
        
        if account_name.lower() == "all":
            # 모든 활성 계정 테스트
            from common.multi_client_factory import multi_factory
            status = multi_factory.get_account_status()
            
            print("\n📊 전체 계정 상태:")
            print("-" * 60)
            for acc_name, acc_status in status.items():
                status_icon = "✅" if acc_status.get('valid', False) else "❌"
                active_icon = "🟢" if acc_status.get('active', False) else "🔴"
                print(f"{status_icon} {acc_name} {active_icon}")
                if not acc_status.get('valid', False) and 'error' in acc_status:
                    print(f"    오류: {acc_status['error']}")
            
        else:
            # 특정 계정 테스트
            if account_name not in self.config.accounts:
                print(f"❌ 존재하지 않는 계정: {account_name}")
                return
            
            try:
                from common.multi_client_factory import multi_factory
                from cs import CSClient
                
                client = multi_factory.create_client(CSClient, account_name)
                if client:
                    print(f"✅ '{account_name}' 계정 연결 성공")
                else:
                    print(f"❌ '{account_name}' 계정 연결 실패")
                    
            except Exception as e:
                print(f"❌ '{account_name}' 계정 테스트 중 오류: {e}")
    
    def export_accounts(self):
        """계정 정보 내보내기"""
        print("📤 계정 정보 내보내기")
        
        include_secrets = input("시크릿 키를 포함하시겠습니까? (y/N): ").strip().lower() == 'y'
        file_path = input("저장할 파일 경로 (기본: accounts_export.json): ").strip()
        
        if not file_path:
            file_path = "accounts_export.json"
        
        self.config.export_accounts(file_path, include_secrets)
    
    def show_summary(self):
        """계정 요약 정보 표시"""
        summary = self.config.get_account_summary()
        
        print("📊 계정 요약 정보")
        print("=" * 40)
        print(f"총 계정 수: {summary['total_accounts']}")
        print(f"활성 계정: {summary['active_accounts']}")
        print(f"비활성 계정: {summary['inactive_accounts']}")
        print(f"기본 계정: {summary['default_account'] or 'None'}")
        
        if summary['available_tags']:
            print(f"\n사용 중인 태그:")
            for tag, count in summary['tag_counts'].items():
                print(f"  - {tag}: {count}개 계정")
    
    def run_interactive_menu(self):
        """대화형 메뉴 실행"""
        while True:
            print("\n" + "=" * 50)
            print("🏪 쿠팡 파트너스 멀티 계정 관리자")
            print("=" * 50)
            print("1. 계정 목록 보기")
            print("2. 계정 추가")
            print("3. 계정 제거")
            print("4. 기본 계정 설정")
            print("5. 계정 상태 변경 (활성화/비활성화)")
            print("6. 계정 연결 테스트")
            print("7. 계정 요약 정보")
            print("8. 계정 정보 내보내기")
            print("9. 종료")
            print("-" * 50)
            
            try:
                choice = input("선택하세요 (1-9): ").strip()
                
                if choice == "1":
                    self.list_accounts()
                elif choice == "2":
                    self.add_account_interactive()
                elif choice == "3":
                    self.remove_account_interactive()
                elif choice == "4":
                    self.set_default_account_interactive()
                elif choice == "5":
                    self.toggle_account_status()
                elif choice == "6":
                    self.test_account_connection()
                elif choice == "7":
                    self.show_summary()
                elif choice == "8":
                    self.export_accounts()
                elif choice == "9":
                    print("👋 종료합니다.")
                    break
                else:
                    print("❌ 올바른 번호를 선택하세요.")
                    
            except KeyboardInterrupt:
                print("\n👋 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    manager = MultiAccountManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            manager.list_accounts()
        elif command == "add":
            manager.add_account_interactive()
        elif command == "remove":
            manager.remove_account_interactive()
        elif command == "default":
            manager.set_default_account_interactive()
        elif command == "test":
            manager.test_account_connection()
        elif command == "summary":
            manager.show_summary()
        elif command == "export":
            manager.export_accounts()
        else:
            print(f"❌ 알 수 없는 명령: {command}")
            print("사용 가능한 명령: list, add, remove, default, test, summary, export")
    else:
        # 대화형 메뉴
        manager.run_interactive_menu()


if __name__ == "__main__":
    main()