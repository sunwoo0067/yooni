# 공급사 통합 관리 인터페이스 가이드

## 개요
공급사 상품 수집 시스템의 웹 기반 관리 인터페이스입니다. 실시간 수집 상태 모니터링, AI 분석 결과 확인, 수동 수집 트리거 기능을 제공합니다.

## 구성 요소

### 1. 백엔드 API 서버
- **파일**: `/backend/api/supplier_management_api.py`
- **포트**: 8004
- **엔드포인트**:
  - `GET /api/suppliers` - 공급사 현황
  - `GET /api/collection/status` - 수집 상태
  - `POST /api/collection/trigger` - 수집 트리거
  - `GET /api/dashboard/stats` - 대시보드 통계
  - `GET /api/ai/insights` - AI 분석 결과

### 2. 프론트엔드 페이지
- **위치**: `/frontend/app/suppliers/management/page.tsx`
- **접속**: http://localhost:3000/suppliers/management

## 주요 기능

### 대시보드
- 전체 상품 수 및 활성 상품 통계
- AI 분석 완료 상품 수
- 24시간 수집 현황
- 성공률 모니터링

### 공급사 현황
- 각 공급사별 상태 카드
- 실시간 수집 상태 표시
- 성공률 및 평균 처리 시간
- 개별 수집 트리거 버튼

### 수집 모니터링
- 실행 중인 수집 작업 실시간 표시
- 최근 완료된 수집 내역
- 수집 성공/실패 상태
- 처리된 상품 수 및 소요 시간

### AI 인사이트
- 가격 예측 결과
- 수요 등급 (A~E)
- 수요 점수
- 카테고리별 분석

## 실행 방법

### 1. 백엔드 API 서버 실행
```bash
cd /home/sunwoo/yooni/backend
source venv/bin/activate
python api/supplier_management_api.py
```

### 2. 프론트엔드 실행
```bash
cd /home/sunwoo/yooni/frontend
npm run dev
```

### 3. 접속
브라우저에서 http://localhost:3000/suppliers/management 접속

## 사용 방법

### 수동 수집 시작
1. "공급사 현황" 탭으로 이동
2. 원하는 공급사의 "수집 시작" 버튼 클릭
3. 수집이 시작되면 상태가 "실행중"으로 변경
4. 30초마다 자동으로 상태 업데이트

### 전체 수집
- 상단의 "전체 수집" 버튼 클릭
- 모든 공급사의 수집이 순차적으로 실행

### AI 분석 결과 확인
1. "AI 인사이트" 탭으로 이동
2. 수요 등급별로 색상 구분
   - A등급: 빨간색 (매우 높은 수요)
   - B등급: 주황색 (높은 수요)
   - C등급: 노란색 (보통 수요)
   - D등급: 파란색 (낮은 수요)
   - E등급: 회색 (매우 낮은 수요)

## 기술 스택
- **백엔드**: FastAPI, PostgreSQL, APScheduler
- **프론트엔드**: Next.js 15, React 19, Tailwind CSS
- **UI 컴포넌트**: shadcn/ui
- **상태 관리**: React Hooks
- **데이터 페칭**: Fetch API with 30초 폴링

## 추가 개발 예정
- WebSocket을 통한 실시간 업데이트
- 스케줄 관리 UI
- 수집 로그 상세 보기
- AI 모델 재학습 트리거
- 알림 설정 (Slack, Email)