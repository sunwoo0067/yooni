#!/bin/bash

# 통합 테스트 실행 스크립트
# 백엔드와 프론트엔드의 모든 통합 테스트를 실행합니다.

set -e  # 에러 발생 시 즉시 종료

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 테스트 결과 변수
BACKEND_TEST_PASSED=0
FRONTEND_TEST_PASSED=0

# PostgreSQL 연결 확인
check_postgres() {
    log_info "PostgreSQL 연결 확인 중..."
    
    if pg_isready -h localhost -p 5434 -U postgres > /dev/null 2>&1; then
        log_info "PostgreSQL 연결 성공"
        return 0
    else
        log_error "PostgreSQL 연결 실패. 데이터베이스가 실행 중인지 확인하세요."
        return 1
    fi
}

# 백엔드 테스트 실행
run_backend_tests() {
    log_info "백엔드 통합 테스트 시작..."
    
    cd backend
    
    # Python 가상 환경 활성화 (있는 경우)
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # pytest 설치 확인
    if ! command -v pytest &> /dev/null; then
        log_warning "pytest가 설치되지 않았습니다. 설치 중..."
        pip install pytest pytest-asyncio pytest-cov
    fi
    
    # 통합 테스트 실행
    log_info "데이터베이스 연결 풀 테스트 실행 중..."
    if pytest tests/integration/test_database_pool.py -v; then
        log_info "데이터베이스 연결 풀 테스트 통과"
    else
        log_error "데이터베이스 연결 풀 테스트 실패"
        BACKEND_TEST_PASSED=1
    fi
    
    log_info "에러 핸들러 테스트 실행 중..."
    if pytest tests/integration/test_error_handlers.py -v; then
        log_info "에러 핸들러 테스트 통과"
    else
        log_error "에러 핸들러 테스트 실패"
        BACKEND_TEST_PASSED=1
    fi
    
    # 전체 백엔드 테스트 실행 (coverage 포함)
    log_info "전체 백엔드 테스트 실행 중 (coverage 포함)..."
    pytest tests/integration/ \
        --cov=core \
        --cov=db \
        --cov=ai \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        -v
    
    cd ..
}

# 프론트엔드 테스트 실행
run_frontend_tests() {
    log_info "프론트엔드 통합 테스트 시작..."
    
    cd frontend
    
    # npm 설치 확인
    if [ ! -d "node_modules" ]; then
        log_warning "node_modules가 없습니다. 의존성 설치 중..."
        npm install
    fi
    
    # Jest 설정 파일 확인
    if [ ! -f "jest.config.js" ]; then
        log_warning "jest.config.js가 없습니다. 기본 설정으로 실행합니다."
    fi
    
    # 통합 테스트 실행
    log_info "컬렉션 통합 테스트 실행 중..."
    if npm test -- __tests__/integration/collection.test.ts --coverage; then
        log_info "컬렉션 통합 테스트 통과"
    else
        log_error "컬렉션 통합 테스트 실패"
        FRONTEND_TEST_PASSED=1
    fi
    
    # 전체 프론트엔드 테스트 실행
    log_info "전체 프론트엔드 테스트 실행 중..."
    npm test -- --coverage --watchAll=false
    
    cd ..
}

# 테스트 결과 요약
print_summary() {
    echo ""
    echo "=================================="
    echo "        테스트 결과 요약          "
    echo "=================================="
    
    if [ $BACKEND_TEST_PASSED -eq 0 ]; then
        echo -e "백엔드 테스트: ${GREEN}통과${NC}"
    else
        echo -e "백엔드 테스트: ${RED}실패${NC}"
    fi
    
    if [ $FRONTEND_TEST_PASSED -eq 0 ]; then
        echo -e "프론트엔드 테스트: ${GREEN}통과${NC}"
    else
        echo -e "프론트엔드 테스트: ${RED}실패${NC}"
    fi
    
    echo ""
    
    # Coverage 리포트 위치 안내
    if [ -d "backend/htmlcov" ]; then
        log_info "백엔드 커버리지 리포트: backend/htmlcov/index.html"
    fi
    
    if [ -d "frontend/coverage" ]; then
        log_info "프론트엔드 커버리지 리포트: frontend/coverage/lcov-report/index.html"
    fi
    
    # 전체 테스트 결과 반환
    if [ $BACKEND_TEST_PASSED -eq 0 ] && [ $FRONTEND_TEST_PASSED -eq 0 ]; then
        log_info "모든 테스트가 성공적으로 통과했습니다!"
        return 0
    else
        log_error "일부 테스트가 실패했습니다."
        return 1
    fi
}

# 메인 실행
main() {
    log_info "통합 테스트 실행을 시작합니다..."
    
    # PostgreSQL 연결 확인
    if ! check_postgres; then
        exit 1
    fi
    
    # 백엔드 테스트
    run_backend_tests
    
    # 프론트엔드 테스트
    run_frontend_tests
    
    # 결과 요약
    print_summary
}

# 스크립트 실행
main