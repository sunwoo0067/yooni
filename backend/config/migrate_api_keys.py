#!/usr/bin/env python3
"""
환경변수의 API 키들을 DB로 마이그레이션하는 스크립트
"""
import os
import sys
import json
from dotenv import load_dotenv

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager

load_dotenv()

def migrate_api_keys():
    """API 키들을 DB로 마이그레이션"""
    config = ConfigManager()
    
    migrations = [
        # 쿠팡 API
        {
            'category': 'api_keys',
            'key': 'COUPANG_ACCESS_KEY',
            'value': os.getenv('COUPANG_ACCESS_KEY'),
            'description': '쿠팡 파트너스 API Access Key'
        },
        {
            'category': 'api_keys',
            'key': 'COUPANG_SECRET_KEY',
            'value': os.getenv('COUPANG_SECRET_KEY'),
            'description': '쿠팡 파트너스 API Secret Key',
            'encrypted': True  # 나중에 암호화 구현
        },
        {
            'category': 'api_keys',
            'key': 'COUPANG_VENDOR_ID',
            'value': os.getenv('COUPANG_VENDOR_ID'),
            'description': '쿠팡 벤더 ID'
        },
        
        # 네이버 API
        {
            'category': 'api_keys',
            'key': 'NAVER_CLIENT_ID',
            'value': os.getenv('NAVER_CLIENT_ID'),
            'description': '네이버 스마트스토어 Client ID'
        },
        {
            'category': 'api_keys',
            'key': 'NAVER_CLIENT_SECRET',
            'value': os.getenv('NAVER_CLIENT_SECRET'),
            'description': '네이버 스마트스토어 Client Secret',
            'encrypted': True
        },
        
        # 11번가 API
        {
            'category': 'api_keys',
            'key': 'ELEVEN_API_KEY',
            'value': os.getenv('ELEVEN_API_KEY'),
            'description': '11번가 Open API Key'
        },
        
        # 오너클랜 API
        {
            'category': 'api_keys',
            'key': 'OWNERCLAN_API_KEY',
            'value': os.getenv('OWNERCLAN_API_KEY'),
            'description': '오너클랜 API Key'
        },
        {
            'category': 'api_keys',
            'key': 'OWNERCLAN_API_SECRET',
            'value': os.getenv('OWNERCLAN_API_SECRET'),
            'description': '오너클랜 API Secret',
            'encrypted': True
        },
        
        # 젠트레이드 API
        {
            'category': 'api_keys',
            'key': 'ZENTRADE_API_KEY',
            'value': os.getenv('ZENTRADE_API_KEY'),
            'description': '젠트레이드 API Key'
        },
        {
            'category': 'api_keys',
            'key': 'ZENTRADE_API_SECRET',
            'value': os.getenv('ZENTRADE_API_SECRET'),
            'description': '젠트레이드 API Secret',
            'encrypted': True
        },
        
        # 마켓플레이스 설정
        {
            'category': 'marketplace',
            'key': 'COUPANG_API_URL',
            'value': 'https://api-gateway.coupang.com',
            'description': '쿠팡 API 기본 URL'
        },
        {
            'category': 'marketplace',
            'key': 'NAVER_API_URL',
            'value': 'https://bizapi.naver.com',
            'description': '네이버 비즈니스 API URL'
        },
        {
            'category': 'marketplace',
            'key': 'ELEVEN_API_URL',
            'value': 'https://openapi.11st.co.kr/openapi/OpenApiService.tmall',
            'description': '11번가 Open API URL'
        },
        {
            'category': 'marketplace',
            'key': 'OWNERCLAN_API_URL',
            'value': 'https://api.ownerclan.com/v1/graphql',
            'description': '오너클랜 GraphQL API URL'
        },
        {
            'category': 'marketplace',
            'key': 'OWNERCLAN_SANDBOX_URL',
            'value': 'https://api-sandbox.ownerclan.com/v1/graphql',
            'description': '오너클랜 샌드박스 API URL'
        },
        
        # 수집 설정
        {
            'category': 'collection',
            'key': 'PRODUCT_COLLECTION_INTERVAL',
            'value': '3600',
            'description': '상품 수집 주기 (초)',
            'data_type': 'integer'
        },
        {
            'category': 'collection',
            'key': 'ORDER_COLLECTION_INTERVAL',
            'value': '1800',
            'description': '주문 수집 주기 (초)',
            'data_type': 'integer'
        },
        {
            'category': 'collection',
            'key': 'STOCK_SYNC_INTERVAL',
            'value': '300',
            'description': '재고 동기화 주기 (초)',
            'data_type': 'integer'
        },
        {
            'category': 'collection',
            'key': 'ENABLE_AUTO_COLLECTION',
            'value': 'true',
            'description': '자동 수집 활성화',
            'data_type': 'boolean'
        }
    ]
    
    success_count = 0
    failed_count = 0
    
    print("API 키 마이그레이션 시작...")
    
    for item in migrations:
        if item.get('value'):
            # 암호화 플래그는 set 메서드에서 지원하지 않으므로 제거
            encrypted = item.pop('encrypted', False)
            data_type = item.pop('data_type', 'string')
            
            # 값이 있을 때만 저장
            success = config.set(
                category=item['category'],
                key=item['key'],
                value=item['value'],
                description=item['description'],
                user='migration_script'
            )
            
            if success:
                success_count += 1
                print(f"✓ {item['category']}.{item['key']} 저장 완료")
            else:
                failed_count += 1
                print(f"✗ {item['category']}.{item['key']} 저장 실패")
        else:
            print(f"- {item['category']}.{item['key']} 스킵 (값 없음)")
    
    print(f"\n마이그레이션 완료: 성공 {success_count}개, 실패 {failed_count}개")
    
    # 저장된 설정 확인
    print("\n현재 저장된 설정:")
    all_configs = config.get_all()
    for category, items in all_configs.items():
        print(f"\n[{category}]")
        for key, value in items.items():
            # 민감한 정보는 일부만 표시
            if 'SECRET' in key or 'KEY' in key:
                display_value = value[:10] + '***' if value and len(value) > 10 else '***'
            else:
                display_value = value
            print(f"  {key}: {display_value}")

if __name__ == "__main__":
    migrate_api_keys()