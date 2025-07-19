#!/usr/bin/env python3
"""
데이터베이스 파티션 관리자
파티션 생성, 유지보수, 모니터링 기능 제공
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


class PartitionManager:
    """파티션 관리자"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.db_config = {
            'host': self.config.get('database', 'host', 'localhost'),
            'port': self.config.get('database', 'port', 5434),
            'database': self.config.get('database', 'name', 'yoonni'),
            'user': self.config.get('database', 'user', 'postgres'),
            'password': self.config.get('database', 'password', '1234')
        }
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('partition_manager')
        logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        return logger
        
    def get_connection(self):
        """데이터베이스 연결"""
        return psycopg2.connect(**self.db_config)
        
    def create_monthly_partitions(self, table_name: str, months_ahead: int = 3):
        """월별 파티션 생성"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # 현재 날짜 기준으로 파티션 생성
            current_date = datetime.now()
            
            for i in range(-1, months_ahead):
                partition_date = current_date + relativedelta(months=i)
                start_date = partition_date.replace(day=1)
                end_date = start_date + relativedelta(months=1)
                partition_name = f"{table_name}_{start_date.strftime('%Y_%m')}"
                
                # 파티션 존재 확인
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = 'public' AND c.relname = %s
                    )
                """, (partition_name,))
                
                exists = cur.fetchone()[0]
                
                if not exists:
                    # 파티션 생성
                    create_sql = f"""
                        CREATE TABLE {partition_name} 
                        PARTITION OF {table_name}_partitioned
                        FOR VALUES FROM ('{start_date.strftime('%Y-%m-%d')}') 
                        TO ('{end_date.strftime('%Y-%m-%d')}')
                    """
                    
                    cur.execute(create_sql)
                    self.logger.info(f"파티션 생성: {partition_name}")
                    
                    # 인덱스 생성
                    self._create_partition_indexes(cur, table_name, partition_name)
                    
            conn.commit()
            self.logger.info(f"{table_name} 테이블의 월별 파티션 생성 완료")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"파티션 생성 오류: {str(e)}")
            raise
        finally:
            cur.close()
            conn.close()
            
    def _create_partition_indexes(self, cur, parent_table: str, partition_name: str):
        """파티션 인덱스 생성"""
        index_configs = {
            'market_orders': [
                ('market_account_id', 'btree'),
                ('order_status', 'btree'),
                ('buyer_email', 'btree')
            ],
            'market_raw_data': [
                ('market_code', 'btree'),
                ('data_type', 'btree'),
                ('processed', 'btree', 'WHERE NOT processed')
            ],
            'job_executions': [
                ('job_id', 'btree'),
                ('status', 'btree')
            ]
        }
        
        if parent_table in index_configs:
            for index_config in index_configs[parent_table]:
                column = index_config[0]
                method = index_config[1]
                where_clause = index_config[2] if len(index_config) > 2 else ''
                
                index_name = f"idx_{partition_name}_{column}"
                create_index_sql = f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {partition_name} USING {method} ({column})
                    {where_clause}
                """
                
                cur.execute(create_index_sql)
                
    def drop_old_partitions(self, table_name: str, retention_months: int):
        """오래된 파티션 삭제"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cutoff_date = datetime.now() - relativedelta(months=retention_months)
            
            # 파티션 목록 조회
            cur.execute("""
                SELECT 
                    c.relname as partition_name,
                    pg_get_expr(c.relpartbound, c.oid) as partition_bound
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                AND c.relispartition = true
                AND c.relname LIKE %s
                ORDER BY c.relname
            """, (f"{table_name}_%",))
            
            partitions = cur.fetchall()
            dropped_count = 0
            
            for partition in partitions:
                partition_name = partition['partition_name']
                
                # 파티션 날짜 추출 (YYYY_MM 형식)
                if '_' in partition_name:
                    date_parts = partition_name.split('_')[-2:]
                    try:
                        year = int(date_parts[0])
                        month = int(date_parts[1])
                        partition_date = datetime(year, month, 1)
                        
                        if partition_date < cutoff_date:
                            # 파티션 크기 확인
                            cur.execute("""
                                SELECT 
                                    pg_size_pretty(pg_relation_size(%s::regclass)) as size,
                                    pg_stat_get_live_tuples(%s::regclass) as rows
                            """, (partition_name, partition_name))
                            
                            size_info = cur.fetchone()
                            
                            # 파티션 삭제
                            cur.execute(f"DROP TABLE IF EXISTS {partition_name} CASCADE")
                            dropped_count += 1
                            
                            self.logger.info(
                                f"파티션 삭제: {partition_name} "
                                f"(크기: {size_info['size']}, 행: {size_info['rows']})"
                            )
                    except (ValueError, IndexError):
                        pass
                        
            conn.commit()
            self.logger.info(f"{table_name} 테이블에서 {dropped_count}개 파티션 삭제 완료")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"파티션 삭제 오류: {str(e)}")
            raise
        finally:
            cur.close()
            conn.close()
            
    def get_partition_status(self) -> List[Dict]:
        """파티션 상태 조회"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # 파티션 정보 조회
            cur.execute("""
                SELECT 
                    parent.relname as parent_table,
                    child.relname as partition_name,
                    pg_size_pretty(pg_relation_size(child.oid)) as size,
                    pg_stat_get_live_tuples(child.oid) as row_count,
                    pg_stat_get_dead_tuples(child.oid) as dead_rows,
                    pg_get_expr(child.relpartbound, child.oid) as partition_bound,
                    CASE 
                        WHEN child.relname ~ '\d{4}_\d{2}$' THEN
                            to_date(right(child.relname, 7), 'YYYY_MM')
                        ELSE NULL
                    END as partition_date
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                JOIN pg_namespace n ON n.oid = parent.relnamespace
                WHERE n.nspname = 'public'
                AND parent.relkind = 'p'  -- partitioned table
                ORDER BY parent.relname, child.relname
            """)
            
            partitions = cur.fetchall()
            
            # 파티션별 통계 집계
            stats = {}
            for partition in partitions:
                parent = partition['parent_table']
                if parent not in stats:
                    stats[parent] = {
                        'parent_table': parent,
                        'partition_count': 0,
                        'total_rows': 0,
                        'total_size_bytes': 0,
                        'partitions': []
                    }
                
                stats[parent]['partition_count'] += 1
                stats[parent]['total_rows'] += partition['row_count']
                
                # 크기 파싱
                size_str = partition['size']
                size_bytes = self._parse_size_to_bytes(size_str)
                stats[parent]['total_size_bytes'] += size_bytes
                
                stats[parent]['partitions'].append({
                    'name': partition['partition_name'],
                    'size': partition['size'],
                    'rows': partition['row_count'],
                    'dead_rows': partition['dead_rows'],
                    'date': partition['partition_date']
                })
            
            # 전체 크기 포맷팅
            for table_stats in stats.values():
                table_stats['total_size'] = self._format_bytes(table_stats['total_size_bytes'])
                
            return list(stats.values())
            
        except Exception as e:
            self.logger.error(f"파티션 상태 조회 오류: {str(e)}")
            return []
        finally:
            cur.close()
            conn.close()
            
    def _parse_size_to_bytes(self, size_str: str) -> int:
        """크기 문자열을 바이트로 변환"""
        size_str = size_str.strip()
        if size_str.endswith('bytes'):
            return int(size_str.replace('bytes', '').strip())
        
        units = {
            'kB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                value = float(size_str.replace(unit, '').strip())
                return int(value * multiplier)
                
        return 0
        
    def _format_bytes(self, bytes_value: int) -> str:
        """바이트를 사람이 읽기 쉬운 형식으로 변환"""
        if bytes_value == 0:
            return '0 bytes'
            
        units = ['bytes', 'kB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.2f} {units[unit_index]}"
        
    def analyze_partitions(self):
        """파티션 통계 업데이트"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # 모든 파티션에 대해 ANALYZE 실행
            cur.execute("""
                SELECT 
                    n.nspname || '.' || c.relname as table_name
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                AND c.relispartition = true
            """)
            
            partitions = cur.fetchall()
            
            for partition in partitions:
                table_name = partition[0]
                cur.execute(f"ANALYZE {table_name}")
                self.logger.info(f"통계 업데이트: {table_name}")
                
            conn.commit()
            self.logger.info("파티션 통계 업데이트 완료")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"통계 업데이트 오류: {str(e)}")
            raise
        finally:
            cur.close()
            conn.close()
            
    def maintenance_report(self):
        """파티션 유지보수 보고서"""
        print("\n" + "="*80)
        print("파티션 유지보수 보고서")
        print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 파티션 상태
        status = self.get_partition_status()
        
        if not status:
            print("\n파티션된 테이블이 없습니다.")
            return
            
        for table_info in status:
            print(f"\n## {table_info['parent_table']} 테이블")
            print(f"  - 파티션 수: {table_info['partition_count']}")
            print(f"  - 총 레코드: {table_info['total_rows']:,}")
            print(f"  - 총 크기: {table_info['total_size']}")
            
            # 최신/최오래된 파티션
            if table_info['partitions']:
                partitions_with_date = [
                    p for p in table_info['partitions'] 
                    if p.get('date')
                ]
                
                if partitions_with_date:
                    oldest = min(partitions_with_date, key=lambda x: x['date'])
                    newest = max(partitions_with_date, key=lambda x: x['date'])
                    
                    print(f"  - 가장 오래된 파티션: {oldest['name']} ({oldest['date'].strftime('%Y-%m')})")
                    print(f"  - 가장 최신 파티션: {newest['name']} ({newest['date'].strftime('%Y-%m')})")
                    
            # 파티션별 상세 정보
            print("\n  파티션 목록:")
            for partition in sorted(table_info['partitions'], key=lambda x: x['name']):
                dead_ratio = (
                    partition['dead_rows'] / partition['rows'] * 100 
                    if partition['rows'] > 0 else 0
                )
                
                print(f"    - {partition['name']}: "
                      f"{partition['rows']:,} rows, "
                      f"{partition['size']}, "
                      f"dead rows: {dead_ratio:.1f}%")
                      
        print("\n" + "="*80)


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터베이스 파티션 관리')
    parser.add_argument('command', choices=['create', 'drop', 'status', 'analyze', 'report'],
                        help='실행할 명령')
    parser.add_argument('--table', help='테이블 이름')
    parser.add_argument('--months', type=int, help='개월 수')
    
    args = parser.parse_args()
    
    manager = PartitionManager()
    
    if args.command == 'create':
        if not args.table:
            # 기본 테이블들에 대해 파티션 생성
            tables = ['market_orders', 'market_raw_data', 'job_executions']
            for table in tables:
                manager.create_monthly_partitions(table, args.months or 3)
        else:
            manager.create_monthly_partitions(args.table, args.months or 3)
            
    elif args.command == 'drop':
        if not args.table or not args.months:
            print("테이블 이름과 보관 개월 수를 지정하세요.")
            return
        manager.drop_old_partitions(args.table, args.months)
        
    elif args.command == 'status':
        status = manager.get_partition_status()
        for table in status:
            print(f"\n{table['parent_table']}: "
                  f"{table['partition_count']} 파티션, "
                  f"{table['total_rows']:,} rows, "
                  f"{table['total_size']}")
                  
    elif args.command == 'analyze':
        manager.analyze_partitions()
        
    elif args.command == 'report':
        manager.maintenance_report()


if __name__ == "__main__":
    main()