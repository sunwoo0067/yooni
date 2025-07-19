# 쿠팡 파트너스 API 멀티 계정 사용 가이드

## 개요
이 가이드는 쿠팡 파트너스 API 클라이언트에서 여러 계정을 관리하고 사용하는 방법을 설명합니다. 멀티 계정 기능을 통해 여러 스토어나 사업부를 효율적으로 관리할 수 있습니다.

## 목차
- [멀티 계정 시스템 구조](#멀티-계정-시스템-구조)
- [계정 설정 및 관리](#계정-설정-및-관리)
- [기본 사용법](#기본-사용법)
- [고급 사용법](#고급-사용법)
- [실전 시나리오](#실전-시나리오)
- [관리 도구](#관리-도구)
- [보안 고려사항](#보안-고려사항)

---

## 멀티 계정 시스템 구조

### 핵심 컴포넌트

1. **MultiAccountConfig**: 계정 정보 관리
2. **MultiClientFactory**: 계정별 클라이언트 생성
3. **CoupangAccount**: 개별 계정 정보 모델
4. **MultiAccountManager**: CLI 관리 도구

### 지원 기능

- ✅ **계정별 독립적 API 접근**
- ✅ **태그 기반 계정 분류**
- ✅ **기본 계정 설정**
- ✅ **활성화/비활성화 관리**
- ✅ **일괄 작업 실행**
- ✅ **캐시 기반 성능 최적화**
- ✅ **JSON 기반 설정 관리**

---

## 계정 설정 및 관리

### 1. 계정 설정 파일 생성

#### accounts.json 파일 예제
```json
{
  "default_account": "main_store",
  "accounts": [
    {
      "account_name": "main_store",
      "access_key": "your_main_access_key_here",
      "secret_key": "your_main_secret_key_here",
      "vendor_id": "your_main_vendor_id_here",
      "description": "메인 온라인 스토어",
      "is_active": true,
      "tags": ["main", "electronics", "books"]
    },
    {
      "account_name": "fashion_store",
      "access_key": "your_fashion_access_key_here",
      "secret_key": "your_fashion_secret_key_here",
      "vendor_id": "your_fashion_vendor_id_here",
      "description": "패션 전문 스토어",
      "is_active": true,
      "tags": ["fashion", "clothing", "accessories"]
    }
  ]
}
```

### 2. 환경변수 방식 (하위 호환성)

기존 단일 계정 환경변수 방식도 계속 지원됩니다:

```bash
# .env 파일
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=your_vendor_id
```

환경변수로 설정된 계정은 자동으로 "default"라는 이름으로 등록됩니다.

### 3. 계정 관리 CLI 도구

```bash
# 대화형 관리 도구 실행
python multi_account_manager.py

# 특정 명령 실행
python multi_account_manager.py list      # 계정 목록
python multi_account_manager.py add       # 계정 추가
python multi_account_manager.py test      # 연결 테스트
```

---

## 기본 사용법

### 1. 단일 계정 클라이언트 생성

```python
from market.coupang.common.multi_client_factory import create_client_for_account
from market.coupang.cs import CSClient

# 기본 계정으로 CS 클라이언트 생성
cs_client = create_client_for_account(CSClient)

# 특정 계정으로 CS 클라이언트 생성
fashion_cs_client = create_client_for_account(CSClient, "fashion_store")

# 클라이언트 사용
if cs_client:
    inquiries = cs_client.get_today_inquiries()
    print(f"오늘 문의: {len(inquiries.get('data', []))}건")
```

### 2. 통합 클라이언트 생성

```python
from market.coupang.common.multi_client_factory import create_unified_client_for_account

# 기본 계정의 모든 모듈 클라이언트
unified = create_unified_client_for_account()

# 특정 계정의 모든 모듈 클라이언트
fashion_unified = create_unified_client_for_account("fashion_store")

if unified:
    # 각 모듈 사용
    cs_data = unified['cs'].get_today_inquiries()
    sales_data = unified['sales'].get_recent_revenue_history()
    settlement_data = unified['settlement'].get_current_month_settlement()
```

### 3. 계정 정보 조회

```python
from market.coupang.common.multi_account_config import (
    get_account, 
    list_account_names, 
    get_default_account_name
)

# 기본 계정 정보
default_account = get_account()
print(f"기본 계정: {default_account.account_name if default_account else 'None'}")

# 모든 계정 이름
account_names = list_account_names()
print(f"등록된 계정: {account_names}")

# 특정 계정 정보
fashion_account = get_account("fashion_store")
if fashion_account:
    print(f"패션 스토어 벤더 ID: {fashion_account.vendor_id}")
```

---

## 고급 사용법

### 1. 모든 계정에서 일괄 작업 실행

```python
from market.coupang.common.multi_client_factory import execute_on_all_accounts
from market.coupang.cs import CSClient

# 모든 활성 계정에서 오늘 문의 조회
results = execute_on_all_accounts(
    CSClient, 
    'get_today_inquiries'
)

print("🔍 전체 계정 문의 현황:")
for account_name, result in results.items():
    if result['success']:
        inquiry_count = len(result['data'].get('data', []))
        print(f"  {account_name}: {inquiry_count}건")
    else:
        print(f"  {account_name}: 오류 - {result['error']}")
```

### 2. 태그별 계정 그룹 작업

```python
from market.coupang.common.multi_client_factory import multi_factory
from market.coupang.sales import SalesClient

# 패션 관련 계정들에서 매출 조회
fashion_sales_results = multi_factory.execute_on_tagged_accounts(
    SalesClient,
    "fashion",
    'get_recent_revenue_history',
    days=7
)

print("👗 패션 스토어 매출 현황:")
for account_name, result in fashion_sales_results.items():
    if result['success']:
        revenue_items = len(result['data'].get('data', []))
        print(f"  {account_name}: {revenue_items}개 매출 항목")
```

### 3. 계정별 맞춤형 클라이언트 생성

```python
from market.coupang.common.multi_client_factory import multi_factory
from market.coupang.cs import CSClient
from market.coupang.sales import SalesClient

# 태그별 클라이언트 생성
fashion_cs_clients = multi_factory.create_clients_by_tag(CSClient, "fashion")
electronics_sales_clients = multi_factory.create_clients_by_tag(SalesClient, "electronics")

# 패션 스토어들의 고객문의 처리
for account_name, cs_client in fashion_cs_clients.items():
    unanswered = cs_client.get_unanswered_inquiries(days=1)
    print(f"{account_name}: 미답변 문의 {len(unanswered.get('data', []))}건")
```

### 4. 계정 상태 모니터링

```python
from market.coupang.common.multi_client_factory import get_multi_account_status

# 모든 계정 상태 확인
status = get_multi_account_status()

print("📊 계정 상태 요약:")
for account_name, account_status in status.items():
    status_icon = "✅" if account_status.get('valid', False) else "❌"
    active_icon = "🟢" if account_status.get('active', False) else "🔴"
    
    print(f"{status_icon} {account_name} {active_icon}")
    if 'error' in account_status:
        print(f"    오류: {account_status['error']}")
```

---

## 실전 시나리오

### 시나리오 1: 멀티 스토어 일일 대시보드

```python
from market.coupang.common.multi_client_factory import multi_factory
from market.coupang.cs import CSClient
from market.coupang.sales import SalesClient
from market.coupang.order import OrderClient
from datetime import datetime

def create_multi_store_dashboard():
    """멀티 스토어 일일 대시보드 생성"""
    print(f"📊 멀티 스토어 대시보드 - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 80)
    
    # 모든 활성 계정에서 데이터 수집
    cs_results = multi_factory.execute_on_all_accounts(
        CSClient, 'get_today_inquiries'
    )
    
    sales_results = multi_factory.execute_on_all_accounts(
        SalesClient, 'get_recent_revenue_history', days=1
    )
    
    order_results = multi_factory.execute_on_all_accounts(
        OrderClient, 'get_today_orders', hours=24
    )
    
    # 계정별 요약 출력
    for account_name in cs_results.keys():
        print(f"\n🏪 {account_name}")
        print("-" * 40)
        
        # 고객문의
        if cs_results[account_name]['success']:
            inquiries = len(cs_results[account_name]['data'].get('data', []))
            print(f"📞 오늘 문의: {inquiries}건")
        
        # 매출
        if sales_results.get(account_name, {}).get('success'):
            revenue_items = len(sales_results[account_name]['data'].get('data', []))
            print(f"💰 오늘 매출: {revenue_items}개 항목")
        
        # 주문
        if order_results.get(account_name, {}).get('success'):
            orders = len(order_results[account_name]['data'].get('data', []))
            print(f"📦 오늘 주문: {orders}건")
    
    print("\n" + "=" * 80)

# 실행
create_multi_store_dashboard()
```

### 시나리오 2: 계정별 맞춤형 자동 답변

```python
from market.coupang.common.multi_account_config import multi_config
from market.coupang.common.multi_client_factory import multi_factory
from market.coupang.cs import CSClient

def auto_reply_by_store_type():
    """스토어 유형별 맞춤형 자동 답변"""
    
    # 스토어 유형별 답변 템플릿
    reply_templates = {
        "fashion": {
            "사이즈": "사이즈 관련 문의주셔서 감사합니다. 상품 페이지의 사이즈 가이드를 참고해주세요.",
            "배송": "패션 상품은 당일 오후 3시 이전 주문시 익일 배송됩니다."
        },
        "electronics": {
            "A/S": "전자제품 A/S 관련 문의는 제조사 서비스센터로 연결해드리겠습니다.",
            "배송": "전자제품은 안전한 포장을 위해 2-3일 소요됩니다."
        },
        "beauty": {
            "성분": "화장품 성분 관련 문의주셔서 감사합니다. 제품 상세페이지에서 전체 성분을 확인하실 수 있습니다.",
            "사용법": "제품 사용법은 패키지 내 사용 설명서를 참고해주세요."
        }
    }
    
    # 태그별로 계정 그룹화하여 처리
    for store_type, templates in reply_templates.items():
        print(f"\n🏷️ {store_type} 스토어 자동 답변 처리")
        
        # 해당 태그의 계정들 조회
        cs_clients = multi_factory.create_clients_by_tag(CSClient, store_type)
        
        for account_name, cs_client in cs_clients.items():
            print(f"  📝 {account_name} 처리 중...")
            
            try:
                # 미답변 문의 조회
                unanswered = cs_client.get_unanswered_inquiries(days=1)
                
                for inquiry in unanswered.get('data', []):
                    inquiry_content = inquiry.get('content', '').lower()
                    
                    # 키워드 매칭
                    for keyword, template in templates.items():
                        if keyword in inquiry_content:
                            try:
                                result = cs_client.reply_to_inquiry(
                                    inquiry['inquiry_id'],
                                    account_name,  # vendor_id 대신 account_name 사용
                                    template,
                                    f"auto_{store_type}"
                                )
                                print(f"    ✅ 자동 답변 완료: 문의 {inquiry['inquiry_id']}")
                            except Exception as e:
                                print(f"    ❌ 답변 실패: {e}")
                            break
                            
            except Exception as e:
                print(f"    ❌ {account_name} 처리 실패: {e}")

# 실행
auto_reply_by_store_type()
```

### 시나리오 3: 계정별 성과 분석 리포트

```python
from market.coupang.common.multi_client_factory import multi_factory
from market.coupang.sales import SalesClient
from market.coupang.settlement import SettlementClient
from market.coupang.cs import CSClient

def generate_multi_account_performance_report():
    """멀티 계정 성과 분석 리포트"""
    print("📈 멀티 계정 성과 분석 리포트")
    print("=" * 60)
    
    # 데이터 수집
    sales_results = multi_factory.execute_on_all_accounts(
        SalesClient, 'get_recent_revenue_history', days=30
    )
    
    settlement_results = multi_factory.execute_on_all_accounts(
        SettlementClient, 'get_current_month_settlement'
    )
    
    cs_results = multi_factory.execute_on_all_accounts(
        CSClient, 'get_unanswered_inquiries', days=7
    )
    
    # 성과 분석
    performance_data = []
    
    for account_name in sales_results.keys():
        account = multi_config.get_account(account_name)
        if not account:
            continue
        
        account_data = {
            'name': account_name,
            'description': account.description,
            'tags': account.tags,
            'revenue_items': 0,
            'settlement_amount': 0,
            'unanswered_inquiries': 0,
            'performance_score': 0
        }
        
        # 매출 데이터
        if sales_results[account_name]['success']:
            revenue_data = sales_results[account_name]['data']
            account_data['revenue_items'] = len(revenue_data.get('data', []))
        
        # 정산 데이터
        if settlement_results.get(account_name, {}).get('success'):
            settlement_data = settlement_results[account_name]['data']
            if settlement_data.get('data'):
                account_data['settlement_amount'] = sum(
                    item.get('settlement_amount', 0) 
                    for item in settlement_data['data']
                )
        
        # CS 데이터
        if cs_results.get(account_name, {}).get('success'):
            cs_data = cs_results[account_name]['data']
            account_data['unanswered_inquiries'] = len(cs_data.get('data', []))
        
        # 성과 점수 계산 (간단한 예시)
        revenue_score = min(account_data['revenue_items'] / 10, 10)  # 매출 항목 기준
        cs_score = max(10 - account_data['unanswered_inquiries'], 0)  # 미답변 문의 차감
        account_data['performance_score'] = (revenue_score + cs_score) / 2
        
        performance_data.append(account_data)
    
    # 성과순으로 정렬
    performance_data.sort(key=lambda x: x['performance_score'], reverse=True)
    
    # 리포트 출력
    print(f"{'순위':<4} {'계정명':<15} {'매출항목':<8} {'정산금액':<12} {'미답변':<6} {'점수':<6}")
    print("-" * 60)
    
    for i, data in enumerate(performance_data, 1):
        settlement_amount_k = data['settlement_amount'] // 1000
        print(f"{i:<4} {data['name']:<15} {data['revenue_items']:<8} {settlement_amount_k}K원{'':<6} {data['unanswered_inquiries']:<6} {data['performance_score']:.1f}")
    
    # 태그별 요약
    tag_summary = {}
    for data in performance_data:
        for tag in data['tags']:
            if tag not in tag_summary:
                tag_summary[tag] = {'count': 0, 'total_score': 0}
            tag_summary[tag]['count'] += 1
            tag_summary[tag]['total_score'] += data['performance_score']
    
    print(f"\n📊 태그별 평균 성과:")
    for tag, summary in tag_summary.items():
        avg_score = summary['total_score'] / summary['count']
        print(f"  {tag}: {avg_score:.1f}점 ({summary['count']}개 계정)")

# 실행
generate_multi_account_performance_report()
```

---

## 관리 도구

### 1. CLI 관리 도구 사용법

#### 대화형 모드
```bash
cd /home/sunwoo/project/yooni_02/market/coupang
python multi_account_manager.py
```

#### 명령행 모드
```bash
# 계정 목록 보기
python multi_account_manager.py list

# 계정 추가
python multi_account_manager.py add

# 계정 연결 테스트
python multi_account_manager.py test

# 계정 요약 정보
python multi_account_manager.py summary
```

### 2. 프로그래매틱 관리

```python
from market.coupang.common.multi_account_config import MultiAccountConfig, CoupangAccount

# 설정 객체 생성
config = MultiAccountConfig()

# 새 계정 추가
new_account = CoupangAccount(
    account_name="beauty_store",
    access_key="access_key_here",
    secret_key="secret_key_here",
    vendor_id="vendor_id_here",
    description="뷰티 전문 스토어",
    tags=["beauty", "cosmetics"]
)

# 계정 추가 및 저장
if config.add_account(new_account):
    config.save_to_file()
    print("✅ 계정 추가 완료")

# 계정 목록 조회
accounts = config.list_accounts()
for account in accounts:
    print(f"📱 {account.account_name}: {account.description}")
```

---

## 보안 고려사항

### 1. 설정 파일 보안

```bash
# accounts.json 파일 권한 설정 (소유자만 읽기/쓰기)
chmod 600 accounts.json

# git에서 제외
echo "accounts.json" >> .gitignore
```

### 2. 환경변수 분리

```bash
# 계정별 환경변수 파일 분리
# .env.main_store
COUPANG_ACCESS_KEY=main_store_access_key
COUPANG_SECRET_KEY=main_store_secret_key
COUPANG_VENDOR_ID=main_store_vendor_id

# .env.fashion_store
COUPANG_ACCESS_KEY=fashion_store_access_key
COUPANG_SECRET_KEY=fashion_store_secret_key
COUPANG_VENDOR_ID=fashion_store_vendor_id
```

### 3. 계정 정보 내보내기 (보안 버전)

```python
from market.coupang.common.multi_account_config import multi_config

# 시크릿 키 제외하고 내보내기
multi_config.export_accounts("accounts_backup.json", include_secrets=False)
```

---

## 문제 해결

### 일반적인 문제들

#### 1. 계정 설정 파일을 찾을 수 없음
```python
# 설정 파일 경로 확인
from market.coupang.common.multi_account_config import multi_config
print(f"설정 파일 경로: {multi_config.config_file}")

# 예제 파일 복사
import shutil
shutil.copy("accounts.example.json", "accounts.json")
```

#### 2. 특정 계정 연결 실패
```python
# 계정별 상태 확인
from market.coupang.common.multi_client_factory import get_multi_account_status

status = get_multi_account_status()
for account_name, account_status in status.items():
    if not account_status.get('valid', False):
        print(f"❌ {account_name}: {account_status.get('error', 'Unknown error')}")
```

#### 3. 캐시 관련 문제
```python
# 캐시 정리
from market.coupang.common.multi_client_factory import multi_factory

# 특정 계정 캐시 정리
multi_factory.clear_cache("fashion_store")

# 전체 캐시 정리
multi_factory.clear_cache()

# 캐시 상태 확인
cache_info = multi_factory.get_cache_info()
print(f"캐시된 클라이언트: {cache_info['total_cached_clients']}개")
```

---

## 베스트 프랙티스

### 1. 계정 명명 규칙
- 의미있는 이름 사용: `main_store`, `fashion_store`, `test_account`
- 일관된 명명 패턴 유지
- 특수문자 대신 언더스코어 사용

### 2. 태그 활용
- 비즈니스 카테고리별 태그: `fashion`, `electronics`, `beauty`
- 환경별 태그: `production`, `staging`, `test`
- 지역별 태그: `korea`, `global`, `asia`

### 3. 기본 계정 설정
- 가장 자주 사용하는 계정을 기본 계정으로 설정
- 기본 계정은 안정적이고 검증된 계정 사용

### 4. 정기적인 계정 상태 확인
```python
# 일일 계정 상태 체크 스크립트
def daily_account_health_check():
    from market.coupang.common.multi_client_factory import get_multi_account_status
    
    status = get_multi_account_status()
    failed_accounts = [
        name for name, info in status.items() 
        if not info.get('valid', False)
    ]
    
    if failed_accounts:
        print(f"⚠️ 연결 실패 계정: {failed_accounts}")
        # 알림 발송 로직 추가
    else:
        print("✅ 모든 계정 정상")

# crontab으로 정기 실행 설정
```

이 가이드를 통해 쿠팡 파트너스 API의 멀티 계정 기능을 효과적으로 활용하여 여러 스토어를 체계적으로 관리할 수 있습니다.