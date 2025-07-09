ALTER TABLE coupang_orders
ADD COLUMN IF NOT EXISTS delivery_company_code TEXT,
ADD COLUMN IF NOT EXISTS shipping_price NUMERIC,
ADD COLUMN IF NOT EXISTS remote_price NUMERIC,
ADD COLUMN IF NOT EXISTS orderer_phone_number TEXT,
ADD COLUMN IF NOT EXISTS receiver_phone_number TEXT;

COMMENT ON COLUMN coupang_orders.delivery_company_code IS '택배사 코드';
COMMENT ON COLUMN coupang_orders.shipping_price IS '배송비';
COMMENT ON COLUMN coupang_orders.remote_price IS '도서산간 배송비';
COMMENT ON COLUMN coupang_orders.orderer_phone_number IS '주문자 연락처';
COMMENT ON COLUMN coupang_orders.receiver_phone_number IS '수취인 연락처';
