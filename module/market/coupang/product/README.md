# 쿠팡 상품 관리 API 클라이언트

쿠팡 파트너스 API의 상품 관리 기능을 위한 모듈화된 Python 클라이언트 라이브러리입니다.

## 📁 모듈 구조

```
product/
├── __init__.py          # 패키지 초기화 및 편의 import
├── client.py            # 메인 ProductClient 클래스
├── models.py            # 데이터 모델 클래스들
├── constants.py         # API 상수 및 설정값들
├── validators.py        # 데이터 검증 함수들
├── product_client_legacy.py  # 기존 단일 파일 (백업)
└── README.md           # 이 파일
```

## 🚀 빠른 시작

### 기본 사용법

```python
from market.coupang.product import ProductClient, ProductRequest, ProductItem

# 클라이언트 초기화
client = ProductClient()

# 상품 등록
product_request = ProductRequest(
    display_category_code=56137,
    seller_product_name="테스트 상품",
    vendor_id="A00012345",
    # ... 기타 필수 필드들
)

result = client.create_product(product_request)
```

### 편의 별칭 사용

```python
from market.coupang.product import Client, SearchParams

# 짧은 별칭으로 사용 가능
client = Client()
params = SearchParams(vendor_id="A00012345")
```

## 📋 주요 기능

### 1. 상품 관리
- **상품 등록**: `create_product()`
- **상품 조회**: `get_product()`, `get_product_partial()`
- **상품 수정**: `update_product()`, `update_product_partial()`
- **상품 승인**: `request_product_approval()`

### 2. 상품 목록 조회
- **페이징 조회**: `list_products()`
- **시간 구간 조회**: `get_products_by_time_frame()`
- **등록 현황 조회**: `get_inflow_status()`

### 3. 유틸리티
- **카테고리 추천**: `recommend_category()`

## 🗂️ 데이터 모델

### ProductRequest
상품 등록/수정을 위한 메인 요청 모델

```python
from market.coupang.product import ProductRequest, ProductItem, ProductImage

request = ProductRequest(
    display_category_code=56137,
    seller_product_name="상품명",
    vendor_id="A00012345",
    sale_started_at="2024-01-01T00:00:00",
    sale_ended_at="2099-12-31T23:59:59",
    vendor_user_id="testuser",
    items=[
        ProductItem(
            item_name="옵션1",
            original_price=20000,
            sale_price=15000,
            maximum_buy_count=100,
            maximum_buy_for_person=5,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1
        )
    ],
    images=[
        ProductImage(
            image_order=0,
            image_type="REPRESENTATION",
            vendor_path="https://example.com/image.jpg"
        )
    ]
)
```

### ProductSearchParams
상품 목록 조회를 위한 검색 파라미터

```python
from market.coupang.product import ProductSearchParams

params = ProductSearchParams(
    vendor_id="A00012345",
    max_per_page=20,
    status="APPROVED",
    seller_product_name="검색어"
)
```

## 🔧 상수 및 설정

```python
from market.coupang.product import PRODUCT_STATUS, DELIVERY_METHODS

# 상품 상태 확인
if status in PRODUCT_STATUS:
    print(f"상태: {PRODUCT_STATUS[status]}")

# 배송 방법 확인
if method in DELIVERY_METHODS:
    print(f"배송 방법: {DELIVERY_METHODS[method]}")
```

## ✅ 데이터 검증

```python
from market.coupang.product import validate_product_request, validate_vendor_id

# 상품 요청 검증
try:
    validate_product_request(request)
    print("✅ 검증 통과")
except ValueError as e:
    print(f"❌ 검증 실패: {e}")

# 판매자 ID 검증
if validate_vendor_id("A00012345"):
    print("✅ 유효한 판매자 ID")
```

## 📖 예제 파일

### 기본 예제들
- `product_example.py` - 전체 기능 종합 예제
- `product_list_example.py` - 상품 목록 조회 예제
- `product_time_frame_example.py` - 시간 구간 조회 예제
- `product_inflow_status_example.py` - 등록 현황 조회 예제

### 실제 API 테스트
- `product_test.py` - 실제 API 기본 테스트
- `product_list_test.py` - 실제 API 목록 조회 테스트
- `product_time_frame_test.py` - 실제 API 시간 구간 테스트
- `product_inflow_status_test.py` - 실제 API 현황 조회 테스트

### 특화 예제들
- `product_update_example.py` - 상품 수정 예제
- `product_partial_update_example.py` - 부분 수정 예제

## 🔑 환경 설정

실제 API 사용을 위해 다음 환경변수를 설정하세요:

```bash
export COUPANG_ACCESS_KEY='your_access_key'
export COUPANG_SECRET_KEY='your_secret_key'
export COUPANG_VENDOR_ID='your_vendor_id'
```

## 🏗️ 아키텍처 장점

### 1. 모듈화
- **분리된 책임**: 각 모듈이 명확한 역할을 담당
- **재사용성**: 개별 모듈을 독립적으로 import 가능
- **유지보수성**: 기능별로 코드가 분리되어 수정이 용이

### 2. 확장성
- **새로운 모델 추가**: `models.py`에 추가
- **새로운 상수 추가**: `constants.py`에 추가
- **새로운 검증 추가**: `validators.py`에 추가

### 3. 편의성
- **통합 import**: `__init__.py`를 통한 편리한 import
- **별칭 제공**: 자주 사용하는 클래스의 짧은 별칭
- **타입 힌트**: 모든 함수와 클래스에 타입 힌트 제공

## 📝 주요 개선사항

### 기존 대비 장점
1. **코드 길이 단축**: 1300+ 줄 → 4개 모듈로 분산
2. **가독성 향상**: 기능별 파일 분리
3. **재사용성 증대**: 모듈 단위 import 가능
4. **유지보수성**: 수정 시 해당 모듈만 변경
5. **확장성**: 새 기능 추가 시 모듈별 확장

### 호환성 
- **기존 코드**: `product_client_legacy.py`로 백업 보관
- **신규 코드**: 새로운 모듈 구조 사용 권장
- **마이그레이션**: import 문만 변경하면 완료

## 🛠️ 개발자 가이드

### 새로운 API 추가
1. **모델**: `models.py`에 필요한 데이터 클래스 추가
2. **상수**: `constants.py`에 API 경로 및 관련 상수 추가
3. **검증**: `validators.py`에 검증 함수 추가
4. **클라이언트**: `client.py`에 메서드 추가
5. **익스포트**: `__init__.py`에 새 클래스/함수 추가

### 예제 파일 작성
1. **기본 예제**: 기능 시연용 Mock 데이터 사용
2. **실제 테스트**: 환경변수 기반 실제 API 호출
3. **import 구조**: `from market.coupang.product import ...` 사용

이제 더욱 깔끔하고 유지보수가 쉬운 구조로 쿠팡 상품 API를 활용할 수 있습니다! 🎉