-- 상품 테이블에 재고 관련 컬럼 추가
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS stock_status VARCHAR(20) DEFAULT 'in_stock', -- 'in_stock', 'out_of_stock', 'low_stock'
ADD COLUMN IF NOT EXISTS stock_quantity INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_stock_check TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS stock_sync_enabled BOOLEAN DEFAULT true;

-- 재고 변경 이력 테이블
CREATE TABLE IF NOT EXISTS stock_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    previous_quantity INTEGER,
    new_quantity INTEGER,
    change_reason VARCHAR(50), -- 'api_sync', 'manual_update', 'order_placed', 'order_cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 품절 알림 테이블
CREATE TABLE IF NOT EXISTS stock_alerts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL, -- 'out_of_stock', 'low_stock', 'back_in_stock'
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_products_stock_status ON products(stock_status);
CREATE INDEX idx_products_stock_sync ON products(stock_sync_enabled);
CREATE INDEX idx_stock_history_product_id ON stock_history(product_id);
CREATE INDEX idx_stock_history_created_at ON stock_history(created_at DESC);
CREATE INDEX idx_stock_alerts_is_read ON stock_alerts(is_read);
CREATE INDEX idx_stock_alerts_created_at ON stock_alerts(created_at DESC);