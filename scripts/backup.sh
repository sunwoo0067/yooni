#!/bin/bash

# 데이터베이스 백업 스크립트
set -e

# 백업 디렉토리 설정
BACKUP_DIR="/backup/yoonni"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/yoonni_backup_$TIMESTAMP.sql"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

echo "🔧 데이터베이스 백업 시작..."

# PostgreSQL 백업
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres yoonni > $BACKUP_FILE

# 백업 압축
gzip $BACKUP_FILE

echo "✅ 백업 완료: ${BACKUP_FILE}.gz"

# 7일 이상 된 백업 파일 삭제
find $BACKUP_DIR -name "yoonni_backup_*.sql.gz" -mtime +7 -delete

echo "🧹 오래된 백업 파일 정리 완료"

# S3 업로드 (AWS CLI 설치 필요)
if command -v aws &> /dev/null; then
    echo "☁️ S3 업로드 시작..."
    aws s3 cp ${BACKUP_FILE}.gz s3://your-backup-bucket/yoonni/database/
    echo "✅ S3 업로드 완료"
fi