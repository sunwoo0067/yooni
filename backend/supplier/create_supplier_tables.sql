-- 공급사 관련 테이블 생성

-- 공급사 설정 테이블
CREATE TABLE IF NOT EXISTS supplier_configs (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    api_type VARCHAR(50) NOT NULL, -- 'graphql', 'rest', 'soap' 등
    api_endpoint VARCHAR(255),
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    vendor_id VARCHAR(100), -- 쿠팡 등에서 사용
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_second INTEGER DEFAULT 10,
    settings JSONB, -- 추가 설정
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 공급사 상품 테이블
CREATE TABLE IF NOT EXISTS supplier_products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    supplier_product_id VARCHAR(100) NOT NULL, -- 공급사의 상품 ID
    product_name VARCHAR(500) NOT NULL,
    product_code VARCHAR(100),
    barcode VARCHAR(50),
    brand VARCHAR(200),
    manufacturer VARCHAR(200),
    origin VARCHAR(100),
    description TEXT,
    category VARCHAR(300),
    price DECIMAL(12,2) DEFAULT 0,
    cost_price DECIMAL(12,2) DEFAULT 0,
    stock_quantity INTEGER DEFAULT 0,
    weight DECIMAL(10,3) DEFAULT 0,
    dimensions VARCHAR(100), -- 크기 정보
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, discontinued
    image_url TEXT,
    raw_data JSONB, -- 원본 API 응답
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(supplier_id, supplier_product_id)
);

-- 공급사 수집 로그 테이블
CREATE TABLE IF NOT EXISTS supplier_collection_logs (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    collection_type VARCHAR(50), -- 'products', 'orders', 'inventory'
    status VARCHAR(50), -- 'success', 'failed', 'partial'
    total_items INTEGER DEFAULT 0,
    new_items INTEGER DEFAULT 0,
    updated_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_products_code ON supplier_products(supplier_product_id);
CREATE INDEX IF NOT EXISTS idx_supplier_products_status ON supplier_products(status);
CREATE INDEX IF NOT EXISTS idx_supplier_products_collected ON supplier_products(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_configs_active ON supplier_configs(supplier_id, is_active);
CREATE INDEX IF NOT EXISTS idx_collection_logs_supplier ON supplier_collection_logs(supplier_id, started_at DESC);

-- 오너클랜 기본 데이터 추가
INSERT INTO suppliers (name, contact_email) 
VALUES ('오너클랜', 'api@ownerclan.com')
ON CONFLICT DO NOTHING;

INSERT INTO suppliers (name, contact_email) 
VALUES ('젠트레이드', 'api@zentrade.co.kr')
ON CONFLICT DO NOTHING;

-- 기본 설정 추가 (실제 API 키는 환경변수에서 관리)
INSERT INTO supplier_configs (supplier_id, api_type, api_endpoint, api_key, api_secret, is_active, rate_limit_per_second)
SELECT 
    s.id, 
    'graphql',
    'https://api.ownerclan.com/v1/graphql',
    'test_api_key',
    'test_api_secret',
    true,
    5
FROM suppliers s 
WHERE s.name = '오너클랜'
ON CONFLICT DO NOTHING;

INSERT INTO supplier_configs (supplier_id, api_type, api_endpoint, api_key, api_secret, is_active, rate_limit_per_second)
SELECT 
    s.id, 
    'rest',
    'https://api.zentrade.co.kr/v1',
    'test_api_key',
    'test_api_secret',
    true,
    10
FROM suppliers s 
WHERE s.name = '젠트레이드'
ON CONFLICT DO NOTHING;

-- 테이블 설명
COMMENT ON TABLE supplier_configs IS '공급사 API 설정 정보';
COMMENT ON TABLE supplier_products IS '공급사별 상품 데이터';
COMMENT ON TABLE supplier_collection_logs IS '상품 수집 로그';