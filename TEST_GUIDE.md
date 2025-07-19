# 통합 테스트 가이드

## 개요

이 문서는 Yoonni 프로젝트의 통합 테스트 실행 방법과 테스트 구조에 대해 설명합니다.

## 테스트 구조

### 백엔드 테스트
```
backend/
├── tests/
│   ├── __init__.py
│   └── integration/
│       ├── __init__.py
│       ├── test_database_pool.py      # 데이터베이스 연결 풀 테스트
│       └── test_error_handlers.py     # 에러 핸들링 테스트
└── pytest.ini                         # pytest 설정 파일
```

### 프론트엔드 테스트
```
frontend/
├── __tests__/
│   └── integration/
│       └── collection.test.ts         # 컬렉션 API 통합 테스트
├── jest.config.js                     # Jest 설정
└── jest.setup.js                      # Jest 글로벌 설정
```

## 테스트 실행 방법

### 1. 전체 통합 테스트 실행
```bash
# 실행 권한 부여 (최초 1회)
chmod +x run_integration_tests.sh

# 테스트 실행
./run_integration_tests.sh
```

### 2. 백엔드 테스트만 실행
```bash
cd backend

# 가상 환경 활성화
source venv/bin/activate

# 특정 테스트 실행
pytest tests/integration/test_database_pool.py -v
pytest tests/integration/test_error_handlers.py -v

# 전체 통합 테스트 실행 (커버리지 포함)
pytest tests/integration/ --cov=core --cov=db --cov=ai -v
```

### 3. 프론트엔드 테스트만 실행
```bash
cd frontend

# 특정 테스트 실행
npm test -- __tests__/integration/collection.test.ts

# 전체 테스트 실행 (워치 모드)
npm test

# CI 모드로 실행 (워치 모드 비활성화)
npm test -- --watchAll=false

# 커버리지 포함
npm test -- --coverage
```

## 주요 테스트 항목

### 백엔드 테스트

#### 데이터베이스 연결 풀 테스트
- 싱글톤 패턴 검증
- 동시 연결 처리
- 연결 재시도 로직
- 트랜잭션 롤백
- 쿼리 실행 헬퍼

#### 에러 핸들러 테스트
- API 에러 처리
- 검증 에러 처리
- Rate Limit 처리
- 재시도 데코레이터
- 서킷 브레이커 패턴

### 프론트엔드 테스트

#### 컬렉션 API 테스트
- GraphQL 요청/응답
- 에러 처리
- 재시도 로직
- 배치 처리
- 재고 상태 계산

## 테스트 환경 요구사항

### 데이터베이스
- PostgreSQL 15+ (포트: 5434)
- 데이터베이스명: yoonni
- 사용자: postgres
- 비밀번호: 1234

### 백엔드
- Python 3.11+
- pytest, pytest-asyncio, pytest-cov
- 가상 환경 권장

### 프론트엔드
- Node.js 20+
- npm 또는 yarn
- Jest 29+

## 커버리지 리포트

테스트 실행 후 다음 위치에서 커버리지 리포트를 확인할 수 있습니다:

- **백엔드**: `backend/htmlcov/index.html`
- **프론트엔드**: `frontend/coverage/lcov-report/index.html`

## CI/CD 통합

GitHub Actions를 통해 자동으로 통합 테스트가 실행됩니다:

- Push to main/develop 브랜치
- Pull Request 생성 시
- 매일 자정 (스케줄)

### CI 워크플로우 구성
1. 백엔드 테스트 (Python 3.11, PostgreSQL, Redis)
2. 프론트엔드 테스트 (Node.js 20, PostgreSQL)
3. 코드 린팅 및 타입 체크
4. 보안 취약점 스캔 (Trivy)

## 테스트 작성 가이드

### 백엔드 테스트 작성
```python
import pytest
from your_module import YourClass

class TestYourFeature:
    @pytest.fixture
    def setup_data(self):
        # 테스트 데이터 준비
        return {"key": "value"}
    
    def test_feature_success(self, setup_data):
        # Given
        data = setup_data
        
        # When
        result = YourClass.process(data)
        
        # Then
        assert result.success is True
```

### 프론트엔드 테스트 작성
```typescript
import { describe, test, expect } from '@jest/globals';

describe('YourComponent', () => {
  test('should handle success case', async () => {
    // Given
    const input = { data: 'test' };
    
    // When
    const result = await yourFunction(input);
    
    // Then
    expect(result).toEqual(expectedOutput);
  });
});
```

## 문제 해결

### PostgreSQL 연결 실패
```bash
# PostgreSQL 상태 확인
pg_isready -h localhost -p 5434

# Docker로 PostgreSQL 실행
docker run -d \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=yoonni \
  -p 5434:5432 \
  postgres:15
```

### Python 가상 환경 문제
```bash
# 가상 환경 재생성
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node modules 문제
```bash
# node_modules 재설치
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 추가 리소스

- [pytest 문서](https://docs.pytest.org/)
- [Jest 문서](https://jestjs.io/docs/getting-started)
- [GitHub Actions 문서](https://docs.github.com/en/actions)