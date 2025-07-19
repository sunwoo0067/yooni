# 상품 수집 스케줄러 시스템

## 개요
APScheduler를 사용한 자동 상품 수집 및 주기적 업데이트 시스템

## 주요 기능

### 1. 자동 스케줄링
- **개별 공급사 스케줄**: Cron 표현식으로 정기 수집
  - 오너클랜: 매일 새벽 3시 (0 3 * * *)
  - 젠트레이드: 매일 새벽 4시 (0 4 * * *)
- **전체 수집**: 매주 일요일 새벽 2시
- **상태 모니터링**: 30분마다 시스템 상태 확인

### 2. 중복 실행 방지
- `supplier_collection_status` 테이블로 실행 상태 관리
- 6시간 이상 running 상태면 강제 재시작 허용

### 3. 알림 시스템
- 수집 실패 시 알림 (10개 이상 실패 또는 전체 실패)
- 장시간 실행 작업 감지
- 연속 실패 모니터링

## 사용 방법

### 스케줄러 제어
```bash
# 스케줄러 시작
./scheduler_control.sh start

# 스케줄러 중지
./scheduler_control.sh stop

# 스케줄러 재시작
./scheduler_control.sh restart

# 상태 확인
./scheduler_control.sh status

# 로그 보기
./scheduler_control.sh logs

# 수동 수집
./scheduler_control.sh collect                # 전체 수집
./scheduler_control.sh collect 오너클랜       # 특정 공급사
```

### Python으로 직접 실행
```bash
# 가상환경 활성화
source ../venv/bin/activate

# 데몬 모드 실행
python scheduler.py --daemon

# 특정 공급사 즉시 수집
python scheduler.py --collect 오너클랜

# 전체 공급사 즉시 수집
python scheduler.py --collect-all
```

## 데이터베이스 스키마

### supplier_collection_status
- 현재 수집 상태 추적 (running/completed/failed)
- 중복 실행 방지

### scheduler_execution_history
- 모든 스케줄 실행 이력 저장
- 성능 분석 및 문제 추적용

### supplier_collection_stats (뷰)
- 공급사별 수집 통계
- 평균 수집 시간, 성공률 등

## 설정 변경

### 스케줄 변경
```sql
-- supplier_configs 테이블의 settings JSONB 컬럼 수정
UPDATE supplier_configs 
SET settings = settings || jsonb_build_object(
    'collection_schedule', '0 5 * * *',  -- 새벽 5시로 변경
    'collection_interval_hours', 12      -- 12시간마다
)
WHERE supplier_id = (SELECT id FROM suppliers WHERE name = '오너클랜');
```

### 환경 변수
- 로그 파일: `supplier_scheduler.log`
- PID 파일: `scheduler.pid`
- 데이터베이스: PostgreSQL (localhost:5434)

## 모니터링

### 수집 통계 조회
```sql
-- 공급사별 통계
SELECT * FROM supplier_collection_stats;

-- 최근 수집 로그
SELECT * FROM supplier_collection_logs 
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;

-- 현재 실행 상태
SELECT * FROM supplier_collection_status;
```

### 로그 확인
```bash
# 실시간 로그
tail -f supplier_scheduler.log

# 특정 날짜 로그
grep "2025-07-19" supplier_scheduler.log

# 오류만 확인
grep "ERROR" supplier_scheduler.log
```

## 문제 해결

### 스케줄러가 시작되지 않을 때
1. PID 파일 확인: `rm -f scheduler.pid`
2. 포트 충돌 확인: PostgreSQL 5434 포트
3. 가상환경 확인: `which python`

### 수집이 실패할 때
1. API 인증 정보 확인: `supplier_configs` 테이블
2. 네트워크 연결 확인
3. 로그 파일에서 상세 오류 확인

### 중복 실행 문제
1. `supplier_collection_status` 테이블 확인
2. 6시간 이상 running 상태 확인
3. 필요시 수동으로 상태 초기화

## 성능 최적화

### 배치 크기 조정
```sql
UPDATE supplier_configs 
SET settings = settings || jsonb_build_object('batch_size', 200)
WHERE supplier_id = 1;
```

### 동시 실행 제한
- 공급사별 순차 실행 (1초 간격)
- API 율 제한 준수 (기본 5 req/sec)

## 향후 개선 사항
1. Slack/Email 알림 연동
2. 웹 기반 모니터링 대시보드
3. 동적 스케줄 조정 (부하 기반)
4. 분산 처리 지원 (Celery 연동)