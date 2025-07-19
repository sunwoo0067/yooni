#!/bin/bash

# 프로젝트 초기 설정 스크립트

set -e

echo "=== Project Setup Script ==="

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Python 버전 확인
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ "$PYTHON_VERSION" < "$REQUIRED_VERSION" ]]; then
    echo -e "${RED}Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Node.js 버전 확인
echo -e "${YELLOW}Checking Node.js version...${NC}"
NODE_VERSION=$(node --version 2>&1 | cut -d'v' -f2)
REQUIRED_NODE="18"

if [[ "${NODE_VERSION%%.*}" -lt "$REQUIRED_NODE" ]]; then
    echo -e "${RED}Node.js $REQUIRED_NODE or higher is required. Found: v$NODE_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js v$NODE_VERSION${NC}"

# PostgreSQL 확인
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL installed${NC}"

# Redis 확인
echo -e "${YELLOW}Checking Redis...${NC}"
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}Redis is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis installed${NC}"

# Python 가상환경 생성
echo -e "\n${YELLOW}Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# 가상환경 활성화
source venv/bin/activate

# Backend 종속성 설치
echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
cd backend
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..

# Frontend 종속성 설치
echo -e "\n${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..

# Pre-commit hooks 설치
echo -e "\n${YELLOW}Installing pre-commit hooks...${NC}"
pip install pre-commit
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# 데이터베이스 설정
echo -e "\n${YELLOW}Setting up database...${NC}"
read -p "Do you want to create the database? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    createdb -h localhost -p 5434 -U postgres yoonni || echo "Database may already exist"
    createdb -h localhost -p 5434 -U postgres yoonni_test || echo "Test database may already exist"
    
    # 마이그레이션 실행
    cd backend
    python -m database.migrations
    cd ..
    echo -e "${GREEN}✓ Database setup completed${NC}"
fi

# 환경 변수 파일 생성
echo -e "\n${YELLOW}Creating environment files...${NC}"

# Backend .env
if [ ! -f "backend/.env" ]; then
    cat > backend/.env << EOF
# Database
DATABASE_URL=postgresql://postgres:1234@localhost:5434/yoonni

# Redis
REDIS_URL=redis://localhost:6379

# API Keys (add your actual keys here)
COUPANG_ACCESS_KEY=
COUPANG_SECRET_KEY=
COUPANG_VENDOR_ID=

OWNERCLAN_API_KEY=
ZENTRADE_API_KEY=
EOF
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${GREEN}✓ backend/.env already exists${NC}"
fi

# Frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    cat > frontend/.env.local << EOF
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8002

# Database (for API routes)
DATABASE_URL=postgresql://postgres:1234@localhost:5434/yoonni
EOF
    echo -e "${GREEN}✓ Created frontend/.env.local${NC}"
else
    echo -e "${GREEN}✓ frontend/.env.local already exists${NC}"
fi

# Git hooks 설정
echo -e "\n${YELLOW}Setting up git hooks...${NC}"
if [ -d ".git" ]; then
    # Commit message template
    cat > .gitmessage << EOF
# <type>: <subject>
# 
# <body>
# 
# <footer>
# 
# Type: feat, fix, docs, style, refactor, test, chore
# Subject: 50 chars max, imperative mood
# Body: Explain what and why, not how
# Footer: Issues closed, breaking changes
EOF
    git config commit.template .gitmessage
    echo -e "${GREEN}✓ Git commit template configured${NC}"
fi

# 테스트 실행
echo -e "\n${YELLOW}Running initial tests...${NC}"
read -p "Do you want to run tests now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    make test
fi

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo -e "\nNext steps:"
echo -e "1. Update .env files with your API keys"
echo -e "2. Run ${YELLOW}make run${NC} to start all services"
echo -e "3. Visit ${YELLOW}http://localhost:3000${NC} to access the application"
echo -e "\nUseful commands:"
echo -e "- ${YELLOW}make help${NC}: Show all available commands"
echo -e "- ${YELLOW}make test${NC}: Run all tests"
echo -e "- ${YELLOW}make docker-up${NC}: Start with Docker"
echo -e "\nDon't forget to activate the virtual environment:"
echo -e "${YELLOW}source venv/bin/activate${NC}"