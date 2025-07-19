# 실시간 모니터링 시스템 가이드

## 개요
실시간 모니터링 시스템은 WebSocket을 통해 비즈니스 메트릭과 시스템 상태를 실시간으로 추적합니다.

## 아키텍처

```
┌─────────────┐     WebSocket      ┌──────────────┐     ┌─────────────┐
│   Frontend  │ ◄─────────────────► │   WebSocket  │ ◄──► │   Redis     │
│  Dashboard  │                     │    Server    │      │   Cache     │
└─────────────┘                     └──────────────┘      └─────────────┘
                                            │                      ▲
                                            ▼                      │
                                    ┌──────────────┐      ┌────────┴────┐
                                    │  PostgreSQL  │      │ API Health  │
                                    │   Database   │      │   Checker   │
                                    └──────────────┘      └─────────────┘
```

## 구성 요소

### 1. WebSocket 서버 (`backend/websocket_server.py`)
- 실시간 메트릭 수집 및 브로드캐스트
- 5초 간격으로 자동 업데이트
- 다중 클라이언트 지원

### 2. API 헬스 체커 (`backend/services/api_health_checker.py`)
- 외부 API (쿠팡, 네이버, 11번가) 상태 모니터링
- 60초 간격으로 헬스 체크
- Redis에 상태 캐싱

### 3. 실시간 대시보드 (`frontend/app/monitoring/dashboard`)
- Chart.js를 이용한 실시간 차트
- WebSocket 자동 재연결
- 반응형 디자인

## 설치 및 실행

### 사전 요구사항
- Redis 서버
- PostgreSQL (포트 5434)
- Node.js 18+
- Python 3.8+

### Redis 설치
```bash
./scripts/install_redis.sh
```

### 의존성 설치
```bash
# Python 의존성
pip install websockets aiohttp redis psycopg2-binary

# Frontend 의존성
cd frontend
npm install
```

### 서비스 시작
```bash
# 모든 모니터링 서비스 시작
./scripts/start_monitoring.sh

# 개별 서비스 시작
python3 backend/websocket_server.py
python3 backend/services/api_health_checker.py
cd frontend && npm run dev
```

### 서비스 중지
```bash
./scripts/stop_monitoring.sh
```

## 모니터링 메트릭

### 실시간 메트릭
1. **매출 지표**
   - 오늘 주문 수
   - 오늘 매출액
   - 고유 고객 수
   - 시간별 매출 추이

2. **주문 상태**
   - 대기중/처리중/완료 주문 수
   - 마켓별 주문 분포

3. **재고 현황**
   - 총 상품 수
   - 재고 부족 상품
   - 품절 상품
   - 재고 가치

4. **시스템 성능**
   - API 응답 시간
   - 에러율
   - 경고 수
   - 총 요청 수

5. **외부 API 상태**
   - 각 마켓 API 상태
   - 응답 시간
   - 가용성

## 커스터마이징

### 메트릭 추가
1. `MetricsCollector` 클래스에 새 메서드 추가
2. `get_realtime_metrics()`에서 호출
3. Frontend에서 새 메트릭 표시

### 업데이트 간격 변경
```python
# backend/websocket_server.py
self.update_interval = 10  # 10초로 변경
```

### 새 차트 추가
```typescript
// frontend에서 Chart.js 컴포넌트 추가
<Line data={chartData} options={chartOptions} />
```

## 문제 해결

### WebSocket 연결 실패
- Redis 서버 실행 확인: `redis-cli ping`
- 방화벽 설정 확인 (포트 8765)
- 로그 확인: `tail -f logs/websocket_server.log`

### 데이터 없음
- PostgreSQL 연결 확인
- 데이터베이스에 데이터 존재 확인
- 로그에서 SQL 에러 확인

### 성능 이슈
- Redis 메모리 사용량 확인
- WebSocket 클라이언트 수 제한
- 메트릭 수집 쿼리 최적화

## 보안 고려사항
- WebSocket 인증 구현 필요
- HTTPS/WSS 사용 권장
- Redis 암호 설정
- CORS 설정 확인