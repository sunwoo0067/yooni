#!/usr/bin/env python3
"""
스케줄러 실행 스크립트 (데몬 모드)
"""

import os
import sys
import logging
import signal
import time
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.info(f"시그널 {signum} 받음. 종료 중...")
    sys.exit(0)

def main():
    """메인 실행 함수"""
    logger.info("🚀 상품 수집 스케줄러 시작")
    logger.info(f"PID: {os.getpid()}")
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 현재 디렉토리를 Python 경로에 추가
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from scheduler import SupplierCollectionScheduler
        
        # 스케줄러 생성 및 시작
        scheduler = SupplierCollectionScheduler()
        
        logger.info("✅ 스케줄러 초기화 완료")
        logger.info(f"📋 등록된 공급사: {list(scheduler.supplier_configs.keys())}")
        
        # 스케줄러 시작
        scheduler.start()
        
    except Exception as e:
        logger.error(f"스케줄러 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # PID 파일 생성
    pid_file = 'scheduler.pid'
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    try:
        main()
    finally:
        # PID 파일 삭제
        if os.path.exists(pid_file):
            os.remove(pid_file)