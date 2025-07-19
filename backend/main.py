#!/usr/bin/env python3
"""
통합 AI/ML API 서버
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 환경 변수
from dotenv import load_dotenv
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AI 모듈 임포트
from ai.advanced.chatbot_api import app as chatbot_app
from ai.advanced.model_manager import ModelManager

# 데이터베이스 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:1234@localhost:5434/yoonni"
)

# 전역 객체
model_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global model_manager
    
    # 시작 시
    logger.info("AI/ML 서버 시작...")
    
    # 모델 매니저 초기화
    model_manager = ModelManager({
        'registry_path': './model_registry',
        'tracking_uri': './mlruns',
        'email_alerts': False
    })
    
    # 챗봇 데이터베이스 초기화
    try:
        from ai.advanced.nlp_chatbot import chatbot
        await chatbot.initialize_database(DATABASE_URL)
        logger.info("챗봇 데이터베이스 연결 완료")
    except Exception as e:
        logger.error(f"챗봇 데이터베이스 연결 실패: {e}")
    
    yield
    
    # 종료 시
    logger.info("AI/ML 서버 종료...")


# FastAPI 앱 생성
app = FastAPI(
    title="Yooni AI/ML API",
    version="1.0.0",
    description="통합 AI/ML 서비스 API",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 챗봇 라우터 마운트
app.mount("/chatbot", chatbot_app)


# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트"""
    return {
        "service": "Yooni AI/ML API",
        "version": "1.0.0",
        "endpoints": {
            "chatbot": "/chatbot/docs",
            "models": "/api/models",
            "predictions": "/api/predict",
            "monitoring": "/api/monitoring",
            "health": "/health"
        }
    }


# 헬스체크
@app.get("/health")
async def health_check():
    """서비스 헬스체크"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "unknown",
            "ml_models": "up" if model_manager else "down"
        }
    }
    
    # 데이터베이스 체크
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        health_status["services"]["database"] = "up"
    except Exception as e:
        health_status["services"]["database"] = "down"
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")
    
    return health_status


# 모델 관리 API
@app.get("/api/models")
async def list_models():
    """등록된 모델 목록"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    models = model_manager.registry.list_models()
    return {"models": models, "total": len(models)}


@app.post("/api/models/train")
async def train_model(request: Dict[str, Any]):
    """새 모델 학습"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    try:
        model_id = request.get("model_id")
        model_type = request.get("model_type", "classification")
        params = request.get("params", {})
        
        version = await model_manager.train_and_register_model(
            model_id=model_id,
            model_type=model_type,
            train_data=None,  # 실제로는 데이터 로드
            params=params
        )
        
        return {
            "model_id": model_id,
            "version": version,
            "status": "training_started"
        }
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/deploy")
async def deploy_model(request: Dict[str, Any]):
    """모델 배포"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    try:
        model_id = request.get("model_id")
        version = request.get("version")
        config = request.get("config", {})
        
        deployment = await model_manager.deploy_model(
            model_id=model_id,
            version=version,
            config=config
        )
        
        return deployment
    except Exception as e:
        logger.error(f"Model deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 예측 API
@app.post("/api/predict/{model_id}")
async def predict(model_id: str, request: Dict[str, Any]):
    """모델 예측"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    try:
        # 모델 로드
        model_version = model_manager.registry.get_model(model_id)
        
        # 예측 수행 (시뮬레이션)
        prediction = {
            "model_id": model_id,
            "version": model_version.version,
            "prediction": "시뮬레이션 예측 결과",
            "confidence": 0.95
        }
        
        return prediction
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 모니터링 API
@app.get("/api/monitoring/{model_id}")
async def get_monitoring_data(model_id: str, hours: int = 24):
    """모델 모니터링 데이터"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    report = model_manager.monitor.get_monitoring_report(model_id, hours)
    return report


# 시계열 예측 API
@app.post("/api/forecast/sales")
async def forecast_sales(request: Dict[str, Any]):
    """매출 예측"""
    try:
        from ai.advanced.time_series_models import ProphetModel
        
        # 데이터 로드 (실제로는 DB에서)
        days_ahead = request.get("days_ahead", 7)
        
        # Prophet 모델 사용
        model = ProphetModel()
        
        # 예측 (시뮬레이션)
        forecast = {
            "forecast_days": days_ahead,
            "predictions": [
                {"date": f"2024-01-{20+i}", "sales": 1000000 + i * 50000}
                for i in range(days_ahead)
            ],
            "confidence_interval": {
                "lower": 900000,
                "upper": 1200000
            }
        }
        
        return forecast
    except Exception as e:
        logger.error(f"Sales forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 고객 이탈 예측 API
@app.post("/api/predict/churn")
async def predict_churn(request: Dict[str, Any]):
    """고객 이탈 예측"""
    try:
        customer_ids = request.get("customer_ids", [])
        
        # 예측 (시뮬레이션)
        predictions = []
        for customer_id in customer_ids:
            predictions.append({
                "customer_id": customer_id,
                "churn_probability": 0.15,
                "risk_level": "low",
                "retention_actions": [
                    "Send promotional email",
                    "Offer loyalty points"
                ]
            })
        
        return {"predictions": predictions}
    except Exception as e:
        logger.error(f"Churn prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 가격 최적화 API
@app.post("/api/optimize/price")
async def optimize_price(request: Dict[str, Any]):
    """가격 최적화"""
    try:
        product_id = request.get("product_id")
        current_price = request.get("current_price", 10000)
        optimization_goal = request.get("goal", "profit_maximization")
        
        # 최적화 (시뮬레이션)
        result = {
            "product_id": product_id,
            "current_price": current_price,
            "optimal_price": current_price * 1.1,
            "expected_profit_increase": "15%",
            "confidence": 0.85
        }
        
        return result
    except Exception as e:
        logger.error(f"Price optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 재고 최적화 API
@app.post("/api/optimize/inventory")
async def optimize_inventory(request: Dict[str, Any]):
    """재고 최적화"""
    try:
        from ai.advanced.inventory_ai import InventoryAI
        
        product_id = request.get("product_id")
        current_stock = request.get("current_stock", 100)
        
        # 재고 AI 초기화
        inventory_ai = InventoryAI()
        
        # 재주문 필요 여부 확인
        needs_reorder, info = inventory_ai.check_reorder_needed(
            product_id, current_stock
        )
        
        result = {
            "product_id": product_id,
            "current_stock": current_stock,
            "needs_reorder": needs_reorder,
            "recommended_order_quantity": info.get("recommended_quantity", 0),
            "urgency_score": info.get("urgency_score", 0)
        }
        
        return result
    except Exception as e:
        logger.error(f"Inventory optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 에러 핸들러"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )