-- 통합 상품 마스터 테이블
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    internal_sku VARCHAR(100) UNIQUE NOT NULL,  -- 내부 관리 SKU
    name VARCHAR(500) NOT NULL,
    base_price DECIMAL(12,2),
    cost_price DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, discontinued
    brand VARCHAR(200),
    manufacturer VARCHAR(200),
    barcode VARCHAR(50),
    weight_kg DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 마켓별 상품 연결 테이블
CREATE TABLE IF NOT EXISTS market_products (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    market_id INTEGER REFERENCES markets(id),
    market_account_id INTEGER,  -- 쿠팡의 경우 coupang.id 참조
    market_product_id VARCHAR(100) NOT NULL,  -- 마켓의 상품 ID
    market_sku VARCHAR(100),  -- 마켓의 SKU
    market_name VARCHAR(500),  -- 마켓에서의 상품명
    market_status VARCHAR(50),  -- 마켓에서의 상태
    sale_price DECIMAL(12,2),
    stock_quantity INTEGER DEFAULT 0,
    common_fields JSONB DEFAULT '{}',  -- 공통 필드 (카테고리, 이미지 등)
    market_specific JSONB DEFAULT '{}',  -- 마켓 고유 데이터
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market_id, market_account_id, market_product_id)
);

-- 가격 이력 테이블
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    market_product_id INTEGER REFERENCES market_products(id) ON DELETE CASCADE,
    price_type VARCHAR(50),  -- sale, original, cost
    price DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'KRW',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100),  -- system, manual, promotion
    reason VARCHAR(500)
);

-- 재고 이력 테이블
CREATE TABLE IF NOT EXISTS inventory_history (
    id SERIAL PRIMARY KEY,
    market_product_id INTEGER REFERENCES market_products(id) ON DELETE CASCADE,
    quantity_before INTEGER,
    quantity_after INTEGER,
    quantity_change INTEGER,
    change_type VARCHAR(50),  -- sale, return, adjustment, restock
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100),
    reason VARCHAR(500)
);

-- 동기화 로그 테이블
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    market_account_id INTEGER,
    sync_type VARCHAR(50),  -- full, incremental, product, inventory, price
    sync_status VARCHAR(50),  -- started, completed, failed
    total_items INTEGER,
    processed_items INTEGER,
    success_items INTEGER,
    failed_items INTEGER,
    error_details JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- 상품 매핑 테이블 (여러 마켓의 같은 상품을 하나로 관리)
CREATE TABLE IF NOT EXISTS product_mappings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    market_product_id INTEGER REFERENCES market_products(id) ON DELETE CASCADE,
    mapping_type VARCHAR(50),  -- auto, manual
    confidence_score DECIMAL(5,2),  -- 자동 매핑의 경우 신뢰도
    mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mapped_by VARCHAR(100)
);

-- 인덱스 생성
CREATE INDEX idx_market_products_product_id ON market_products(product_id);
CREATE INDEX idx_market_products_market_id ON market_products(market_id);
CREATE INDEX idx_market_products_market_account_id ON market_products(market_account_id);
CREATE INDEX idx_market_products_last_sync ON market_products(last_sync_at);
CREATE INDEX idx_price_history_market_product ON price_history(market_product_id);
CREATE INDEX idx_price_history_changed_at ON price_history(changed_at);
CREATE INDEX idx_inventory_history_market_product ON inventory_history(market_product_id);
CREATE INDEX idx_sync_logs_market ON sync_logs(market_id, market_account_id);

-- 트리거: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_products_updated_at BEFORE UPDATE ON market_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰: 활성 상품 통합 뷰
CREATE OR REPLACE VIEW v_active_products AS
SELECT 
    p.id,
    p.internal_sku,
    p.name,
    p.base_price,
    p.brand,
    m.name as market_name,
    mp.market_product_id,
    mp.market_name,
    mp.sale_price,
    mp.stock_quantity,
    mp.market_status,
    mp.last_sync_at
FROM products p
JOIN market_products mp ON p.id = mp.product_id
JOIN markets m ON mp.market_id = m.id
WHERE p.status = 'active' 
  AND mp.is_active = true;

-- 뷰: 마켓별 상품 요약
CREATE OR REPLACE VIEW v_market_product_summary AS
SELECT 
    m.name as market_name,
    COUNT(DISTINCT mp.market_product_id) as total_products,
    COUNT(DISTINCT CASE WHEN mp.stock_quantity > 0 THEN mp.market_product_id END) as in_stock_products,
    SUM(mp.stock_quantity) as total_stock,
    AVG(mp.sale_price) as avg_price,
    MAX(mp.last_sync_at) as last_sync
FROM markets m
LEFT JOIN market_products mp ON m.id = mp.market_id
GROUP BY m.id, m.name;