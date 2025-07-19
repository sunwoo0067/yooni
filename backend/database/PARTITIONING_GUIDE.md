# 데이터베이스 파티셔닝 가이드

## 개요

이 시스템은 500만 레코드 이상의 대용량 데이터를 효율적으로 처리하기 위해 PostgreSQL 파티셔닝을 구현합니다.

## 파티셔닝 전략

### 1. 파티션된 테이블

#### market_orders (월별 범위 파티셔닝)
- **파티션 키**: order_date
- **파티션 단위**: 월별
- **보관 기간**: 24개월
- **용도**: 주문 데이터의 시계열 분석 및 빠른 조회

#### market_products (마켓별 리스트 파티셔닝)
- **파티션 키**: market_code
- **파티션 단위**: 마켓별 (coupang, naver, eleven 등)
- **용도**: 마켓별 상품 데이터 격리 및 병렬 처리

#### market_raw_data (월별 범위 파티셔닝)
- **파티션 키**: created_at
- **파티션 단위**: 월별
- **보관 기간**: 6개월
- **용도**: API 원본 데이터 보관 및 감사

#### job_executions (월별 범위 파티셔닝)
- **파티션 키**: started_at
- **파티션 단위**: 월별
- **보관 기간**: 3개월
- **용도**: 작업 실행 로그 관리

### 2. 파티션 명명 규칙

- 월별 파티션: `{table_name}_{YYYY}_{MM}`
  - 예: `market_orders_2024_01`
- 리스트 파티션: `{table_name}_{partition_value}`
  - 예: `market_products_coupang`

## 관리 명령어

### Python 스크립트 사용

```bash
cd /home/sunwoo/yooni/backend/database

# 파티션 상태 확인
python3 partition_manager.py status

# 파티션 생성 (향후 3개월)
python3 partition_manager.py create --table market_orders --months 3

# 오래된 파티션 삭제
python3 partition_manager.py drop --table market_orders --months 24

# 통계 업데이트
python3 partition_manager.py analyze

# 상세 보고서
python3 partition_manager.py report
```

### SQL 직접 실행

```sql
-- 파티션 목록 조회
SELECT * FROM v_partition_info;

-- 파티션 성능 보고서
SELECT * FROM partition_performance_report();

-- 수동 파티션 생성
SELECT create_monthly_partition_orders();
SELECT create_monthly_partition_raw_data();
SELECT create_monthly_partition_job_executions();

-- 오래된 파티션 삭제
SELECT drop_old_partitions('market_orders', 24);
```

## 웹 UI 관리

1. 프론트엔드 접속: http://localhost:3000/settings/database
2. 파티션 관리 탭에서 실시간 모니터링
3. 파티션 추가/삭제 버튼으로 관리

## 성능 고려사항

### 1. 쿼리 최적화

파티션 프루닝을 활용하려면 WHERE 절에 파티션 키를 포함해야 합니다:

```sql
-- 좋은 예 (파티션 프루닝 발생)
SELECT * FROM market_orders 
WHERE order_date >= '2024-01-01' 
AND order_date < '2024-02-01';

-- 나쁜 예 (모든 파티션 스캔)
SELECT * FROM market_orders 
WHERE buyer_email = 'user@example.com';
```

### 2. 인덱스 전략

각 파티션은 독립적인 인덱스를 가집니다:
- 파티션 키에 대한 인덱스는 불필요
- 자주 사용되는 조회 조건에 대한 인덱스 생성
- 파티션별로 인덱스 통계 관리

### 3. 유지보수

- **VACUUM**: 파티션별로 실행 가능
- **ANALYZE**: 정기적인 통계 업데이트 필요
- **백업**: 파티션 단위로 백업/복원 가능

## 모니터링 지표

### Dead Row 비율
- 20% 초과 시 VACUUM 필요
- 웹 UI에서 시각적으로 표시

### 파티션 크기
- 단일 파티션이 10GB 초과 시 주의
- 필요시 더 작은 단위로 재파티셔닝 고려

### 파티션 수
- 테이블당 100개 이하 권장
- 오래된 데이터 정기적 정리

## 문제 해결

### 파티션 제약 조건 위반
```sql
-- 파티션 범위 확인
SELECT 
  relname,
  pg_get_expr(relpartbound, oid) 
FROM pg_class 
WHERE relispartition = true;
```

### 파티션 통계 불일치
```bash
# 전체 파티션 통계 재계산
python3 partition_manager.py analyze
```

### 파티션 생성 실패
- 디스크 공간 확인
- 파티션 이름 중복 확인
- 날짜 범위 중복 확인

## 향후 확장

### 1. 자동 파티션 관리
- pg_partman 확장 고려
- 커스텀 트리거 구현

### 2. 파티션 압축
- 오래된 파티션 압축 저장
- 콜드 스토리지 이동

### 3. 병렬 처리
- 파티션별 병렬 쿼리
- 파티션별 병렬 유지보수

## 베스트 프랙티스

1. **정기적인 모니터링**: 매일 파티션 상태 확인
2. **사전 파티션 생성**: 최소 1개월 전 미리 생성
3. **점진적 마이그레이션**: 기존 테이블을 한 번에 변경하지 말고 단계적으로
4. **테스트 환경 검증**: 프로덕션 적용 전 충분한 테스트
5. **백업 계획**: 파티션 구조 변경 전 전체 백업