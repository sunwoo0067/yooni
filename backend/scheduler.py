#!/usr/bin/env python3
"""
스케줄러: 정기적인 작업 실행
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import schedule
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
import os
import aiohttp

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5434/yoonni')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:redis123@localhost:6379')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8003')

class Scheduler:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.setup_connections()
        
    def setup_connections(self):
        """데이터베이스 연결 설정"""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            
            redis_url_parts = REDIS_URL.replace('redis://', '').split('@')
            password = redis_url_parts[0].split(':')[1] if ':' in redis_url_parts[0] else None
            host_port = redis_url_parts[1].split(':')
            
            self.redis_client = redis.Redis(
                host=host_port[0],
                port=int(host_port[1]),
                password=password,
                decode_responses=True
            )
            
            logger.info("데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"연결 실패: {str(e)}")
            raise
            
    def run_collection_job(self):
        """수집 작업 실행"""
        try:
            logger.info("수집 작업 시작")
            
            # 활성화된 수집 스케줄 조회
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM collection_schedules 
                    WHERE is_active = true 
                    AND (next_run_at IS NULL OR next_run_at <= NOW())
                """)
                schedules = cursor.fetchall()
                
            for schedule in schedules:
                self._execute_collection(schedule)
                
        except Exception as e:
            logger.error(f"수집 작업 실패: {str(e)}")
            
    def _execute_collection(self, schedule: Dict[str, Any]):
        """개별 수집 실행"""
        try:
            supplier_id = schedule['supplier_id']
            collection_type = schedule['collection_type']
            
            logger.info(f"수집 시작: {supplier_id} - {collection_type}")
            
            # 수집 API 호출
            # 실제 구현에서는 비동기 작업 큐 사용
            asyncio.run(self._call_collection_api(supplier_id, collection_type))
            
            # 다음 실행 시간 업데이트
            next_run = datetime.now() + timedelta(hours=schedule['interval_hours'])
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE collection_schedules 
                    SET next_run_at = %s, last_run_at = NOW()
                    WHERE id = %s
                """, (next_run, schedule['id']))
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"수집 실행 실패: {str(e)}")
            
    async def _call_collection_api(self, supplier_id: int, collection_type: str):
        """수집 API 호출"""
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/api/suppliers/{supplier_id}/collect"
            data = {"collection_type": collection_type}
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"수집 API 호출 성공: {supplier_id}")
                else:
                    logger.error(f"수집 API 호출 실패: {response.status}")
                    
    def train_models_job(self):
        """AI 모델 재학습"""
        try:
            logger.info("모델 재학습 시작")
            
            # 재학습이 필요한 모델 확인
            models_to_train = [
                'sales_forecast',
                'churn_prediction',
                'price_optimization',
                'inventory_forecast'
            ]
            
            for model_name in models_to_train:
                asyncio.run(self._train_model(model_name))
                
        except Exception as e:
            logger.error(f"모델 재학습 실패: {str(e)}")
            
    async def _train_model(self, model_name: str):
        """개별 모델 학습"""
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/api/ai/models/{model_name}/train"
            
            async with session.post(url) as response:
                if response.status == 200:
                    logger.info(f"모델 학습 성공: {model_name}")
                else:
                    logger.error(f"모델 학습 실패: {model_name}")
                    
    def generate_reports_job(self):
        """일일 리포트 생성"""
        try:
            logger.info("일일 리포트 생성 시작")
            
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 일일 매출 집계
                cursor.execute("""
                    SELECT 
                        DATE(order_date) as date,
                        market_name,
                        COUNT(*) as order_count,
                        SUM(total_price) as total_sales
                    FROM market_orders
                    WHERE order_date >= CURRENT_DATE - INTERVAL '1 day'
                    GROUP BY DATE(order_date), market_name
                """)
                sales_data = cursor.fetchall()
                
                # Redis에 캐시
                cache_key = f"daily_report:{datetime.now().strftime('%Y%m%d')}"
                self.redis_client.setex(
                    cache_key,
                    86400,  # 24시간
                    json.dumps(sales_data, default=str)
                )
                
                logger.info(f"일일 리포트 생성 완료: {len(sales_data)}개 시장")
                
        except Exception as e:
            logger.error(f"리포트 생성 실패: {str(e)}")
            
    def cleanup_old_data_job(self):
        """오래된 데이터 정리"""
        try:
            logger.info("데이터 정리 작업 시작")
            
            with self.db_conn.cursor() as cursor:
                # 90일 이상 된 로그 삭제
                cursor.execute("""
                    DELETE FROM collection_logs 
                    WHERE created_at < CURRENT_DATE - INTERVAL '90 days'
                """)
                deleted_logs = cursor.rowcount
                
                # 180일 이상 된 원시 데이터 아카이브
                cursor.execute("""
                    INSERT INTO market_raw_data_archive 
                    SELECT * FROM market_raw_data 
                    WHERE created_at < CURRENT_DATE - INTERVAL '180 days'
                """)
                
                cursor.execute("""
                    DELETE FROM market_raw_data 
                    WHERE created_at < CURRENT_DATE - INTERVAL '180 days'
                """)
                archived_data = cursor.rowcount
                
                self.db_conn.commit()
                
                logger.info(f"데이터 정리 완료: {deleted_logs}개 로그 삭제, {archived_data}개 데이터 아카이브")
                
        except Exception as e:
            logger.error(f"데이터 정리 실패: {str(e)}")
            self.db_conn.rollback()
            
    def monitor_system_health(self):
        """시스템 헬스 모니터링"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "database": self._check_database_health(),
                "redis": self._check_redis_health(),
                "disk_usage": self._check_disk_usage(),
                "model_status": self._check_model_status()
            }
            
            # 이상 감지
            if any(status['status'] == 'critical' for status in health_status.values() if isinstance(status, dict)):
                logger.critical("시스템 이상 감지!")
                # 알림 발송 (이메일, 슬랙 등)
                
            # Redis에 상태 저장
            self.redis_client.setex(
                "system_health:latest",
                300,  # 5분
                json.dumps(health_status)
            )
            
        except Exception as e:
            logger.error(f"헬스 모니터링 실패: {str(e)}")
            
    def _check_database_health(self) -> Dict[str, Any]:
        """데이터베이스 상태 확인"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
                connection_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT pg_database_size('yoonni')")
                db_size = cursor.fetchone()[0]
                
            return {
                "status": "healthy" if connection_count < 100 else "warning",
                "connections": connection_count,
                "size_mb": db_size / 1024 / 1024
            }
        except:
            return {"status": "critical", "error": "Connection failed"}
            
    def _check_redis_health(self) -> Dict[str, Any]:
        """Redis 상태 확인"""
        try:
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "memory_mb": info['used_memory'] / 1024 / 1024,
                "connected_clients": info['connected_clients']
            }
        except:
            return {"status": "critical", "error": "Connection failed"}
            
    def _check_disk_usage(self) -> Dict[str, Any]:
        """디스크 사용량 확인"""
        import shutil
        
        try:
            usage = shutil.disk_usage("/")
            percent_used = (usage.used / usage.total) * 100
            
            return {
                "status": "healthy" if percent_used < 80 else "warning",
                "percent_used": percent_used,
                "free_gb": usage.free / 1024 / 1024 / 1024
            }
        except:
            return {"status": "unknown"}
            
    def _check_model_status(self) -> Dict[str, Any]:
        """AI 모델 상태 확인"""
        try:
            # MLflow에서 모델 상태 확인
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT model_id, status, updated_at 
                    FROM model_registry 
                    WHERE status = 'production'
                """)
                models = cursor.fetchall()
                
            outdated_models = [
                m for m in models 
                if (datetime.now() - m['updated_at']).days > 7
            ]
            
            return {
                "status": "warning" if outdated_models else "healthy",
                "active_models": len(models),
                "outdated_models": len(outdated_models)
            }
        except:
            return {"status": "unknown"}
            
    def run(self):
        """스케줄러 실행"""
        # 작업 스케줄 설정
        schedule.every(1).hours.do(self.run_collection_job)
        schedule.every().day.at("02:00").do(self.train_models_job)
        schedule.every().day.at("06:00").do(self.generate_reports_job)
        schedule.every().sunday.at("03:00").do(self.cleanup_old_data_job)
        schedule.every(5).minutes.do(self.monitor_system_health)
        
        logger.info("스케줄러 시작")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 확인
            except KeyboardInterrupt:
                logger.info("스케줄러 종료")
                break
            except Exception as e:
                logger.error(f"스케줄러 오류: {str(e)}")
                time.sleep(60)
                
if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.run()