-- Yoonni 데이터베이스 성능 최적화 스크립트
-- 실행: PGPASSWORD=1234 psql -h localhost -p 5434 -U postgres -d yoonni -f scripts/optimize_database.sql

-- 1. JSONB 컬럼에 GIN 인덱스 추가 (빠른 JSON 검색)
CREATE INDEX IF NOT EXISTS idx_products_metadata_gin ON products USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_market_products_data ON market_products USING gin(market_specific_data) WHERE market_specific_data IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_raw_product_data_content ON raw_product_data USING gin(data) WHERE data IS NOT NULL;

-- 2. 자주 사용되는 복합 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_products_supplier_status ON products(supplier_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_orders_date_status ON market_orders(order_date DESC, status);
CREATE INDEX IF NOT EXISTS idx_market_products_supplier ON market_products(supplier_id, market_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_created_status ON orders(created_at DESC, status);

-- 3. 부분 인덱스 (특정 조건에만 인덱스 생성)
CREATE INDEX IF NOT EXISTS idx_products_active_only ON products(supplier_id, updated_at DESC) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_market_orders_pending ON market_orders(created_at DESC) 
WHERE status IN ('pending', 'processing', 'ACCEPT', 'INSTRUCT');

CREATE INDEX IF NOT EXISTS idx_products_in_stock ON products(supplier_id, stock_quantity) 
WHERE stock_status = 'in_stock' AND stock_quantity > 0;

-- 4. 텍스트 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_market_products_name ON market_products(product_name);

-- 5. 외래 키 관계를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_market_orders_market_id ON market_orders(market_id);
CREATE INDEX IF NOT EXISTS idx_market_products_market_id ON market_products(market_id);

-- 6. 날짜 범위 검색을 위한 BRIN 인덱스 (대용량 데이터에 효율적)
CREATE INDEX IF NOT EXISTS idx_market_orders_date_brin ON market_orders USING brin(order_date);
CREATE INDEX IF NOT EXISTS idx_collection_logs_created_brin ON collection_logs USING brin(created_at);

-- 7. 통계 정보 업데이트
ANALYZE products;
ANALYZE market_orders;
ANALYZE market_products;
ANALYZE orders;
ANALYZE raw_product_data;
ANALYZE collection_logs;

-- 8. 인덱스 사용량 및 크기 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS index_size,
    idx_scan as index_scans,
    idx_tup_read as tuples_read
FROM pg_indexes
LEFT JOIN pg_stat_user_indexes ON indexrelname = indexname
WHERE schemaname = 'public'
AND tablename IN ('products', 'orders', 'market_orders', 'market_products')
ORDER BY tablename, indexname;

-- 9. 테이블 크기 및 통계
SELECT 
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND relname IN ('products', 'orders', 'market_orders', 'market_products')
ORDER BY pg_total_relation_size(relid) DESC;