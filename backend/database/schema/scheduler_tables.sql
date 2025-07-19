-- 스케줄러 관련 테이블

-- 스케줄 작업 정의
CREATE TABLE IF NOT EXISTS schedule_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    interval VARCHAR(10),
    cron_expression VARCHAR(100),
    specific_times TIME[],
    market_codes TEXT[],
    account_ids INTEGER[],
    parameters JSONB DEFAULT '{}',
    max_retries INTEGER DEFAULT 3,
    timeout_minutes INTEGER DEFAULT 30,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT check_schedule_type CHECK (
        (interval IS NOT NULL AND cron_expression IS NULL AND specific_times IS NULL) OR
        (interval IS NULL AND cron_expression IS NOT NULL AND specific_times IS NULL) OR
        (interval IS NULL AND cron_expression IS NULL AND specific_times IS NOT NULL)
    )
);

-- 작업 실행 기록
CREATE TABLE IF NOT EXISTS job_executions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES schedule_jobs(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    log_file_path TEXT,
    parameters JSONB DEFAULT '{}',
    result_summary JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 스케줄 잠금 (중복 실행 방지)
CREATE TABLE IF NOT EXISTS schedule_locks (
    job_id INTEGER PRIMARY KEY REFERENCES schedule_jobs(id) ON DELETE CASCADE,
    locked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    locked_by VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- 인덱스
CREATE INDEX idx_schedule_jobs_status ON schedule_jobs(status) WHERE is_active = true;
CREATE INDEX idx_schedule_jobs_next_run ON schedule_jobs(next_run_at) WHERE status = 'active' AND is_active = true;
CREATE INDEX idx_schedule_jobs_job_type ON schedule_jobs(job_type) WHERE is_active = true;
CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_started_at ON job_executions(started_at);
CREATE INDEX idx_job_executions_status ON job_executions(status);

-- 트리거: 업데이트 시간 자동 갱신
CREATE OR REPLACE FUNCTION update_schedule_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_schedule_jobs_updated_at
    BEFORE UPDATE ON schedule_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_schedule_jobs_updated_at();

-- 뷰: 활성 작업 요약
CREATE OR REPLACE VIEW v_active_schedule_jobs AS
SELECT 
    j.id,
    j.name,
    j.job_type,
    j.status,
    j.interval,
    j.cron_expression,
    j.specific_times,
    j.market_codes,
    j.next_run_at,
    j.last_run_at,
    j.last_success_at,
    j.run_count,
    j.success_count,
    j.error_count,
    CASE 
        WHEN j.run_count > 0 THEN (j.success_count::FLOAT / j.run_count * 100)::NUMERIC(5,2)
        ELSE 0
    END as success_rate,
    e.avg_duration_seconds,
    e.total_records_processed
FROM schedule_jobs j
LEFT JOIN (
    SELECT 
        job_id,
        AVG(duration_seconds) as avg_duration_seconds,
        SUM(records_processed) as total_records_processed
    FROM job_executions
    WHERE status = 'completed'
    GROUP BY job_id
) e ON j.id = e.job_id
WHERE j.is_active = true
ORDER BY j.priority DESC, j.next_run_at ASC;

-- 뷰: 최근 실행 기록
CREATE OR REPLACE VIEW v_recent_job_executions AS
SELECT 
    e.id,
    e.job_id,
    j.name as job_name,
    j.job_type,
    e.status,
    e.started_at,
    e.completed_at,
    e.duration_seconds,
    e.records_processed,
    e.error_message,
    e.result_summary
FROM job_executions e
JOIN schedule_jobs j ON e.job_id = j.id
ORDER BY e.started_at DESC
LIMIT 100;

-- 샘플 스케줄 작업
INSERT INTO schedule_jobs (name, job_type, status, interval, market_codes, parameters) VALUES
('쿠팡 상품 수집 (5분)', 'product_collection', 'active', '5m', ARRAY['coupang'], '{"batch_size": 100, "include_details": true}'::jsonb),
('네이버 상품 수집 (15분)', 'product_collection', 'active', '15m', ARRAY['naver'], '{"batch_size": 50}'::jsonb),
('11번가 상품 수집 (30분)', 'product_collection', 'active', '30m', ARRAY['eleven'], '{"batch_size": 50}'::jsonb),
('전체 주문 수집 (10분)', 'order_collection', 'active', '10m', ARRAY['coupang', 'naver', 'eleven'], '{"days_back": 1}'::jsonb),
('재고 동기화 (매시간)', 'inventory_sync', 'active', '1h', ARRAY['coupang', 'naver', 'eleven'], '{}'::jsonb),
('가격 업데이트 (6시간)', 'price_update', 'active', '6h', ARRAY['coupang', 'naver', 'eleven'], '{"update_competitors": true}'::jsonb)
ON CONFLICT DO NOTHING;

-- 특정 시간 실행 작업
INSERT INTO schedule_jobs (name, job_type, status, specific_times, market_codes, parameters) VALUES
('데이터베이스 백업 (매일 새벽 3시)', 'database_backup', 'active', ARRAY['03:00:00'::time], NULL, '{"backup_type": "full", "retention_days": 30}'::jsonb),
('일일 보고서 생성 (매일 오전 9시)', 'report_generation', 'active', ARRAY['09:00:00'::time], NULL, '{"report_types": ["sales", "inventory", "orders"]}'::jsonb)
ON CONFLICT DO NOTHING;