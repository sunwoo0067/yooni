-- 마켓플레이스 통합 관리를 위한 데이터베이스 테이블 생성 (수정된 버전)

-- 마켓플레이스 헬스 상태 테이블
CREATE TABLE IF NOT EXISTS marketplace_health_status (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) NOT NULL,
    is_healthy BOOLEAN NOT NULL,
    response_time FLOAT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- 마켓플레이스 메트릭 테이블
CREATE TABLE IF NOT EXISTS marketplace_metrics (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    rate_limited_requests INTEGER DEFAULT 0,
    avg_response_time FLOAT DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 마켓플레이스 API 요청 로그 테이블
CREATE TABLE IF NOT EXISTS marketplace_request_logs (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time FLOAT,
    request_size INTEGER,
    response_size INTEGER,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- 마켓플레이스 계정 상태 테이블 (멀티 계정 지원)
CREATE TABLE IF NOT EXISTS marketplace_accounts (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    vendor_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    daily_quota INTEGER DEFAULT 10000,
    used_quota INTEGER DEFAULT 0,
    quota_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(marketplace, account_name)
);

-- 마켓플레이스 율 제한 설정 테이블
CREATE TABLE IF NOT EXISTS marketplace_rate_limits (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) UNIQUE NOT NULL,
    max_requests_per_second FLOAT DEFAULT 10.0,
    max_requests_per_minute INTEGER DEFAULT 500,
    max_requests_per_hour INTEGER DEFAULT 10000,
    burst_allowance INTEGER DEFAULT 15,
    current_rate FLOAT DEFAULT 10.0,
    last_optimized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    optimization_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 마켓플레이스 회로 차단기 상태 테이블
CREATE TABLE IF NOT EXISTS marketplace_circuit_breaker_status (
    id SERIAL PRIMARY KEY,
    marketplace VARCHAR(50) UNIQUE NOT NULL,
    state VARCHAR(20) DEFAULT 'CLOSED', -- CLOSED, OPEN, HALF_OPEN
    failure_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP,
    last_success_at TIMESTAMP,
    total_failures INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_health_status_marketplace_time ON marketplace_health_status(marketplace, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_marketplace_time ON marketplace_metrics(marketplace, collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_logs_marketplace_time ON marketplace_request_logs(marketplace, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_logs_endpoint_time ON marketplace_request_logs(endpoint, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_accounts_marketplace_active ON marketplace_accounts(marketplace, is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_marketplace_default ON marketplace_accounts(marketplace, is_default);

-- 초기 데이터 삽입
INSERT INTO marketplace_rate_limits (marketplace, max_requests_per_second, max_requests_per_minute, max_requests_per_hour, burst_allowance) 
VALUES 
    ('coupang', 10.0, 500, 10000, 15),
    ('naver', 20.0, 1000, 20000, 30),
    ('eleven', 15.0, 800, 15000, 20)
ON CONFLICT (marketplace) DO UPDATE SET
    max_requests_per_second = EXCLUDED.max_requests_per_second,
    max_requests_per_minute = EXCLUDED.max_requests_per_minute,
    max_requests_per_hour = EXCLUDED.max_requests_per_hour,
    burst_allowance = EXCLUDED.burst_allowance,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO marketplace_circuit_breaker_status (marketplace) 
VALUES ('coupang'), ('naver'), ('eleven')
ON CONFLICT (marketplace) DO NOTHING;

-- 테이블 설명 추가
COMMENT ON TABLE marketplace_health_status IS '마켓플레이스 헬스 체크 상태 기록';
COMMENT ON TABLE marketplace_metrics IS '마켓플레이스 API 사용 메트릭';
COMMENT ON TABLE marketplace_request_logs IS 'API 요청 상세 로그';
COMMENT ON TABLE marketplace_accounts IS '멀티 계정 관리';
COMMENT ON TABLE marketplace_rate_limits IS '동적 율 제한 설정';
COMMENT ON TABLE marketplace_circuit_breaker_status IS '회로 차단기 상태 관리';