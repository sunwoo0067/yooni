# 자동화 스케줄러 시스템

ERP 시스템의 자동화된 작업 실행을 관리하는 스케줄러 시스템입니다.

## 주요 기능

- **정기 작업 실행**: 간격 기반(5분~1개월) 또는 특정 시간 스케줄
- **다중 작업 유형**: 상품 수집, 주문 수집, 재고 동기화, DB 백업 등
- **실행 모니터링**: 웹 UI를 통한 실시간 상태 확인
- **오류 처리**: 자동 재시도 및 오류 알림
- **병렬 실행**: 여러 작업 동시 처리
- **실행 기록**: 모든 실행 내역 저장 및 조회

## 지원 작업 유형

1. **상품 수집** (`product_collection`)
   - 쿠팡, 네이버, 11번가 상품 정보 수집
   - 배치 크기 및 상세 정보 포함 옵션

2. **주문 수집** (`order_collection`)
   - 마켓별 주문 정보 수집
   - 지정 기간 내 주문 조회

3. **재고 동기화** (`inventory_sync`)
   - 마켓 간 재고 수량 동기화
   - 품절/재고부족 알림

4. **가격 업데이트** (`price_update`)
   - 상품 가격 정보 갱신
   - 경쟁사 가격 비교 (옵션)

5. **데이터베이스 백업** (`database_backup`)
   - 전체/부분 백업
   - 자동 보관 기간 관리

6. **보고서 생성** (`report_generation`)
   - 일일/주간/월간 보고서
   - 매출, 재고, 주문 분석

## 시작 방법

### 1. 스케줄러 서비스 시작

```bash
cd /home/sunwoo/yooni/backend
python3 start_scheduler.py
```

### 2. 백그라운드 실행 (systemd)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/erp-scheduler.service

# 내용:
[Unit]
Description=ERP Scheduler Service
After=network.target postgresql.service

[Service]
Type=simple
User=sunwoo
WorkingDirectory=/home/sunwoo/yooni/backend
ExecStart=/usr/bin/python3 /home/sunwoo/yooni/backend/start_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 서비스 활성화 및 시작
sudo systemctl enable erp-scheduler
sudo systemctl start erp-scheduler
```

### 3. PM2로 실행 (권장)

```bash
# PM2 설치 (없는 경우)
npm install -g pm2

# 스케줄러 시작
pm2 start /home/sunwoo/yooni/backend/start_scheduler.py --name erp-scheduler --interpreter python3

# 자동 시작 설정
pm2 save
pm2 startup
```

## 웹 UI 접근

1. 프론트엔드 서버 실행
2. http://localhost:3000/scheduler 접속
3. 작업 관리 및 모니터링

## 설정 관리

### 작업 추가 (SQL)

```sql
INSERT INTO schedule_jobs (name, job_type, status, interval, market_codes, parameters) 
VALUES (
  '새 작업 이름',
  'product_collection',
  'active',
  '30m',  -- 30분마다
  ARRAY['coupang', 'naver'],
  '{"batch_size": 100}'::jsonb
);
```

### 작업 비활성화

```sql
UPDATE schedule_jobs 
SET status = 'paused' 
WHERE id = 1;
```

### 특정 시간 실행 설정

```sql
UPDATE schedule_jobs 
SET 
  interval = NULL,
  specific_times = ARRAY['09:00:00'::time, '18:00:00'::time]
WHERE id = 1;
```

## 로그 확인

```bash
# 스케줄러 메인 로그
tail -f /home/sunwoo/yooni/backend/logs/scheduler/scheduler_*.log

# 작업별 로그
tail -f /home/sunwoo/yooni/backend/logs/product_collection_*.log
tail -f /home/sunwoo/yooni/backend/logs/order_collection_*.log
```

## 문제 해결

### 작업이 실행되지 않을 때

1. 스케줄러 서비스 상태 확인
   ```bash
   pm2 status erp-scheduler
   # 또는
   sudo systemctl status erp-scheduler
   ```

2. 작업 상태 확인
   ```sql
   SELECT * FROM schedule_jobs WHERE id = ?;
   SELECT * FROM schedule_locks WHERE job_id = ?;
   ```

3. 잠금 해제 (필요시)
   ```sql
   DELETE FROM schedule_locks WHERE job_id = ?;
   ```

### 오류 발생 시

1. 최근 실행 기록 확인
   ```sql
   SELECT * FROM job_executions 
   WHERE job_id = ? 
   ORDER BY started_at DESC 
   LIMIT 10;
   ```

2. 오류 메시지 확인
   ```sql
   SELECT last_error FROM schedule_jobs WHERE id = ?;
   ```

## 성능 튜닝

### 동시 실행 제한

스케줄러는 기본적으로 모든 작업을 병렬로 실행합니다. 
시스템 리소스에 따라 동시 실행 수를 제한할 수 있습니다.

### 타임아웃 설정

각 작업별 타임아웃 시간 조정:
```sql
UPDATE schedule_jobs 
SET timeout_minutes = 60 
WHERE job_type = 'product_collection';
```

### 재시도 설정

실패 시 재시도 횟수 조정:
```sql
UPDATE schedule_jobs 
SET max_retries = 5 
WHERE id = ?;
```

## 모니터링

### 대시보드 지표

- 총 작업 수 / 활성 작업 수
- 평균 성공률
- 최근 실행 기록
- 오류 발생 작업

### 알림 설정

중요 작업 실패 시 알림을 받으려면 시스템 설정에서 
이메일 또는 Slack 웹훅을 구성하세요.

## 확장 가능성

### 커스텀 작업 추가

1. `scheduler_manager.py`에 새 핸들러 등록
2. JobType enum에 새 유형 추가
3. 핸들러 함수 구현

### 외부 시스템 연동

- REST API 호출
- 외부 데이터베이스 동기화
- FTP/SFTP 파일 전송
- 이메일 발송