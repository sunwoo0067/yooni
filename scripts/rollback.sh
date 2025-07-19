#!/bin/bash

# 롤백 스크립트
set -e

echo "⚠️ Yoonni 시스템 롤백"
echo "===================="

# 롤백 확인
read -p "정말로 이전 버전으로 롤백하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "롤백 취소됨"
    exit 0
fi

# 현재 상태 백업
echo "📸 현재 상태 백업 중..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres yoonni > /tmp/yoonni_before_rollback_$(date +%Y%m%d_%H%M%S).sql

# 이전 이미지 태그 확인
PREVIOUS_TAG=${1:-"previous"}
echo "🔄 롤백 태그: $PREVIOUS_TAG"

# 서비스 중지
echo "🛑 서비스 중지..."
docker-compose -f docker-compose.prod.yml down

# 이전 버전으로 이미지 변경
echo "📦 이전 버전 이미지로 변경..."
# 여기에 실제 이미지 태그 변경 로직 추가
# docker tag yoonni/backend:current yoonni/backend:rollback-$(date +%Y%m%d_%H%M%S)
# docker tag yoonni/backend:$PREVIOUS_TAG yoonni/backend:current

# 서비스 재시작
echo "🚀 서비스 재시작..."
docker-compose -f docker-compose.prod.yml up -d

# 헬스 체크
echo "❤️ 헬스 체크..."
sleep 10
./scripts/monitor.sh

echo "✅ 롤백 완료!"