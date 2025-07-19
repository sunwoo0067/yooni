#!/usr/bin/env python3
"""
쿠팡 출고지/반품지 센터 정보 조회 및 저장
승인된 센터 코드를 계정에 저장
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

sys.path.append('/home/sunwoo/yooni/module/market/coupang')
from ShippingCenters.shipping_center_client import ShippingCenterClient
from ReturnCenters.return_center_client import ReturnCenterClient


class CoupangCenterFetcher:
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
    
    def fetch_shipping_centers(self, access_key, secret_key, vendor_id):
        """출고지 목록 조회"""
        client = ShippingCenterClient(
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id
        )
        
        try:
            # 활성화된 출고지만 조회
            result = client.get_active_shipping_places()
            return result
        except Exception as e:
            print(f"출고지 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_return_centers(self, access_key, secret_key, vendor_id):
        """반품지 목록 조회"""
        client = ReturnCenterClient(
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id
        )
        
        try:
            # 전체 반품지 조회
            result = client.get_all_return_centers(vendor_id)
            return result
        except Exception as e:
            print(f"반품지 조회 오류: {e}")
            return None
    
    def update_account_centers(self, account_id, shipping_center_code, return_center_code):
        """계정에 출고지/반품지 코드 업데이트"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE coupang 
                    SET shipping_center_code = %s,
                        return_center_code = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (shipping_center_code, return_center_code, account_id))
                
                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"업데이트 오류: {e}")
            return False
    
    def process_account(self, account):
        """특정 계정의 센터 정보 처리"""
        print(f"\n{'='*60}")
        print(f"계정: {account['alias']} (Vendor ID: {account['vendor_id']}) 센터 정보 조회")
        print(f"{'='*60}")
        
        # 출고지 조회
        print("\n📦 출고지 센터 조회 중...")
        shipping_response = self.fetch_shipping_centers(
            account['access_key'],
            account['secret_key'],
            account['vendor_id']
        )
        
        shipping_center_code = None
        if shipping_response and shipping_response.get('success'):
            shipping_centers = shipping_response.get('shipping_places', [])
            print(f"   총 {len(shipping_centers)}개 활성 출고지 발견")
            
            # 첫 번째 활성 출고지 선택
            if shipping_centers:
                center = shipping_centers[0]
                shipping_center_code = str(center.outbound_shipping_place_code)
                print(f"   ✅ 승인된 출고지: {center.shipping_place_name} (코드: {shipping_center_code})")
                if center.place_addresses:
                    addr = center.place_addresses[0]
                    print(f"      주소: {addr.return_address} {addr.return_address_detail}")
                    print(f"      연락처: {addr.company_contact_number}")
        else:
            print("   ❌ 출고지 조회 실패")
        
        # 반품지 조회
        print("\n📦 반품지 센터 조회 중...")
        return_response = self.fetch_return_centers(
            account['access_key'],
            account['secret_key'],
            account['vendor_id']
        )
        
        return_center_code = None
        if return_response and return_response.get('success'):
            return_centers = return_response.get('return_centers', [])
            print(f"   총 {len(return_centers)}개 반품지 발견")
            
            # 사용 가능한 반품지 찾기
            usable_centers = [c for c in return_centers if c.usable]
            
            if usable_centers:
                # 첫 번째 사용 가능한 반품지 선택
                center = usable_centers[0]
                return_center_code = center.return_center_code
                print(f"   ✅ 승인된 반품지: {center.shipping_place_name} (코드: {return_center_code})")
                if center.place_addresses:
                    addr = center.place_addresses[0]
                    print(f"      주소: {addr.return_address} {addr.return_address_detail}")
                    print(f"      연락처: {addr.company_contact_number}")
                print(f"      택배사: {center.deliver_name} ({center.deliver_code})")
        else:
            print("   ❌ 반품지 조회 실패")
        
        # 계정 정보 업데이트
        if shipping_center_code or return_center_code:
            print(f"\n💾 계정 정보 업데이트 중...")
            if self.update_account_centers(account['id'], shipping_center_code, return_center_code):
                print(f"   ✅ 업데이트 완료")
                print(f"      출고지 코드: {shipping_center_code or 'N/A'}")
                print(f"      반품지 코드: {return_center_code or 'N/A'}")
            else:
                print(f"   ❌ 업데이트 실패")
        else:
            print(f"\n⚠️  승인된 센터 정보가 없습니다.")
        
        return shipping_center_code, return_center_code
    
    def run(self):
        """모든 계정의 센터 정보 조회 및 저장"""
        print("🚀 쿠팡 출고지/반품지 센터 정보 조회 시작")
        print(f"시작 시간: {datetime.now()}")
        
        accounts = self.get_coupang_accounts()
        print(f"\n조회할 계정 수: {len(accounts)}개")
        
        success_count = 0
        
        for account in accounts:
            try:
                shipping_code, return_code = self.process_account(account)
                if shipping_code or return_code:
                    success_count += 1
            except Exception as e:
                print(f"❌ {account['alias']} 계정 처리 중 오류: {e}")
        
        print(f"\n{'='*60}")
        print(f"🎉 센터 정보 조회 완료!")
        print(f"   성공: {success_count}/{len(accounts)} 계정")
        print(f"   완료 시간: {datetime.now()}")
        print(f"{'='*60}")
        
        # 최종 결과 출력
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    alias,
                    vendor_id,
                    shipping_center_code,
                    return_center_code
                FROM coupang
                WHERE is_active = true
                ORDER BY id
            """)
            
            print("\n📊 계정별 센터 정보:")
            print(f"{'계정명':<15} {'Vendor ID':<12} {'출고지 코드':<15} {'반품지 코드':<15}")
            print("-" * 60)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<15} {row[1]:<12} {row[2] or 'N/A':<15} {row[3] or 'N/A':<15}")
        
        self.conn.close()


if __name__ == "__main__":
    fetcher = CoupangCenterFetcher()
    fetcher.run()