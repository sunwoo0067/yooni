# API Reference

## API Endpoints

### AI Service (http://localhost:8003)
- `GET /` - Service info
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /api/ai/models/status` - Model status
- `POST /api/ai/predict/{model_name}` - Run prediction
- `POST /api/ai/chatbot/message` - Chatbot interaction
- `POST /api/ai/models/{model_name}/train` - Trigger training

### Marketplace APIs
- **Coupang**: HMAC-SHA256 auth, multi-account via accounts.json
- **OwnerClan**: GraphQL with JWT, rate limit 1000 req/s
- **ZenTrade**: Session-based authentication

## API Request/Response Examples

### 1. Sales Forecast
**Request:**
```bash
POST /api/ai/predict/sales_forecast
Content-Type: application/json

{
  "product_id": "PROD123",
  "period": "weekly",
  "history_days": 30
}
```

**Response:**
```json
{
  "model": "sales_forecast",
  "timestamp": "2024-01-15T10:30:00",
  "prediction": {
    "forecast": [120000, 135000, 142000, 138000, 145000, 150000, 148000],
    "dates": ["2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19", "2024-01-20", "2024-01-21", "2024-01-22"],
    "confidence": 0.85,
    "trend": "upward",
    "seasonality": "weekly_pattern_detected"
  }
}
```

### 2. Customer Churn Prediction
**Request:**
```bash
POST /api/ai/predict/churn_prediction
Content-Type: application/json

{
  "customer_id": "CUST456",
  "include_features": true
}
```

**Response:**
```json
{
  "model": "churn_prediction",
  "timestamp": "2024-01-15T10:32:00",
  "prediction": {
    "churn_probability": 0.73,
    "risk_level": "high",
    "reasons": [
      "최근 30일간 구매 없음",
      "고객 문의 3회 이상",
      "평균 주문 금액 50% 감소"
    ],
    "retention_actions": [
      "개인화된 할인 쿠폰 발송",
      "VIP 고객 서비스 제공"
    ]
  }
}
```

### 3. Price Optimization
**Request:**
```bash
POST /api/ai/predict/price_optimization
Content-Type: application/json

{
  "product_id": "PROD789",
  "current_price": 25000,
  "competitor_prices": [23000, 24500, 26000],
  "inventory_level": 150
}
```

**Response:**
```json
{
  "model": "price_optimization",
  "timestamp": "2024-01-15T10:33:00",
  "prediction": {
    "optimal_price": 24500,
    "expected_revenue_increase": "12%",
    "price_elasticity": -1.2,
    "recommendation": "가격 인하 권장",
    "confidence_interval": {
      "lower": 24000,
      "upper": 25000
    }
  }
}
```

### 4. Inventory Forecast
**Request:**
```bash
POST /api/ai/predict/inventory_forecast
Content-Type: application/json

{
  "product_id": "PROD321",
  "warehouse_id": "WH01",
  "forecast_days": 14
}
```

**Response:**
```json
{
  "model": "inventory_forecast",
  "timestamp": "2024-01-15T10:34:00",
  "prediction": {
    "current_stock": 500,
    "forecasted_demand": [45, 50, 48, 52, 60, 55, 40],
    "reorder_point": 150,
    "reorder_quantity": 300,
    "stockout_risk": "low",
    "safety_stock": 100
  }
}
```

### 5. Chatbot Interaction
**Request:**
```bash
POST /api/ai/chatbot/message
Content-Type: application/json

{
  "message": "쿠팡 주문 처리 상태를 확인하고 싶습니다",
  "session_id": "SESSION123",
  "context": {}
}
```

**Response:**
```json
{
  "response": "쿠팡 주문 처리 상태를 확인해 드리겠습니다. 주문번호를 알려주시겠어요?",
  "intent": "order_status_inquiry",
  "entities": {
    "platform": "coupang",
    "action": "status_check"
  },
  "confidence": 0.92,
  "timestamp": "2024-01-15T10:35:00",
  "suggested_actions": [
    "주문번호 입력",
    "최근 주문 목록 보기"
  ]
}
```