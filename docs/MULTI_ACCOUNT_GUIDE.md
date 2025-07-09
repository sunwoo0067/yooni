# 멀티계정/멀티마켓 시스템 가이드

## 개요

이 시스템은 여러 마켓플레이스(쿠팡, 네이버, 11번가 등)의 여러 계정을 동시에 관리하고, 여러 공급처(오너클랜, 1688, 타오바오 등)로 자동 발주할 수 있는 통합 자동화 시스템입니다.

## 데이터베이스 구조

### 핵심 개념

1. **사용자 (users)**: 시스템을 사용하는 실제 사용자
2. **마켓 계정 (market_accounts)**: 사용자가 보유한 각 마켓플레이스 판매 계정
3. **공급처 계정 (supplier_accounts)**: 사용자가 보유한 각 공급처 구매 계정
4. **통합 주문 (orders)**: 모든 마켓의 주문을 통합 관리
5. **상품 매핑 (product_mappings)**: 마켓 상품과 공급처 상품 간 매핑

### 주요 테이블

```sql
-- 사용자별로 여러 마켓 계정 보유 가능
users (1) --> (N) market_accounts
users (1) --> (N) supplier_accounts

-- 각 주문은 특정 마켓 계정에 속함
market_accounts (1) --> (N) orders

-- 주문은 여러 공급처로 발주 가능
orders (1) --> (N) supplier_orders

-- 상품 매핑으로 자동 발주 지원
market_accounts + supplier_accounts --> product_mappings
```

## 사용 방법

### 1. 데이터베이스 마이그레이션

```bash
# Supabase CLI 사용
supabase db push

# 또는 직접 SQL 실행
psql $DATABASE_URL < supabase/migrations/001_multi_account_schema.sql
```

### 2. 계정 설정

#### 마켓 계정 추가 (쿠팡 예시)

```sql
INSERT INTO market_accounts (user_id, market_id, account_name, credentials) VALUES
    ('your-user-id', 
     (SELECT id FROM markets WHERE code = 'coupang'),
     '쿠팡 메인 계정',
     '{
        "vendor_id": "A01234567",
        "access_key": "your-access-key",
        "secret_key": "your-secret-key"
     }'::jsonb
    );
```

#### 공급처 계정 추가 (오너클랜 예시)

```sql
INSERT INTO supplier_accounts (user_id, supplier_id, account_name, credentials) VALUES
    ('your-user-id',
     (SELECT id FROM suppliers WHERE code = 'ownerclan'),
     '오너클랜 메인 계정',
     '{
        "username": "your-username",
        "password": "your-password"
     }'::jsonb
    );
```

### 3. 상품 매핑 설정

```sql
INSERT INTO product_mappings (
    user_id, 
    market_account_id, 
    supplier_account_id,
    market_sku,
    supplier_sku,
    supplier_item_key,
    market_product_name,
    supplier_product_name
) VALUES
    ('your-user-id',
     1,  -- 마켓 계정 ID
     1,  -- 공급처 계정 ID
     'COUPANG_SKU_123',
     'OC_SKU_456',
     'OC_ITEM_789',
     '쿠팡 상품명',
     '오너클랜 상품명'
    );
```

### 4. 워커 실행

#### 쿠팡 주문 수집

```bash
python workers/coupang_fetch_worker_v2.py \
    --user-id "your-user-id" \
    --market-account-id 1 \
    --from 2025-01-01 \
    --to 2025-01-31
```

#### 오너클랜 자동 발주

```bash
python workers/ownerclan_place_worker_v2.py \
    --user-id "your-user-id" \
    --supplier-account-id 1
```

## 멀티계정 장점

1. **계정별 독립 관리**: 각 마켓/공급처 계정을 독립적으로 관리
2. **유연한 상품 매핑**: 같은 상품을 여러 공급처에서 구매 가능
3. **통합 주문 관리**: 모든 마켓의 주문을 한 곳에서 관리
4. **보안성**: Row Level Security로 사용자별 데이터 격리
5. **확장성**: 새로운 마켓/공급처 쉽게 추가 가능

## 주문 처리 흐름

```
1. 쿠팡 주문 수집 (CoupangFetchWorkerV2)
   - 각 마켓 계정별로 주문 수집
   - orders 테이블에 통합 저장
   - 상태: NEW

2. 오너클랜 자동 발주 (OwnerclanPlaceWorkerV2)
   - NEW 상태 주문 조회
   - product_mappings로 상품 매핑
   - 오너클랜으로 발주
   - 상태: PROCESSING

3. 송장 업데이트 (InvoiceUpdateWorkerV2)
   - 오너클랜에서 송장 조회
   - 쿠팡으로 송장 업데이트
   - 상태: SHIPPED
```

## 모니터링

### 주문 현황 조회

```sql
-- 사용자의 모든 주문 현황
SELECT 
    ma.account_name as market_account,
    o.status,
    COUNT(*) as count
FROM orders o
JOIN market_accounts ma ON o.market_account_id = ma.id
WHERE o.user_id = 'your-user-id'
GROUP BY ma.account_name, o.status;
```

### 자동화 로그 확인

```sql
-- 최근 에러 로그
SELECT * FROM automation_logs
WHERE user_id = 'your-user-id'
  AND level = 'ERROR'
ORDER BY created_at DESC
LIMIT 20;
```

## 주의사항

1. **인증 정보 보안**: credentials는 암호화하여 저장 권장
2. **API 제한**: 각 마켓/공급처의 API 호출 제한 준수
3. **상품 매핑 관리**: 정확한 SKU 매핑 필수
4. **에러 처리**: ERROR 상태 주문 정기적 확인 필요