#!/usr/bin/env python3
"""
Docker 컨테이너 내부 연결 테스트
"""
import os
import sys

# Docker 컨테이너 내부에서 실행하는 명령
docker_command = """
python3 -c "
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker 컨테이너 내부에서 localhost 연결
conn = psycopg2.connect(
    host='localhost',
    port=5432,  # 컨테이너 내부 포트
    database='yoonni',
    user='postgres',
    password='postgres'
)

print('✅ 데이터베이스 연결 성공')

cursor = conn.cursor(cursor_factory=RealDictCursor)

# 공급사 확인
cursor.execute('SELECT id, name FROM suppliers WHERE name = \'오너클랜\'')
supplier = cursor.fetchone()
print(f'✅ 공급사: {supplier}')

# 테이블 확인
cursor.execute('SELECT COUNT(*) FROM supplier_products')
count = cursor.fetchone()[0]
print(f'✅ supplier_products 행 수: {count}')

# 테스트 상품 추가
cursor.execute('''
    INSERT INTO supplier_products (
        supplier_id, supplier_product_id, product_name, 
        price, stock_quantity, status
    ) VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (supplier_id, supplier_product_id) 
    DO UPDATE SET product_name = EXCLUDED.product_name
''', (supplier['id'], 'DOCKER_TEST_001', 'Docker 테스트 상품', 15000, 100, 'active'))

conn.commit()
print('✅ 테스트 상품 추가 완료')

# 확인
cursor.execute('SELECT COUNT(*) FROM supplier_products')
final_count = cursor.fetchone()[0]
print(f'✅ 최종 상품 수: {final_count}')

conn.close()
print('🎉 Docker 내부 테스트 성공!')
"
"""

# Docker 컨테이너에서 실행
os.system(f'docker exec yooni-postgres-1 {docker_command}')