#!/bin/bash
# 모니터링 서비스 중지 스크립트

echo "모니터링 서비스를 중지합니다..."

PROJECT_DIR="/home/sunwoo/yooni"
PID_DIR="$PROJECT_DIR/pids"

# WebSocket 서버 중지
if [ -f "$PID_DIR/websocket_server.pid" ]; then
    PID=$(cat "$PID_DIR/websocket_server.pid")
    if ps -p $PID > /dev/null; then
        echo "WebSocket 서버 중지 (PID: $PID)"
        kill $PID
        rm "$PID_DIR/websocket_server.pid"
    fi
fi

# API 헬스 체커 중지
if [ -f "$PID_DIR/api_health_checker.pid" ]; then
    PID=$(cat "$PID_DIR/api_health_checker.pid")
    if ps -p $PID > /dev/null; then
        echo "API 헬스 체커 중지 (PID: $PID)"
        kill $PID
        rm "$PID_DIR/api_health_checker.pid"
    fi
fi

# Next.js 개발 서버 중지
echo "프론트엔드 서버 중지..."
pkill -f "next dev"

echo "모니터링 서비스가 중지되었습니다."