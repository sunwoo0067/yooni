#!/bin/bash

# 시스템 모니터링 스크립트
set -e

echo "📊 Yoonni 시스템 모니터링"
echo "========================="
echo ""

# 컨테이너 상태 확인
echo "🐳 컨테이너 상태:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💾 디스크 사용량:"
df -h | grep -E '^/dev/|Filesystem'

echo ""
echo "🧠 메모리 사용량:"
free -h

echo ""
echo "📈 PostgreSQL 연결 수:"
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

echo ""
echo "🔥 Redis 메모리 사용량:"
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli -a ${REDIS_PASSWORD:-redis123} INFO memory | grep used_memory_human

echo ""
echo "📊 MLflow 실험 수:"
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres mlflow -c "SELECT COUNT(DISTINCT experiment_id) as experiments, COUNT(*) as runs FROM runs;" 2>/dev/null || echo "MLflow 데이터베이스 초기화 필요"

echo ""
echo "🤖 AI 모델 상태:"
curl -s http://localhost/api/ai/models/status 2>/dev/null | jq '.' || echo "AI 서비스 확인 필요"

echo ""
echo "⚠️ 최근 에러 로그 (최근 10개):"
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error | tail -10 || echo "에러 없음"