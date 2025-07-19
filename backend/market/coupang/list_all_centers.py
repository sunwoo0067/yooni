#!/usr/bin/env python3
"""
쿠팡 계정별 모든 출고지/반품지 목록 조회
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ShippingCenters.shipping_center_client import ShippingCenterClient
from ReturnCenters.return_center_client import ReturnCenterClient


class CoupangCenterLister:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
    def get_coupang_accounts(self):
        """활성화된 쿠팡 계정 조회"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, vendor_id, access_key, secret_key, alias 
                FROM coupang 
                WHERE is_active = true
                ORDER BY id
            """)
            return cursor.fetchall()
    
    def list_all_shipping_centers(self, access_key, secret_key, vendor_id):
        """모든 출고지 목록 조회"""
        client = ShippingCenterClient(
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id
        )
        
        try:
            print("   📦 출고지 목록 조회 중...")
            result = client.get_all_shipping_places()
            
            if result.get('success'):
                all_places = result.get('shipping_places', [])
                print(f"   전체 {len(all_places)}개 출고지 발견\n")
                
                for idx, place in enumerate(all_places, 1):
                    print(f"   [{idx}] 출고지: {place.shipping_place_name}")
                    print(f"       코드: {place.outbound_shipping_place_code}")
                    print(f"       사용가능: {'✅' if place.usable else '❌'}")
                    print(f"       생성일: {place.create_date}")
                    
                    if place.place_addresses:
                        for addr in place.place_addresses:
                            print(f"       주소: {addr.return_address} {addr.return_address_detail}")
                            print(f"       우편번호: {addr.return_zip_code}")
                            print(f"       연락처: {addr.company_contact_number}")
                            if addr.phone_number2:
                                print(f"       보조연락처: {addr.phone_number2}")
                    print()
                
                return {'success': True, 'shipping_places': all_places}
            else:
                return result
                
        except Exception as e:
            print(f"   출고지 조회 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_all_return_centers(self, access_key, secret_key, vendor_id):
        """모든 반품지 목록 조회"""
        client = ReturnCenterClient(
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id
        )
        
        try:
            print("   📦 반품지 목록 조회 중...")
            all_centers = client.get_all_return_centers(vendor_id)
            
            print(f"   전체 {len(all_centers)}개 반품지 발견\n")
            
            for idx, center in enumerate(all_centers, 1):
                print(f"   [{idx}] 반품지: {center.shipping_place_name}")
                print(f"       코드: {center.return_center_code}")
                print(f"       사용가능: {'✅' if center.usable else '❌'}")
                print(f"       택배사: {center.deliver_name} ({center.deliver_code})")
                if isinstance(center.created_at, (int, float)):
                    print(f"       생성일: {datetime.fromtimestamp(center.created_at / 1000).strftime('%Y-%m-%d')}")
                else:
                    print(f"       생성일: {center.created_at}")
                
                if center.place_addresses:
                    for addr in center.place_addresses:
                        print(f"       주소: {addr.return_address} {addr.return_address_detail}")
                        print(f"       우편번호: {addr.return_zip_code}")
                        print(f"       연락처: {addr.company_contact_number}")
                        if addr.phone_number2:
                            print(f"       보조연락처: {addr.phone_number2}")
                
                # 반품비 정보 출력
                fees = []
                if center.return_fee_05kg is not None:
                    fees.append(f"5kg: {center.return_fee_05kg:,}원")
                if center.return_fee_10kg is not None:
                    fees.append(f"10kg: {center.return_fee_10kg:,}원")
                if center.return_fee_20kg is not None:
                    fees.append(f"20kg: {center.return_fee_20kg:,}원")
                if fees:
                    print(f"       반품비: {', '.join(fees)}")
                print()
            
            return {'success': True, 'return_centers': all_centers}
                
        except Exception as e:
            print(f"   반품지 조회 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_account(self, account):
        """특정 계정의 모든 센터 정보 조회"""
        print(f"\n{'='*80}")
        print(f"계정: {account['alias']} (Vendor ID: {account['vendor_id']})")
        print(f"{'='*80}")
        
        # 출고지 조회
        print("\n출고지 목록:")
        print("-" * 80)
        self.list_all_shipping_centers(
            account['access_key'],
            account['secret_key'],
            account['vendor_id']
        )
        
        # 반품지 조회
        print("\n반품지 목록:")
        print("-" * 80)
        self.list_all_return_centers(
            account['access_key'],
            account['secret_key'],
            account['vendor_id']
        )
    
    def run(self):
        """모든 계정의 센터 정보 조회"""
        print("🚀 쿠팡 전체 출고지/반품지 목록 조회")
        print(f"시작 시간: {datetime.now()}")
        
        accounts = self.get_coupang_accounts()
        print(f"\n조회할 계정 수: {len(accounts)}개")
        
        for account in accounts:
            try:
                self.process_account(account)
            except Exception as e:
                print(f"❌ {account['alias']} 계정 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*80}")
        print(f"🎉 전체 센터 정보 조회 완료!")
        print(f"완료 시간: {datetime.now()}")
        print(f"{'='*80}")
        
        self.conn.close()


if __name__ == "__main__":
    lister = CoupangCenterLister()
    lister.run()