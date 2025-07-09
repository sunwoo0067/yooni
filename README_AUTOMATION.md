# 쿠팡-오너클렌 자동화 시스템

쿠팡에서 주문이 들어오면 오너클렌에 자동으로 주문하고 송장을 받아오는 자동화 시스템입니다.

## 주요 기능

1. **쿠팡 주문 자동 수집**: 쿠팡 API를 통해 신규 주문을 자동으로 수집
2. **오너클렌 자동 발주**: 수집된 주문을 오너클렌에 자동으로 발주
3. **송장 번호 자동 업데이트**: 오너클렌에서 발송 완료 시 송장 번호를 쿠팡에 자동 업데이트

## 시스템 구성

### 워커 (Workers)

1. **CoupangFetchWorker** (`workers/coupang_fetch_worker.py`)
   - 쿠팡 API에서 주문 데이터 수집
   - ACCEPT 상태 주문을 NEW로 변환하여 저장

2. **OwnerclanPlaceWorker** (`workers/ownerclan_place_worker.py`)
   - NEW 상태 주문을 오너클렌에 발주
   - 상품 매핑 테이블을 통해 SKU 변환
   - 발주 완료 시 상태를 RECEIVED로 변경

3. **InvoiceUpdateWorker** (`workers/invoice_update_worker.py`)
   - 오너클렌에서 송장 번호 조회
   - 쿠팡 API로 송장 번호 업데이트
   - 완료 시 상태를 SHIPPED로 변경

4. **MainAutomationWorker** (`workers/main_automation_worker.py`)
   - 전체 자동화 프로세스 통합 실행
   - 주기적 실행 지원

## 사용 방법

### 1. 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정하세요:

```bash
# 쿠팡 API
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=your_vendor_id

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# 오너클렌
OWNERCLAN_USERNAME=your_username
OWNERCLAN_PASSWORD=your_password
```

### 2. 개별 워커 실행

```bash
# 쿠팡 주문 수집
python workers/coupang_fetch_worker.py --account-id 1

# 오너클렌 발주
python workers/ownerclan_place_worker.py --account-id 1

# 송장 업데이트
python workers/invoice_update_worker.py --account-id 1
```

### 3. 전체 자동화 실행

```bash
# 1회 실행
python workers/main_automation_worker.py --account-id 1

# 지속적 실행 (10분 간격)
python workers/main_automation_worker.py --account-id 1 --continuous

# 지속적 실행 (30분 간격)
python workers/main_automation_worker.py --account-id 1 --continuous --interval 30
```

### 4. 테스트 실행

```bash
# 전체 프로세스 테스트
python test_automation.py
```

## 데이터베이스 구조

### 주요 테이블

- **orders**: 통합 주문 관리
  - status: NEW → RECEIVED → SHIPPED
  - market_order_id: 쿠팡 주문번호
  - shipment_box_id: 쿠팡 묶음배송번호

- **order_items**: 주문 상품 정보

- **product_mappings**: 쿠팡-오너클렌 상품 매핑
  - market_sku: 쿠팡 상품 코드
  - ownerclan_item_key: 오너클렌 상품 키

- **ownerclan_orders**: 오너클렌 발주 정보
  - ownerclan_key: 오너클렌 주문 키
  - status: 오너클렌 주문 상태

## 주문 상태 플로우

```
쿠팡 주문 (ACCEPT) 
    ↓ [CoupangFetchWorker]
DB 저장 (NEW)
    ↓ [OwnerclanPlaceWorker]  
오너클렌 발주 (RECEIVED)
    ↓ [InvoiceUpdateWorker]
송장 업데이트 (SHIPPED)
```

## 주의사항

1. **상품 매핑**: 쿠팡 상품과 오너클렌 상품의 매핑이 `product_mappings` 테이블에 미리 설정되어 있어야 합니다.

2. **API 제한**: 쿠팡과 오너클렌 API의 호출 제한을 고려하여 적절한 간격으로 실행하세요.

3. **에러 처리**: 각 워커는 에러 발생 시 `automation_logs` 테이블에 로그를 기록합니다.

4. **송장 업데이트 타이밍**: 오너클렌에서 실제 송장이 등록된 후에 송장 업데이트가 가능합니다.

## 문제 해결

### 주문이 수집되지 않는 경우
- 환경 변수 확인
- 쿠팡 API 자격 증명 확인
- 날짜 범위 확인

### 오너클렌 발주가 실패하는 경우
- 상품 매핑 확인
- 오너클렌 자격 증명 확인
- 수신자 정보 유효성 확인

### 송장이 업데이트되지 않는 경우
- 오너클렌에서 송장 등록 여부 확인
- 택배사 코드 매핑 확인

## 모니터링

`automation_logs` 테이블에서 실행 로그를 확인할 수 있습니다:

```sql
SELECT * FROM automation_logs 
WHERE account_id = 1 
ORDER BY created_at DESC 
LIMIT 100;
```