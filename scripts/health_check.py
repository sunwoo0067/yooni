#!/usr/bin/env python3
"""
헬스체크 스크립트: 시스템 상태를 확인하고 문제 발견시 알림
"""
import requests
import psycopg2
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수
SERVICES = {
    "frontend": "http://localhost:3000/api/health",
    "backend_ai": "http://localhost:8003/health",
    "mlflow": "http://localhost:5000/health",
    "nginx": "http://localhost/health"
}

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:1234@localhost:5434/yoonni')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:redis123@localhost:6379')

# 이메일 설정
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', '')

class HealthChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def check_services(self):
        """HTTP 서비스 확인"""
        for service_name, url in SERVICES.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: OK")
                else:
                    self.errors.append(f"{service_name}: HTTP {response.status_code}")
            except Exception as e:
                self.errors.append(f"{service_name}: {str(e)}")
                logger.error(f"❌ {service_name}: {str(e)}")
                
    def check_database(self):
        """데이터베이스 확인"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                # 연결 수 확인
                cur.execute("SELECT count(*) FROM pg_stat_activity")
                connection_count = cur.fetchone()[0]
                
                if connection_count > 100:
                    self.warnings.append(f"Database connections high: {connection_count}")
                    
                # 데이터베이스 크기 확인
                cur.execute("SELECT pg_database_size('yoonni')")
                db_size_bytes = cur.fetchone()[0]
                db_size_gb = db_size_bytes / 1024 / 1024 / 1024
                
                if db_size_gb > 50:
                    self.warnings.append(f"Database size large: {db_size_gb:.2f}GB")
                    
            conn.close()
            logger.info("✅ PostgreSQL: OK")
            
        except Exception as e:
            self.errors.append(f"PostgreSQL: {str(e)}")
            logger.error(f"❌ PostgreSQL: {str(e)}")
            
    def check_redis(self):
        """Redis 확인"""
        try:
            # Redis URL 파싱
            redis_url_parts = REDIS_URL.replace('redis://', '').split('@')
            password = redis_url_parts[0].split(':')[1] if ':' in redis_url_parts[0] else None
            host_port = redis_url_parts[1].split(':')
            
            r = redis.Redis(
                host=host_port[0],
                port=int(host_port[1]),
                password=password
            )
            
            info = r.info()
            memory_mb = info['used_memory'] / 1024 / 1024
            
            if memory_mb > 1024:  # 1GB 이상
                self.warnings.append(f"Redis memory high: {memory_mb:.2f}MB")
                
            logger.info("✅ Redis: OK")
            
        except Exception as e:
            self.errors.append(f"Redis: {str(e)}")
            logger.error(f"❌ Redis: {str(e)}")
            
    def check_disk_space(self):
        """디스크 공간 확인"""
        try:
            import shutil
            stat = shutil.disk_usage("/")
            percent_used = (stat.used / stat.total) * 100
            
            if percent_used > 90:
                self.errors.append(f"Disk space critical: {percent_used:.1f}% used")
            elif percent_used > 80:
                self.warnings.append(f"Disk space warning: {percent_used:.1f}% used")
                
            logger.info(f"✅ Disk space: {percent_used:.1f}% used")
            
        except Exception as e:
            self.warnings.append(f"Disk check failed: {str(e)}")
            
    def check_ai_models(self):
        """AI 모델 상태 확인"""
        try:
            response = requests.get("http://localhost:8003/api/ai/models/status", timeout=5)
            if response.status_code == 200:
                models = response.json()
                
                for model in models:
                    if model.get('status') != 'ready':
                        self.warnings.append(f"Model {model['name']} not ready: {model.get('status')}")
                        
                logger.info("✅ AI Models: OK")
            else:
                self.warnings.append("AI models status check failed")
                
        except Exception as e:
            self.warnings.append(f"AI models check failed: {str(e)}")
            
    def send_alert(self):
        """이메일 알림 발송"""
        if not (self.errors or self.warnings) or not ALERT_EMAIL_TO:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = ALERT_EMAIL_TO
            msg['Subject'] = f"[Yoonni] Health Check Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = "Yoonni 시스템 헬스체크 결과\n\n"
            
            if self.errors:
                body += "🚨 심각한 오류:\n"
                for error in self.errors:
                    body += f"  - {error}\n"
                body += "\n"
                
            if self.warnings:
                body += "⚠️ 경고:\n"
                for warning in self.warnings:
                    body += f"  - {warning}\n"
                    
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                
            logger.info("📧 Alert email sent")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            
    def run(self):
        """헬스체크 실행"""
        logger.info("🏥 Starting health check...")
        
        self.check_services()
        self.check_database()
        self.check_redis()
        self.check_disk_space()
        self.check_ai_models()
        
        # 결과 요약
        logger.info("\n📊 Health Check Summary:")
        logger.info(f"  Errors: {len(self.errors)}")
        logger.info(f"  Warnings: {len(self.warnings)}")
        
        # 알림 발송
        self.send_alert()
        
        # 종료 코드 반환
        if self.errors:
            return 2  # Critical
        elif self.warnings:
            return 1  # Warning
        else:
            return 0  # OK

if __name__ == "__main__":
    checker = HealthChecker()
    sys.exit(checker.run())