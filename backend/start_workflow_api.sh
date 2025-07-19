#!/bin/bash

# 워크플로우 API 서버 시작 스크립트

echo "Starting Workflow API Server..."

# Python 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed!"
    exit 1
fi

# 필요한 패키지 설치 확인
echo "Checking required packages..."
pip install -q fastapi uvicorn croniter aiohttp

# 서버 실행
cd /home/sunwoo/yooni/backend
python3 workflow_api_server.py