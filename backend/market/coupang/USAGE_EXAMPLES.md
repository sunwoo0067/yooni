# 쿠팡 파트너스 API 클라이언트 사용 예제

## 개요
이 문서는 쿠팡 파트너스 API 통합 클라이언트의 실제 사용 예제를 제공합니다.

## 목차
- [기본 설정](#기본-설정)
- [통합 클라이언트 사용](#통합-클라이언트-사용)
- [모듈별 사용 예제](#모듈별-사용-예제)
- [고급 사용 패턴](#고급-사용-패턴)
- [에러 처리](#에러-처리)
- [실전 시나리오](#실전-시나리오)

---

## 기본 설정

### 환경변수 설정 (.env 파일)
```bash
# 쿠팡 파트너스 API 인증 정보
COUPANG_ACCESS_KEY=your_access_key_here
COUPANG_SECRET_KEY=your_secret_key_here
COUPANG_VENDOR_ID=your_vendor_id_here
```

### 환경 검증
```python
from market.coupang import validate_environment, get_default_vendor_id

# 환경 설정 검증
if validate_environment():
    print("✅ 환경 설정 완료")
    print(f"📋 기본 벤더 ID: {get_default_vendor_id()}")
else:
    print("❌ 환경 설정 필요 - .env 파일을 확인하세요")
```

---

## 통합 클라이언트 사용

### 모든 모듈에 접근하는 통합 클라이언트
```python
from market.coupang import create_unified_client

# 통합 클라이언트 생성
unified = create_unified_client()

# 사용 가능한 모듈 확인
print("사용 가능한 모듈:", list(unified.keys()))
# 출력: ['cs', 'sales', 'settlement', 'order', 'product', 'returns', 'exchange']

# 각 모듈 접근
cs_client = unified['cs']
sales_client = unified['sales']
settlement_client = unified['settlement']
order_client = unified['order']
product_client = unified['product']
returns_client = unified['returns']
exchange_client = unified['exchange']
```

---

## 모듈별 사용 예제

### 1. CS (고객문의) 모듈

#### 기본 사용
```python
from market.coupang.cs import (
    create_cs_client,
    get_today_inquiries_quick,
    get_unanswered_inquiries_quick,
    reply_to_inquiry_quick
)

# 클라이언트 생성
cs_client = create_cs_client()

# 오늘의 문의 조회
today_inquiries = get_today_inquiries_quick()
print(f"오늘 문의 수: {len(today_inquiries.get('data', []))}")

# 미답변 문의 조회 (최근 7일)
unanswered = get_unanswered_inquiries_quick(days=7)
print(f"미답변 문의 수: {len(unanswered.get('data', []))}")

# 문의에 답변하기
result = reply_to_inquiry_quick(
    inquiry_id=12345,
    content="안녕하세요. 문의해주신 내용에 대해 답변드립니다...",
    reply_by="your_wing_id"
)
print(f"답변 결과: {result['success']}")
```

#### 고급 사용 - 일괄 답변 처리
```python
from market.coupang.cs import CSClient, bulk_reply_quick

# 여러 문의에 일괄 답변
reply_requests = [
    {
        "inquiry_id": 12345,
        "content": "첫 번째 문의 답변입니다.",
        "reply_by": "wing_id_1"
    },
    {
        "inquiry_id": 12346,
        "content": "두 번째 문의 답변입니다.",
        "reply_by": "wing_id_2"
    }
]

bulk_result = bulk_reply_quick(reply_requests)
print(f"일괄 답변 결과: {bulk_result}")
```

#### 콜센터 문의 관리
```python
from market.coupang.cs import (
    create_call_center_client,
    get_call_center_inquiries_quick,
    reply_to_call_center_inquiry_quick
)

# 콜센터 클라이언트 생성
cc_client = create_call_center_client()

# 답변 대기 중인 콜센터 문의 조회
pending_inquiries = get_call_center_inquiries_quick(
    counseling_status="ANSWER", 
    days=7
)

# 콜센터 문의에 답변
cc_reply_result = reply_to_call_center_inquiry_quick(
    inquiry_id=54321,
    vendor_id="your_vendor_id",
    content="콜센터 문의에 대한 답변입니다.",
    reply_by="wing_id",
    parent_answer_id=123
)
```

### 2. Sales (매출내역) 모듈

#### 기본 매출 조회
```python
from market.coupang.sales import (
    create_sales_client,
    get_recent_revenue_quick,
    get_monthly_revenue_quick,
    get_revenue_summary_quick
)

# 최근 7일 매출
recent_revenue = get_recent_revenue_quick(days=7)
print(f"최근 7일 매출 항목: {len(recent_revenue.get('data', []))}")

# 이번 달 매출
monthly_revenue = get_monthly_revenue_quick(year=2025, month=7)
print(f"이번 달 매출: {monthly_revenue}")

# 매출 요약 (최근 30일)
revenue_summary = get_revenue_summary_quick(days=30)
print(f"30일 매출 요약: {revenue_summary}")
```

#### 고급 매출 분석
```python
from market.coupang.sales import SalesClient
from datetime import datetime, timedelta

sales_client = create_sales_client()

# 특정 기간 상세 매출 분석
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

detailed_revenue = sales_client.get_revenue_history_with_date_range(
    vendor_id="your_vendor_id",
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d')
)

# 매출 패턴 분석 리포트 생성
analysis_report = sales_client.create_revenue_summary_report(
    vendor_id="your_vendor_id",
    days=30
)
print(f"매출 분석 리포트: {analysis_report}")
```

### 3. Settlement (지급내역) 모듈

#### 기본 지급내역 조회
```python
from market.coupang.settlement import (
    create_settlement_client,
    get_current_month_settlement_quick,
    get_previous_month_settlement_quick
)

# 이번 달 지급내역
current_settlement = get_current_month_settlement_quick()
print(f"이번 달 지급내역: {current_settlement}")

# 지난 달 지급내역
previous_settlement = get_previous_month_settlement_quick()
print(f"지난 달 지급내역: {previous_settlement}")
```

#### 지급내역 상세 분석
```python
from market.coupang.settlement import SettlementClient

settlement_client = create_settlement_client()

# 최근 3개월 지급내역 요약
settlement_summary = settlement_client.create_settlement_summary_report(months=3)
print(f"3개월 지급내역 요약: {settlement_summary}")

# 특정 월의 상세 지급내역
settlement_detail = settlement_client.get_settlement_history("2025-07")
for history in settlement_detail.get('data', []):
    print(f"지급일: {history['settlement_date']}, 금액: {history['settlement_amount']:,}원")
```

### 4. Order (주문관리) 모듈

#### 기본 주문 조회
```python
from market.coupang.order import (
    create_order_client,
    get_today_orders_quick
)

# 오늘 주문 조회 (최근 24시간)
today_orders = get_today_orders_quick(hours=24)
print(f"오늘 주문 수: {len(today_orders.get('data', []))}")

# 최근 12시간 주문
recent_orders = get_today_orders_quick(hours=12)
print(f"최근 12시간 주문: {len(recent_orders.get('data', []))}")
```

#### 주문 상세 관리
```python
from market.coupang.order import OrderClient

order_client = create_order_client()

# 특정 주문 상세 조회
order_detail = order_client.get_order_sheet_by_order_id(
    vendor_id="your_vendor_id",
    order_id="20250714123456"
)

# 주문 상태 변경
processing_result = order_client.update_shipment_box_info(
    vendor_id="your_vendor_id",
    shipment_box_id="BOX123456",
    delivery_company_code="CJGLS",
    invoice_number="123456789012"
)
```

### 5. Product (상품관리) 모듈

#### 기본 상품 관리
```python
from market.coupang.product import create_product_client

product_client = create_product_client()

# 상품 목록 조회
products = product_client.get_products_by_vendor_id(
    vendor_id="your_vendor_id",
    page=1,
    size=20
)

# 특정 상품 상세 조회
product_detail = product_client.get_product_by_id(
    vendor_id="your_vendor_id",
    product_id="PROD123456"
)
```

### 6. Returns (반품관리) 모듈

#### 반품 요청 관리
```python
from market.coupang.returns import (
    create_return_client,
    get_today_returns_quick
)

# 오늘 반품 요청
today_returns = get_today_returns_quick(days=1)
print(f"오늘 반품 요청: {len(today_returns.get('data', []))}")

# 최근 7일 반품 요청
recent_returns = get_today_returns_quick(days=7)
print(f"최근 7일 반품: {len(recent_returns.get('data', []))}")
```

### 7. Exchange (교환관리) 모듈

#### 교환 요청 관리
```python
from market.coupang.exchange import (
    create_exchange_client,
    get_today_exchanges_quick
)

# 오늘 교환 요청
today_exchanges = get_today_exchanges_quick(days=1)
print(f"오늘 교환 요청: {len(today_exchanges.get('data', []))}")
```

---

## 고급 사용 패턴

### 1. 통합 대시보드 데이터 수집
```python
from market.coupang import create_unified_client
from market.coupang.cs import get_today_inquiries_quick, get_unanswered_inquiries_quick
from market.coupang.sales import get_recent_revenue_quick
from market.coupang.settlement import get_current_month_settlement_quick
from market.coupang.order import get_today_orders_quick
from market.coupang.returns import get_today_returns_quick
from market.coupang.exchange import get_today_exchanges_quick

def create_dashboard_data():
    """통합 대시보드 데이터 생성"""
    dashboard = {
        'timestamp': datetime.now().isoformat(),
        'inquiries': {
            'today': get_today_inquiries_quick(),
            'unanswered': get_unanswered_inquiries_quick(days=7)
        },
        'sales': {
            'recent_7days': get_recent_revenue_quick(days=7),
            'recent_30days': get_recent_revenue_quick(days=30)
        },
        'settlement': {
            'current_month': get_current_month_settlement_quick()
        },
        'orders': {
            'today': get_today_orders_quick(hours=24)
        },
        'returns': {
            'today': get_today_returns_quick(days=1)
        },
        'exchanges': {
            'today': get_today_exchanges_quick(days=1)
        }
    }
    return dashboard

# 대시보드 데이터 생성
dashboard_data = create_dashboard_data()
print("📊 통합 대시보드 데이터 생성 완료")
```

### 2. 배치 작업 처리
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from market.coupang import create_unified_client

def process_batch_operations():
    """배치 작업 처리 예제"""
    unified = create_unified_client()
    
    def fetch_cs_data():
        return unified['cs'].get_inquiry_list()
    
    def fetch_sales_data():
        return unified['sales'].get_revenue_history()
    
    def fetch_settlement_data():
        return unified['settlement'].get_settlement_history()
    
    # 병렬 처리
    with ThreadPoolExecutor(max_workers=3) as executor:
        cs_future = executor.submit(fetch_cs_data)
        sales_future = executor.submit(fetch_sales_data)
        settlement_future = executor.submit(fetch_settlement_data)
        
        # 결과 수집
        results = {
            'cs': cs_future.result(),
            'sales': sales_future.result(),
            'settlement': settlement_future.result()
        }
    
    return results
```

### 3. 자동화된 고객 서비스
```python
from market.coupang.cs import (
    create_cs_client,
    get_unanswered_inquiries_quick,
    reply_to_inquiry_quick
)

def auto_reply_common_inquiries():
    """공통 문의에 대한 자동 답변"""
    
    # 자동 답변 템플릿
    AUTO_REPLY_TEMPLATES = {
        "배송": "안녕하세요. 배송 관련 문의해주셔서 감사합니다. 일반적으로 주문 후 1-2일 내 배송됩니다.",
        "반품": "안녕하세요. 반품 절차는 다음과 같습니다...",
        "교환": "안녕하세요. 교환 관련 안내드립니다..."
    }
    
    # 미답변 문의 조회
    unanswered = get_unanswered_inquiries_quick(days=1)
    
    for inquiry in unanswered.get('data', []):
        inquiry_content = inquiry.get('content', '').lower()
        
        # 키워드 매칭하여 자동 답변
        for keyword, template in AUTO_REPLY_TEMPLATES.items():
            if keyword in inquiry_content:
                try:
                    result = reply_to_inquiry_quick(
                        inquiry_id=inquiry['inquiry_id'],
                        content=template,
                        reply_by="auto_system"
                    )
                    print(f"✅ 자동 답변 완료: 문의 ID {inquiry['inquiry_id']}")
                except Exception as e:
                    print(f"❌ 자동 답변 실패: {e}")
                break
```

---

## 에러 처리

### 공통 에러 처리 패턴
```python
from market.coupang.common.errors import (
    CoupangAPIError,
    CoupangAuthError,
    CoupangNetworkError,
    error_handler
)

def safe_api_call(api_func, *args, **kwargs):
    """안전한 API 호출 래퍼"""
    try:
        return api_func(*args, **kwargs)
    except CoupangAuthError as e:
        print(f"🔐 인증 오류: {e}")
        # 토큰 갱신 시도
        return None
    except CoupangNetworkError as e:
        print(f"🌐 네트워크 오류: {e}")
        # 재시도 로직
        return None
    except CoupangAPIError as e:
        print(f"📡 API 오류: {e}")
        error_handler(e, context="API 호출")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

# 사용 예제
from market.coupang.cs import get_today_inquiries_quick

result = safe_api_call(get_today_inquiries_quick)
if result:
    print("✅ API 호출 성공")
else:
    print("❌ API 호출 실패")
```

### 재시도 로직
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    """실패 시 재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"🔄 재시도 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# 사용 예제
@retry_on_failure(max_retries=3, delay=2)
def fetch_sales_data():
    from market.coupang.sales import get_recent_revenue_quick
    return get_recent_revenue_quick(days=7)
```

---

## 실전 시나리오

### 시나리오 1: 일일 운영 보고서 생성
```python
from datetime import datetime
from market.coupang import create_unified_client

def generate_daily_report():
    """일일 운영 보고서 생성"""
    unified = create_unified_client()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📊 {today} 일일 운영 보고서")
    print("=" * 50)
    
    # 1. 고객문의 현황
    try:
        inquiries = unified['cs'].get_today_inquiries()
        unanswered = unified['cs'].get_unanswered_inquiries(days=1)
        
        print(f"📞 고객문의 현황:")
        print(f"   - 오늘 접수: {len(inquiries.get('data', []))}건")
        print(f"   - 미답변: {len(unanswered.get('data', []))}건")
    except Exception as e:
        print(f"   ❌ 고객문의 데이터 조회 실패: {e}")
    
    # 2. 주문 현황
    try:
        orders = unified['order'].get_today_orders(hours=24)
        print(f"🛒 주문 현황:")
        print(f"   - 오늘 주문: {len(orders.get('data', []))}건")
    except Exception as e:
        print(f"   ❌ 주문 데이터 조회 실패: {e}")
    
    # 3. 반품/교환 현황
    try:
        returns = unified['returns'].get_today_returns(days=1)
        exchanges = unified['exchange'].get_today_exchanges(days=1)
        
        print(f"🔄 반품/교환 현황:")
        print(f"   - 반품 요청: {len(returns.get('data', []))}건")
        print(f"   - 교환 요청: {len(exchanges.get('data', []))}건")
    except Exception as e:
        print(f"   ❌ 반품/교환 데이터 조회 실패: {e}")
    
    # 4. 매출 현황
    try:
        revenue = unified['sales'].get_recent_revenue(days=1)
        print(f"💰 매출 현황:")
        print(f"   - 오늘 매출 항목: {len(revenue.get('data', []))}건")
    except Exception as e:
        print(f"   ❌ 매출 데이터 조회 실패: {e}")
    
    print("=" * 50)
    print("✅ 일일 보고서 생성 완료")

# 실행
generate_daily_report()
```

### 시나리오 2: 고객 만족도 향상 자동화
```python
from market.coupang.cs import (
    get_unanswered_inquiries_quick,
    reply_to_inquiry_quick,
    create_inquiry_analysis_quick
)

def customer_satisfaction_automation():
    """고객 만족도 향상을 위한 자동화"""
    
    # 1. 미답변 문의 우선순위 처리
    unanswered = get_unanswered_inquiries_quick(days=2)
    urgent_inquiries = []
    
    for inquiry in unanswered.get('data', []):
        # 긴급 키워드 검사
        urgent_keywords = ['환불', '취소', '불만', '문제', '오류']
        content = inquiry.get('content', '').lower()
        
        if any(keyword in content for keyword in urgent_keywords):
            urgent_inquiries.append(inquiry)
    
    print(f"🚨 긴급 처리 필요한 문의: {len(urgent_inquiries)}건")
    
    # 2. 자동 우선 답변
    priority_template = "안녕하세요. 중요한 문의사항으로 확인되어 우선 답변드립니다. 담당자가 신속히 처리하도록 하겠습니다."
    
    for inquiry in urgent_inquiries[:5]:  # 상위 5건만 자동 처리
        try:
            result = reply_to_inquiry_quick(
                inquiry_id=inquiry['inquiry_id'],
                content=priority_template,
                reply_by="priority_system"
            )
            print(f"✅ 우선 답변 완료: 문의 ID {inquiry['inquiry_id']}")
        except Exception as e:
            print(f"❌ 우선 답변 실패: {e}")
    
    # 3. 고객문의 패턴 분석
    analysis = create_inquiry_analysis_quick(days=7)
    print(f"📈 주간 문의 분석: {analysis}")

# 실행
customer_satisfaction_automation()
```

### 시나리오 3: 매출 최적화 분석
```python
from market.coupang.sales import (
    get_recent_revenue_quick,
    get_revenue_summary_quick
)
from market.coupang.settlement import get_current_month_settlement_quick

def revenue_optimization_analysis():
    """매출 최적화 분석"""
    
    print("💼 매출 최적화 분석 시작")
    print("=" * 40)
    
    # 1. 최근 매출 트렌드 분석
    revenue_7days = get_recent_revenue_quick(days=7)
    revenue_30days = get_recent_revenue_quick(days=30)
    
    print(f"📊 매출 트렌드:")
    print(f"   - 최근 7일: {len(revenue_7days.get('data', []))}건")
    print(f"   - 최근 30일: {len(revenue_30days.get('data', []))}건")
    
    # 2. 매출 요약 분석
    summary = get_revenue_summary_quick(days=30)
    print(f"💰 30일 매출 요약: {summary}")
    
    # 3. 이번 달 정산 현황
    settlement = get_current_month_settlement_quick()
    print(f"🏦 이번 달 정산: {settlement}")
    
    # 4. 개선 권장사항
    print("🎯 개선 권장사항:")
    
    if len(revenue_7days.get('data', [])) < len(revenue_30days.get('data', [])) / 4:
        print("   - 최근 매출이 감소 추세입니다. 마케팅 활동을 강화하세요.")
    else:
        print("   - 매출이 안정적입니다. 현재 전략을 유지하세요.")
    
    print("=" * 40)
    print("✅ 매출 분석 완료")

# 실행
revenue_optimization_analysis()
```

---

## 정기 실행 스크립트

### crontab 설정 예제
```bash
# 매일 오전 9시에 일일 보고서 생성
0 9 * * * cd /home/sunwoo/project/yooni_02 && python -c "from market.coupang.examples import generate_daily_report; generate_daily_report()"

# 매 시간마다 긴급 문의 자동 처리
0 * * * * cd /home/sunwoo/project/yooni_02 && python -c "from market.coupang.examples import customer_satisfaction_automation; customer_satisfaction_automation()"

# 매주 월요일 오전 10시에 주간 분석
0 10 * * 1 cd /home/sunwoo/project/yooni_02 && python -c "from market.coupang.examples import revenue_optimization_analysis; revenue_optimization_analysis()"
```

이 사용 예제들은 실제 운영 환경에서 쿠팡 파트너스 API를 효과적으로 활용하는 방법을 보여줍니다. 각 예제는 실제 비즈니스 요구사항을 반영하여 작성되었으며, 필요에 따라 수정하여 사용하실 수 있습니다.