-- 마켓별 원본 데이터 JSONB 저장 테이블
CREATE TABLE IF NOT EXISTS market_raw_products (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id) NOT NULL,
    market_account_id INTEGER NOT NULL,  -- 마켓별 계정 ID (coupang.id, naver.id 등)
    market_product_id VARCHAR(100) NOT NULL,  -- 마켓의 상품 ID
    raw_data JSONB NOT NULL,  -- 원본 API 응답 데이터
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market_id, market_account_id, market_product_id)
);

-- 인덱스 생성
CREATE INDEX idx_market_raw_products_market ON market_raw_products(market_id, market_account_id);
CREATE INDEX idx_market_raw_products_collected ON market_raw_products(collected_at);
CREATE INDEX idx_market_raw_products_jsonb ON market_raw_products USING gin(raw_data);

-- 빠른 검색을 위한 추가 인덱스 (자주 사용하는 필드)
CREATE INDEX idx_market_raw_products_coupang_name ON market_raw_products ((raw_data->>'sellerProductName')) 
    WHERE market_id = (SELECT id FROM markets WHERE code = 'COUPANG');
CREATE INDEX idx_market_raw_products_coupang_status ON market_raw_products ((raw_data->>'statusName')) 
    WHERE market_id = (SELECT id FROM markets WHERE code = 'COUPANG');

-- 트리거: updated_at 자동 업데이트
CREATE TRIGGER update_market_raw_products_updated_at BEFORE UPDATE ON market_raw_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰: 쿠팡 상품 조회용
CREATE OR REPLACE VIEW v_coupang_products AS
SELECT 
    mrp.id,
    c.alias as account_name,
    c.vendor_id,
    mrp.market_product_id,
    raw_data->>'sellerProductName' as product_name,
    raw_data->>'brand' as brand,
    (raw_data->>'salePrice')::numeric as sale_price,
    (raw_data->>'originalPrice')::numeric as original_price,
    (raw_data->>'stockQuantity')::integer as stock_quantity,
    raw_data->>'statusName' as status,
    raw_data->>'displayCategoryCode' as category_code,
    raw_data->>'productTypeName' as product_type,
    raw_data->>'taxType' as tax_type,
    raw_data->>'barcode' as barcode,
    mrp.collected_at,
    mrp.raw_data
FROM market_raw_products mrp
JOIN coupang c ON mrp.market_account_id = c.id
WHERE mrp.market_id = (SELECT id FROM markets WHERE code = 'COUPANG');

-- 뷰: 마켓별 상품 수 요약
CREATE OR REPLACE VIEW v_market_product_counts AS
SELECT 
    m.name as market_name,
    m.code as market_code,
    COUNT(DISTINCT mrp.id) as total_products,
    COUNT(DISTINCT mrp.market_account_id) as total_accounts,
    MAX(mrp.collected_at) as last_collected
FROM markets m
LEFT JOIN market_raw_products mrp ON m.id = mrp.market_id
GROUP BY m.id, m.name, m.code;