"""
pytest 전역 설정 및 픽스처
"""
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 테스트 데이터베이스 설정
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': int(os.getenv('TEST_DB_PORT', '5434')),
    'database': 'yoonni_test',
    'user': os.getenv('TEST_DB_USER', 'postgres'),
    'password': os.getenv('TEST_DB_PASSWORD', '1234')
}


@pytest.fixture(scope='session')
def test_db():
    """테스트 데이터베이스 생성 및 정리"""
    # 기본 연결 (postgres 데이터베이스)
    conn = psycopg2.connect(
        host=TEST_DB_CONFIG['host'],
        port=TEST_DB_CONFIG['port'],
        database='postgres',
        user=TEST_DB_CONFIG['user'],
        password=TEST_DB_CONFIG['password']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # 테스트 데이터베이스 생성
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_CONFIG['database']}")
        cur.execute(f"CREATE DATABASE {TEST_DB_CONFIG['database']}")
    except Exception as e:
        print(f"테스트 DB 생성 오류: {e}")
    finally:
        cur.close()
        conn.close()
    
    yield TEST_DB_CONFIG
    
    # 테스트 후 정리
    conn = psycopg2.connect(
        host=TEST_DB_CONFIG['host'],
        port=TEST_DB_CONFIG['port'],
        database='postgres',
        user=TEST_DB_CONFIG['user'],
        password=TEST_DB_CONFIG['password']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_CONFIG['database']}")
    except:
        pass
    finally:
        cur.close()
        conn.close()


@pytest.fixture(scope='function')
def db_connection(test_db):
    """데이터베이스 연결 픽스처"""
    conn = psycopg2.connect(**test_db)
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def db_cursor(db_connection):
    """데이터베이스 커서 픽스처"""
    cur = db_connection.cursor()
    yield cur
    db_connection.rollback()
    cur.close()


@pytest.fixture(scope='session')
def sample_product_data():
    """샘플 상품 데이터"""
    return {
        'market_product_id': 'TEST123456',
        'product_name': '테스트 상품',
        'brand': '테스트 브랜드',
        'category_name': '테스트 카테고리',
        'sale_price': 10000,
        'cost_price': 7000,
        'stock_quantity': 100,
        'status': 'active',
        'market_code': 'coupang'
    }


@pytest.fixture(scope='session')
def sample_order_data():
    """샘플 주문 데이터"""
    return {
        'market_order_id': 'ORD123456',
        'order_date': datetime.now(),
        'buyer_name': '테스트 구매자',
        'buyer_email': 'test@example.com',
        'buyer_phone': '010-1234-5678',
        'total_price': 25000,
        'order_status': 'pending',
        'payment_method': '신용카드',
        'shipping_address': '서울시 강남구 테스트로 123'
    }


@pytest.fixture(scope='function')
def mock_coupang_api(monkeypatch):
    """쿠팡 API 모킹"""
    def mock_get_products(*args, **kwargs):
        return {
            'code': 200,
            'message': 'OK',
            'data': {
                'products': [
                    {
                        'sellerProductId': 123456,
                        'displayCategoryCode': 1001,
                        'productName': '모킹된 상품',
                        'brand': '모킹 브랜드',
                        'salePrice': 15000
                    }
                ],
                'nextToken': None
            }
        }
    
    def mock_get_orders(*args, **kwargs):
        return {
            'code': 200,
            'message': 'OK',
            'data': {
                'orders': [
                    {
                        'orderId': 789012,
                        'orderDate': '2024-01-15T10:00:00',
                        'buyer': {
                            'name': '모킹 구매자',
                            'email': 'mock@example.com'
                        },
                        'totalPrice': 30000
                    }
                ],
                'nextToken': None
            }
        }
    
    # API 호출 모킹
    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResponse(mock_get_products()))
    monkeypatch.setattr('requests.post', lambda *args, **kwargs: MockResponse(mock_get_orders()))
    
    return {
        'get_products': mock_get_products,
        'get_orders': mock_get_orders
    }


class MockResponse:
    """Mock HTTP Response"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture(scope='function')
def temp_config_file(tmp_path):
    """임시 설정 파일"""
    config_file = tmp_path / "test_config.json"
    config_data = {
        'database': {
            'host': 'localhost',
            'port': 5434,
            'name': 'yoonni_test'
        },
        'api': {
            'timeout': 30,
            'retry_count': 3
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    yield config_file
    
    # 정리
    if config_file.exists():
        config_file.unlink()


@pytest.fixture(autouse=True)
def reset_singleton():
    """싱글톤 객체 초기화"""
    # ConfigManager 싱글톤 초기화
    import config.config_manager
    config.config_manager._config_instance = None
    yield
    config.config_manager._config_instance = None


@pytest.fixture
def captured_logs(caplog):
    """로그 캡처 헬퍼"""
    def get_logs(level='INFO'):
        return [r for r in caplog.records if r.levelname == level]
    
    return get_logs