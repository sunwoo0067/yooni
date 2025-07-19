#!/bin/bash

# 간단한 시스템 모니터링 스크립트
echo "📊 Yoonni 시스템 모니터링"
echo "========================="
echo ""

# 서비스 상태 확인
echo "🌐 서비스 상태:"
echo "- AI API: $(curl -s http://localhost:8003/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ 응답 없음')"
echo "- PostgreSQL: $(psql postgresql://postgres:1234@localhost:5434/yoonni -c 'SELECT 1' > /dev/null 2>&1 && echo '✅ 정상' || echo '❌ 연결 실패')"
echo ""

# PostgreSQL 상태
echo "🗄️ PostgreSQL 정보:"
psql postgresql://postgres:1234@localhost:5434/yoonni -c "SELECT count(*) as connections FROM pg_stat_activity;" 2>/dev/null || echo "연결 실패"
echo ""

# AI 모델 상태
echo "🤖 AI 모델 상태:"
curl -s http://localhost:8003/api/ai/models/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "AI 서비스 확인 실패"
echo ""

# 디스크 사용량
echo "💾 디스크 사용량:"
df -h / | tail -1
echo ""

# 메모리 사용량
echo "🧠 메모리 사용량:"
free -h | grep Mem
echo ""

echo "✅ 모니터링 완료!"