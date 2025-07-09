CREATE TABLE IF NOT EXISTS coupang_order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES coupang_orders(order_id),
    vendor_item_id BIGINT,
    vendor_item_name TEXT,
    product_id BIGINT,
    product_name TEXT,
    quantity INTEGER,
    shipping_count INTEGER,
    sales_price NUMERIC,
    order_price NUMERIC,
    discount_price NUMERIC,
    canceled BOOLEAN,
    raw_item_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE coupang_order_items IS '쿠팡 주문 아이템 데이터';
COMMENT ON COLUMN coupang_order_items.id IS '쿠팡 주문 아이템 ID (기본 키)';
COMMENT ON COLUMN coupang_order_items.order_id IS '쿠팡 주문 ID (FK)';
COMMENT ON COLUMN coupang_order_items.product_id IS '판매자 상품 ID';
COMMENT ON COLUMN coupang_order_items.product_name IS '판매자 상품명';
COMMENT ON COLUMN coupang_order_items.sales_price IS '판매가';
COMMENT ON COLUMN coupang_order_items.order_price IS '주문금액';
COMMENT ON COLUMN coupang_order_items.raw_item_data IS '원본 아이템 데이터 (JSON)';
