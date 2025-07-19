"""
시스템 설정 관리자
DB에서 환경 변수 및 설정을 관리
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """시스템 설정 관리 클래스"""
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        Args:
            db_config: 데이터베이스 연결 설정 (None이면 환경변수에서 읽음)
        """
        load_dotenv()
        
        # DB 연결 설정
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5434)),
                'database': os.getenv('DB_NAME', 'yoonni'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '1234')
            }
        
        self._connection = None
        self._ensure_connection()
    
    def _ensure_connection(self):
        """데이터베이스 연결 확인 및 재연결"""
        try:
            if self._connection and not self._connection.closed:
                # 연결 상태 확인
                with self._connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return
        except:
            pass
        
        # 새 연결 생성
        self._connection = psycopg2.connect(**self.db_config)
        self._connection.autocommit = True
    
    def get(self, category: str, key: str, default: Any = None) -> Any:
        """설정 값 조회
        
        Args:
            category: 설정 카테고리
            key: 설정 키
            default: 기본값
            
        Returns:
            설정 값 (타입에 따라 자동 변환)
        """
        try:
            self._ensure_connection()
            
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT value, data_type, encrypted 
                    FROM system_configs 
                    WHERE category = %s AND key = %s AND is_active = true
                """, (category, key))
                
                result = cursor.fetchone()
                
                if not result:
                    return default
                
                # 암호화된 값 처리 (추후 구현)
                if result['encrypted']:
                    # TODO: 복호화 로직 추가
                    value = result['value']
                else:
                    value = result['value']
                
                # 타입 변환
                return self._convert_value(value, result['data_type'])
                
        except Exception as e:
            logger.error(f"설정 조회 오류: {e}")
            return default
    
    def set(self, category: str, key: str, value: Any, 
            description: str = None, user: str = 'system') -> bool:
        """설정 값 저장
        
        Args:
            category: 설정 카테고리
            key: 설정 키
            value: 설정 값
            description: 설명
            user: 변경한 사용자
            
        Returns:
            성공 여부
        """
        try:
            self._ensure_connection()
            
            # 값 타입 결정
            data_type = self._get_data_type(value)
            
            # 값 변환
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                value_str = 'true' if value else 'false'
            else:
                value_str = str(value)
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO system_configs 
                    (category, key, value, description, data_type, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (category, key) 
                    DO UPDATE SET 
                        value = EXCLUDED.value,
                        description = COALESCE(EXCLUDED.description, system_configs.description),
                        data_type = EXCLUDED.data_type,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = EXCLUDED.updated_by
                """, (category, key, value_str, description, data_type, user, user))
                
                return True
                
        except Exception as e:
            logger.error(f"설정 저장 오류: {e}")
            return False
    
    def delete(self, category: str, key: str, user: str = 'system') -> bool:
        """설정 삭제 (비활성화)
        
        Args:
            category: 설정 카테고리
            key: 설정 키
            user: 변경한 사용자
            
        Returns:
            성공 여부
        """
        try:
            self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE system_configs 
                    SET is_active = false, 
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = %s
                    WHERE category = %s AND key = %s
                """, (user, category, key))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"설정 삭제 오류: {e}")
            return False
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """카테고리의 모든 설정 조회
        
        Args:
            category: 설정 카테고리
            
        Returns:
            {key: value} 형태의 딕셔너리
        """
        try:
            self._ensure_connection()
            
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, value, data_type, encrypted 
                    FROM system_configs 
                    WHERE category = %s AND is_active = true
                    ORDER BY key
                """, (category,))
                
                results = cursor.fetchall()
                
                config_dict = {}
                for row in results:
                    value = row['value']
                    
                    # 암호화된 값 처리
                    if row['encrypted']:
                        # TODO: 복호화 로직 추가
                        pass
                    
                    config_dict[row['key']] = self._convert_value(value, row['data_type'])
                
                return config_dict
                
        except Exception as e:
            logger.error(f"카테고리 설정 조회 오류: {e}")
            return {}
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """모든 설정 조회
        
        Returns:
            {category: {key: value}} 형태의 중첩 딕셔너리
        """
        try:
            self._ensure_connection()
            
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT category, key, value, data_type, encrypted 
                    FROM system_configs 
                    WHERE is_active = true
                    ORDER BY category, key
                """)
                
                results = cursor.fetchall()
                
                config_dict = {}
                for row in results:
                    category = row['category']
                    if category not in config_dict:
                        config_dict[category] = {}
                    
                    value = row['value']
                    
                    # 암호화된 값 처리
                    if row['encrypted']:
                        # TODO: 복호화 로직 추가
                        pass
                    
                    config_dict[category][row['key']] = self._convert_value(value, row['data_type'])
                
                return config_dict
                
        except Exception as e:
            logger.error(f"전체 설정 조회 오류: {e}")
            return {}
    
    def get_history(self, category: str = None, key: str = None, 
                   limit: int = 100) -> List[Dict]:
        """설정 변경 이력 조회
        
        Args:
            category: 특정 카테고리만 조회
            key: 특정 키만 조회
            limit: 조회 개수 제한
            
        Returns:
            변경 이력 리스트
        """
        try:
            self._ensure_connection()
            
            query = """
                SELECT h.*, c.key, c.category
                FROM system_config_history h
                JOIN system_configs c ON h.config_id = c.id
                WHERE 1=1
            """
            params = []
            
            if category:
                query += " AND c.category = %s"
                params.append(category)
            
            if key:
                query += " AND c.key = %s"
                params.append(key)
            
            query += " ORDER BY h.changed_at DESC LIMIT %s"
            params.append(limit)
            
            with self._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"이력 조회 오류: {e}")
            return []
    
    def _convert_value(self, value: str, data_type: str) -> Any:
        """문자열 값을 지정된 타입으로 변환
        
        Args:
            value: 문자열 값
            data_type: 데이터 타입
            
        Returns:
            변환된 값
        """
        if value is None:
            return None
        
        try:
            if data_type == 'integer':
                return int(value)
            elif data_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif data_type == 'json':
                return json.loads(value)
            else:  # string
                return value
        except:
            logger.warning(f"값 변환 실패: {value} -> {data_type}")
            return value
    
    def _get_data_type(self, value: Any) -> str:
        """값의 데이터 타입 결정
        
        Args:
            value: 값
            
        Returns:
            데이터 타입 문자열
        """
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, (dict, list)):
            return 'json'
        else:
            return 'string'
    
    def close(self):
        """연결 종료"""
        if self._connection:
            self._connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 전역 설정 인스턴스 (싱글톤)
_config_instance = None

def get_config_manager() -> ConfigManager:
    """전역 설정 관리자 인스턴스 반환"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def get_config(category: str, key: str, default: Any = None) -> Any:
    """간편한 설정 조회 함수"""
    return get_config_manager().get(category, key, default)

def set_config(category: str, key: str, value: Any, 
               description: str = None, user: str = 'system') -> bool:
    """간편한 설정 저장 함수"""
    return get_config_manager().set(category, key, value, description, user)