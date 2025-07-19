"""
ConfigManager 테스트
"""
import pytest
from config.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager 테스트 클래스"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스 테스트"""
        from config.config_manager import get_config_manager
        
        instance1 = get_config_manager()
        instance2 = get_config_manager()
        
        assert instance1 is instance2
    
    def test_get_config_with_default(self, db_connection):
        """기본값을 사용한 설정 조회 테스트"""
        config = ConfigManager()
        
        # 존재하지 않는 설정은 기본값 반환
        value = config.get('test_category', 'test_key', 'default_value')
        assert value == 'default_value'
    
    def test_set_and_get_config(self, db_connection):
        """설정 저장 및 조회 테스트"""
        config = ConfigManager()
        
        # 설정 저장
        config.set('test_category', 'test_key', 'test_value')
        
        # 설정 조회
        value = config.get('test_category', 'test_key')
        assert value == 'test_value'
    
    def test_get_int_config(self, db_connection):
        """정수형 설정 조회 테스트"""
        config = ConfigManager()
        
        # 정수 저장
        config.set('test', 'port', '5432')
        
        # 정수로 조회
        port = config.get_int('test', 'port')
        assert port == 5432
        assert isinstance(port, int)
    
    def test_get_bool_config(self, db_connection):
        """불린형 설정 조회 테스트"""
        config = ConfigManager()
        
        # 불린 값 테스트
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('', False)
        ]
        
        for value_str, expected in test_cases:
            config.set('test', 'flag', value_str)
            result = config.get_bool('test', 'flag')
            assert result == expected
    
    def test_get_json_config(self, db_connection):
        """JSON 설정 조회 테스트"""
        config = ConfigManager()
        
        # JSON 데이터
        json_data = {'key': 'value', 'number': 123, 'list': [1, 2, 3]}
        config.set('test', 'json_data', json_data)
        
        # JSON으로 조회
        result = config.get_json('test', 'json_data')
        assert result == json_data
    
    def test_update_existing_config(self, db_connection):
        """기존 설정 업데이트 테스트"""
        config = ConfigManager()
        
        # 초기 설정
        config.set('test', 'update_key', 'initial_value')
        
        # 업데이트
        config.set('test', 'update_key', 'updated_value')
        
        # 확인
        value = config.get('test', 'update_key')
        assert value == 'updated_value'
    
    def test_get_all_by_category(self, db_connection):
        """카테고리별 전체 설정 조회 테스트"""
        config = ConfigManager()
        
        # 여러 설정 저장
        config.set('test_category', 'key1', 'value1')
        config.set('test_category', 'key2', 'value2')
        config.set('other_category', 'key3', 'value3')
        
        # 카테고리별 조회
        category_configs = config.get_all('test_category')
        
        assert len(category_configs) == 2
        assert category_configs['key1'] == 'value1'
        assert category_configs['key2'] == 'value2'
        assert 'key3' not in category_configs
    
    def test_error_handling(self, db_connection, monkeypatch):
        """에러 처리 테스트"""
        config = ConfigManager()
        
        # DB 연결 오류 시뮬레이션
        def mock_connect(*args, **kwargs):
            raise Exception("DB 연결 실패")
        
        monkeypatch.setattr('psycopg2.connect', mock_connect)
        
        # 오류 발생해도 기본값 반환
        value = config.get('test', 'key', 'default')
        assert value == 'default'