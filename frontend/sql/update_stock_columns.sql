-- 재고 관련 컬럼 추가 (없는 경우에만)
DO $$ 
BEGIN 
    -- stock_status 컬럼 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'products' AND column_name = 'stock_status') THEN
        ALTER TABLE products ADD COLUMN stock_status VARCHAR(20) DEFAULT 'in_stock';
    END IF;
    
    -- stock_quantity 컬럼 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'products' AND column_name = 'stock_quantity') THEN
        ALTER TABLE products ADD COLUMN stock_quantity INTEGER DEFAULT 0;
    END IF;
    
    -- last_stock_check 컬럼 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'products' AND column_name = 'last_stock_check') THEN
        ALTER TABLE products ADD COLUMN last_stock_check TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- stock_sync_enabled 컬럼 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'products' AND column_name = 'stock_sync_enabled') THEN
        ALTER TABLE products ADD COLUMN stock_sync_enabled BOOLEAN DEFAULT true;
    END IF;
END $$;

-- 재고 이력 테이블 생성
CREATE TABLE IF NOT EXISTS stock_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    previous_quantity INTEGER,
    new_quantity INTEGER,
    change_reason VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 재고 알림 테이블 생성
CREATE TABLE IF NOT EXISTS stock_alerts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (없는 경우에만)
CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(stock_status);
CREATE INDEX IF NOT EXISTS idx_products_stock_sync ON products(stock_sync_enabled);
CREATE INDEX IF NOT EXISTS idx_stock_history_product_id ON stock_history(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_history_created_at ON stock_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_is_read ON stock_alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_created_at ON stock_alerts(created_at DESC);

-- 기존 상품 데이터의 재고 상태 업데이트
UPDATE products 
SET stock_status = CASE 
    WHEN status = 'soldout' THEN 'out_of_stock'
    WHEN status = 'active' THEN 'in_stock'
    ELSE 'in_stock'
END
WHERE stock_status IS NULL;