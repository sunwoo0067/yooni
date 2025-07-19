#!/usr/bin/env python3
"""
워크플로우 실행 API 서버
"""
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys

sys.path.append('/home/sunwoo/yooni/backend')
from workflow.engine import WorkflowEngine
from workflow.event_manager import EventManager
from workflow.scheduler import WorkflowScheduler
from core import get_logger

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="워크플로우 실행 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni',
    'user': 'postgres',
    'password': '1234'
}

# 전역 인스턴스
workflow_engine = WorkflowEngine(DB_CONFIG)
event_manager = EventManager(DB_CONFIG)
workflow_scheduler = WorkflowScheduler(DB_CONFIG)


class WorkflowExecuteRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow_id: int
    trigger_data: Dict[str, Any] = {}


class EventEmitRequest(BaseModel):
    """이벤트 발행 요청"""
    event_type: str
    event_source: str
    data: Dict[str, Any] = {}


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("워크플로우 API 서버 시작")
    
    # 이벤트 매니저 시작
    event_manager.start()
    
    # 스케줄러 시작
    await workflow_scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("워크플로우 API 서버 종료")
    
    # 이벤트 매니저 중지
    event_manager.stop()
    
    # 스케줄러 중지
    workflow_scheduler.stop()


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


@app.post("/execute-workflow")
async def execute_workflow(request: WorkflowExecuteRequest):
    """워크플로우 실행"""
    try:
        logger.info(f"워크플로우 실행 요청: {request.workflow_id}")
        
        # 트리거 데이터에 소스 추가
        trigger_data = request.trigger_data
        if 'source' not in trigger_data:
            trigger_data['source'] = 'api'
        
        # 워크플로우 실행
        result = await workflow_engine.execute_workflow(
            request.workflow_id,
            trigger_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"워크플로우 실행 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/emit-event")
async def emit_event(request: EventEmitRequest):
    """이벤트 발행"""
    try:
        logger.info(f"이벤트 발행: {request.event_type} from {request.event_source}")
        
        await event_manager.emit_event(
            request.event_type,
            request.event_source,
            request.data
        )
        
        return {
            "success": True,
            "message": "이벤트가 발행되었습니다",
            "event_type": request.event_type,
            "event_source": request.event_source
        }
        
    except Exception as e:
        logger.error(f"이벤트 발행 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduled-jobs")
async def get_scheduled_jobs():
    """스케줄된 작업 목록 조회"""
    try:
        jobs = workflow_scheduler.get_scheduled_jobs()
        return {"jobs": jobs}
        
    except Exception as e:
        logger.error(f"스케줄 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 서버 실행
    uvicorn.run(
        "workflow_api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )