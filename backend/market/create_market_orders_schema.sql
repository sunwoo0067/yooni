-- 마켓별 주문/판매내역 원본 데이터 JSONB 저장 테이블
CREATE TABLE IF NOT EXISTS market_raw_orders (
    id SERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id) NOT NULL,
    market_account_id INTEGER NOT NULL,  -- 마켓별 계정 ID (coupang.id, naver.id 등)
    market_order_id VARCHAR(100) NOT NULL,  -- 마켓의 주문 ID
    order_date TIMESTAMP,  -- 주문일시 (빠른 검색용)
    order_status VARCHAR(50),  -- 주문상태 (빠른 검색용)
    raw_data JSONB NOT NULL,  -- 원본 API 응답 데이터
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market_id, market_account_id, market_order_id)
);

-- 인덱스 생성
CREATE INDEX idx_market_raw_orders_market ON market_raw_orders(market_id, market_account_id);
CREATE INDEX idx_market_raw_orders_date ON market_raw_orders(order_date);
CREATE INDEX idx_market_raw_orders_status ON market_raw_orders(order_status);
CREATE INDEX idx_market_raw_orders_collected ON market_raw_orders(collected_at);
CREATE INDEX idx_market_raw_orders_jsonb ON market_raw_orders USING gin(raw_data);

-- 쿠팡 특화 인덱스
CREATE INDEX idx_market_raw_orders_coupang_date ON market_raw_orders((raw_data->>'paidAt'))
    WHERE market_id = (SELECT id FROM markets WHERE code = 'COUPANG');

-- 트리거: updated_at 자동 업데이트
CREATE TRIGGER update_market_raw_orders_updated_at BEFORE UPDATE ON market_raw_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰: 쿠팡 주문 조회용
CREATE OR REPLACE VIEW v_coupang_orders AS
SELECT 
    mro.id,
    c.alias as account_name,
    c.vendor_id,
    mro.market_order_id,
    mro.order_date,
    mro.order_status,
    raw_data->>'orderId' as order_id,
    raw_data->>'orderAt' as ordered_at,
    raw_data->>'paidAt' as paid_at,
    (raw_data->>'totalPrice')::numeric as total_price,
    (raw_data->>'totalSalePrice')::numeric as total_sale_price,
    (raw_data->>'discountPrice')::numeric as discount_price,
    raw_data->>'ordererName' as orderer_name,
    raw_data->>'ordererEmail' as orderer_email,
    raw_data->>'ordererPhoneNumber' as orderer_phone,
    raw_data->>'receiverName' as receiver_name,
    raw_data->>'receiverPhoneNumber' as receiver_phone,
    raw_data->>'shippingAddress' as shipping_address,
    raw_data->>'orderStatus' as status,
    raw_data->>'paymentMethod' as payment_method,
    raw_data->'orderItems' as order_items,
    mro.collected_at,
    mro.raw_data
FROM market_raw_orders mro
JOIN coupang c ON mro.market_account_id = c.id
WHERE mro.market_id = (SELECT id FROM markets WHERE code = 'COUPANG');

-- 뷰: 쿠팡 주문 아이템 상세
CREATE OR REPLACE VIEW v_coupang_order_items AS
SELECT 
    mro.id as order_id,
    c.alias as account_name,
    mro.market_order_id,
    item->>'vendorItemId' as vendor_item_id,
    item->>'vendorItemName' as vendor_item_name,
    item->>'productId' as product_id,
    item->>'sellerProductId' as seller_product_id,
    item->>'sellerProductName' as seller_product_name,
    (item->>'unitPrice')::numeric as unit_price,
    (item->>'orderPrice')::numeric as order_price,
    (item->>'discountPrice')::numeric as discount_price,
    (item->>'quantity')::integer as quantity,
    item->>'orderStatus' as item_status,
    item->>'deliveryStatus' as delivery_status,
    item->>'deliveryCompanyCode' as delivery_company,
    item->>'invoiceNumber' as invoice_number,
    item->>'shipmentBoxId' as shipment_box_id
FROM market_raw_orders mro
JOIN coupang c ON mro.market_account_id = c.id
CROSS JOIN LATERAL jsonb_array_elements(mro.raw_data->'orderItems') as item
WHERE mro.market_id = (SELECT id FROM markets WHERE code = 'COUPANG');

-- 뷰: 마켓별 판매 요약
CREATE OR REPLACE VIEW v_market_sales_summary AS
SELECT 
    m.name as market_name,
    m.code as market_code,
    DATE(mro.order_date) as sale_date,
    COUNT(DISTINCT mro.market_order_id) as order_count,
    COUNT(DISTINCT mro.market_account_id) as account_count,
    SUM(
        CASE 
            WHEN m.code = 'COUPANG' THEN (mro.raw_data->>'totalSalePrice')::numeric
            ELSE 0
        END
    ) as total_sales
FROM markets m
LEFT JOIN market_raw_orders mro ON m.id = mro.market_id
WHERE mro.order_date IS NOT NULL
GROUP BY m.id, m.name, m.code, DATE(mro.order_date)
ORDER BY sale_date DESC;

-- 함수: 주문 데이터에서 날짜 추출 (마켓별로 다른 필드명 처리)
CREATE OR REPLACE FUNCTION extract_order_date(market_code VARCHAR, raw_data JSONB)
RETURNS TIMESTAMP AS $$
BEGIN
    CASE market_code
        WHEN 'COUPANG' THEN
            RETURN (raw_data->>'paidAt')::timestamp;
        WHEN 'NAVER' THEN
            RETURN (raw_data->>'orderDate')::timestamp;
        WHEN '11ST' THEN
            RETURN (raw_data->>'ordDt')::timestamp;
        ELSE
            RETURN NULL;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- 함수: 주문 상태 추출 (마켓별로 다른 필드명 처리)
CREATE OR REPLACE FUNCTION extract_order_status(market_code VARCHAR, raw_data JSONB)
RETURNS VARCHAR AS $$
BEGIN
    CASE market_code
        WHEN 'COUPANG' THEN
            RETURN raw_data->>'orderStatus';
        WHEN 'NAVER' THEN
            RETURN raw_data->>'productOrderStatus';
        WHEN '11ST' THEN
            RETURN raw_data->>'ordStatNm';
        ELSE
            RETURN NULL;
    END CASE;
END;
$$ LANGUAGE plpgsql;