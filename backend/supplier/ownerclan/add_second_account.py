#!/usr/bin/env python3
"""
오너클랜 2번째 계정 추가 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def add_second_account():
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="yoonni",
        user="postgres",
        password="1234"
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 오너클랜 supplier ID 확인
            cursor.execute("SELECT id FROM suppliers WHERE name = '오너클랜'")
            supplier = cursor.fetchone()
            
            if not supplier:
                print("오너클랜 supplier가 없습니다")
                return
                
            supplier_id = supplier['id']
            
            # 2번째 계정 추가 (프로덕션 환경)
            cursor.execute("""
                INSERT INTO supplier_configs (
                    supplier_id, api_type, api_endpoint, api_key, api_secret,
                    collection_enabled, collection_schedule, schedule_time,
                    settings, created_at
                ) VALUES (
                    %s, 'graphql', 'https://api.ownerclan.com/v1/graphql',
                    'second_account_key', 'second_account_secret',
                    true, 'daily', '02:00:00',
                    %s, NOW()
                )
                RETURNING id
            """, (supplier_id, json.dumps({"name": "오너클랜_계정2"})))
            
            new_config = cursor.fetchone()
            print(f"2번째 계정 추가 완료: ID {new_config['id']}")
            
            # 현재 모든 계정 확인
            cursor.execute("""
                SELECT 
                    sc.id,
                    sc.api_key,
                    sc.api_endpoint,
                    sc.collection_enabled
                FROM supplier_configs sc
                WHERE supplier_id = %s
                ORDER BY id
            """, (supplier_id,))
            
            configs = cursor.fetchall()
            
            print(f"\n총 {len(configs)}개 오너클랜 계정:")
            for config in configs:
                endpoint_type = "프로덕션" if "sandbox" not in config['api_endpoint'] else "샌드박스"
                print(f"- ID {config['id']}: {config['api_key'][:20]}... ({endpoint_type}, 활성: {config['collection_enabled']})")
                
            conn.commit()
            
            print("\n이제 멀티 계정 수집이 가능합니다!")
            print("실행: python3 supplier/ownerclan/collect_products_multi_account.py")
            
    except Exception as e:
        print(f"오류: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_second_account()