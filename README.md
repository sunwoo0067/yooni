# Yoonni - E-commerce Integration Platform with AI/ML

## 개요
Yoonni는 한국 이커머스 플랫폼(쿠팡, OwnerClan, ZenTrade 등)을 통합 관리하는 AI 기반 ERP 시스템입니다.

## 주요 기능

### 🛍️ 이커머스 통합
- **쿠팡 파트너스 API** 완전 통합
- **OwnerClan GraphQL API** 연동
- **ZenTrade** 자동화
- 멀티 계정 동시 관리
- 실시간 재고/주문 동기화

### 🤖 AI/ML 기능
- **시계열 예측**: Prophet, LSTM, ARIMA를 활용한 매출 예측
- **고객 이탈 예측**: XGBoost 기반 고객 행동 분석
- **동적 가격 최적화**: 강화학습(DQN) 기반 가격 전략
- **재고 자동 발주**: 수요 예측 기반 자동 발주 시스템
- **NLP 챗봇**: 한국어 자연어 처리 기반 고객 지원
- **MLOps 플랫폼**: MLflow 기반 모델 관리 및 배포

### 📊 분석 및 모니터링
- 실시간 매출 대시보드
- 상품별 성과 분석
- 재고 알림 시스템
- 수집 작업 모니터링

## 기술 스택

### Frontend
- **Next.js 15** (App Router)
- **TypeScript**
- **Tailwind CSS** + **shadcn/ui**
- **TanStack Query v5**
- **Zustand** (상태 관리)

### Backend
- **Python 3.11**
- **FastAPI**
- **PostgreSQL** (포트: 5434)
- **Redis** (캐싱)
- **Docker** & **Docker Compose**

### AI/ML
- **PyTorch** (딥러닝)
- **scikit-learn** (머신러닝)
- **Prophet** (시계열 예측)
- **Transformers** (NLP)
- **MLflow** (MLOps)

## 빠른 시작

### 사전 요구사항
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15

### 개발 환경 설정

1. **환경 변수 설정**
```bash
cp .env.example .env.local
cp .env.prod.example .env.prod
```

2. **개발 서버 실행**
```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
python main.py
```

### 프로덕션 배포

```bash
# 배포 스크립트 실행
./scripts/deploy.sh
```

배포 후 접속:
- 웹 애플리케이션: http://localhost
- API 문서: http://localhost/api/ai/docs
- MLflow UI: http://localhost/mlflow

## 프로젝트 구조

```
yoonni/
├── frontend/               # Next.js 애플리케이션
│   ├── app/               # App Router 페이지
│   ├── components/        # UI 컴포넌트
│   ├── lib/              # 유틸리티
│   └── store/            # 상태 관리
│
├── backend/               # Python 백엔드
│   ├── market/           # 마켓플레이스 통합
│   ├── supplier/         # 공급사 연동
│   ├── ai/              # AI/ML 모듈
│   └── main.py          # FastAPI 메인
│
├── scripts/              # 운영 스크립트
│   ├── deploy.sh        # 배포
│   ├── backup.sh        # 백업
│   ├── monitor.sh       # 모니터링
│   └── rollback.sh      # 롤백
│
└── docker-compose.yml    # Docker 구성
```

## 운영 가이드

### 모니터링
```bash
# 시스템 상태 확인
./scripts/monitor.sh

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

### 백업
```bash
# 데이터베이스 백업
./scripts/backup.sh
```

### 롤백
```bash
# 이전 버전으로 롤백
./scripts/rollback.sh [태그]
```

## API 문서
- Swagger UI: `/api/ai/docs`
- ReDoc: `/api/ai/redoc`

## 라이선스
Private - 내부 사용 전용