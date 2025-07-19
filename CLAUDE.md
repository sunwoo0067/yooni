# CLAUDE.md - SuperClaude Framework Integration

🌟 **SuperClaude Framework 적용된 Yooni 프로젝트 가이드**

이 파일은 Claude Code (claude.ai/code)가 SuperClaude Framework를 활용하여 이 저장소에서 작업할 때의 가이드를 제공합니다.

## 🚀 Repository Overview

**Yooni**는 한국 마켓플레이스(쿠팡, 오너클랜, 젠트레이드)를 통합하는 AI 기반 e-commerce ERP 시스템입니다. 
마켓플레이스 API 통합, 자동화된 데이터 수집, ML 기반 비즈니스 최적화 기능을 결합합니다.

## 🎯 SuperClaude Framework 핵심 명령어

### 🔥 빠른 시작 (SuperClaude 방식)

#### 프로젝트 분석 및 이해
```bash
# 전체 시스템 아키텍처 분석
/sc:analyze --focus architecture --depth deep

# 코드 품질 및 보안 분석  
/sc:analyze --focus quality,security --depth deep

# 성능 병목 지점 분석
/sc:analyze --focus performance --depth deep
```

#### 개발 환경 구축
```bash
# 개발 환경 자동 구축
/sc:build --type dev --clean --verbose

# 의존성 설치 및 환경 설정
/sc:setup --environment dev --dependencies auto

# 서비스 상태 확인
/sc:monitor --services all --health-check
```

#### 기능 개발
```bash
# 새로운 마켓플레이스 통합 구현
/sc:implement "신규 마켓플레이스 API 통합" --type module --framework fastapi --with-tests

# AI 모델 개선
/sc:implement "고급 매출 예측 모델" --type feature --safe --iterative

# React 컴포넌트 개발
/sc:implement "실시간 대시보드 컴포넌트" --type component --framework react
```

#### 테스트 및 검증
```bash
# 전체 테스트 스위트 실행
/sc:test --type full --coverage --parallel

# 성능 테스트
/sc:test --type performance --load-test --api

# E2E 테스트
/sc:test --type e2e --browser --headless
```

#### 배포 및 운영
```bash
# 프로덕션 빌드
/sc:build --type prod --optimize

# 배포 실행
/sc:deploy --environment prod --strategy blue-green

# 모니터링 대시보드
/sc:monitor --real-time --alerts
```

### 🛠️ 전통적 명령어 (필요시 사용)

<details>
<summary>기존 개발 명령어 (클릭하여 확장)</summary>

#### Backend 개발
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python simple_api.py      # AI API server (port 8003)
python main.py           # Full AI service (port 8000)
python monitoring_server.py  # Monitoring API
python websocket_server.py   # WebSocket server (port 8002)
```

#### Frontend 개발
```bash
cd frontend
npm install
npm run dev              # Development server (http://localhost:3000)
npm run build && npm start  # Production build
```

#### Makefile 명령어
```bash
make install             # Install all dependencies
make test               # Run all tests
make run                # Start all services
make lint               # Run linters
make format             # Format code (backend only)
make clean              # Clean build files
make ci                 # Run full CI pipeline locally
```

#### 테스트 명령어
```bash
# Backend tests
cd backend
python -m pytest                    # All tests
python -m pytest -m "not slow"      # Skip slow tests
python -m pytest -m unit            # Unit tests only
python -m pytest -m integration     # Integration tests only
python -m pytest --cov=. --cov-report=html  # With coverage
python -m pytest -n auto            # Parallel execution

# Frontend tests
cd frontend
npm test                # Watch mode
npm run test:ci         # CI mode
npm run test:coverage   # With coverage report
```

#### Docker 운영
```bash
docker-compose up -d postgres redis  # Start core services
docker-compose -f docker-compose.prod.yml up -d  # Production deployment
make docker-up          # Start all containers
make docker-logs        # View logs
make docker-clean       # Clean volumes and images
```
</details>

## 🏗️ Architecture & SuperClaude 활용

### 🎯 아키텍처 분석 명령어
```bash
# 전체 시스템 아키텍처 분석
/sc:analyze --focus architecture --depth deep --format diagram

# 마이크로서비스 분석
/sc:analyze backend/ --focus architecture --services

# 데이터베이스 스키마 분석
/sc:analyze backend/database/ --focus architecture --schema
```

### 🔧 Service Ports & 모니터링
```bash
# 서비스 상태 실시간 모니터링
/sc:monitor --ports 5434,6379,3000,8000,8002,8003,5000

# 포트 충돌 검사
/sc:troubleshoot "포트 충돌 감지" --focus network --auto-fix
```

**Service Ports:**
- PostgreSQL: 5434 (non-standard)
- Redis: 6379
- Frontend: 3000
- AI API: 8003 (simple) / 8000 (full)
- Monitoring API: 8000
- WebSocket: 8002
- MLflow UI: 5000

### 📊 Database 관리
```bash
# 데이터베이스 연결 테스트
/sc:test database --connection --health

# 스키마 마이그레이션
/sc:migrate --database yoonni --auto-backup

# 성능 최적화
/sc:optimize database --focus performance --indexes
```

**Database Configuration:**
```
postgresql://postgres:1234@localhost:5434/yoonni  # Main DB
postgresql://postgres:1234@localhost:5434/mlflow   # MLflow DB
```

### 📁 Project Structure 탐색

```bash
# 프로젝트 구조 자동 분석
/sc:analyze --focus structure --depth quick --format tree

# 특정 모듈 세부 분석
/sc:analyze frontend/components/ --focus structure --detailed
/sc:analyze backend/ai/ --focus structure --ml-focus
/sc:analyze backend/market/ --focus structure --api-focus
```

**Project Structure:**
```
yoonni/
├── 🌐 frontend/           # Next.js 15 with App Router
│   ├── 📱 app/           # Routes and pages → /sc:analyze app/ --focus routing
│   ├── 🧩 components/    # Reusable UI components → /sc:analyze components/ --focus reusability  
│   └── 📚 lib/          # Utilities and integrations → /sc:analyze lib/ --focus utilities
├── ⚙️ backend/
│   ├── 🤖 ai/           # ML models and AI services → /sc:analyze ai/ --focus ml --performance
│   ├── 🛒 market/       # Marketplace integrations → /sc:analyze market/ --focus integration
│   ├── 📦 supplier/     # Supplier APIs → /sc:analyze supplier/ --focus api --security
│   └── 🧪 tests/        # Pytest test suite → /sc:test tests/ --coverage --detailed
└── 📖 docs/             # Documentation → /sc:document docs/ --update --comprehensive
```

### 🔍 모듈별 깊이 분석
```bash
# AI/ML 모듈 심화 분석
/sc:analyze backend/ai/ --focus architecture,performance,quality --depth deep

# 마켓플레이스 통합 분석
/sc:analyze backend/market/ --focus security,integration,performance

# 프론트엔드 컴포넌트 분석
/sc:analyze frontend/components/ --focus reusability,performance,accessibility

# 테스트 커버리지 분석
/sc:test --coverage --analysis --detailed-report
```

## 🏛️ High-Level Architecture & SuperClaude 최적화

### 🌐 Frontend Stack 분석 및 최적화
```bash
# Next.js 15 성능 분석
/sc:analyze frontend/ --focus performance --framework nextjs --depth deep

# React 19 컴포넌트 최적화
/sc:optimize frontend/components/ --focus performance --react19

# 상태 관리 분석 (Zustand + TanStack Query)
/sc:analyze frontend/lib/ --focus state-management --performance

# 프론트엔드 테스트 강화
/sc:test frontend/ --type integration --coverage-target 70% --jest
```

**Frontend Tech Stack:**
- **Framework**: Next.js 15 (App Router) + React 19
- **State**: Zustand (global), TanStack Query v5 (server state)
- **Database**: Direct PostgreSQL via pg library (no ORM)
- **Testing**: Jest with 60% coverage thresholds

### ⚙️ Backend Stack 분석 및 최적화
```bash
# FastAPI 성능 분석
/sc:analyze backend/ --focus performance --framework fastapi --async

# 데이터베이스 최적화
/sc:optimize backend/database/ --focus performance --postgresql --redis

# API 보안 강화
/sc:analyze backend/api/ --focus security --depth deep --fastapi

# 백엔드 테스트 확장
/sc:test backend/ --markers "unit,integration,api,db" --coverage-target 80%
```

**Backend Tech Stack:**
- **API**: FastAPI with uvicorn
- **Database**: PostgreSQL (psycopg2, asyncpg) + Redis caching
- **Structure**: Module-based without standard Python packaging  
- **Testing**: pytest with markers (unit, integration, slow, api, db)

### 🤖 AI/ML Pipeline 고도화
```bash
# AI 모델 성능 분석
/sc:analyze backend/ai/ --focus ml-performance --models all

# ML 파이프라인 최적화
/sc:optimize backend/ai/ --focus ml-pipeline --automated

# MLOps 워크플로우 분석
/sc:analyze backend/ai/ --focus mlops --mlflow --experiments

# AI 모델 테스트 자동화
/sc:test backend/ai/ --type ml-validation --automated --comprehensive
```

**AI/ML Pipeline:**
1. **Data Collection**: Scheduled tasks fetch from marketplaces
2. **Processing**: JSONB storage in PostgreSQL for flexible schemas
3. **Models**: 
   - Sales forecasting (Prophet, LSTM, SARIMA)
   - Customer churn (XGBoost with SMOTE)
   - Price optimization (DQN reinforcement learning)
   - Korean NLP chatbot (KoNLPy, Transformers)
4. **MLOps**: MLflow for experiment tracking and model registry

### 🔄 Integration Flow 최적화
```bash
# 데이터 플로우 분석
/sc:analyze --focus data-flow --integration --comprehensive

# API 통합 성능 최적화
/sc:optimize backend/market/ --focus integration --api-performance

# 실시간 업데이트 최적화
/sc:optimize backend/websocket_server.py --focus websocket --real-time

# 전체 통합 테스트
/sc:test --type integration --full-stack --e2e
```

**Integration Flow:**
1. **Marketplace APIs** → **Backend collectors** → **PostgreSQL (JSONB)**
2. **PostgreSQL** → **AI models** → **Predictions/insights**
3. **Backend APIs** → **Frontend (TanStack Query)** → **UI components**
4. **WebSocket server** → **Real-time updates** → **Frontend**

## 🔗 Key Integration Points & SuperClaude 활용

### 🛒 Coupang Integration 최적화
```bash
# 쿠팡 API 연동 분석
/sc:analyze backend/market/coupang/ --focus integration --security --hmac

# 인증 시스템 강화
/sc:implement "HMAC-SHA256 인증 개선" --type security --safe

# 멀티 계정 관리 최적화
/sc:optimize backend/market/coupang/multi_account_manager.py --focus performance

# Rate Limiting 최적화
/sc:troubleshoot "쿠팡 API 율 제한" --focus integration --auto-optimize
```

**Coupang Integration Details:**
- HMAC-SHA256 authentication with vendor-specific keys
- Multi-account support via accounts.json
- Rate limit: 10-15 requests/second
- Required: Shipping/Return center addresses

### 👤 OwnerClan Integration 고도화
```bash
# GraphQL API 성능 분석
/sc:analyze backend/supplier/ownerclan/ --focus graphql --performance

# JWT 인증 보안 강화
/sc:analyze backend/supplier/ownerclan/ --focus security --jwt

# 주문 분할 로직 최적화
/sc:optimize "주문 분할 알고리즘" --focus performance --automated
```

**OwnerClan Integration Details:**
- GraphQL API with JWT authentication
- Endpoints: Production and sandbox available
- Rate limit: 1000 requests/second
- Automatic order splitting by vendor/shipping type

### 📊 Data Collection 패턴 개선
```bash
# 데이터 수집 파이프라인 분석
/sc:analyze backend/supplier/ --focus data-collection --checkpoint

# 수집 성능 최적화
/sc:optimize "체크포인트 기반 수집" --focus performance --resilient

# 우선순위 큐 최적화
/sc:implement "고급 우선순위 큐" --type feature --performance
```

## 🛠️ Development Patterns & Best Practices

### 🚨 Error Handling 강화
```bash
# 에러 처리 패턴 분석
/sc:analyze --focus error-handling --resilience --comprehensive

# 자동 재시도 로직 구현
/sc:implement "지수 백오프 재시도" --type feature --reliability

# 에러 모니터링 대시보드
/sc:implement "실시간 에러 모니터링" --type feature --observability
```

### 🧪 Testing Strategy 고도화
```bash
# 테스트 전략 종합 분석
/sc:analyze tests/ --focus testing-strategy --coverage --comprehensive

# 비동기 테스트 최적화
/sc:optimize backend/tests/ --focus async-testing --pytest

# Mock API 개선
/sc:implement "고급 Mock API 시스템" --type testing --comprehensive

# E2E 테스트 자동화
/sc:test --type e2e --automated --full-coverage
```

### ⚡ Performance Optimization 전략
```bash
# 성능 병목 지점 분석
/sc:analyze --focus performance --bottlenecks --comprehensive

# 데이터베이스 최적화
/sc:optimize database/ --focus jsonb-indexes --partitioning --automated

# API 캐싱 전략 개선
/sc:implement "멀티 레이어 캐싱" --type performance --redis

# ML 모델 최적화
/sc:optimize backend/ai/ --focus ml-performance --lazy-loading
```

## 🎯 SuperClaude 활용 팁 & 중요 사항

### 🌏 한국어 특화 개발
```bash
# 한국어 NLP 최적화
/sc:optimize backend/ai/advanced/nlp_chatbot.py --focus korean-nlp

# 다국어 지원 확장
/sc:implement "다국어 지원 시스템" --type feature --i18n

# 한국 시간대 처리 최적화
/sc:optimize "UTC/KST 시간 처리" --focus timezone --automated
```

### 🔧 환경 설정 최적화
```bash
# 개발 환경 자동 설정
/sc:setup --environment dev --postgresql-port 5434 --automated

# 가상환경 관리 개선
/sc:optimize "Python 가상환경 관리" --focus environment --automated

# 패키징 없는 구조 최적화
/sc:analyze backend/ --focus packaging --module-structure
```

### 📈 품질 관리 목표
```bash
# 테스트 커버리지 모니터링
/sc:monitor --coverage frontend:60% backend:80% --automated

# 코드 품질 지속적 개선
/sc:optimize --focus code-quality --iterative --automated

# 성능 지표 추적
/sc:monitor --performance --real-time --alerts
```

**Important Notes:**
- 🌏 Korean language support throughout (APIs, documentation, NLP)
- 🔌 PostgreSQL on port 5434 (non-standard)
- 🐍 Virtual environment required for Python development
- ⏰ UTC for all timestamps, KST for display
- 📦 No standard Python packaging (no setup.py)
- 📊 Test coverage minimums: 60% (frontend), target 80% (backend)

---

## 🚀 SuperClaude Framework 완전 활용 가이드

더 자세한 SuperClaude Framework 활용 방법은 다음 문서를 참조하세요:
- 📖 [SUPERCLAUDE_INTEGRATION_GUIDE.md](./docs/SUPERCLAUDE_INTEGRATION_GUIDE.md) - 전체 적용 가이드
- 🎯 [SuperClaude Commands Reference](https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/Docs/commands-guide.md)

### 🎯 즉시 시작하기
```bash
# 프로젝트 전체 건강성 체크
/sc:analyze --focus architecture,security,performance --comprehensive

# 신규 기능 개발
/sc:implement "새로운 기능" --type feature --framework auto --with-tests

# 성능 최적화
/sc:optimize --focus performance --automated --iterative

# 문서화 업데이트
/sc:document --update --comprehensive --korean
```

이제 Yooni 프로젝트에서 SuperClaude Framework의 모든 기능을 최대한 활용할 수 있습니다! 🎉