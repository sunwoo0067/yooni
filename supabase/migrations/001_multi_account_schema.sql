-- 멀티계정, 멀티마켓 대응 데이터베이스 스키마
-- 쿠팡, 네이버스마트스토어, 11번가 등 다양한 마켓플레이스 지원
-- 오너클렌, 1688, 타오바오 등 다양한 공급처 지원

-- 기존 테이블 삭제 (주의: 데이터가 모두 삭제됩니다)
DROP TABLE IF EXISTS automation_logs CASCADE;
DROP TABLE IF EXISTS ownerclan_orders CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS product_mappings CASCADE;
DROP TABLE IF EXISTS coupang_orders CASCADE;
DROP TABLE IF EXISTS coupang_order_items CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS markets CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. 사용자 테이블 (멀티 테넌트 지원)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 마켓플레이스 정의
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL, -- 'coupang', 'naver', '11st' 등
    name TEXT NOT NULL,
    api_version TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 공급처 정의
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL, -- 'ownerclan', '1688', 'taobao' 등
    name TEXT NOT NULL,
    api_version TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 마켓 계정 (멀티계정 지원)
CREATE TABLE market_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    market_id INTEGER REFERENCES markets(id),
    account_name TEXT NOT NULL,
    credentials JSONB NOT NULL, -- {vendor_id, access_key, secret_key 등}
    settings JSONB DEFAULT '{}', -- 계정별 설정
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, market_id, account_name)
);

-- 5. 공급처 계정
CREATE TABLE supplier_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(id),
    account_name TEXT NOT NULL,
    credentials JSONB NOT NULL, -- {username, password, api_key 등}
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, supplier_id, account_name)
);

-- 6. 통합 주문 테이블
CREATE TABLE orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    market_account_id INTEGER REFERENCES market_accounts(id),
    market_order_id TEXT NOT NULL, -- 마켓별 주문번호
    shipment_box_id TEXT, -- 묶음배송번호 (쿠팡)
    status TEXT NOT NULL DEFAULT 'NEW', -- NEW, PROCESSING, ORDERED, SHIPPED, DELIVERED, ERROR, CANCELLED
    ordered_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    shipping_fee DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) DEFAULT 0,
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    shipping_address JSONB, -- {addr1, addr2, postal_code, etc}
    invoice_number TEXT,
    shipping_company_code TEXT,
    delivered_at TIMESTAMP WITH TIME ZONE,
    raw_data JSONB, -- 마켓별 원본 데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(market_account_id, market_order_id)
);

-- 7. 주문 상품
CREATE TABLE order_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    market_item_id TEXT, -- 마켓별 상품 ID
    market_sku TEXT, -- 마켓별 SKU/옵션ID
    product_name TEXT,
    option_name TEXT,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. 공급처 주문
CREATE TABLE supplier_orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    supplier_account_id INTEGER REFERENCES supplier_accounts(id),
    supplier_order_id TEXT, -- 공급처 주문번호
    supplier_order_key TEXT, -- 공급처 주문키 (오너클렌)
    status TEXT DEFAULT 'PENDING', -- PENDING, ORDERED, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    total_amount DECIMAL(10,2),
    tracking_number TEXT,
    shipping_company TEXT,
    shipped_at TIMESTAMP WITH TIME ZONE,
    raw_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(supplier_account_id, supplier_order_id)
);

-- 9. 상품 매핑
CREATE TABLE product_mappings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    market_account_id INTEGER REFERENCES market_accounts(id),
    supplier_account_id INTEGER REFERENCES supplier_accounts(id),
    market_sku TEXT NOT NULL, -- 마켓 SKU/옵션ID
    supplier_sku TEXT NOT NULL, -- 공급처 SKU
    supplier_item_key TEXT, -- 공급처 상품키 (오너클렌)
    market_product_name TEXT,
    supplier_product_name TEXT,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}', -- 가격 마진, 배송비 설정 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(market_account_id, market_sku, supplier_account_id)
);

-- 10. 자동화 로그
CREATE TABLE automation_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    market_account_id INTEGER REFERENCES market_accounts(id),
    supplier_account_id INTEGER REFERENCES supplier_accounts(id),
    worker_type TEXT NOT NULL, -- 'fetch', 'place_order', 'update_tracking' 등
    level TEXT NOT NULL DEFAULT 'INFO', -- INFO, WARNING, ERROR
    message TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. 워커 실행 상태
CREATE TABLE worker_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    market_account_id INTEGER REFERENCES market_accounts(id),
    worker_type TEXT NOT NULL,
    status TEXT DEFAULT 'IDLE', -- IDLE, RUNNING, ERROR, STOPPED
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}', -- 실행 주기, 옵션 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(market_account_id, worker_type)
);

-- 인덱스 생성
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_market_account ON orders(market_account_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_supplier_orders_order_id ON supplier_orders(order_id);
CREATE INDEX idx_supplier_orders_status ON supplier_orders(status);
CREATE INDEX idx_product_mappings_market ON product_mappings(market_account_id, market_sku);
CREATE INDEX idx_automation_logs_created_at ON automation_logs(created_at DESC);
CREATE INDEX idx_automation_logs_level ON automation_logs(level);

-- 초기 데이터 삽입
INSERT INTO markets (code, name) VALUES
    ('coupang', '쿠팡'),
    ('naver', '네이버 스마트스토어'),
    ('11st', '11번가'),
    ('gmarket', 'G마켓'),
    ('auction', '옥션');

INSERT INTO suppliers (code, name) VALUES
    ('ownerclan', '오너클랜'),
    ('1688', '1688'),
    ('taobao', '타오바오'),
    ('alibaba', '알리바바');

-- Row Level Security (RLS) 설정
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_status ENABLE ROW LEVEL SECURITY;

-- RLS 정책 생성 (사용자는 자신의 데이터만 접근 가능)
CREATE POLICY "Users can view own data" ON users FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users can view own market accounts" ON market_accounts FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own supplier accounts" ON supplier_accounts FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own orders" ON orders FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own order items" ON order_items FOR ALL USING (order_id IN (SELECT id FROM orders WHERE user_id = auth.uid()));
CREATE POLICY "Users can view own supplier orders" ON supplier_orders FOR ALL USING (order_id IN (SELECT id FROM orders WHERE user_id = auth.uid()));
CREATE POLICY "Users can view own product mappings" ON product_mappings FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own automation logs" ON automation_logs FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can view own worker status" ON worker_status FOR ALL USING (user_id = auth.uid());