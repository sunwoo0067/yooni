CREATE TABLE IF NOT EXISTS coupang_orders (
    shipment_box_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    ordered_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    status TEXT,
    orderer_name TEXT,
    orderer_safe_number TEXT,
    receiver_name TEXT,
    receiver_address TEXT,
    receiver_post_code TEXT,
    delivery_company_name TEXT,
    invoice_number TEXT,
    delivered_date TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE coupang_orders IS '쿠팡 주문 데이터';
COMMENT ON COLUMN coupang_orders.shipment_box_id IS '쿠팡 배송 ID (기본 키)';
COMMENT ON COLUMN coupang_orders.order_id IS '쿠팡 주문 ID';
COMMENT ON COLUMN coupang_orders.ordered_at IS '주문 시각';
COMMENT ON COLUMN coupang_orders.paid_at IS '결제 시각';
COMMENT ON COLUMN coupang_orders.status IS '주문 상태';
COMMENT ON COLUMN coupang_orders.orderer_name IS '주문자 이름';
COMMENT ON COLUMN coupang_orders.orderer_safe_number IS '주문자 안심번호';
COMMENT ON COLUMN coupang_orders.receiver_name IS '수취인 이름';
COMMENT ON COLUMN coupang_orders.receiver_address IS '수취인 주소';
COMMENT ON COLUMN coupang_orders.receiver_post_code IS '수취인 우편번호';
COMMENT ON COLUMN coupang_orders.delivery_company_name IS '택배사';
COMMENT ON COLUMN coupang_orders.invoice_number IS '송장번호';
COMMENT ON COLUMN coupang_orders.delivered_date IS '배송완료 시각';
COMMENT ON COLUMN coupang_orders.raw_data IS '원본 주문 데이터 (JSON)';
COMMENT ON COLUMN coupang_orders.created_at IS '레코드 생성 시각';
COMMENT ON COLUMN coupang_orders.updated_at IS '레코드 업데이트 시각';
