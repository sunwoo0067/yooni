import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import sys
from dotenv import load_dotenv

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import DatabaseConfig, get_config
except ImportError:
    # config 모듈이 없으면 환경변수 사용
    get_config = None

load_dotenv()

class MarketBase:
    """마켓 공통 기본 클래스"""
    
    def __init__(self):
        self.connection = self._get_connection()
    
    def _get_connection(self):
        """데이터베이스 연결"""
        # ConfigManager가 있으면 DB에서 설정 읽기
        if get_config:
            try:
                db_config = DatabaseConfig()
                return psycopg2.connect(**db_config.get_connection_config())
            except:
                pass
        
        # 환경변수에서 읽기 (폴백)
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5434),
            database=os.getenv('DB_NAME', 'yoonni'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '1234')
        )
    
    def get_market_id(self, market_code: str) -> Optional[int]:
        """마켓 코드로 마켓 ID 조회"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM markets WHERE code = %s AND is_active = true",
                (market_code,)
            )
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_market_account(self, market_code: str, account_name: str) -> Optional[Dict]:
        """마켓 계정 정보 조회"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT ma.*, m.code as market_code, m.name as market_name
                FROM market_accounts ma
                JOIN markets m ON m.id = ma.market_id
                WHERE m.code = %s AND ma.account_name = %s AND ma.is_active = true
            """, (market_code, account_name))
            return cursor.fetchone()
    
    def create_market_account(self, market_code: str, account_data: Dict) -> int:
        """마켓 계정 생성"""
        market_id = self.get_market_id(market_code)
        if not market_id:
            raise ValueError(f"Unknown market code: {market_code}")
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO market_accounts 
                (market_id, account_name, api_key, api_secret, vendor_id, extra_config)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (market_id, account_name) 
                DO UPDATE SET 
                    api_key = EXCLUDED.api_key,
                    api_secret = EXCLUDED.api_secret,
                    vendor_id = EXCLUDED.vendor_id,
                    extra_config = EXCLUDED.extra_config,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                market_id,
                account_data['account_name'],
                account_data.get('api_key'),
                account_data.get('api_secret'),
                account_data.get('vendor_id'),
                Json(account_data.get('extra_config', {}))
            ))
            self.connection.commit()
            return cursor.fetchone()[0]
    
    def close(self):
        """연결 종료"""
        if self.connection:
            self.connection.close()