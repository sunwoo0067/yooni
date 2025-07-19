#!/bin/bash
# Redis 설치 스크립트

echo "Redis 설치를 시작합니다..."

# Ubuntu/Debian 기반 시스템
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y redis-server
    
    # Redis 설정 수정 (필요시)
    sudo sed -i 's/^# requirepass/requirepass redis123/' /etc/redis/redis.conf
    sudo sed -i 's/^bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
    
    # Redis 서비스 시작
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    echo "Redis가 성공적으로 설치되었습니다."
    
# macOS
elif command -v brew &> /dev/null; then
    brew install redis
    brew services start redis
    
    echo "Redis가 성공적으로 설치되었습니다."
    
else
    echo "지원하지 않는 운영체제입니다. 수동으로 Redis를 설치해주세요."
    exit 1
fi

# Redis 연결 테스트
redis-cli ping
if [ $? -eq 0 ]; then
    echo "Redis 연결 테스트 성공!"
else
    echo "Redis 연결 테스트 실패. 설정을 확인해주세요."
fi