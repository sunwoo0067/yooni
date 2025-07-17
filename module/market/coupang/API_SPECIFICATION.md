# 쿠팡 파트너스 API 명세서

## 개요
이 문서는 쿠팡 파트너스 API 통합 클라이언트의 전체 명세서입니다. 각 모듈별 API 엔드포인트, 데이터 모델, 사용법을 포함합니다.

## 목차
- [아키텍처 구조](#아키텍처-구조)
- [공통 모듈](#공통-모듈)
- [CS (고객문의) 모듈](#cs-고객문의-모듈)
- [Sales (매출내역) 모듈](#sales-매출내역-모듈)
- [Settlement (지급내역) 모듈](#settlement-지급내역-모듈)
- [Order (주문관리) 모듈](#order-주문관리-모듈)
- [Product (상품관리) 모듈](#product-상품관리-모듈)
- [Returns (반품관리) 모듈](#returns-반품관리-모듈)
- [Exchange (교환관리) 모듈](#exchange-교환관리-모듈)
- [통합 클라이언트 사용법](#통합-클라이언트-사용법)

---

## 아키텍처 구조

### 공통 베이스 클라이언트
모든 API 클라이언트는 `BaseCoupangClient`를 상속받아 일관된 구조를 유지합니다:

```python
from market.coupang.common.base_client import BaseCoupangClient

class SpecificClient(BaseCoupangClient):
    def __init__(self, access_key=None, secret_key=None, vendor_id=None):
        super().__init__(access_key, secret_key, vendor_id)
    
    def get_api_name(self) -> str:
        return "특정 API 이름"
```

### 인증 시스템
- **HMAC-SHA256** 기반 인증
- 환경변수 자동 로드 (.env 파일)
- 필수 환경변수:
  - `COUPANG_ACCESS_KEY`
  - `COUPANG_SECRET_KEY`
  - `COUPANG_VENDOR_ID`

### 에러 핸들링
통합 에러 핸들링 시스템:
- `CoupangAPIError`: API 호출 관련 에러
- `CoupangAuthError`: 인증 관련 에러
- `CoupangNetworkError`: 네트워크 관련 에러

---

## 공통 모듈

### config.py - 통합 설정 관리
```python
from market.coupang.common.config import config

# 환경변수 검증
is_valid = config.validate_coupang_credentials()

# 설정값 조회
access_key = config.coupang_access_key
secret_key = config.coupang_secret_key
vendor_id = config.coupang_vendor_id
```

### errors.py - 에러 핸들링
```python
from market.coupang.common.errors import error_handler, CoupangAPIError

try:
    result = api_call()
except CoupangAPIError as e:
    error_handler(e, context="API 호출")
```

---

## CS (고객문의) 모듈

### API 엔드포인트

#### 1. 온라인 고객문의 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/onlineInquiries`
- **설명**: 고객문의 목록 조회 (7일 제한)
- **파라미터**:
  - `answeredType`: ALL, ANSWERED, NOANSWER
  - `createdAtFrom`, `createdAtTo`: YYYY-MM-DD 형식
  - `pageNum`, `pageSize`: 페이징

#### 2. 고객문의 답변
- **URL**: `POST /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/onlineInquiries/{inquiryId}/replies`
- **설명**: 고객문의에 답변 작성
- **Body**:
  ```json
  {
    "content": "답변 내용 (1~1000자)",
    "replyBy": "WING ID"
  }
  ```

#### 3. 콜센터 문의 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/callCenterInquiries`
- **설명**: 콜센터 문의 목록 조회
- **파라미터**:
  - `partnerCounselingStatus`: NONE, ANSWER, NO_ANSWER, TRANSFER

#### 4. 콜센터 문의 답변
- **URL**: `POST /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/callCenterInquiries/{inquiryId}/replies`

#### 5. 콜센터 문의 확인
- **URL**: `POST /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/callCenterInquiries/{inquiryId}/confirmations`

### 데이터 모델

#### InquirySearchParams
```python
@dataclass
class InquirySearchParams:
    vendor_id: str
    answered_type: str = "ALL"  # ALL, ANSWERED, NOANSWER
    created_at_from: str = None  # YYYY-MM-DD
    created_at_to: str = None    # YYYY-MM-DD
    page_num: int = 1
    page_size: int = 20
```

#### CustomerInquiry
```python
@dataclass
class CustomerInquiry:
    inquiry_id: int
    customer_id: str
    vendor_id: str
    category: str
    title: str
    content: str
    created_at: str
    status: str
```

### 편의 함수

#### 클라이언트 생성
```python
from market.coupang.cs import create_cs_client

# 기본 생성 (.env에서 자동 로드)
client = create_cs_client()

# 수동 설정
client = create_cs_client(access_key="key", secret_key="secret", vendor_id="vendor")
```

#### 빠른 조회 함수들
```python
from market.coupang.cs import (
    get_today_inquiries_quick,
    get_unanswered_inquiries_quick,
    reply_to_inquiry_quick
)

# 오늘의 문의 조회
today_inquiries = get_today_inquiries_quick()

# 미답변 문의 조회 (7일)
unanswered = get_unanswered_inquiries_quick(days=7)

# 빠른 답변
result = reply_to_inquiry_quick(
    inquiry_id=12345,
    content="답변 내용",
    reply_by="wing_id"
)
```

---

## Sales (매출내역) 모듈

### API 엔드포인트

#### 매출내역 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v1/revenue-history`
- **설명**: 매출내역 조회 (31일 제한)
- **파라미터**:
  - `vendorId`: 판매자 ID
  - `recognitionDateFrom`, `recognitionDateTo`: YYYY-MM-DD
  - `maxPerPage`: 페이지당 최대 개수 (1~1000)
  - `token`: 페이징 토큰

### 데이터 모델

#### RevenueSearchParams
```python
@dataclass
class RevenueSearchParams:
    vendor_id: str
    recognition_date_from: str  # YYYY-MM-DD
    recognition_date_to: str    # YYYY-MM-DD
    max_per_page: int = 20
    token: str = None
```

#### RevenueItem
```python
@dataclass
class RevenueItem:
    order_id: str
    product_id: str
    vendor_item_id: str
    product_name: str
    sale_price: int
    quantity: int
    commission_rate: float
    commission_fee: int
    recognition_date: str
```

### 편의 함수

```python
from market.coupang.sales import (
    create_sales_client,
    get_recent_revenue_quick,
    get_monthly_revenue_quick
)

# 최근 7일 매출
recent_revenue = get_recent_revenue_quick(days=7)

# 월별 매출
monthly_revenue = get_monthly_revenue_quick(year=2025, month=7)
```

---

## Settlement (지급내역) 모듈

### API 엔드포인트

#### 지급내역 조회
- **URL**: `GET /v2/providers/marketplace_openapi/apis/api/v1/settlement-histories`
- **설명**: 지급내역 조회
- **파라미터**:
  - `revenueRecognitionYearMonth`: YYYY-MM 형식

### 데이터 모델

#### SettlementHistory
```python
@dataclass
class SettlementHistory:
    settlement_date: str
    settlement_type: str  # MONTHLY, WEEKLY, DAILY, ADDITIONAL, RESERVE
    payment_status: str   # DONE, SUBJECT
    settlement_amount: int
    service_fee: int
    vat: int
    bank_name: str
    account_number: str
```

### 편의 함수

```python
from market.coupang.settlement import (
    create_settlement_client,
    get_current_month_settlement_quick
)

# 이번 달 지급내역
current_settlement = get_current_month_settlement_quick()
```

---

## Order (주문관리) 모듈

### API 엔드포인트

#### 1. 주문서 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets`
- **파라미터**: 날짜 범위, 주문 상태 등

#### 2. 주문 상태 변경
- **URL**: `PUT /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets`

#### 3. 배송정보 업로드
- **URL**: `POST /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets/acknowledgments`

### 편의 함수

```python
from market.coupang.order import create_order_client, get_today_orders_quick

# 오늘 주문 조회
today_orders = get_today_orders_quick(hours=24)
```

---

## Product (상품관리) 모듈

### API 엔드포인트

#### 1. 상품 등록
- **URL**: `POST /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/products`

#### 2. 상품 수정
- **URL**: `PUT /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/products/{productId}`

#### 3. 상품 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/products`

### 편의 함수

```python
from market.coupang.product import create_product_client

client = create_product_client()
```

---

## Returns (반품관리) 모듈

### API 엔드포인트

#### 반품/취소 요청 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/returnRequests`

### 편의 함수

```python
from market.coupang.returns import create_return_client, get_today_returns_quick

# 오늘 반품 요청
today_returns = get_today_returns_quick(days=1)
```

---

## Exchange (교환관리) 모듈

### API 엔드포인트

#### 교환 요청 조회
- **URL**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/exchangeRequests`

### 편의 함수

```python
from market.coupang.exchange import create_exchange_client, get_today_exchanges_quick

# 오늘 교환 요청
today_exchanges = get_today_exchanges_quick(days=1)
```

---

## 통합 클라이언트 사용법

### 1. 통합 클라이언트 생성

```python
from market.coupang import create_unified_client

# 모든 모듈을 포함하는 통합 클라이언트 생성
unified = create_unified_client()

# 개별 모듈 접근
cs_client = unified['cs']
sales_client = unified['sales']
settlement_client = unified['settlement']
order_client = unified['order']
product_client = unified['product']
returns_client = unified['returns']
exchange_client = unified['exchange']
```

### 2. 환경 설정 검증

```python
from market.coupang import validate_environment

if validate_environment():
    print("✅ 환경 설정 완료")
else:
    print("❌ 환경 설정 필요")
```

### 3. 개별 모듈 직접 사용

```python
from market.coupang import CSClient, SalesClient, SettlementClient

# 개별 클라이언트 직접 생성
cs_client = CSClient()
sales_client = SalesClient()
settlement_client = SettlementClient()
```

### 4. 편의 함수 활용

```python
from market.coupang.cs import get_today_inquiries_quick
from market.coupang.sales import get_recent_revenue_quick
from market.coupang.settlement import get_current_month_settlement_quick

# 대시보드 데이터 한 번에 수집
dashboard_data = {
    'inquiries': get_today_inquiries_quick(),
    'revenue': get_recent_revenue_quick(days=7),
    'settlement': get_current_month_settlement_quick()
}
```

---

## 모듈별 주요 특징

### CS 모듈
- **특징**: 온라인 문의와 콜센터 문의 분리 관리
- **제한**: 7일 날짜 범위 제한
- **고급 기능**: 답변 자동화, 일괄 답변 처리

### Sales 모듈
- **특징**: 매출 인식 날짜 기준 조회
- **제한**: 31일 날짜 범위 제한
- **고급 기능**: 매출 패턴 분석, 요약 리포트

### Settlement 모듈
- **특징**: 월별 지급내역 관리
- **제한**: 현재 월까지만 조회 가능
- **고급 기능**: 지급 유형별 분류, 수수료 계산

### Order 모듈
- **특징**: 실시간 주문 관리
- **제한**: 시간 기반 조회 (최대 24시간)
- **고급 기능**: 주문 상태 추적, 배송 관리

### Product 모듈
- **특징**: 상품 라이프사이클 관리
- **제한**: 상품별 개별 처리
- **고급 기능**: 옵션 관리, 이미지 처리

### Returns 모듈
- **특징**: 반품/취소 통합 관리
- **제한**: 처리 상태별 필터링
- **고급 기능**: 반품 패턴 분석

### Exchange 모듈
- **특징**: 교환 프로세스 관리
- **제한**: 교환 상태별 처리
- **고급 기능**: 교환 승인/거부 자동화

---

## 확장 가이드

### 새 모듈 추가 시

1. **기본 구조 생성**:
   ```python
   # new_module/
   # ├── __init__.py
   # ├── client.py (BaseCoupangClient 상속)
   # ├── models.py
   # ├── constants.py
   # ├── validators.py
   # └── utils.py
   ```

2. **편의 함수 추가**:
   ```python
   def create_new_module_client(access_key=None, secret_key=None, vendor_id=None):
       return NewModuleClient(access_key, secret_key, vendor_id)
   ```

3. **메인 __init__.py에 등록**:
   ```python
   from .new_module import create_new_module_client
   ```

### API 버전 업그레이드 시

1. **버전별 엔드포인트 관리**
2. **하위 호환성 유지**
3. **마이그레이션 가이드 제공**

이 명세서는 쿠팡 파트너스 API 통합 클라이언트의 모든 기능을 포괄하며, 향후 확장과 유지보수를 위한 가이드라인을 제공합니다.