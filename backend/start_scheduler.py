#!/usr/bin/env python3
"""
스케줄러 시작 스크립트
"""
import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from scheduler.scheduler_manager import SchedulerManager


def main():
    """스케줄러 메인 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("="*50)
        logger.info("ERP 자동화 스케줄러 시작")
        logger.info("="*50)
        
        # 스케줄러 매니저 생성 및 시작
        scheduler = SchedulerManager()
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"스케줄러 오류: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("스케줄러 종료")


if __name__ == "__main__":
    main()