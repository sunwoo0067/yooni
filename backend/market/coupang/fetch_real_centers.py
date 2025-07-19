#!/usr/bin/env python3
"""
쿠팡 실제 출고지/반품지 센터 정보 조회 및 저장
ShippingCenters와 ReturnCenters 모듈 사용
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


class CoupangRealCenterFetcher:
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
            # 전체 출고지 조회
            print("   전체 출고지 조회 중...")
            result = client.get_all_shipping_places()
            
            if result.get('success'):
                all_places = result.get('shipping_places', [])
                print(f"   전체 {len(all_places)}개 출고지 발견")
                
                # 활성화된 출고지만 필터링
                active_places = [p for p in all_places if p.usable]
                print(f"   활성화된 출고지: {len(active_places)}개")
                
                return {'success': True, 'shipping_places': active_places}
            else:
                return result
                
        except Exception as e:
            print(f"   출고지 조회 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_return_centers(self, access_key, secret_key, vendor_id):
        """반품지 목록 조회"""
        client = ReturnCenterClient(
            access_key=access_key,
            secret_key=secret_key,
            vendor_id=vendor_id
        )
        
        try:
            # 전체 반품지 조회
            print("   전체 반품지 조회 중...")
            all_centers = client.get_all_return_centers(vendor_id)
            
            print(f"   전체 {len(all_centers)}개 반품지 발견")
            
            # 사용 가능한 반품지만 필터링
            usable_centers = [c for c in all_centers if c.usable]
            print(f"   사용 가능한 반품지: {len(usable_centers)}개")
            
            return {'success': True, 'return_centers': usable_centers}
                
        except Exception as e:
            print(f"   반품지 조회 오류: {e}")
            return {'success': False, 'error': str(e)}
    
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
        if shipping_response.get('success'):
            shipping_places = shipping_response.get('shipping_places', [])
            
            if shipping_places:
                # 첫 번째 활성 출고지 선택
                center = shipping_places[0]
                shipping_center_code = str(center.outbound_shipping_place_code)
                print(f"\n   ✅ 선택된 출고지:")
                print(f"      이름: {center.shipping_place_name}")
                print(f"      코드: {shipping_center_code}")
                print(f"      생성일: {center.create_date}")
                
                if center.place_addresses:
                    addr = center.place_addresses[0]
                    print(f"      주소: {addr.return_address} {addr.return_address_detail}")
                    print(f"      우편번호: {addr.return_zip_code}")
                    print(f"      연락처: {addr.company_contact_number}")
                    if addr.phone_number2:
                        print(f"      보조연락처: {addr.phone_number2}")
                
                # 배송비 정보 출력
                if center.remote_infos:
                    print(f"\n      도서산간 배송비 정보:")
                    for remote in center.remote_infos:
                        if remote.usable:
                            print(f"      - {remote.delivery_code}: 제주 {remote.jeju:,}원, 제주외 {remote.not_jeju:,}원")
            else:
                print("   ⚠️  활성화된 출고지가 없습니다.")
        else:
            print(f"   ❌ 출고지 조회 실패: {shipping_response.get('error', '알 수 없는 오류')}")
        
        # 반품지 조회
        print("\n📦 반품지 센터 조회 중...")
        return_response = self.fetch_return_centers(
            account['access_key'],
            account['secret_key'],
            account['vendor_id']
        )
        
        return_center_code = None
        if return_response.get('success'):
            return_centers = return_response.get('return_centers', [])
            
            if return_centers:
                # 첫 번째 사용 가능한 반품지 선택
                center = return_centers[0]
                return_center_code = center.return_center_code
                print(f"\n   ✅ 선택된 반품지:")
                print(f"      이름: {center.shipping_place_name}")
                print(f"      코드: {return_center_code}")
                print(f"      택배사: {center.deliver_name} ({center.deliver_code})")
                if isinstance(center.created_at, (int, float)):
                    print(f"      생성일: {datetime.fromtimestamp(center.created_at / 1000).strftime('%Y-%m-%d')}")
                else:
                    print(f"      생성일: {center.created_at}")
                
                if center.place_addresses:
                    addr = center.place_addresses[0]
                    print(f"      주소: {addr.return_address} {addr.return_address_detail}")
                    print(f"      우편번호: {addr.return_zip_code}")
                    print(f"      연락처: {addr.company_contact_number}")
                    if addr.phone_number2:
                        print(f"      보조연락처: {addr.phone_number2}")
                
                # 반품비 정보 출력
                print(f"\n      반품비 정보:")
                if center.return_fee_05kg is not None:
                    print(f"      - 5kg: {center.return_fee_05kg:,}원")
                if center.return_fee_10kg is not None:
                    print(f"      - 10kg: {center.return_fee_10kg:,}원")
                if center.return_fee_20kg is not None:
                    print(f"      - 20kg: {center.return_fee_20kg:,}원")
            else:
                print("   ⚠️  사용 가능한 반품지가 없습니다.")
        else:
            print(f"   ❌ 반품지 조회 실패: {return_response.get('error', '알 수 없는 오류')}")
        
        # 계정 정보 업데이트
        if shipping_center_code or return_center_code:
            print(f"\n💾 계정 정보 업데이트 중...")
            if self.update_account_centers(account['id'], shipping_center_code, return_center_code):
                print(f"   ✅ 업데이트 완료")
                print(f"      출고지 코드: {shipping_center_code or '변경없음'}")
                print(f"      반품지 코드: {return_center_code or '변경없음'}")
            else:
                print(f"   ❌ 업데이트 실패")
        else:
            print(f"\n⚠️  승인된 센터 정보가 없습니다.")
        
        return shipping_center_code, return_center_code
    
    def run(self):
        """모든 계정의 센터 정보 조회 및 저장"""
        print("🚀 쿠팡 실제 출고지/반품지 센터 정보 조회 시작")
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
                import traceback
                traceback.print_exc()
        
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
            print(f"{'계정명':<15} {'Vendor ID':<12} {'출고지 코드':<20} {'반품지 코드':<20}")
            print("-" * 70)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<15} {row[1]:<12} {row[2] or 'N/A':<20} {row[3] or 'N/A':<20}")
        
        self.conn.close()


if __name__ == "__main__":
    fetcher = CoupangRealCenterFetcher()
    fetcher.run()