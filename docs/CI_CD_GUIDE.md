# CI/CD 가이드

## 개요

이 프로젝트는 GitHub Actions를 사용한 자동화된 CI/CD 파이프라인을 구축했습니다.

## CI/CD 파이프라인 구성

### 1. Backend 테스트
- Python 3.11 환경
- PostgreSQL 15 + Redis 7
- pytest를 사용한 단위 테스트
- 커버리지 측정 및 Codecov 업로드

### 2. Frontend 테스트
- Node.js 18 환경
- Jest를 사용한 단위 테스트
- ESLint 코드 품질 검사
- Next.js 빌드 검증

### 3. 통합 테스트
- 전체 시스템 통합 테스트
- API 엔드포인트 테스트
- E2E 시나리오 테스트

### 4. Docker 빌드 및 배포
- 멀티 스테이지 Docker 빌드
- Docker Hub로 자동 푸시
- 커밋 SHA 태그

## 로컬 테스트 실행

### 필수 요구사항
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### 테스트 명령어

```bash
# 모든 종속성 설치
make install

# 데이터베이스 마이그레이션
make migrate

# 모든 테스트 실행
make test

# 개별 테스트 실행
make test-backend      # Backend 단위 테스트
make test-frontend     # Frontend 단위 테스트
make test-integration  # 통합 테스트

# 코드 품질 검사
make lint

# 코드 포맷팅
make format

# CI 파이프라인 실행 (로컬)
make ci
```

### Docker를 사용한 테스트

```bash
# Docker 이미지 빌드
make docker-build

# 컨테이너 실행
make docker-up

# 로그 확인
make docker-logs

# 컨테이너 중지
make docker-down
```

## GitHub Actions 설정

### 필수 Secrets

GitHub 저장소 Settings > Secrets에 다음 값들을 설정해야 합니다:

- `DOCKER_USERNAME`: Docker Hub 사용자명
- `DOCKER_PASSWORD`: Docker Hub 비밀번호

### 브랜치 보호 규칙

- `main` 브랜치는 보호되며 PR을 통해서만 병합 가능
- 모든 PR은 테스트를 통과해야 병합 가능
- 커밋은 squash merge 사용 권장

## 테스트 커버리지

### Backend 커버리지
```bash
cd backend
pytest --cov=. --cov-report=html
# HTML 리포트: htmlcov/index.html
```

### Frontend 커버리지
```bash
cd frontend
npm test -- --coverage
# 리포트: coverage/lcov-report/index.html
```

## 통합 테스트 시나리오

### 1. 워크플로우 통합 테스트
- 이벤트 기반 워크플로우 생성 및 실행
- 수동 워크플로우 실행
- 워크플로우 CRUD 작업
- 오류 처리 테스트

### 2. API 통합 테스트
- 전체 서비스 헬스 체크
- 모니터링 메트릭 흐름
- 상품/주문 관리 흐름
- 로그 집계
- 서비스 간 이벤트 흐름

### 3. E2E 시나리오 테스트
- 주문 처리 전체 프로세스
- 재고 부족 알림 워크플로우
- 일일 리포트 생성
- 멀티 마켓플레이스 동기화

## 트러블슈팅

### 테스트 실패 시

1. **데이터베이스 연결 오류**
   ```bash
   # PostgreSQL 서비스 확인
   sudo systemctl status postgresql
   
   # 포트 확인
   lsof -i :5434
   ```

2. **Redis 연결 오류**
   ```bash
   # Redis 서비스 확인
   redis-cli ping
   ```

3. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   lsof -i :8000
   lsof -i :8001
   lsof -i :8002
   lsof -i :3000
   ```

### CI 실패 시

1. GitHub Actions 로그 확인
2. 로컬에서 동일한 환경으로 테스트
3. 종속성 버전 확인

## 베스트 프랙티스

1. **커밋 메시지**
   - 명확한 커밋 메시지 작성
   - 타입 표시: feat, fix, docs, style, refactor, test, chore

2. **테스트 작성**
   - 모든 새 기능에 테스트 포함
   - 테스트 커버리지 80% 이상 유지

3. **코드 리뷰**
   - 모든 PR은 코드 리뷰 필수
   - 자동화된 테스트 통과 확인

4. **배포**
   - main 브랜치 병합 시 자동 Docker 이미지 빌드
   - 태그 생성 시 자동 릴리스