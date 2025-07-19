# 쿠팡 파트너스 발주서 관리 API

쿠팡 파트너스 API를 사용한 발주서 목록 조회 및 관리 기능을 제공합니다.

## 📁 파일 구조

```
order/
├── __init__.py                 # 패키지 초기화 및 공개 API
├── constants.py               # API 상수 및 설정값
├── models.py                  # 데이터 모델 (OrderSheet, Orderer, Receiver 등)
├── validators.py              # 파라미터 검증 함수들
├── utils.py                   # 공통 유틸리티 함수들
├── order_client.py           # 메인 API 클라이언트
├── order_example.py          # 사용 예제 코드
├── test_order.py             # 테스트 코드
└── README.md                 # 이 문서
```

## 🚀 주요 기능

### 1. 발주서 목록 조회
- **일단위 페이징**: 기본 페이징 방식으로 발주서 목록 조회
- **분단위 전체**: 지정된 시간 범위의 모든 발주서 일괄 조회
- **상태별 필터링**: 특정 상태(ACCEPT, INSTRUCT, DEPARTURE 등)의 발주서만 조회
- **전체 페이지 조회**: 자동으로 모든 페이지를 순회하여 전체 데이터 수집

### 2. 데이터 모델
- **OrderSheet**: 발주서 정보
- **Orderer**: 주문자 정보
- **Receiver**: 수취인 정보
- **OrderItem**: 주문 아이템 정보
- **OrderSheetSearchParams**: 검색 파라미터

### 3. 검증 및 유틸리티
- **파라미터 검증**: 판매자 ID, 날짜 형식, 상태 코드 등 검증
- **응답 처리**: 일관된 형식의 API 응답 처리
- **요약 정보**: 발주서 통계 및 요약 정보 계산

## 📖 사용법

### 기본 설정

```python
from order_client import OrderClient
from models import OrderSheetSearchParams

# 클라이언트 초기화 (환경변수에서 키 읽기)
client = OrderClient()

# 또는 직접 키 지정
client = OrderClient(access_key="your_access_key", secret_key="your_secret_key")
```

### 기본 발주서 조회

```python
from datetime import datetime, timedelta

# 검색 파라미터 설정
params = OrderSheetSearchParams(
    vendor_id="A12345678",  # 실제 판매자 ID
    created_at_from="2024-01-01",
    created_at_to="2024-01-02", 
    status="ACCEPT",  # 결제완료 상태
    max_per_page=20
)

# 발주서 목록 조회
result = client.get_order_sheets(params)

if result["success"]:
    print(f"조회된 발주서 수: {len(result['data'])}개")
    for order in result["data"]:
        print(f"주문번호: {order['orderId']}, 상태: {order['status']}")
else:
    print(f"조회 실패: {result['error']}")
```

### 전체 페이지 조회

```python
# 전체 페이지를 자동으로 순회하여 모든 발주서 조회
result = client.get_order_sheets_all_pages(params)

if result["success"]:
    print(f"전체 발주서 수: {len(result['data'])}개")
    print(f"조회한 페이지 수: {result['page_count']}페이지")
    
    # 요약 정보 출력
    if result.get("summary"):
        summary = result["summary"]
        print(f"총 주문 금액: {summary['total_amount']:,}원")
        print(f"총 배송비: {summary['total_shipping_fee']:,}원")
```

### 상태별 조회 (편의 메서드)

```python
# 특정 상태의 발주서만 조회
result = client.get_order_sheets_by_status(
    vendor_id="A12345678",
    created_at_from="2024-01-01",
    created_at_to="2024-01-07",
    status="DELIVERING",  # 배송중 상태
    max_per_page=50
)
```

### 분단위 전체 조회

```python
# searchType을 timeFrame으로 설정하여 분단위 전체 조회
params.search_type = "timeFrame"
result = client.get_order_sheets_timeframe(params)
```

### 요약 정보 조회

```python
# 날짜 범위별 발주서 요약 정보 조회
summary_result = client.get_order_summary_by_date_range(
    vendor_id="A12345678",
    created_at_from="2024-01-01",
    created_at_to="2024-01-07"
)

if summary_result["success"]:
    data = summary_result["data"]
    total = data["total_summary"]
    
    print(f"총 발주서 수: {total['total_orders']}개")
    print(f"총 주문 금액: {total['total_amount']:,}원")
    
    # 상태별 현황
    for status, count in total["status_summary"].items():
        print(f"{status}: {count}개")
```

## 📋 발주서 상태 코드

| 코드 | 의미 |
|------|------|
| ACCEPT | 결제완료 |
| INSTRUCT | 상품준비중 |
| DEPARTURE | 배송지시 |
| DELIVERING | 배송중 |
| FINAL_DELIVERY | 배송완료 |
| NONE_TRACKING | 업체 직접 배송(추적불가) |

## 🔧 환경 설정

환경변수를 설정하여 API 키를 관리할 수 있습니다:

```bash
export COUPANG_ACCESS_KEY="your_access_key"
export COUPANG_SECRET_KEY="your_secret_key"
export COUPANG_VENDOR_ID="your_vendor_id"
```

또는 `.env` 파일을 생성하여 설정할 수 있습니다:

```env
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=A12345678
```

## 📝 예제 실행

```bash
# 기본 예제 실행
python order_example.py

# 전체 예제 실행 (order_example.py 내에서 주석 해제 필요)
python order_example.py
```

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
python test_order.py

# 단일 테스트 클래스 실행
python test_order.py single
```

## ⚠️ 주의사항

1. **판매자 ID**: 실제 쿠팡 파트너스에서 발급받은 판매자 ID를 사용해야 합니다 (예: A12345678)
2. **날짜 범위**: 최대 31일까지만 조회 가능합니다
3. **API 제한**: 쿠팡 파트너스 API의 호출 제한에 주의하세요
4. **인증**: 올바른 ACCESS_KEY와 SECRET_KEY가 필요합니다

## 🔍 트러블슈팅

### 인증 오류 (401)
```
해결방법: ACCESS_KEY와 SECRET_KEY 확인
```

### 잘못된 판매자 ID (400)
```
해결방법: 판매자 ID가 A+8자리 숫자 형태인지 확인
```

### 날짜 범위 오류 (400)
```
해결방법: 날짜 형식(YYYY-MM-DD)과 31일 이내 범위 확인
```

### 데이터 없음
```
해결방법: 날짜 범위나 상태 조건 조정
```

## 📚 추가 정보

- [쿠팡 파트너스 API 공식 문서](https://developers.coupangcorp.com/)
- [API 명세서](https://developers.coupangcorp.com/hc/ko/articles/360034549853)

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.