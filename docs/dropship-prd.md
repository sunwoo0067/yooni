# AI 자율 드롭쉬핑 에이전트 PRD
## Product Requirements Document v2.0

### 1. 프로젝트 개요

#### 1.1 프로젝트 명
**DropShip AI Agent** - 자율 운영 드롭쉬핑 AI 에이전트

#### 1.2 비전
AI가 드롭쉬핑 비즈니스를 자율적으로 운영하며, 매출 최적화와 운영 효율화를 달성하는 지능형 에이전트 시스템

#### 1.3 핵심 목표
- 멀티 공급사 & 멀티 마켓 계정 통합 관리
- AI 기반 자율 운영 (상품 선정, 가공, 등록, 삭제)
- 데이터 기반 의사결정 및 자동 실행
- 오케스트레이션을 통한 워크플로우 자동화

### 2. 기술 스택

#### 2.1 핵심 기술
- **언어**: Python 3.11+
- **데이터베이스**: PostgreSQL 16+ (JSONB 활용)
- **웹 프레임워크**: FastAPI
- **작업 스케줄러**: Celery + Redis
- **오케스트레이션**: Apache Airflow

#### 2.2 AI/ML 스택
- **LLM 로컬 (Ollama)**:
  - DeepSeek-R1: 전략적 의사결정, 복잡한 분석
  - Qwen 2.5 Coder: 데이터 변환, 자동화 스크립트
  - Llama 3.3: 상품명 생성, 카테고리 분류
- **외부 API**: Google Gemini 2.5 Flash (대량 처리)
- **이미지 처리**: 
  - OpenCV, Pillow (기본 처리)
  - Rembg (배경 제거)
  - Stable Diffusion (이미지 합성)
- **ML**: scikit-learn (판매 예측, 트렌드 분석)

#### 2.3 자동화 도구
- **웹 스크래핑**: Playwright
- **스크린샷/캡처**: Playwright + OpenCV
- **스케줄링**: APScheduler
- **워크플로우**: Airflow DAGs

### 3. 시스템 아키텍처

#### 3.1 모듈 구조
```
├── core/                    # 핵심 시스템
│   ├── orchestrator/       # AI 오케스트레이터
│   ├── agent_brain/        # AI 의사결정 엔진
│   └── workflow_engine/    # 워크플로우 실행
├── collectors/             # 데이터 수집
│   ├── supplier_scrapers/  # 공급사별 스크래퍼
│   └── market_apis/        # 마켓 API 클라이언트
├── processors/             # 데이터 처리
│   ├── product_analyzer/   # 상품 분석
│   ├── image_processor/    # 이미지 가공
│   └── text_generator/     # 텍스트 생성
├── managers/               # 비즈니스 로직
│   ├── account_manager/    # 계정 관리
│   ├── product_manager/    # 상품 관리
│   └── order_manager/      # 주문 처리
└── analytics/              # 분석 및 인사이트
    ├── sales_analyzer/     # 판매 분석
    └── trend_predictor/    # 트렌드 예측
```

### 4. 데이터베이스 설계

#### 4.1 계정 관리
```sql
-- 공급사 계정
CREATE TABLE supplier_accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'oneclean', 'gentrade', 'domeme'
    credentials JSONB NOT NULL, -- 암호화된 로그인 정보
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

-- 마켓플레이스 계정
CREATE TABLE marketplace_accounts (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL, -- 사업자 ID
    marketplace VARCHAR(50) NOT NULL, -- 'coupang', 'naver', '11st'
    account_name VARCHAR(100) NOT NULL,
    credentials JSONB NOT NULL,
    api_keys JSONB,
    limits JSONB, -- 일일 등록 제한 등
    is_active BOOLEAN DEFAULT true
);

-- 사업자 정보
CREATE TABLE business_entities (
    id SERIAL PRIMARY KEY,
    business_number VARCHAR(20) NOT NULL,
    business_name VARCHAR(100) NOT NULL,
    metadata JSONB
);
```

#### 4.2 상품 데이터
```sql
-- 공급사 원본 상품 (500만개+)
CREATE TABLE supplier_products (
    id BIGSERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES supplier_accounts(id),
    supplier_product_id VARCHAR(100) NOT NULL,
    raw_data JSONB NOT NULL,
    normalized_data JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN DEFAULT true,
    price_changes JSONB DEFAULT '[]', -- 가격 변동 이력
    UNIQUE(supplier_id, supplier_product_id)
);

-- 마켓 등록 상품 (10만개+)
CREATE TABLE marketplace_products (
    id BIGSERIAL PRIMARY KEY,
    supplier_product_id BIGINT REFERENCES supplier_products(id),
    marketplace_account_id INTEGER REFERENCES marketplace_accounts(id),
    marketplace_product_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, active, paused, deleted
    listing_data JSONB NOT NULL,
    performance_metrics JSONB DEFAULT '{}',
    ai_decisions JSONB DEFAULT '[]', -- AI 결정 이력
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 판매 데이터
CREATE TABLE sales_data (
    id BIGSERIAL PRIMARY KEY,
    marketplace_product_id BIGINT REFERENCES marketplace_products(id),
    date DATE NOT NULL,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    UNIQUE(marketplace_product_id, date)
);
```

### 5. 핵심 기능 상세

#### 5.1 상품 수집 모듈

**지원 공급사**:
- 오너클랜
- 젠트레이드
- 도매매
- (확장 가능한 구조)

**수집 전략**:
```python
class SupplierCollector:
    def __init__(self, supplier_type):
        self.scraper = self._get_scraper(supplier_type)
        
    async def collect_products(self, filters=None):
        """
        유연한 필터 조건:
        - 카테고리
        - 가격 범위
        - 재고 수량
        - 신상품 여부
        - 커스텀 조건
        """
        products = await self.scraper.fetch_products(filters)
        await self._update_inventory(products)
        await self._track_price_changes(products)
```

**일일 업데이트 스케줄**:
- 매일 새벽 2시: 전체 상품 업데이트
- 5분 간격: 등록된 상품 재고/가격 체크
- 실시간: 품절 상품 즉시 처리

#### 5.2 AI 상품 분석 & 가공

**상품 재해석 기능**:
```python
class ProductReinterpreter:
    async def reinterpret_product(self, product):
        """
        상품을 다른 용도로 재해석
        예: 플라스틱 박스 → 낚시 태클박스
        """
        # 상세페이지 분석
        details = await self.analyze_product_details(product)
        
        # AI로 가능한 용도 탐색
        prompt = f"""
        상품: {product.name}
        특징: {details.features}
        
        이 상품의 다른 활용 가능성을 찾아주세요:
        1. 다른 카테고리에서의 용도
        2. 특정 취미/직업군을 위한 활용
        3. 계절별 다른 용도
        """
        
        alternatives = await self.llm.generate(prompt)
        return alternatives
```

**이미지 자동 캡처 & 가공**:
```python
class SmartImageProcessor:
    async def auto_capture_details(self, product_url):
        """
        AI가 상세페이지에서 중요 부분 자동 캡처
        """
        # 페이지 스크린샷
        page = await self.browser.new_page()
        await page.goto(product_url)
        
        # AI가 중요 영역 식별
        important_areas = await self.identify_key_areas(page)
        
        # 영역별 캡처 및 가공
        processed_images = []
        for area in important_areas:
            img = await self.capture_area(page, area)
            img = await self.remove_background(img)
            processed_images.append(img)
            
        return processed_images
```

#### 5.3 AI 자율 운영 에이전트

**핵심 의사결정 엔진**:
```python
class AutonomousAgent:
    def __init__(self):
        self.decision_history = []
        
    async def daily_operation(self):
        """일일 자율 운영"""
        # 1. 판매 데이터 분석
        insights = await self.analyze_sales_performance()
        
        # 2. 부진 상품 식별
        poor_performers = await self.identify_poor_performers()
        
        # 3. 순환 등록 실행
        if len(poor_performers) > 1000:
            await self.rotate_products(poor_performers[:1000])
        
        # 4. 고성과 상품 최적화
        top_performers = await self.identify_top_performers()
        await self.optimize_listings(top_performers)
        
        # 5. 신규 상품 소싱
        new_products = await self.source_new_products()
        await self.process_and_list(new_products)
```

**오케스트레이션 워크플로우**:
```python
# Airflow DAG 예시
from airflow import DAG
from datetime import datetime, timedelta

default_args = {
    'owner': 'ai-agent',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'dropship_daily_operations',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # 매일 새벽 2시
)

# 태스크 정의
collect_supplier_data = PythonOperator(
    task_id='collect_supplier_data',
    python_callable=collect_all_suppliers
)

analyze_market_trends = PythonOperator(
    task_id='analyze_market_trends',
    python_callable=analyze_trends
)

ai_decision_making = PythonOperator(
    task_id='ai_decision_making',
    python_callable=make_strategic_decisions
)

execute_decisions = PythonOperator(
    task_id='execute_decisions',
    python_callable=execute_ai_decisions
)

# 워크플로우 정의
collect_supplier_data >> analyze_market_trends >> ai_decision_making >> execute_decisions
```

#### 5.4 판매 데이터 통합 분석

**내 판매 데이터 활용**:
```python
class SalesAnalyzer:
    async def integrate_my_sales_data(self):
        """기존 운영 중인 마켓 데이터 통합"""
        # 각 마켓에서 판매 데이터 수집
        for account in self.marketplace_accounts:
            sales_data = await account.fetch_sales_report()
            await self.store_sales_data(sales_data)
            
        # AI 학습용 데이터 준비
        training_data = await self.prepare_training_data()
        await self.train_prediction_model(training_data)
```

### 6. MVP 구현 계획

#### 6.1 Phase 1: 오너클랜 → 쿠팡 (1개월)

**Week 1-2**: 기초 구축
- PostgreSQL 스키마 설정
- FastAPI 기본 구조
- 오너클랜 스크래퍼 개발

**Week 3**: 상품 가공
- 기본 이미지 처리
- 상품명 생성 (LLM)
- 카테고리 매핑

**Week 4**: 쿠팡 연동
- Wing API 연동
- 상품 업로드
- 상태 동기화

#### 6.2 구현 우선순위
1. 오너클랜 상품 수집 (조건별 필터링)
2. 상품 데이터 정규화
3. AI 상품명 생성
4. 이미지 기본 가공
5. 쿠팡 업로드 자동화

### 7. 고급 기능 로드맵

#### 7.1 Phase 2: AI 자율성 강화 (2-3개월)
- 판매 데이터 기반 학습
- 자동 상품 순환
- 가격 최적화

#### 7.2 Phase 3: 멀티 마켓 확장 (3-4개월)
- 네이버, 11번가 추가
- 마켓별 최적화
- 통합 대시보드

#### 7.3 Phase 4: 완전 자율 운영 (4-6개월)
- AI 에이전트 고도화
- 자율 의사결정
- 24/7 무인 운영

### 8. 성능 목표

- **상품 수집**: 일 50만개 업데이트
- **동시 관리 상품**: 마켓당 10만개
- **의사결정 주기**: 5분
- **일일 처리량**: 
  - 신규 등록: 1,000개
  - 수정/삭제: 5,000개
  - 순환 등록: 1,000개

### 9. AI 에이전트 학습 전략

#### 9.1 초기 학습
- 기존 판매 데이터 입력
- 성공/실패 패턴 분석
- 마켓별 특성 학습

#### 9.2 지속적 개선
- 일일 성과 피드백
- A/B 테스트 자동화
- 전략 자동 조정

### 10. SuperClaude Framework 적용

#### 10.1 개발 워크플로우 혁신
```bash
# 시스템 아키텍처 분석
/sc:analyze --focus architecture --depth deep --format diagram

# AI 드롭쉬핑 에이전트 구현
/sc:implement "AI 자율 운영 에이전트" --type feature --ai-driven --autonomous

# 멀티 마켓플레이스 통합 개발
/sc:implement "통합 마켓플레이스 API" --type module --multi-platform

# 성능 최적화
/sc:optimize --focus performance --ai-pipeline --automated
```

#### 10.2 AI/ML 개발 특화
```bash
# AI 모델 분석 및 최적화
/sc:analyze backend/ai/ --focus ml-performance --models all

# 상품 재해석 AI 구현
/sc:implement "상품 재해석 AI 모듈" --type ai-feature --creative

# 이미지 처리 파이프라인 최적화
/sc:optimize "자동 이미지 가공" --focus image-processing --ai

# AI 의사결정 엔진 테스트
/sc:test backend/ai/ --type ai-validation --autonomous --comprehensive
```

#### 10.3 통합 테스트 및 배포
```bash
# 드롭쉬핑 워크플로우 E2E 테스트
/sc:test --type e2e --dropshipping --autonomous --comprehensive

# 프로덕션 배포 자동화
/sc:deploy --environment prod --ai-enabled --monitoring

# 실시간 모니터링
/sc:monitor --ai-decisions --real-time --autonomous
```

#### 10.4 지속적 개선
```bash
# AI 학습 성과 분석
/sc:analyze --focus ai-learning --performance-metrics --trend

# 자율 운영 최적화
/sc:optimize --focus autonomous-operation --iterative --ai-driven

# 드롭쉬핑 전략 개선
/sc:improve "드롭쉬핑 전략" --focus business-logic --ai-enhanced
```

### 11. 개발 시 주의사항

- **확장성**: 공급사/마켓 추가가 쉬운 플러그인 구조
- **유연성**: JSONB를 활용한 동적 데이터 구조
- **자율성**: AI가 독립적으로 운영 가능한 구조
- **모니터링**: 모든 AI 결정사항 추적 가능
- **SuperClaude 활용**: 개발 전 과정에 SuperClaude Framework 명령어 적극 활용
- **AI 우선**: AI 기반 의사결정과 자동화를 최우선으로 설계
- **한국어 특화**: 한국 마켓플레이스와 한국어 처리에 최적화

### 12. SuperClaude Framework 통합 이점

#### 12.1 개발 속도 향상
- **50% 빠른 개발**: 자동화된 코드 분석 및 구현
- **90% 정확한 아키텍처**: AI 기반 시스템 설계
- **자동 테스트**: 포괄적인 테스트 자동 생성

#### 12.2 코드 품질 보장
- **실시간 품질 모니터링**: 지속적인 코드 품질 관리
- **보안 강화**: 자동 보안 취약점 탐지 및 수정
- **성능 최적화**: AI 기반 성능 병목 지점 자동 개선

#### 12.3 AI 개발 특화
- **AI 모델 최적화**: ML 파이프라인 자동 최적화
- **데이터 플로우 분석**: 복잡한 데이터 흐름 자동 분석
- **예측 정확도 향상**: AI 모델 성능 지속적 개선

---

**참고 문서:**
- [SuperClaude Integration Guide](../SUPERCLAUDE_INTEGRATION_GUIDE.md)
- [CLAUDE.md](../CLAUDE.md) - SuperClaude 활용 가이드