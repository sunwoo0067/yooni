-- 마켓 공통 데이터 테이블 설계
-- 모든 마켓플레이스의 데이터를 통합 관리

-- 1. 마켓 정의 테이블
CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- coupang, naver, 11st, etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기본 마켓 데이터 삽입
INSERT INTO markets (code, name, description) VALUES
    ('coupang', '쿠팡', '쿠팡 파트너스 마켓플레이스'),
    ('naver', '네이버 스마트스토어', '네이버 커머스 플랫폼'),
    ('11st', '11번가', '11번가 오픈마켓'),
    ('gmarket', 'G마켓', 'G마켓 오픈마켓'),
    ('auction', '옥션', '옥션 오픈마켓')
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description;

-- 2. 마켓 계정 테이블 (멀티 계정 지원)
CREATE TABLE IF NOT EXISTS market_accounts (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    account_name VARCHAR(200) NOT NULL,
    api_key VARCHAR(500),
    api_secret VARCHAR(500),
    vendor_id VARCHAR(200),
    extra_config JSONB, -- 마켓별 추가 설정
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market_id, account_name)
);

-- 3. 마켓 상품 통합 테이블
CREATE TABLE IF NOT EXISTS market_products (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    market_account_id INTEGER REFERENCES market_accounts(id),
    market_product_id VARCHAR(200) NOT NULL, -- 마켓별 상품 ID
    unified_product_id INTEGER, -- unified_products 테이블 참조
    
    -- 기본 상품 정보
    product_name VARCHAR(500) NOT NULL,
    brand VARCHAR(200),
    manufacturer VARCHAR(200),
    model_name VARCHAR(200),
    
    -- 가격 정보
    original_price DECIMAL(15, 2),
    sale_price DECIMAL(15, 2),
    discount_rate DECIMAL(5, 2),
    
    -- 상태 정보
    status VARCHAR(50), -- active, inactive, soldout, suspended
    stock_quantity INTEGER DEFAULT 0,
    
    -- 카테고리
    category_code VARCHAR(100),
    category_name VARCHAR(500),
    category_path TEXT,
    
    -- 배송 정보
    shipping_type VARCHAR(50), -- free, paid, conditional_free
    shipping_fee DECIMAL(10, 2),
    
    -- 마켓별 추가 정보
    market_data JSONB,
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    
    -- 인덱스를 위한 복합 유니크 제약
    UNIQUE(market_account_id, market_product_id)
);

-- 4. 마켓 주문 통합 테이블
CREATE TABLE IF NOT EXISTS market_orders (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    market_account_id INTEGER REFERENCES market_accounts(id),
    market_order_id VARCHAR(200) NOT NULL, -- 마켓별 주문 번호
    
    -- 주문 기본 정보
    order_date TIMESTAMP NOT NULL,
    payment_date TIMESTAMP,
    
    -- 구매자 정보
    buyer_name VARCHAR(100),
    buyer_email VARCHAR(200),
    buyer_phone VARCHAR(50),
    
    -- 수령자 정보
    receiver_name VARCHAR(100),
    receiver_phone VARCHAR(50),
    receiver_address TEXT,
    receiver_zipcode VARCHAR(20),
    delivery_message TEXT,
    
    -- 주문 상태
    order_status VARCHAR(50), -- pending, confirmed, shipped, delivered, cancelled
    payment_method VARCHAR(50),
    
    -- 금액 정보
    total_price DECIMAL(15, 2),
    product_price DECIMAL(15, 2),
    discount_amount DECIMAL(15, 2),
    shipping_fee DECIMAL(10, 2),
    
    -- 마켓별 추가 정보
    market_data JSONB,
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    
    UNIQUE(market_account_id, market_order_id)
);

-- 5. 마켓 주문 상품 테이블
CREATE TABLE IF NOT EXISTS market_order_items (
    id SERIAL PRIMARY KEY,
    market_order_id INTEGER REFERENCES market_orders(id),
    market_product_id VARCHAR(200),
    
    -- 상품 정보
    product_name VARCHAR(500),
    option_name VARCHAR(500),
    
    -- 수량 및 금액
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(15, 2),
    total_price DECIMAL(15, 2),
    
    -- 상태
    item_status VARCHAR(50),
    
    -- 배송 정보
    tracking_company VARCHAR(100),
    tracking_number VARCHAR(100),
    shipped_date TIMESTAMP,
    delivered_date TIMESTAMP,
    
    -- 추가 정보
    item_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 마켓 배송 통합 테이블
CREATE TABLE IF NOT EXISTS market_shipments (
    id SERIAL PRIMARY KEY,
    market_order_id INTEGER REFERENCES market_orders(id),
    
    -- 배송 정보
    shipment_type VARCHAR(50), -- normal, express, international
    tracking_company VARCHAR(100),
    tracking_number VARCHAR(100),
    
    -- 배송 상태
    shipment_status VARCHAR(50), -- preparing, shipped, in_transit, delivered
    
    -- 배송 일자
    shipped_date TIMESTAMP,
    estimated_delivery_date DATE,
    delivered_date TIMESTAMP,
    
    -- 배송지 정보
    receiver_name VARCHAR(100),
    receiver_phone VARCHAR(50),
    receiver_address TEXT,
    receiver_zipcode VARCHAR(20),
    
    -- 추가 정보
    shipment_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 마켓 정산 테이블
CREATE TABLE IF NOT EXISTS market_settlements (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    market_account_id INTEGER REFERENCES market_accounts(id),
    
    -- 정산 정보
    settlement_date DATE NOT NULL,
    settlement_amount DECIMAL(15, 2),
    
    -- 상세 내역
    sales_amount DECIMAL(15, 2),
    commission_amount DECIMAL(15, 2),
    shipping_fee_amount DECIMAL(15, 2),
    promotion_amount DECIMAL(15, 2),
    adjustment_amount DECIMAL(15, 2),
    
    -- 상태
    settlement_status VARCHAR(50), -- pending, completed, delayed
    
    -- 추가 정보
    settlement_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(market_account_id, settlement_date)
);

-- 인덱스 생성
CREATE INDEX idx_market_products_market_id ON market_products(market_id);
CREATE INDEX idx_market_products_status ON market_products(status);
CREATE INDEX idx_market_products_unified_id ON market_products(unified_product_id);
CREATE INDEX idx_market_products_updated ON market_products(updated_at);

CREATE INDEX idx_market_orders_market_id ON market_orders(market_id);
CREATE INDEX idx_market_orders_order_date ON market_orders(order_date);
CREATE INDEX idx_market_orders_status ON market_orders(order_status);
CREATE INDEX idx_market_orders_buyer_phone ON market_orders(buyer_phone);

CREATE INDEX idx_market_order_items_status ON market_order_items(item_status);
CREATE INDEX idx_market_order_items_tracking ON market_order_items(tracking_number);

CREATE INDEX idx_market_shipments_status ON market_shipments(shipment_status);
CREATE INDEX idx_market_shipments_tracking ON market_shipments(tracking_number);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_market_accounts_updated_at BEFORE UPDATE ON market_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_products_updated_at BEFORE UPDATE ON market_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_orders_updated_at BEFORE UPDATE ON market_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_order_items_updated_at BEFORE UPDATE ON market_order_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_shipments_updated_at BEFORE UPDATE ON market_shipments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();