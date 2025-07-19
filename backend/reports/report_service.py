#!/usr/bin/env python3
"""
리포트 서비스 API
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reports.report_generator import ReportGenerator
from reports.report_scheduler import ReportScheduler
from reports.report_templates import ReportTemplate
from core import get_logger

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Advanced Reporting System API")

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

# SMTP 설정 (환경변수에서 로드)
SMTP_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'username': os.getenv('SMTP_USERNAME'),
    'password': os.getenv('SMTP_PASSWORD'),
    'use_tls': True
}

# 서비스 초기화
report_generator = ReportGenerator(DB_CONFIG)
report_scheduler = ReportScheduler(DB_CONFIG, SMTP_CONFIG if SMTP_CONFIG['sender_email'] else None)
report_templates = ReportTemplate(DB_CONFIG)

# Request/Response 모델
class GenerateReportRequest(BaseModel):
    report_type: str  # sales, inventory, customer
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    format: str = 'pdf'  # pdf, excel, html
    include_charts: bool = True
    template_id: Optional[int] = None


class CreateScheduleRequest(BaseModel):
    name: str
    report_type: str
    schedule_time: str  # HH:MM
    frequency: str  # daily, weekly, monthly
    recipients: List[str]
    params: Dict[str, Any]


class UpdateScheduleRequest(BaseModel):
    name: Optional[str] = None
    schedule_time: Optional[str] = None
    frequency: Optional[str] = None
    recipients: Optional[List[str]] = None
    params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class CreateTemplateRequest(BaseModel):
    name: str
    template_type: str
    config: Dict[str, Any]
    description: Optional[str] = None
    created_by: Optional[str] = None


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """API 서버 시작 시 실행"""
    logger.info("고급 리포팅 시스템 API 시작")
    report_scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """API 서버 종료 시 실행"""
    report_scheduler.stop()
    logger.info("고급 리포팅 시스템 API 종료")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "Advanced Reporting System",
        "timestamp": datetime.now().isoformat()
    }


# 리포트 생성 엔드포인트
@app.post("/reports/generate")
async def generate_report(request: GenerateReportRequest):
    """리포트 생성"""
    try:
        report_path = None
        
        if request.report_type == 'sales':
            if not request.start_date or not request.end_date:
                raise HTTPException(status_code=400, detail="매출 리포트는 시작일과 종료일이 필요합니다")
            
            report_path = report_generator.generate_sales_report(
                start_date=request.start_date,
                end_date=request.end_date,
                format=request.format,
                include_charts=request.include_charts
            )
            
        elif request.report_type == 'inventory':
            report_path = report_generator.generate_inventory_report(
                format=request.format
            )
            
        elif request.report_type == 'customer':
            if not request.start_date or not request.end_date:
                raise HTTPException(status_code=400, detail="고객 리포트는 시작일과 종료일이 필요합니다")
            
            report_path = report_generator.generate_customer_report(
                start_date=request.start_date,
                end_date=request.end_date,
                format=request.format
            )
        else:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 리포트 타입: {request.report_type}")
        
        if report_path and os.path.exists(report_path):
            return {
                "success": True,
                "report_path": report_path,
                "filename": os.path.basename(report_path),
                "format": request.format,
                "size": os.path.getsize(report_path)
            }
        else:
            raise HTTPException(status_code=500, detail="리포트 생성 실패")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"리포트 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/download/{filename}")
async def download_report(filename: str):
    """리포트 다운로드"""
    file_path = os.path.join(report_generator.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


# 스케줄 관리 엔드포인트
@app.get("/schedules")
async def list_schedules():
    """스케줄 목록 조회"""
    return {
        "schedules": report_scheduler.get_schedules(),
        "count": len(report_scheduler.get_schedules())
    }


@app.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    """스케줄 상세 조회"""
    schedule = report_scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")
    return schedule


@app.post("/schedules")
async def create_schedule(request: CreateScheduleRequest):
    """스케줄 생성"""
    try:
        schedule = report_scheduler.add_schedule(
            name=request.name,
            report_type=request.report_type,
            schedule_time=request.schedule_time,
            frequency=request.frequency,
            recipients=request.recipients,
            params=request.params
        )
        return schedule
    except Exception as e:
        logger.error(f"스케줄 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, request: UpdateScheduleRequest):
    """스케줄 업데이트"""
    updates = request.dict(exclude_unset=True)
    schedule = report_scheduler.update_schedule(schedule_id, updates)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")
    
    return schedule


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """스케줄 삭제"""
    success = report_scheduler.delete_schedule(schedule_id)
    return {"success": success}


@app.post("/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: str, background_tasks: BackgroundTasks):
    """스케줄 즉시 실행"""
    schedule = report_scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")
    
    background_tasks.add_task(report_scheduler.run_schedule_now, schedule_id)
    
    return {
        "message": "스케줄 실행이 시작되었습니다",
        "schedule_id": schedule_id
    }


# 템플릿 관리 엔드포인트
@app.get("/templates")
async def list_templates(template_type: Optional[str] = None):
    """템플릿 목록 조회"""
    templates = report_templates.list_templates(template_type)
    return {
        "templates": templates,
        "count": len(templates),
        "default_templates": report_templates.get_default_templates()
    }


@app.get("/templates/{template_id}")
async def get_template(template_id: int):
    """템플릿 상세 조회"""
    template = report_templates.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    return template


@app.post("/templates")
async def create_template(request: CreateTemplateRequest):
    """템플릿 생성"""
    try:
        # 템플릿 검증
        validation = report_templates.validate_template(request.config)
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "템플릿 검증 실패",
                    "errors": validation['errors'],
                    "warnings": validation['warnings']
                }
            )
        
        template_id = report_templates.create_template(
            name=request.name,
            template_type=request.template_type,
            config=request.config,
            description=request.description,
            created_by=request.created_by
        )
        
        return {
            "template_id": template_id,
            "message": "템플릿이 생성되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/templates/{template_id}")
async def update_template(template_id: int, request: UpdateTemplateRequest):
    """템플릿 업데이트"""
    updates = request.dict(exclude_unset=True)
    
    # config 업데이트 시 검증
    if 'config' in updates:
        validation = report_templates.validate_template(updates['config'])
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "템플릿 검증 실패",
                    "errors": validation['errors'],
                    "warnings": validation['warnings']
                }
            )
    
    success = report_templates.update_template(template_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    return {"success": success}


@app.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """템플릿 삭제"""
    success = report_templates.delete_template(template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    return {"success": success}


@app.post("/templates/validate")
async def validate_template(config: Dict[str, Any]):
    """템플릿 구성 검증"""
    validation = report_templates.validate_template(config)
    return validation


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "report_service:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    )