#!/usr/bin/env python3
"""
비즈니스 인텔리전스 통합 API
- 수익성 분석
- 경쟁사 모니터링
- 시장 트렌드 분석
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# BI 모듈 임포트
from bi.profitability_analyzer import ProfitabilityAnalyzer
from bi.competitor_monitor import CompetitorMonitor
from bi.market_trend_analyzer import MarketTrendAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Business Intelligence API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class PricingOptimizationRequest(BaseModel):
    product_id: int
    supplier_price: float
    min_price: float
    max_price: float
    demand_elasticity: Optional[float] = -1.5

class CompetitorMonitoringRequest(BaseModel):
    product_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    monitor_all: bool = False

class DemandPredictionRequest(BaseModel):
    category: str
    days_ahead: Optional[int] = 30

# 전역 인스턴스
profitability_analyzer = None
competitor_monitor = None
trend_analyzer = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global profitability_analyzer, competitor_monitor, trend_analyzer
    
    profitability_analyzer = ProfitabilityAnalyzer()
    competitor_monitor = CompetitorMonitor()
    trend_analyzer = MarketTrendAnalyzer()
    
    logger.info("✅ Business Intelligence API 시작됨")

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "service": "Business Intelligence API",
        "status": "running",
        "version": "1.0.0",
        "modules": {
            "profitability": "/api/bi/profitability",
            "competitors": "/api/bi/competitors",
            "trends": "/api/bi/trends"
        }
    }

# 수익성 분석 엔드포인트
@app.get("/api/bi/profitability/report")
async def get_profitability_report():
    """종합 수익성 리포트"""
    try:
        report = profitability_analyzer.generate_profitability_report()
        return report
    except Exception as e:
        logger.error(f"수익성 리포트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/profitability/categories")
async def get_category_profitability():
    """카테고리별 수익성 분석"""
    try:
        categories = profitability_analyzer.analyze_category_profitability()
        return {
            "categories": categories,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"카테고리 수익성 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/profitability/suppliers")
async def get_supplier_profitability():
    """공급사별 수익성 분석"""
    try:
        suppliers = profitability_analyzer.analyze_supplier_profitability()
        return {
            "suppliers": suppliers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"공급사 수익성 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bi/profitability/optimize-price")
async def optimize_pricing(request: PricingOptimizationRequest):
    """최적 가격 찾기"""
    try:
        result = profitability_analyzer.find_optimal_pricing(
            product_id=request.product_id,
            supplier_price=request.supplier_price,
            market_price_range=(request.min_price, request.max_price),
            demand_elasticity=request.demand_elasticity
        )
        return result
    except Exception as e:
        logger.error(f"가격 최적화 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/profitability/products/top")
async def get_top_profitable_products(limit: int = 20):
    """수익성 상위 상품"""
    try:
        products = profitability_analyzer._get_top_profitable_products(limit)
        return {
            "products": products,
            "count": len(products),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"상위 수익 상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 경쟁사 모니터링 엔드포인트
@app.post("/api/bi/competitors/monitor")
async def monitor_competitors(
    request: CompetitorMonitoringRequest,
    background_tasks: BackgroundTasks
):
    """경쟁사 가격 모니터링 시작"""
    try:
        # 백그라운드에서 모니터링 실행
        background_tasks.add_task(
            run_competitor_monitoring,
            request.product_ids,
            request.categories,
            request.monitor_all
        )
        
        return {
            "status": "monitoring_started",
            "message": "경쟁사 모니터링이 백그라운드에서 시작되었습니다",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"경쟁사 모니터링 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/competitors/alerts")
async def get_price_alerts(
    acknowledged: bool = False,
    limit: int = 50
):
    """가격 알림 조회"""
    try:
        alerts = competitor_monitor.detect_price_alerts()
        
        # 필터링
        if not acknowledged:
            alerts = [a for a in alerts if not a.get('acknowledged', False)]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"가격 알림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/competitors/position/{product_id}")
async def get_price_position(product_id: int):
    """특정 상품의 가격 포지션 분석"""
    try:
        # 상품 정보 조회
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT price FROM supplier_products WHERE id = %s",
                (product_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
            
            our_price = float(result[0])
        
        conn.close()
        
        # 가격 포지션 분석
        position = competitor_monitor.analyze_price_position(product_id, our_price)
        
        if not position:
            return {
                "error": "경쟁사 가격 데이터가 없습니다",
                "product_id": product_id
            }
        
        return {
            "product_id": product_id,
            "our_price": position.our_price,
            "market_average": position.market_average,
            "our_position": position.our_position,
            "price_gap": position.price_gap,
            "competitor_prices": position.competitor_prices,
            "recommendation": position.recommendation,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"가격 포지션 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/competitors/recommendations")
async def get_pricing_recommendations(limit: int = 20):
    """가격 조정 추천"""
    try:
        recommendations = competitor_monitor.get_pricing_recommendations(limit)
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"가격 추천 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 시장 트렌드 엔드포인트
@app.get("/api/bi/trends/analysis")
async def get_market_trends():
    """전체 시장 트렌드 분석"""
    try:
        trends = trend_analyzer.analyze_market_trends()
        return trends
    except Exception as e:
        logger.error(f"시장 트렌드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/trends/categories")
async def get_category_trends():
    """카테고리별 트렌드"""
    try:
        trends = trend_analyzer._analyze_category_trends()
        return {
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"카테고리 트렌드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/trends/seasonal")
async def get_seasonal_patterns():
    """계절성 패턴 분석"""
    try:
        patterns = trend_analyzer._detect_seasonal_patterns()
        return {
            "seasonal_patterns": patterns,
            "current_month": datetime.now().month,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"계절성 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bi/trends/opportunities")
async def get_market_opportunities():
    """시장 기회 발굴"""
    try:
        opportunities = trend_analyzer._find_emerging_opportunities()
        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"기회 발굴 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bi/trends/predict")
async def predict_demand(request: DemandPredictionRequest):
    """수요 예측"""
    try:
        prediction = trend_analyzer.predict_demand_trend(
            category=request.category,
            days_ahead=request.days_ahead
        )
        return prediction
    except Exception as e:
        logger.error(f"수요 예측 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 통합 대시보드 엔드포인트
@app.get("/api/bi/dashboard/summary")
async def get_bi_dashboard_summary():
    """BI 대시보드 요약"""
    try:
        # 수익성 요약
        profitability_summary = profitability_analyzer._get_profitability_summary()
        
        # 경쟁사 분석 요약
        alerts = competitor_monitor.detect_price_alerts()
        
        # 시장 트렌드 요약
        trends = trend_analyzer._generate_market_insights()
        
        return {
            "profitability": {
                "total_products": profitability_summary.get('total_products', 0),
                "average_margin": profitability_summary.get('avg_margin', 0),
                "high_margin_products": profitability_summary.get('high_margin_products', 0)
            },
            "competition": {
                "active_alerts": len([a for a in alerts if not a.get('acknowledged', False)]),
                "undercut_products": len([a for a in alerts if a['alert_type'] == 'undercut']),
                "price_wars": len([a for a in alerts if a['alert_type'] == 'price_war'])
            },
            "market_trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"대시보드 요약 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 백그라운드 태스크
async def run_competitor_monitoring(
    product_ids: Optional[List[int]] = None,
    categories: Optional[List[str]] = None,
    monitor_all: bool = False
):
    """백그라운드에서 경쟁사 모니터링 실행"""
    try:
        logger.info("🔍 경쟁사 모니터링 시작...")
        
        # 모니터링 대상 결정
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if monitor_all:
                cursor.execute("""
                    SELECT id, product_name as name, price, category
                    FROM supplier_products
                    WHERE status = 'active'
                    LIMIT 500
                """)
            elif product_ids:
                cursor.execute("""
                    SELECT id, product_name as name, price, category
                    FROM supplier_products
                    WHERE id = ANY(%s)
                """, (product_ids,))
            elif categories:
                cursor.execute("""
                    SELECT id, product_name as name, price, category
                    FROM supplier_products
                    WHERE category = ANY(%s) AND status = 'active'
                    LIMIT 200
                """, (categories,))
            else:
                # 기본: 인기 상품
                cursor.execute("""
                    SELECT sp.id, sp.product_name as name, sp.price, sp.category
                    FROM supplier_products sp
                    JOIN product_ai_insights pai ON sp.id = pai.product_id
                    WHERE sp.status = 'active'
                    ORDER BY pai.demand_score DESC
                    LIMIT 100
                """)
            
            products = cursor.fetchall()
        
        conn.close()
        
        # 경쟁사 가격 수집
        for product in products:
            prices = await competitor_monitor.collect_competitor_prices(product)
            competitor_monitor.save_competitor_prices(prices)
        
        # 알림 생성
        alerts = competitor_monitor.detect_price_alerts()
        
        logger.info(f"✅ 경쟁사 모니터링 완료: {len(products)}개 상품, {len(alerts)}개 알림")
        
    except Exception as e:
        logger.error(f"❌ 경쟁사 모니터링 실패: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)