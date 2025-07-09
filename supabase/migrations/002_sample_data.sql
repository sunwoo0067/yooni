-- 샘플 데이터 삽입 (테스트용)
-- 실제 운영 시에는 이 파일을 실행하지 마세요.

-- 1. 테스트 사용자 생성
INSERT INTO users (id, email, name) VALUES
    ('d7b9c5a4-1234-5678-90ab-cdef12345678', 'test@example.com', '테스트 사용자');

-- 2. 마켓 계정 생성 (쿠팡)
INSERT INTO market_accounts (user_id, market_id, account_name, credentials, settings) VALUES
    ('d7b9c5a4-1234-5678-90ab-cdef12345678', 
     (SELECT id FROM markets WHERE code = 'coupang'),
     '내 쿠팡 계정',
     '{
        "vendor_id": "A01409684",
        "access_key": "2d6becfa-e876-47f1-aeab-b83a468313cc",
        "secret_key": "38f22728201cee67c6ad5bc11ad4d829b2a1cb78"
     }'::jsonb,
     '{
        "auto_fetch_enabled": true,
        "fetch_interval_minutes": 10
     }'::jsonb
    );

-- 3. 공급처 계정 생성 (오너클랜)
INSERT INTO supplier_accounts (user_id, supplier_id, account_name, credentials, settings) VALUES
    ('d7b9c5a4-1234-5678-90ab-cdef12345678',
     (SELECT id FROM suppliers WHERE code = 'ownerclan'),
     '내 오너클랜 계정',
     '{
        "username": "your_username",
        "password": "your_password"
     }'::jsonb,
     '{
        "auto_place_enabled": true,
        "shipping_fee_margin": 0
     }'::jsonb
    );

-- 4. 상품 매핑 샘플 (실제 SKU로 변경 필요)
-- INSERT INTO product_mappings (
--     user_id, 
--     market_account_id, 
--     supplier_account_id,
--     market_sku,
--     supplier_sku,
--     supplier_item_key,
--     market_product_name,
--     supplier_product_name,
--     settings
-- ) VALUES
--     ('d7b9c5a4-1234-5678-90ab-cdef12345678',
--      (SELECT id FROM market_accounts WHERE user_id = 'd7b9c5a4-1234-5678-90ab-cdef12345678' AND account_name = '내 쿠팡 계정'),
--      (SELECT id FROM supplier_accounts WHERE user_id = 'd7b9c5a4-1234-5678-90ab-cdef12345678' AND account_name = '내 오너클랜 계정'),
--      'COUPANG_SKU_123456',  -- 쿠팡 SKU
--      'OC_SKU_789012',       -- 오너클랜 SKU
--      'OC_ITEM_KEY_345678',  -- 오너클랜 상품키
--      '쿠팡 상품명',
--      '오너클랜 상품명',
--      '{
--         "price_margin_percent": 10,
--         "min_margin_amount": 1000
--      }'::jsonb
--     );

-- 5. 워커 상태 초기화
INSERT INTO worker_status (user_id, market_account_id, worker_type, status, settings) VALUES
    ('d7b9c5a4-1234-5678-90ab-cdef12345678',
     (SELECT id FROM market_accounts WHERE user_id = 'd7b9c5a4-1234-5678-90ab-cdef12345678' AND account_name = '내 쿠팡 계정'),
     'CoupangFetchWorkerV2',
     'IDLE',
     '{
        "enabled": true,
        "interval_minutes": 10,
        "statuses": ["ACCEPT"]
     }'::jsonb
    );