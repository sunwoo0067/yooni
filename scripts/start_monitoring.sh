#!/bin/bash
# 모니터링 서비스 시작 스크립트

echo "모니터링 서비스를 시작합니다..."

# 프로젝트 디렉토리
PROJECT_DIR="/home/sunwoo/yooni"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# PID 파일 위치
PID_DIR="$PROJECT_DIR/pids"
mkdir -p $PID_DIR

# Redis 확인
echo "Redis 상태 확인..."
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Redis가 실행중이지 않습니다. Redis를 먼저 시작해주세요."
    exit 1
fi

# WebSocket 서버 시작
echo "WebSocket 서버 시작..."
cd $BACKEND_DIR
nohup python3 websocket_server.py > $PROJECT_DIR/logs/websocket_server.log 2>&1 &
echo $! > $PID_DIR/websocket_server.pid
echo "WebSocket 서버 PID: $(cat $PID_DIR/websocket_server.pid)"

# API 헬스 체커 시작
echo "API 헬스 체커 시작..."
cd $BACKEND_DIR
nohup python3 services/api_health_checker.py > $PROJECT_DIR/logs/api_health_checker.log 2>&1 &
echo $! > $PID_DIR/api_health_checker.pid
echo "API 헬스 체커 PID: $(cat $PID_DIR/api_health_checker.pid)"

# 프론트엔드 개발 서버 (개발 환경)
echo "프론트엔드 서버 시작..."
cd $FRONTEND_DIR
npm install
npm run dev &

echo ""
echo "모니터링 서비스가 시작되었습니다!"
echo "- WebSocket 서버: ws://localhost:8765"
echo "- 프론트엔드: http://localhost:3000/monitoring/dashboard"
echo ""
echo "서비스 중지: ./scripts/stop_monitoring.sh"