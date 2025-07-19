# 쿠팡 파트너스 API 통합 클라이언트

## 개요
쿠팡 파트너스 API와의 통합을 위한 포괄적인 Python 클라이언트 라이브러리입니다. 고객문의(CS), 매출내역, 지급내역, 주문관리, 상품관리, 반품관리, 교환관리의 7개 핵심 모듈을 제공합니다.

## 주요 특징
- 🔐 **HMAC-SHA256 인증** 자동 처리
- 🏗️ **모듈형 아키텍처** - 각 기능별 독립적 사용 가능
- 🚀 **편의 함수** 제공 - 빠른 조회 및 처리
- 📊 **통합 클라이언트** - 모든 모듈 한 번에 접근
- ⚡ **자동 에러 핸들링** 및 재시도 로직
- 📝 **완전한 타입 힌트** 지원
- 🧪 **포괄적인 테스트** 스위트

## 빠른 시작

### 1. 환경 설정
```bash
# .env 파일 생성
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=your_vendor_id
```

### 2. 기본 사용법
```python
from market.coupang import create_unified_client, validate_environment

# 환경 검증
if validate_environment():
    # 통합 클라이언트 생성
    unified = create_unified_client()
    
    # 각 모듈 사용
    cs_client = unified['cs']
    sales_client = unified['sales']
    settlement_client = unified['settlement']
```

### 3. 편의 함수 활용
```python
from market.coupang.cs import get_today_inquiries_quick
from market.coupang.sales import get_recent_revenue_quick
from market.coupang.settlement import get_current_month_settlement_quick

# 오늘 고객문의
inquiries = get_today_inquiries_quick()

# 최근 7일 매출
revenue = get_recent_revenue_quick(days=7)

# 이번 달 지급내역
settlement = get_current_month_settlement_quick()
```

## 모듈별 기능

### 📞 CS (고객문의) 모듈
- 온라인 고객문의 조회 및 답변
- 콜센터 문의 관리
- 자동 답변 및 일괄 처리
- 문의 패턴 분석

```python
from market.coupang.cs import create_cs_client, reply_to_inquiry_quick

# 문의에 답변
result = reply_to_inquiry_quick(
    inquiry_id=12345,
    content="답변 내용",
    reply_by="wing_id"
)
```

### 💰 Sales (매출내역) 모듈
- 매출 내역 조회 (최대 31일)
- 매출 패턴 분석
- 수수료 및 순수익 계산
- 상품별 매출 집계

```python
from market.coupang.sales import get_monthly_revenue_quick

# 월별 매출 조회
revenue = get_monthly_revenue_quick(year=2025, month=7)
```

### 🏦 Settlement (지급내역) 모듈
- 월별 지급내역 조회
- 지급 유형별 분류
- 수수료 및 세금 계산
- 지급 상태 추적

```python
from market.coupang.settlement import get_current_month_settlement_quick

# 이번 달 지급내역
settlement = get_current_month_settlement_quick()
```

### 📦 Order (주문관리) 모듈
- 주문서 조회 및 관리
- 주문 상태 변경
- 배송정보 업로드
- 주문 취소 처리

```python
from market.coupang.order import get_today_orders_quick

# 오늘 주문 조회
orders = get_today_orders_quick(hours=24)
```

### 📱 Product (상품관리) 모듈
- 상품 등록 및 수정
- 상품 조회 및 검색
- 재고 관리
- 카테고리 관리

```python
from market.coupang.product import create_product_client

client = create_product_client()
products = client.get_products_by_vendor_id("vendor_id")
```

### 🔄 Returns (반품관리) 모듈
- 반품 요청 조회
- 반품 승인/거부 처리
- 반품 패턴 분석
- 귀책사유별 분류

```python
from market.coupang.returns import get_today_returns_quick

# 오늘 반품 요청
returns = get_today_returns_quick(days=1)
```

### 🔀 Exchange (교환관리) 모듈
- 교환 요청 조회
- 교환 승인/거부 처리
- 교환 배송 관리
- 교환 사유 분석

```python
from market.coupang.exchange import get_today_exchanges_quick

# 오늘 교환 요청
exchanges = get_today_exchanges_quick(days=1)
```

## 고급 사용법

### 통합 대시보드 데이터 수집
```python
from market.coupang import create_unified_client

def create_dashboard():
    unified = create_unified_client()
    
    return {
        'inquiries': unified['cs'].get_today_inquiries(),
        'revenue': unified['sales'].get_recent_revenue(days=7),
        'settlement': unified['settlement'].get_current_month(),
        'orders': unified['order'].get_today_orders(),
        'returns': unified['returns'].get_today_returns(),
        'exchanges': unified['exchange'].get_today_exchanges()
    }

dashboard = create_dashboard()
```

### 배치 작업 처리
```python
from concurrent.futures import ThreadPoolExecutor

def process_batch_operations():
    unified = create_unified_client()
    
    def fetch_cs_data():
        return unified['cs'].get_inquiry_list()
    
    def fetch_sales_data():
        return unified['sales'].get_revenue_history()
    
    # 병렬 처리
    with ThreadPoolExecutor(max_workers=3) as executor:
        cs_future = executor.submit(fetch_cs_data)
        sales_future = executor.submit(fetch_sales_data)
        
        results = {
            'cs': cs_future.result(),
            'sales': sales_future.result()
        }
    
    return results
```

### 자동화된 고객 서비스
```python
from market.coupang.cs import get_unanswered_inquiries_quick, reply_to_inquiry_quick

def auto_reply_system():
    # 미답변 문의 조회
    unanswered = get_unanswered_inquiries_quick(days=1)
    
    # 자동 답변 템플릿
    templates = {
        "배송": "배송 관련 안내드립니다...",
        "반품": "반품 절차는 다음과 같습니다..."
    }
    
    for inquiry in unanswered.get('data', []):
        content = inquiry.get('content', '').lower()
        
        for keyword, template in templates.items():
            if keyword in content:
                reply_to_inquiry_quick(
                    inquiry_id=inquiry['inquiry_id'],
                    content=template,
                    reply_by="auto_system"
                )
                break
```

## 에러 처리

### 공통 에러 처리
```python
from market.coupang.common.errors import (
    CoupangAPIError,
    CoupangAuthError,
    CoupangNetworkError
)

try:
    result = api_call()
except CoupangAuthError:
    print("인증 오류 - 토큰을 확인하세요")
except CoupangNetworkError:
    print("네트워크 오류 - 연결을 확인하세요")
except CoupangAPIError as e:
    print(f"API 오류: {e}")
```

### 재시도 로직
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=2)
def fetch_data():
    return api_call()
```

## 테스트

### 개별 모듈 테스트
```bash
# CS 모듈 테스트
python -m cs.test_cs

# Sales 모듈 테스트  
python -m sales.test_sales

# Settlement 모듈 테스트
python -m settlement.test_settlement
```

### 통합 테스트
```bash
# 전체 모듈 테스트
python -c "from market.coupang import validate_environment; print('✅ 성공' if validate_environment() else '❌ 실패')"
```

## API 제한사항

### 날짜 범위 제한
- **CS 모듈**: 최대 7일
- **Sales 모듈**: 최대 31일  
- **Settlement 모듈**: 현재 월까지
- **Order 모듈**: 최대 7일

### 페이징 제한
- **CS**: 페이지당 최대 100건
- **Sales**: 페이지당 최대 1000건
- **기타**: 페이지당 최대 50건

### Rate Limiting
- 초당 최대 10-15 요청
- 자동 재시도 로직 포함
- 타임아웃 설정 가능

## 확장 가이드

### 새 모듈 추가
1. `BaseCoupangClient` 상속
2. 편의 함수 추가
3. 메인 `__init__.py`에 등록
4. 테스트 코드 작성

### 커스텀 클라이언트
```python
from market.coupang.common.base_client import BaseCoupangClient

class CustomClient(BaseCoupangClient):
    def __init__(self, access_key=None, secret_key=None, vendor_id=None):
        super().__init__(access_key, secret_key, vendor_id)
    
    def get_api_name(self) -> str:
        return "Custom API"
    
    def custom_method(self):
        return self._make_request("GET", "/custom/endpoint")
```

## 문서

- **📋 [API 명세서](./API_SPECIFICATION.md)**: 모든 API 엔드포인트 및 파라미터
- **📊 [데이터 모델](./DATA_MODELS.md)**: 완전한 데이터 스키마 정의
- **💡 [사용 예제](./USAGE_EXAMPLES.md)**: 실전 시나리오 및 코드 예제

## 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 생성해 주세요.

---

**쿠팡 파트너스 API 통합 클라이언트 v2.0.0**  
© 2025 OwnerClan API Team