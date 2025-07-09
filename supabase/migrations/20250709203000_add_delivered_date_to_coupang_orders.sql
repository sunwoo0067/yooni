-- Add delivered_date column to coupang_orders
ALTER TABLE coupang_orders
ADD COLUMN IF NOT EXISTS delivered_date TIMESTAMPTZ;

COMMENT ON COLUMN coupang_orders.delivered_date IS '배송완료 시각';
