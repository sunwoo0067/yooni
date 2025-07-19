.PHONY: help install test build run clean docker-build docker-up docker-down

# 기본 타겟
.DEFAULT_GOAL := help

# 환경 변수
PYTHON := python3
NPM := npm
DOCKER_COMPOSE := docker-compose

# 색상 코드
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

## help: 사용 가능한 명령어 표시
help:
	@echo "Available commands:"
	@echo ""
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/ /'

## install: 모든 종속성 설치
install: install-backend install-frontend
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

## install-backend: Backend 종속성 설치
install-backend:
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	cd backend && pip install -r requirements.txt

## install-frontend: Frontend 종속성 설치
install-frontend:
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	cd frontend && $(NPM) install

## test: 모든 테스트 실행
test: test-backend test-frontend test-integration
	@echo "$(GREEN)✓ All tests completed$(NC)"

## test-backend: Backend 테스트 실행
test-backend:
	@echo "$(YELLOW)Running backend tests...$(NC)"
	cd backend && $(PYTHON) -m pytest -v

## test-frontend: Frontend 테스트 실행
test-frontend:
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	cd frontend && $(NPM) test -- --watchAll=false

## test-integration: 통합 테스트 실행
test-integration:
	@echo "$(YELLOW)Running integration tests...$(NC)"
	./run_integration_tests.sh

## build: 애플리케이션 빌드
build: build-frontend
	@echo "$(GREEN)✓ Build completed$(NC)"

## build-frontend: Frontend 빌드
build-frontend:
	@echo "$(YELLOW)Building frontend...$(NC)"
	cd frontend && $(NPM) run build

## run: 모든 서비스 실행
run:
	@echo "$(YELLOW)Starting all services...$(NC)"
	@make run-backend &
	@make run-frontend &
	@echo "$(GREEN)✓ All services started$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Monitoring API: http://localhost:8000"
	@echo "Workflow API: http://localhost:8001"
	@echo "WebSocket: ws://localhost:8002"

## run-backend: Backend 서비스 실행
run-backend:
	@echo "$(YELLOW)Starting backend services...$(NC)"
	cd backend && $(PYTHON) monitoring_server.py &
	cd backend && $(PYTHON) websocket_server.py &
	cd backend && $(PYTHON) workflow_api_server.py &

## run-frontend: Frontend 실행
run-frontend:
	@echo "$(YELLOW)Starting frontend...$(NC)"
	cd frontend && $(NPM) run dev

## migrate: 데이터베이스 마이그레이션 실행
migrate:
	@echo "$(YELLOW)Running database migrations...$(NC)"
	cd backend && $(PYTHON) -m database.migrations

## lint: 코드 린트 실행
lint: lint-backend lint-frontend
	@echo "$(GREEN)✓ Linting completed$(NC)"

## lint-backend: Backend 린트
lint-backend:
	@echo "$(YELLOW)Linting backend code...$(NC)"
	cd backend && flake8 . --max-line-length=100 --exclude=venv,__pycache__
	cd backend && mypy . --ignore-missing-imports

## lint-frontend: Frontend 린트
lint-frontend:
	@echo "$(YELLOW)Linting frontend code...$(NC)"
	cd frontend && $(NPM) run lint

## format: 코드 포맷팅
format: format-backend
	@echo "$(GREEN)✓ Code formatting completed$(NC)"

## format-backend: Backend 코드 포맷팅
format-backend:
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	cd backend && black . --line-length=100

## clean: 빌드 파일 및 캐시 정리
clean:
	@echo "$(YELLOW)Cleaning build files and cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	rm -rf coverage/
	rm -rf htmlcov/
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

## docker-build: Docker 이미지 빌드
docker-build:
	@echo "$(YELLOW)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

## docker-up: Docker 컨테이너 실행
docker-up:
	@echo "$(YELLOW)Starting Docker containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Docker containers started$(NC)"

## docker-down: Docker 컨테이너 중지
docker-down:
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down

## docker-logs: Docker 컨테이너 로그 확인
docker-logs:
	$(DOCKER_COMPOSE) logs -f

## docker-clean: Docker 볼륨 및 이미지 정리
docker-clean:
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

## ci: CI 파이프라인 실행 (로컬)
ci: clean install lint test
	@echo "$(GREEN)✓ CI pipeline completed successfully$(NC)"