#!/usr/bin/env python3
"""
두 쿠팡 계정의 출고지/반품지를 송내(부일로) 주소로 변경
"""

import psycopg2
from datetime import datetime

def update_centers_to_songnae():
    """두 계정을 송내 센터로 업데이트"""
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="yoonni",
        user="postgres",
        password="1234"
    )
    
    try:
        with conn.cursor() as cursor:
            # 쿠팡계정1 - 이미 송내 사용중 (출고지: 22863192, 반품지: 1002179121)
            print("📦 쿠팡계정1 업데이트")
            print("   이미 송내 출고지/반품지 사용 중")
            print("   출고지: 22863192 (송내)")
            print("   반품지: 1002179121 (송내반품)")
            
            # b00679540 - 송내로 변경 (출고지: 22681849, 반품지: 1002151032)
            print("\n📦 b00679540 계정 업데이트")
            cursor.execute("""
                UPDATE coupang 
                SET shipping_center_code = %s,
                    return_center_code = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE vendor_id = %s
            """, ('22681849', '1002151032', 'A01282691'))
            
            print("   출고지: 22681849 (송내 출고)로 변경")
            print("   반품지: 1002151032 (송내 반품)로 변경")
            
            conn.commit()
            
            # 최종 결과 확인
            cursor.execute("""
                SELECT 
                    alias,
                    vendor_id,
                    shipping_center_code,
                    return_center_code,
                    updated_at
                FROM coupang
                WHERE is_active = true
                ORDER BY id
            """)
            
            print("\n✅ 업데이트 완료!")
            print("\n📊 최종 센터 설정:")
            print(f"{'계정명':<15} {'Vendor ID':<12} {'출고지 코드':<20} {'반품지 코드':<20} {'업데이트 시간'}")
            print("-" * 90)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<15} {row[1]:<12} {row[2]:<20} {row[3]:<20} {row[4].strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n📍 주소 정보:")
            print("  - 쿠팡계정1: 경기도 부천시 원미구 부일로199번길 21 4층 401,402호")
            print("  - b00679540: 경기도 부천시 원미구 부일로199번길 21 4층 슈가맨워크")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_centers_to_songnae()