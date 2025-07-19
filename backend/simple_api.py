#!/usr/bin/env python3
"""
간단한 AI API 서버 - 최소한의 의존성으로 테스트
"""
from fastapi import FastAPI, HTTPException
from datetime import datetime
import random

app = FastAPI(title="Yoonni AI Service", version="1.0.0")

# 인메모리 모델 상태 저장
models = {
    "sales_forecast": {
        "id": "sales_forecast_v1",
        "status": "ready",
        "version": "1.0",
        "last_updated": datetime.now().isoformat()
    },
    "churn_prediction": {
        "id": "churn_v1", 
        "status": "ready",
        "version": "1.0",
        "last_updated": datetime.now().isoformat()
    },
    "price_optimization": {
        "id": "price_opt_v1",
        "status": "ready", 
        "version": "1.0",
        "last_updated": datetime.now().isoformat()
    },
    "inventory_forecast": {
        "id": "inventory_v1",
        "status": "ready",
        "version": "1.0", 
        "last_updated": datetime.now().isoformat()
    }
}

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Yoonni AI Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "models": "/api/ai/models/status",
            "predict": "/api/ai/predict/{model_name}",
            "chatbot": "/api/ai/chatbot/message"
        }
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "up",
            "ml_models": "up"
        }
    }

@app.get("/api/ai/models/status")
async def get_models_status():
    """모델 상태 조회"""
    return list(models.values())

@app.post("/api/ai/predict/{model_name}")
async def predict(model_name: str, data: dict):
    """예측 실행"""
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    
    # 더미 예측 결과 생성
    if model_name == "sales_forecast":
        prediction = {
            "forecast": [random.randint(100000, 500000) for _ in range(7)],
            "dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", 
                     "2024-01-05", "2024-01-06", "2024-01-07"],
            "confidence": 0.85
        }
    elif model_name == "churn_prediction":
        prediction = {
            "churn_probability": random.random(),
            "risk_level": random.choice(["low", "medium", "high"]),
            "reasons": ["최근 구매 감소", "고객 문의 증가"]
        }
    elif model_name == "price_optimization":
        prediction = {
            "optimal_price": round(data.get("current_price", 10000) * random.uniform(0.9, 1.1), 0),
            "expected_revenue_increase": f"{random.randint(5, 15)}%",
            "recommendation": "가격 인상 권장"
        }
    else:
        prediction = {
            "result": "prediction_result",
            "confidence": random.random()
        }
    
    return {
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction
    }

@app.post("/api/ai/chatbot/message")
async def chatbot_message(message: dict):
    """챗봇 메시지 처리"""
    user_message = message.get("message", "")
    
    # 간단한 응답 생성
    responses = [
        "안녕하세요! 무엇을 도와드릴까요?",
        "주문 관련 문의이신가요? 자세한 내용을 말씀해 주세요.",
        "재고 확인을 도와드리겠습니다.",
        "가격 정보를 안내해 드리겠습니다."
    ]
    
    return {
        "response": random.choice(responses),
        "intent": "general_inquiry",
        "confidence": 0.9,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/ai/models/{model_name}/train")
async def train_model(model_name: str):
    """모델 학습"""
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    
    models[model_name]["status"] = "training"
    
    return {
        "model": model_name,
        "status": "training_started",
        "message": f"Model {model_name} training initiated",
        "estimated_time": "30 minutes"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)