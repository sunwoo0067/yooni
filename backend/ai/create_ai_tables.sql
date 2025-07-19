-- AI 분석 결과 저장 테이블

-- 상품 분석 결과 테이블
CREATE TABLE IF NOT EXISTS supplier_product_analysis (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES supplier_products(id),
    analysis_type VARCHAR(50) NOT NULL, -- price_demand, trend, competitor
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 ~ 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, analysis_type)
);

-- AI 모델 메타데이터
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL, -- regression, classification, clustering
    version VARCHAR(20) NOT NULL,
    training_date TIMESTAMP NOT NULL,
    metrics JSONB, -- accuracy, r2_score, etc.
    feature_importance JSONB,
    hyperparameters JSONB,
    training_data_count INTEGER,
    status VARCHAR(20) DEFAULT 'active', -- active, deprecated, testing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 가격 추천 히스토리
CREATE TABLE IF NOT EXISTS price_recommendations (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES supplier_products(id),
    current_price DECIMAL(12,2),
    recommended_price DECIMAL(12,2),
    price_adjustment_percent DECIMAL(5,2),
    margin_percent DECIMAL(5,2),
    confidence_score DECIMAL(3,2),
    recommendation_reason TEXT,
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 수요 예측 히스토리
CREATE TABLE IF NOT EXISTS demand_forecasts (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES supplier_products(id),
    forecast_date DATE NOT NULL,
    demand_score DECIMAL(5,2),
    demand_grade CHAR(1), -- A, B, C, D, E
    recommended_stock INTEGER,
    reorder_point INTEGER,
    forecast_accuracy DECIMAL(3,2),
    actual_demand INTEGER, -- 실제 판매량 (나중에 업데이트)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 카테고리별 트렌드 분석
CREATE TABLE IF NOT EXISTS category_trends (
    id SERIAL PRIMARY KEY,
    category VARCHAR(200) NOT NULL,
    trend_date DATE NOT NULL,
    trend_score DECIMAL(5,2), -- -100 ~ +100
    trending_keywords JSONB,
    price_trend VARCHAR(20), -- increasing, stable, decreasing
    demand_trend VARCHAR(20),
    top_products JSONB, -- 인기 상품 목록
    market_insights TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, trend_date)
);

-- 인덱스 생성
CREATE INDEX idx_product_analysis_product_id ON supplier_product_analysis(product_id);
CREATE INDEX idx_product_analysis_type ON supplier_product_analysis(analysis_type);
CREATE INDEX idx_price_recommendations_product_id ON price_recommendations(product_id);
CREATE INDEX idx_price_recommendations_created_at ON price_recommendations(created_at);
CREATE INDEX idx_demand_forecasts_product_id ON demand_forecasts(product_id);
CREATE INDEX idx_demand_forecasts_date ON demand_forecasts(forecast_date);
CREATE INDEX idx_category_trends_category ON category_trends(category);
CREATE INDEX idx_category_trends_date ON category_trends(trend_date);

-- 분석 결과 조회 뷰
CREATE OR REPLACE VIEW product_ai_insights AS
SELECT 
    sp.id as product_id,
    sp.supplier_product_id,
    sp.product_name,
    s.name as supplier_name,
    sp.category,
    sp.brand,
    sp.price as current_price,
    sp.cost_price,
    sp.stock_quantity,
    spa.analysis_result->>'predicted_price' as predicted_price,
    spa.analysis_result->>'demand_score' as demand_score,
    spa.analysis_result->>'demand_grade' as demand_grade,
    spa.analysis_result->>'recommended_stock' as recommended_stock,
    spa.updated_at as last_analysis_date
FROM supplier_products sp
JOIN suppliers s ON sp.supplier_id = s.id
LEFT JOIN supplier_product_analysis spa ON sp.id = spa.product_id 
    AND spa.analysis_type = 'price_demand'
WHERE sp.status = 'active';

-- 카테고리별 AI 인사이트 뷰
CREATE OR REPLACE VIEW category_ai_insights AS
SELECT 
    category,
    COUNT(DISTINCT product_id) as product_count,
    AVG(CAST(predicted_price AS DECIMAL)) as avg_predicted_price,
    AVG(CAST(demand_score AS DECIMAL)) as avg_demand_score,
    COUNT(CASE WHEN demand_grade IN ('A', 'B') THEN 1 END) as high_demand_count,
    COUNT(CASE WHEN demand_grade IN ('D', 'E') THEN 1 END) as low_demand_count
FROM product_ai_insights
WHERE predicted_price IS NOT NULL
GROUP BY category;

COMMENT ON TABLE supplier_product_analysis IS '공급사 상품 AI 분석 결과';
COMMENT ON TABLE ai_models IS 'AI 모델 메타데이터 및 버전 관리';
COMMENT ON TABLE price_recommendations IS '가격 추천 히스토리';
COMMENT ON TABLE demand_forecasts IS '수요 예측 히스토리';
COMMENT ON TABLE category_trends IS '카테고리별 시장 트렌드 분석';