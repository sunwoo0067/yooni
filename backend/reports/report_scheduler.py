#!/usr/bin/env python3
"""
리포트 스케줄러
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import logging
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ReportScheduler:
    """
    예약된 리포트 생성 및 전송을 관리하는 클래스
    """
    
    def __init__(self, db_config: Dict[str, Any], smtp_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config
        self.smtp_config = smtp_config
        self.report_generator = ReportGenerator(db_config)
        self.schedules = []
        self.running = False
        self.thread = None
        
        # 스케줄 저장 경로
        self.schedule_file = "reports/schedules.json"
        self.load_schedules()
    
    def add_schedule(self, name: str, report_type: str, schedule_time: str, 
                    frequency: str, recipients: List[str], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        리포트 스케줄 추가
        
        Args:
            name: 스케줄 이름
            report_type: 리포트 타입 (sales, inventory, customer 등)
            schedule_time: 실행 시간 (HH:MM 형식)
            frequency: 빈도 (daily, weekly, monthly)
            recipients: 수신자 이메일 목록
            params: 리포트 파라미터
        """
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_schedule = {
            'id': schedule_id,
            'name': name,
            'report_type': report_type,
            'schedule_time': schedule_time,
            'frequency': frequency,
            'recipients': recipients,
            'params': params,
            'created_at': datetime.now().isoformat(),
            'enabled': True,
            'last_run': None,
            'next_run': self._calculate_next_run(schedule_time, frequency)
        }
        
        self.schedules.append(new_schedule)
        self.save_schedules()
        self._setup_schedule(new_schedule)
        
        logger.info(f"새 스케줄 추가: {name}")
        return new_schedule
    
    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """스케줄 업데이트"""
        for i, schedule in enumerate(self.schedules):
            if schedule['id'] == schedule_id:
                self.schedules[i].update(updates)
                if 'schedule_time' in updates or 'frequency' in updates:
                    self.schedules[i]['next_run'] = self._calculate_next_run(
                        self.schedules[i]['schedule_time'],
                        self.schedules[i]['frequency']
                    )
                self.save_schedules()
                self._reschedule_all()
                return self.schedules[i]
        return None
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """스케줄 삭제"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.save_schedules()
        self._reschedule_all()
        return True
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """모든 스케줄 조회"""
        return self.schedules
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """특정 스케줄 조회"""
        for schedule in self.schedules:
            if schedule['id'] == schedule_id:
                return schedule
        return None
    
    def run_schedule_now(self, schedule_id: str) -> bool:
        """스케줄 즉시 실행"""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            self._run_report(schedule)
            return True
        return False
    
    def start(self):
        """스케줄러 시작"""
        if not self.running:
            self.running = True
            self._setup_all_schedules()
            self.thread = threading.Thread(target=self._run_scheduler)
            self.thread.daemon = True
            self.thread.start()
            logger.info("리포트 스케줄러 시작")
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("리포트 스케줄러 중지")
    
    def _run_scheduler(self):
        """스케줄러 실행 루프"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    
    def _setup_all_schedules(self):
        """모든 스케줄 설정"""
        schedule.clear()  # 기존 스케줄 클리어
        for sched in self.schedules:
            if sched['enabled']:
                self._setup_schedule(sched)
    
    def _setup_schedule(self, sched: Dict[str, Any]):
        """개별 스케줄 설정"""
        job_func = lambda: self._run_report(sched)
        
        if sched['frequency'] == 'daily':
            schedule.every().day.at(sched['schedule_time']).do(job_func)
        elif sched['frequency'] == 'weekly':
            # 매주 월요일 실행
            schedule.every().monday.at(sched['schedule_time']).do(job_func)
        elif sched['frequency'] == 'monthly':
            # 매월 1일 실행
            schedule.every().day.at(sched['schedule_time']).do(
                lambda: self._run_monthly_report(sched)
            )
    
    def _run_monthly_report(self, sched: Dict[str, Any]):
        """월간 리포트 실행 (매월 1일만 실행)"""
        if datetime.now().day == 1:
            self._run_report(sched)
    
    def _reschedule_all(self):
        """모든 스케줄 재설정"""
        if self.running:
            self._setup_all_schedules()
    
    def _run_report(self, schedule: Dict[str, Any]):
        """리포트 실행"""
        try:
            logger.info(f"리포트 실행 시작: {schedule['name']}")
            
            # 파라미터 준비
            params = schedule['params'].copy()
            
            # 기간 파라미터 자동 계산
            if 'start_date' not in params or 'end_date' not in params:
                if schedule['frequency'] == 'daily':
                    params['start_date'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    params['end_date'] = params['start_date']
                elif schedule['frequency'] == 'weekly':
                    params['end_date'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    params['start_date'] = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                elif schedule['frequency'] == 'monthly':
                    params['end_date'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    params['start_date'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # 리포트 생성
            report_path = None
            if schedule['report_type'] == 'sales':
                report_path = self.report_generator.generate_sales_report(
                    start_date=params['start_date'],
                    end_date=params['end_date'],
                    format=params.get('format', 'pdf'),
                    include_charts=params.get('include_charts', True)
                )
            elif schedule['report_type'] == 'inventory':
                report_path = self.report_generator.generate_inventory_report(
                    format=params.get('format', 'pdf')
                )
            elif schedule['report_type'] == 'customer':
                report_path = self.report_generator.generate_customer_report(
                    start_date=params['start_date'],
                    end_date=params['end_date'],
                    format=params.get('format', 'pdf')
                )
            
            if report_path and os.path.exists(report_path):
                # 이메일 전송
                if schedule['recipients'] and self.smtp_config:
                    self._send_report_email(
                        report_path=report_path,
                        recipients=schedule['recipients'],
                        schedule_name=schedule['name']
                    )
                
                # 실행 기록 업데이트
                for i, s in enumerate(self.schedules):
                    if s['id'] == schedule['id']:
                        self.schedules[i]['last_run'] = datetime.now().isoformat()
                        self.schedules[i]['next_run'] = self._calculate_next_run(
                            s['schedule_time'], s['frequency']
                        )
                        break
                
                self.save_schedules()
                
                # 실행 기록 DB 저장
                self._save_execution_log(schedule['id'], 'success', report_path)
                
                logger.info(f"리포트 실행 완료: {schedule['name']}")
            else:
                raise Exception("리포트 생성 실패")
                
        except Exception as e:
            logger.error(f"리포트 실행 실패: {schedule['name']} - {str(e)}")
            self._save_execution_log(schedule['id'], 'failed', error=str(e))
    
    def _send_report_email(self, report_path: str, recipients: List[str], schedule_name: str):
        """리포트 이메일 전송"""
        if not self.smtp_config:
            logger.warning("SMTP 설정이 없어 이메일을 전송할 수 없습니다")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['sender_email']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[정기 리포트] {schedule_name} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # 본문
            body = f"""
안녕하세요,

{schedule_name} 리포트를 전달드립니다.

생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
첨부 파일: {os.path.basename(report_path)}

감사합니다.
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 첨부 파일
            with open(report_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(report_path)}'
            )
            msg.attach(part)
            
            # 이메일 전송
            with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            logger.info(f"리포트 이메일 전송 완료: {recipients}")
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {str(e)}")
    
    def _calculate_next_run(self, schedule_time: str, frequency: str) -> str:
        """다음 실행 시간 계산"""
        hour, minute = map(int, schedule_time.split(':'))
        now = datetime.now()
        
        if frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == 'weekly':
            # 다음 월요일
            days_ahead = 0 - now.weekday()  # 월요일은 0
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        elif frequency == 'monthly':
            # 다음 달 1일
            if now.day > 1 or (now.day == 1 and now.hour >= hour):
                if now.month == 12:
                    next_run = datetime(now.year + 1, 1, 1, hour, minute)
                else:
                    next_run = datetime(now.year, now.month + 1, 1, hour, minute)
            else:
                next_run = datetime(now.year, now.month, 1, hour, minute)
        
        return next_run.isoformat()
    
    def _save_execution_log(self, schedule_id: str, status: str, report_path: str = None, error: str = None):
        """실행 로그 저장"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_execution_logs (
                id SERIAL PRIMARY KEY,
                schedule_id VARCHAR(50),
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                report_path TEXT,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO report_execution_logs (schedule_id, status, report_path, error_message)
            VALUES (%s, %s, %s, %s)
        """, (schedule_id, status, report_path, error))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def load_schedules(self):
        """스케줄 로드"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    self.schedules = json.load(f)
                logger.info(f"{len(self.schedules)}개의 스케줄 로드 완료")
            except Exception as e:
                logger.error(f"스케줄 로드 실패: {e}")
                self.schedules = []
        else:
            self.schedules = []
    
    def save_schedules(self):
        """스케줄 저장"""
        os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedules, f, ensure_ascii=False, indent=2)