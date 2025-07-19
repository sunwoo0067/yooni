#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DatabaseMigration:
    """데이터베이스 마이그레이션 관리"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.migrations = [
            ("001_create_base_tables", self.create_base_tables),
            ("002_create_workflow_tables", self.create_workflow_tables),
            ("003_create_monitoring_tables", self.create_monitoring_tables),
            ("004_create_test_tables", self.create_test_tables),
            ("005_create_indexes", self.create_indexes)
        ]
    
    def run(self):
        """마이그레이션 실행"""
        conn = psycopg2.connect(**self.db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 마이그레이션 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for version, migration_func in self.migrations:
            # 이미 적용된 마이그레이션인지 확인
            cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s",
                (version,)
            )
            
            if cursor.fetchone() is None:
                print(f"Applying migration: {version}")
                migration_func(cursor)
                
                # 마이그레이션 기록
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,)
                )
                print(f"Migration {version} completed")
            else:
                print(f"Migration {version} already applied")
        
        cursor.close()
        conn.close()
        print("All migrations completed")
    
    def create_base_tables(self, cursor):
        """기본 테이블 생성"""
        # 상품 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                sku VARCHAR(100) UNIQUE NOT NULL,
                price DECIMAL(10, 2),
                stock INTEGER DEFAULT 0,
                supplier VARCHAR(100),
                category VARCHAR(100),
                marketplace VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 주문 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(100) UNIQUE NOT NULL,
                customer_id VARCHAR(100),
                customer_name VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                total_amount DECIMAL(10, 2),
                shipping_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 주문 상품 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                price DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_workflow_tables(self, cursor):
        """워크플로우 테이블 생성"""
        # workflow_tables.sql 파일 실행
        sql_file = os.path.join(
            os.path.dirname(__file__),
            "schema/workflow_tables.sql"
        )
        
        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                cursor.execute(f.read())
    
    def create_monitoring_tables(self, cursor):
        """모니터링 테이블 생성"""
        # 시스템 로그 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(20),
                logger VARCHAR(100),
                message TEXT,
                source VARCHAR(100),
                user_id VARCHAR(100),
                request_id VARCHAR(100),
                execution_time_ms INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 메트릭 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100),
                metric_value DECIMAL(20, 4),
                metric_type VARCHAR(50),
                tags JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 알림 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_type VARCHAR(50),
                severity VARCHAR(20),
                title VARCHAR(255),
                description TEXT,
                source VARCHAR(100),
                metadata JSONB,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_test_tables(self, cursor):
        """테스트용 테이블 생성"""
        # 테스트 결과 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id VARCHAR(100) PRIMARY KEY,
                status VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 재고 알림 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_alerts (
                id SERIAL PRIMARY KEY,
                product_id VARCHAR(100),
                alert_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_indexes(self, cursor):
        """인덱스 생성"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier)",
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_created_at ON system_metrics(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)"
        ]
        
        for index in indexes:
            cursor.execute(index)


if __name__ == "__main__":
    # 환경 변수에서 데이터베이스 설정 가져오기
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:1234@localhost:5434/yoonni_test"
    )
    
    # URL 파싱
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    db_config = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # Remove leading /
        'user': parsed.username,
        'password': parsed.password
    }
    
    migration = DatabaseMigration(db_config)
    migration.run()