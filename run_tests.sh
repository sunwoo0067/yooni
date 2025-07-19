#!/bin/bash
# 테스트 실행 스크립트

echo "===================="
echo "테스트 프레임워크 실행"
echo "===================="

# Backend 테스트
echo -e "\n[Backend 테스트]"
cd backend
echo "1. 단위 테스트 실행..."
python3 -m pytest tests/test_config_manager.py tests/test_scheduler.py -v -m "not db and not slow"

echo -e "\n2. 데이터베이스 테스트 실행 (선택적)..."
echo "   python3 -m pytest -m db"

echo -e "\n3. 통합 테스트 실행 (선택적)..."
echo "   python3 -m pytest tests/integration/"

cd ..

# Frontend 테스트
echo -e "\n[Frontend 테스트]"
cd frontend
echo "1. Jest 테스트 실행..."
npm test -- --watchAll=false --passWithNoTests

echo -e "\n===================="
echo "테스트 완료!"
echo "====================