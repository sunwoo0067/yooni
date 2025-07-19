#!/usr/bin/env python3
"""
AI 서비스 API
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.analytics_engine import AIAnalyticsEngine
from ai.recommendation_engine import RecommendationEngine
from core import get_logger
from db.connection_pool import init_database_pool, get_database_pool
from core.error_handlers import (
    global_exception_handler, 
    retry_on_exception,
    APIError,
    ValidationError,
    NotFoundError,
    DatabaseError
)

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="AI Business Intelligence API")

# 전역 예외 핸들러 등록
app.add_exception_handler(Exception, global_exception_handler)

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
    'password': '1234',
    'min_connections': 2,
    'max_connections': 10,
    'connect_timeout': 10
}

# 데이터베이스 풀 초기화
db_pool = init_database_pool(DB_CONFIG)

# AI 엔진 초기화
analytics_engine = AIAnalyticsEngine(DB_CONFIG)
recommendation_engine = RecommendationEngine(DB_CONFIG)


# Request/Response 모델
class TrainModelsRequest(BaseModel):
    model_types: Optional[List[str]] = ["sales_prediction", "anomaly_detection"]


class SalesPredictionRequest(BaseModel):
    product_id: Optional[int] = None
    days: int = 7


class AnomalyDetectionRequest(BaseModel):
    data_type: str = "sales"
    threshold: Optional[float] = None


class RecommendationRequest(BaseModel):
    recommendation_type: str  # similar, cross_sell, personalized, trending, bundle
    product_id: Optional[int] = None
    product_ids: Optional[List[int]] = None
    customer_id: Optional[str] = None
    n: int = 5


@app.on_event("startup")
async def startup_event():
    """API 서버 시작 시 실행"""
    logger.info("AI Business Intelligence API 시작")
    
    # 추천 엔진 특성 행렬 구축
    try:
        recommendation_engine.build_product_features()
        logger.info("추천 엔진 초기화 완료")
    except Exception as e:
        logger.error(f"추천 엔진 초기화 실패: {e}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "AI Business Intelligence",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/train-models")
async def train_models(request: TrainModelsRequest, background_tasks: BackgroundTasks):
    """
AI 모델 학습
    """
    logger.info(f"AI 모델 학습 요청: {request.model_types}")
    
    # 백그라운드에서 학습 실행
    background_tasks.add_task(analytics_engine.train_models)
    
    return {
        "message": "AI 모델 학습이 시작되었습니다",
        "models": request.model_types,
        "status": "training_started"
    }


@app.post("/predict/sales")
@retry_on_exception(max_attempts=3, delay=0.5, exceptions=(DatabaseError,), logger=logger)
async def predict_sales(request: SalesPredictionRequest):
    """매출 예측"""
    try:
        # 입력 검증
        if request.days <= 0:
            raise ValidationError("예측 일수는 1 이상이어야 합니다.", field="days")
        
        if request.days > 365:
            raise ValidationError("예측 일수는 365일을 초과할 수 없습니다.", field="days")
        
        predictions = analytics_engine.predict_sales(
            product_id=request.product_id,
            days=request.days
        )
        
        if "error" in predictions:
            raise APIError(predictions["error"], status_code=400, error_code="PREDICTION_ERROR")
        
        return {
            "status": "success",
            "data": predictions,
            "metadata": {
                "product_id": request.product_id,
                "prediction_days": request.days,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"매출 예측 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/anomalies")
async def detect_anomalies(request: AnomalyDetectionRequest):
    """이상치 탐지"""
    try:
        anomalies = analytics_engine.detect_anomalies(
            data_type=request.data_type
        )
        
        if "error" in anomalies:
            raise HTTPException(status_code=400, detail=anomalies["error"])
        
        return anomalies
        
    except Exception as e:
        logger.error(f"이상치 탐지 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insights")
async def get_insights():
    """비즈니스 인사이트 조회"""
    try:
        insights = analytics_engine.get_insights()
        return insights
        
    except Exception as e:
        logger.error(f"인사이트 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """상품 추천"""
    try:
        recommendations = []
        
        if request.recommendation_type == "similar":
            if not request.product_id:
                raise HTTPException(status_code=400, detail="product_id가 필요합니다")
            recommendations = recommendation_engine.get_similar_products(
                request.product_id, n=request.n
            )
            
        elif request.recommendation_type == "cross_sell":
            if not request.product_ids:
                raise HTTPException(status_code=400, detail="product_ids가 필요합니다")
            recommendations = recommendation_engine.get_cross_sell_recommendations(
                request.product_ids, n=request.n
            )
            
        elif request.recommendation_type == "personalized":
            if not request.customer_id:
                raise HTTPException(status_code=400, detail="customer_id가 필요합니다")
            recommendations = recommendation_engine.get_personalized_recommendations(
                request.customer_id, n=request.n
            )
            
        elif request.recommendation_type == "trending":
            recommendations = recommendation_engine.get_trending_products(
                n=request.n
            )
            
        elif request.recommendation_type == "bundle":
            if not request.product_id:
                raise HTTPException(status_code=400, detail="product_id가 필요합니다")
            recommendations = recommendation_engine.get_bundle_recommendations(
                request.product_id, n=request.n
            )
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"지원되지 않는 추천 타입: {request.recommendation_type}"
            )
        
        return {
            "recommendation_type": request.recommendation_type,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"추천 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/status")
async def get_model_status():
    """모델 상태 확인"""
    return {
        "sales_prediction": {
            "is_trained": analytics_engine.sales_model.is_trained,
            "last_updated": None  # TODO: 모델 업데이트 시간 추적
        },
        "anomaly_detection": {
            "is_trained": analytics_engine.anomaly_model.is_trained,
            "last_updated": None
        },
        "recommendation_engine": {
            "is_initialized": recommendation_engine.similarity_matrix is not None,
            "product_count": len(recommendation_engine.product_features) if recommendation_engine.product_features is not None else 0
        }
    }


@app.post("/rebuild-recommendations")
async def rebuild_recommendations(background_tasks: BackgroundTasks):
    """추천 시스템 재구축"""
    background_tasks.add_task(recommendation_engine.build_product_features)
    
    return {
        "message": "추천 시스템 재구축이 시작되었습니다",
        "status": "rebuilding_started"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ai_service:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )