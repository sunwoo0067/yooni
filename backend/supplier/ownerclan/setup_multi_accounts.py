#!/usr/bin/env python3
"""
오너클랜 멀티 계정 설정 스크립트
데이터베이스에 2개의 오너클랜 계정을 설정
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_multi_accounts():
    """오너클랜 멀티 계정 설정"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 현재 오너클랜 supplier 확인
            cursor.execute("""
                SELECT id FROM suppliers WHERE name = '오너클랜'
            """)
            supplier = cursor.fetchone()
            
            if not supplier:
                # 오너클랜 supplier 생성
                cursor.execute("""
                    INSERT INTO suppliers (name, code, description, created_at)
                    VALUES ('오너클랜', 'ownerclan', 'B2B 도매 플랫폼', NOW())
                    RETURNING id
                """)
                supplier = cursor.fetchone()
                logger.info(f"오너클랜 supplier 생성: ID {supplier['id']}")
            else:
                logger.info(f"기존 오너클랜 supplier 사용: ID {supplier['id']}")
                
            supplier_id = supplier['id']
            
            # 현재 설정 확인
            cursor.execute("""
                SELECT COUNT(*) as count FROM supplier_configs
                WHERE supplier_id = %s
            """, (supplier_id,))
            
            existing_count = cursor.fetchone()['count']
            logger.info(f"현재 설정된 계정 수: {existing_count}")
            
            if existing_count < 2:
                # 계정 정보 입력 받기
                accounts = []
                for i in range(1, 3):
                    print(f"\n=== 오너클랜 계정 {i} 정보 입력 ===")
                    api_key = input(f"계정 {i} API Key (username): ").strip()
                    api_secret = input(f"계정 {i} API Secret (password): ").strip()
                    
                    if api_key and api_secret:
                        accounts.append({
                            'api_key': api_key,
                            'api_secret': api_secret,
                            'name': f'오너클랜_계정{i}'
                        })
                    else:
                        logger.warning(f"계정 {i} 정보가 비어있어 건너뜁니다")
                        
                # 계정 추가 또는 업데이트
                for i, account in enumerate(accounts, 1):
                    # 기존 설정 확인
                    cursor.execute("""
                        SELECT id FROM supplier_configs
                        WHERE supplier_id = %s
                        ORDER BY id
                        LIMIT 1 OFFSET %s
                    """, (supplier_id, i-1))
                    
                    existing_config = cursor.fetchone()
                    
                    if existing_config:
                        # 업데이트
                        cursor.execute("""
                            UPDATE supplier_configs SET
                                api_key = %s,
                                api_secret = %s,
                                api_type = 'graphql',
                                api_endpoint = 'https://api.ownerclan.com/v1/graphql',
                                is_active = true,
                                settings = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            account['api_key'],
                            account['api_secret'],
                            f'{{"name": "{account["name"]}"}}',
                            existing_config['id']
                        ))
                        logger.info(f"{account['name']} 업데이트 완료")
                    else:
                        # 신규 추가
                        cursor.execute("""
                            INSERT INTO supplier_configs (
                                supplier_id, api_key, api_secret, api_type,
                                api_endpoint, is_active, settings, created_at
                            ) VALUES (
                                %s, %s, %s, 'graphql',
                                'https://api.ownerclan.com/v1/graphql',
                                true, %s, NOW()
                            )
                        """, (
                            supplier_id,
                            account['api_key'],
                            account['api_secret'],
                            f'{{"name": "{account["name"]}"}}'
                        ))
                        logger.info(f"{account['name']} 추가 완료")
                        
            # 설정된 계정 확인
            cursor.execute("""
                SELECT 
                    sc.id,
                    sc.api_key,
                    sc.is_active,
                    sc.settings
                FROM supplier_configs sc
                WHERE supplier_id = %s
                ORDER BY id
            """, (supplier_id,))
            
            configs = cursor.fetchall()
            
            print("\n=== 설정된 오너클랜 계정 ===")
            for config in configs:
                settings = config.get('settings', {})
                name = settings.get('name', f'계정_{config["id"]}') if isinstance(settings, dict) else f'계정_{config["id"]}'
                print(f"- {name}: {config['api_key'][:20]}... (활성: {config['is_active']})")
                
            conn.commit()
            logger.info("\n멀티 계정 설정 완료!")
            
            print("\n수집 시작 명령어:")
            print("python3 supplier/ownerclan/collect_products_multi_account.py")
            
    except Exception as e:
        logger.error(f"설정 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_multi_accounts()