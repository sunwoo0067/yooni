#!/usr/bin/env python3
"""
쿠팡 계정의 센터 코드 저장 상태 확인
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def verify_center_codes():
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="yoonni",
        user="postgres",
        password="1234"
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 현재 저장된 센터 코드 확인
            cursor.execute("""
                SELECT 
                    id,
                    alias,
                    vendor_id,
                    shipping_center_code,
                    return_center_code,
                    updated_at
                FROM coupang
                WHERE is_active = true
                ORDER BY id
            """)
            
            accounts = cursor.fetchall()
            
            print("📊 쿠팡 계정별 센터 코드 저장 현황")
            print("=" * 100)
            print(f"{'ID':<5} {'계정명':<15} {'Vendor ID':<12} {'출고지 코드':<15} {'반품지 코드':<15} {'업데이트 시간'}")
            print("-" * 100)
            
            for account in accounts:
                print(f"{account['id']:<5} {account['alias']:<15} {account['vendor_id']:<12} "
                      f"{account['shipping_center_code'] or 'NULL':<15} "
                      f"{account['return_center_code'] or 'NULL':<15} "
                      f"{account['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n✅ 센터 코드 상세:")
            print("-" * 50)
            for account in accounts:
                print(f"\n🏪 {account['alias']} (ID: {account['id']})")
                if account['shipping_center_code']:
                    print(f"   출고지 코드: {account['shipping_center_code']}")
                else:
                    print(f"   출고지 코드: ❌ 미설정")
                    
                if account['return_center_code']:
                    print(f"   반품지 코드: {account['return_center_code']}")
                else:
                    print(f"   반품지 코드: ❌ 미설정")
            
            # 테이블 구조 확인
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'coupang' 
                AND column_name IN ('shipping_center_code', 'return_center_code')
                ORDER BY column_name
            """)
            
            columns = cursor.fetchall()
            if columns:
                print("\n📋 테이블 컬럼 정보:")
                print("-" * 50)
                for col in columns:
                    print(f"   {col['column_name']}: {col['data_type']} (NULL 허용: {col['is_nullable']})")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_center_codes()