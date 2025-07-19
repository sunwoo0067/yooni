#!/bin/bash

# 배포 스크립트
set -e

echo "🚀 Yooni AI/ML 시스템 배포 시작..."

# 환경 변수 확인
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod 파일이 없습니다. .env.prod 파일을 생성해주세요."
    exit 1
fi

# 환경 변수 로드
set -a
source .env.prod
set +a

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker-compose -f docker-compose.prod.yml build

# 기존 컨테이너 중지 및 제거
echo "🛑 기존 컨테이너 중지..."
docker-compose -f docker-compose.prod.yml down

# 데이터베이스 초기화 (init.sql이 자동 실행됨)
echo "🗄️ 데이터베이스 초기화 중..."
sleep 5

# 서비스 시작
echo "🚀 서비스 시작..."
docker-compose -f docker-compose.prod.yml up -d

# 헬스 체크
echo "❤️ 서비스 헬스 체크..."
sleep 10

# API 헬스 체크
for service in "localhost" "localhost:8003" "localhost:5000"; do
    if curl -f http://$service/health > /dev/null 2>&1; then
        echo "✅ $service 정상 작동 중"
    else
        echo "❌ $service 응답 없음"
    fi
done

# 로그 확인
echo "📋 최근 로그:"
docker-compose -f docker-compose.prod.yml logs --tail=50

echo "✅ 배포 완료!"
echo ""
echo "📌 접속 정보:"
echo "- 웹 애플리케이션: http://localhost"
echo "- API 문서: http://localhost/api/ai/docs"
echo "- MLflow UI: http://localhost/mlflow"
echo ""
echo "💡 로그 확인: docker-compose -f docker-compose.prod.yml logs -f"