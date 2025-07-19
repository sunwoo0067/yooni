#!/bin/bash

echo "🚀 Yooni 비즈니스 인텔리전스 시스템 시작"
echo "=================================="

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PostgreSQL과 Redis 확인
echo -e "${BLUE}1. 데이터베이스 서비스 확인...${NC}"
docker ps | grep postgres > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL 시작 중...${NC}"
    cd ~/yooni && docker-compose up -d postgres
fi

docker ps | grep redis > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Redis 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 시작 중...${NC}"
    cd ~/yooni && docker-compose up -d redis
fi

# 기존 API 서버들이 실행 중인지 확인
echo -e "\n${BLUE}2. API 서버 상태 확인...${NC}"

# BI API 시작
echo -e "\n${BLUE}3. Business Intelligence API 시작 (포트 8005)...${NC}"
cd ~/yooni/backend/api
python business_intelligence_api.py &
BI_PID=$!
echo "BI API PID: $BI_PID"

# 잠시 대기
sleep 3

# API 상태 확인
echo -e "\n${BLUE}4. API 상태 확인...${NC}"
curl -s http://localhost:8005/ > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ BI API 정상 작동${NC}"
else
    echo -e "${YELLOW}⚠️  BI API 시작 중...${NC}"
fi

echo -e "\n${GREEN}✅ 비즈니스 인텔리전스 시스템 준비 완료!${NC}"
echo -e "\n📊 접속 정보:"
echo -e "   - BI API: http://localhost:8005"
echo -e "   - BI 대시보드: http://localhost:3000/bi/dashboard"
echo -e "   - API 문서: http://localhost:8005/docs"

echo -e "\n💡 다음 명령어로 테스트 실행:"
echo -e "   cd ~/yooni/backend/bi"
echo -e "   python test_bi_system.py"

echo -e "\n🛑 종료하려면:"
echo -e "   kill $BI_PID"

# 프로세스 유지
wait $BI_PID