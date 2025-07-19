#!/bin/bash

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║                                          ║"
echo "║        🛑 Yoonni 로컬 환경 종료         ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Backend 프로세스 종료
if [ -f ".backend.pid" ]; then
    backend_pid=$(cat .backend.pid)
    if kill -0 $backend_pid 2>/dev/null; then
        echo -e "${BLUE}🛑 Backend API 종료 중...${NC}"
        kill $backend_pid
        echo -e "${GREEN}✅ Backend API 종료됨${NC}"
    fi
    rm .backend.pid
fi

# Frontend 프로세스 종료
if [ -f ".frontend.pid" ]; then
    frontend_pid=$(cat .frontend.pid)
    if kill -0 $frontend_pid 2>/dev/null; then
        echo -e "${BLUE}🛑 Frontend 개발 서버 종료 중...${NC}"
        kill $frontend_pid
        echo -e "${GREEN}✅ Frontend 종료됨${NC}"
    fi
    rm .frontend.pid
fi

# Docker 서비스 종료
echo -e "\n${YELLOW}Docker 서비스를 종료하시겠습니까? (y/N)${NC}"
read docker_choice

if [ "$docker_choice" = "y" ] || [ "$docker_choice" = "Y" ]; then
    echo -e "${BLUE}🐳 Docker 서비스 종료 중...${NC}"
    docker-compose -f docker-compose.local.yml down
    
    echo -e "\n${YELLOW}볼륨(데이터)도 삭제하시겠습니까? (y/N)${NC}"
    echo -e "${RED}⚠️  주의: 모든 데이터가 삭제됩니다!${NC}"
    read volume_choice
    
    if [ "$volume_choice" = "y" ] || [ "$volume_choice" = "Y" ]; then
        docker-compose -f docker-compose.local.yml down -v
        echo -e "${GREEN}✅ 볼륨 삭제됨${NC}"
    fi
fi

echo -e "\n${GREEN}✅ 종료 완료!${NC}"