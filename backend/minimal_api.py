#!/usr/bin/env python3
"""
Minimal API server for testing without ML dependencies
"""
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# 환경 변수
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:1234@localhost:5434/yoonni"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("Minimal API 서버 시작...")
    
    yield
    
    # 종료 시
    logger.info("Minimal API 서버 종료...")

# FastAPI 앱 생성
app = FastAPI(
    title="Yoonni Minimal API",
    description="E-commerce ERP System - Minimal API without ML dependencies",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Yoonni Minimal API Server",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "up",
            "database": "pending"  # DB 연결 테스트는 나중에 추가
        }
    }

@app.get("/api/products")
async def get_products():
    """상품 목록 조회 (더미 데이터)"""
    return {
        "products": [
            {
                "id": "PROD-001",
                "name": "샘플 상품 1",
                "price": 25000,
                "stock": 100,
                "vendor": "OwnerClan"
            },
            {
                "id": "PROD-002",
                "name": "샘플 상품 2",
                "price": 35000,
                "stock": 50,
                "vendor": "ZenTrade"
            }
        ],
        "total": 2,
        "page": 1,
        "limit": 10
    }

@app.get("/api/orders")
async def get_orders():
    """주문 목록 조회 (더미 데이터)"""
    return {
        "orders": [
            {
                "id": "ORD-001",
                "date": "2025-07-18",
                "customer": "김철수",
                "total": 50000,
                "status": "배송중"
            },
            {
                "id": "ORD-002",
                "date": "2025-07-17",
                "customer": "이영희",
                "total": 35000,
                "status": "완료"
            }
        ],
        "total": 2
    }

# 기본 에러 핸들러
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"예상치 못한 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "minimal_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )