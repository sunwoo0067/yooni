#!/bin/bash

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로고 출력
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║                                          ║"
echo "║        🚀 Yoonni 로컬 환경 시작         ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 현재 디렉토리 확인
if [ ! -f "docker-compose.local.yml" ]; then
    echo -e "${RED}❌ 에러: Yoonni 프로젝트 루트 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

# 기능 선택
echo -e "${YELLOW}어떤 환경을 시작하시겠습니까?${NC}"
echo "1) 기본 환경 (PostgreSQL + Redis)"
echo "2) ML 포함 (PostgreSQL + Redis + MLflow)"
echo "3) 관리 도구 포함 (모든 서비스 + Adminer + Redis Commander)"
echo "4) 최소 환경 (PostgreSQL만)"
echo -n "선택 [1-4]: "
read choice

# Docker 프로세스 확인
echo -e "\n${BLUE}🔍 기존 Docker 컨테이너 확인 중...${NC}"
existing_containers=$(docker ps -a --filter "name=yoonni" --format "{{.Names}}")
if [ ! -z "$existing_containers" ]; then
    echo -e "${YELLOW}기존 컨테이너가 발견되었습니다:${NC}"
    echo "$existing_containers"
    echo -n "기존 컨테이너를 삭제하시겠습니까? (y/N): "
    read remove_choice
    if [ "$remove_choice" = "y" ] || [ "$remove_choice" = "Y" ]; then
        docker-compose -f docker-compose.local.yml down -v
        echo -e "${GREEN}✅ 기존 컨테이너 삭제 완료${NC}"
    fi
fi

# Docker Compose 실행
echo -e "\n${BLUE}🐳 Docker 서비스 시작 중...${NC}"
case $choice in
    1)
        docker-compose -f docker-compose.local.yml up -d postgres redis
        services="PostgreSQL, Redis"
        ;;
    2)
        docker-compose -f docker-compose.local.yml --profile ml up -d
        services="PostgreSQL, Redis, MLflow"
        ;;
    3)
        docker-compose -f docker-compose.local.yml --profile ml --profile tools up -d
        services="모든 서비스"
        ;;
    4)
        docker-compose -f docker-compose.local.yml up -d postgres
        services="PostgreSQL"
        ;;
    *)
        echo -e "${RED}❌ 잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

# 서비스 상태 확인
echo -e "\n${BLUE}⏳ 서비스 준비 상태 확인 중...${NC}"
sleep 3

# PostgreSQL 상태 확인
echo -n "PostgreSQL 상태: "
if docker exec yoonni-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 정상${NC}"
else
    echo -e "${RED}❌ 실패${NC}"
    echo "로그 확인: docker logs yoonni-postgres-1"
fi

# Redis 상태 확인 (선택된 경우)
if [[ $choice != "4" ]]; then
    echo -n "Redis 상태: "
    if docker exec yoonni-redis-1 redis-cli -a redis123 ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 정상${NC}"
    else
        echo -e "${RED}❌ 실패${NC}"
        echo "로그 확인: docker logs yoonni-redis-1"
    fi
fi

# Backend 시작 옵션
echo -e "\n${YELLOW}Backend API를 시작하시겠습니까?${NC}"
echo "1) simple_api.py (포트 8003) - 기본 AI API"
echo "2) main.py (포트 8000) - 전체 AI 서비스"
echo "3) 건너뛰기"
echo -n "선택 [1-3]: "
read backend_choice

if [ "$backend_choice" != "3" ]; then
    cd backend
    
    # 가상환경 확인
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}🐍 Python 가상환경 생성 중...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Backend 실행
    case $backend_choice in
        1)
            echo -e "${BLUE}🚀 Simple API 서버 시작 중...${NC}"
            python simple_api.py > ../logs/simple_api.log 2>&1 &
            backend_pid=$!
            backend_port=8003
            backend_name="Simple API"
            ;;
        2)
            echo -e "${BLUE}🚀 Main API 서버 시작 중...${NC}"
            python main.py > ../logs/main_api.log 2>&1 &
            backend_pid=$!
            backend_port=8000
            backend_name="Main API"
            ;;
    esac
    
    cd ..
fi

# Frontend 시작 옵션
echo -e "\n${YELLOW}Frontend를 시작하시겠습니까? (y/N)${NC}"
read frontend_choice

if [ "$frontend_choice" = "y" ] || [ "$frontend_choice" = "Y" ]; then
    cd frontend
    
    # 의존성 확인
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}📦 Frontend 의존성 설치 중...${NC}"
        npm install
    fi
    
    echo -e "${BLUE}🎨 Frontend 개발 서버 시작 중...${NC}"
    npm run dev > ../logs/frontend.log 2>&1 &
    frontend_pid=$!
    
    cd ..
fi

# 최종 상태 출력
echo -e "\n${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         ✅ 시작 완료!                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}📋 실행된 서비스:${NC}"
echo -e "   - Docker: $services"
[ ! -z "$backend_name" ] && echo -e "   - Backend: $backend_name (포트 $backend_port)"
[ ! -z "$frontend_pid" ] && echo -e "   - Frontend: Next.js (포트 3000)"

echo -e "\n${BLUE}🔗 접속 URL:${NC}"
[ ! -z "$frontend_pid" ] && echo -e "   - Frontend: ${GREEN}http://localhost:3000${NC}"
[ ! -z "$backend_port" ] && echo -e "   - API Docs: ${GREEN}http://localhost:$backend_port/docs${NC}"
[ "$choice" = "2" ] || [ "$choice" = "3" ] && echo -e "   - MLflow: ${GREEN}http://localhost:5000${NC}"
[ "$choice" = "3" ] && echo -e "   - Adminer: ${GREEN}http://localhost:8080${NC}"
[ "$choice" = "3" ] && echo -e "   - Redis Commander: ${GREEN}http://localhost:8081${NC}"

echo -e "\n${BLUE}🛑 종료하려면:${NC}"
echo "   ./scripts/stop-local.sh"

# PID 저장
echo "$backend_pid" > .backend.pid 2>/dev/null
echo "$frontend_pid" > .frontend.pid 2>/dev/null

echo -e "\n${YELLOW}💡 팁: 로그 확인${NC}"
echo "   - Backend: tail -f logs/simple_api.log"
echo "   - Frontend: tail -f logs/frontend.log"
echo "   - Docker: docker-compose -f docker-compose.local.yml logs -f"