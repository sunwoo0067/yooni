ALTER TABLE coupang_orders
ADD COLUMN IF NOT EXISTS invoice_number TEXT;

COMMENT ON COLUMN coupang_orders.invoice_number IS '송장번호';
