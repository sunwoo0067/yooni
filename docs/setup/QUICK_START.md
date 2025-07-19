# Quick Start Guide

## Prerequisites
- Docker & Docker Compose installed
- Node.js 18+ and Python 3.11+
- PostgreSQL client tools
- Git

## 1. Clone and Setup Environment
```bash
# Clone repository
git clone <repository-url>
cd yoonni

# Copy environment files
cp .env.prod.example .env.prod
cp frontend/.env.local.example frontend/.env.local

# Edit environment files with your credentials
nano .env.prod
nano frontend/.env.local
```

## 2. Start Core Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker ps

# Check database connection
psql postgresql://postgres:1234@localhost:5434/yoonni
```

## 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start AI API server
python simple_api.py  # Runs on port 8003

# Or start full AI service
python main.py  # Runs on port 8000
```

## 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev  # Runs on http://localhost:3000

# Build for production
npm run build
npm start
```

## 5. Verify Installation
- Frontend: http://localhost:3000
- AI API Docs: http://localhost:8003/docs
- Health Check: http://localhost:8003/health

## 6. Run Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```