-- 스케줄러 관련 테이블 생성

-- 수집 상태 테이블 (중복 실행 방지)
CREATE TABLE IF NOT EXISTS supplier_collection_status (
    supplier_name VARCHAR(100) PRIMARY KEY,
    status VARCHAR(50) NOT NULL, -- running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스케줄 실행 히스토리
CREATE TABLE IF NOT EXISTS scheduler_execution_history (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(200) NOT NULL,
    job_name VARCHAR(200),
    supplier_name VARCHAR(100),
    status VARCHAR(50) NOT NULL, -- started, completed, failed
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스케줄 설정 업데이트 (supplier_configs 테이블에 컬럼 추가)
DO $$ 
BEGIN
    -- settings JSONB 컬럼이 없으면 추가
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'supplier_configs' 
        AND column_name = 'settings'
    ) THEN
        ALTER TABLE supplier_configs ADD COLUMN settings JSONB DEFAULT '{}';
    END IF;
END $$;

-- 기본 스케줄 설정 추가
UPDATE supplier_configs 
SET settings = jsonb_build_object(
    'collection_schedule', '0 3 * * *',  -- 매일 새벽 3시
    'collection_interval_hours', 24,
    'collection_enabled', 'true',
    'rate_limit_per_second', 5.0,
    'batch_size', 100,
    'max_retries', 3
)
WHERE settings IS NULL OR settings = '{}';

-- 오너클랜 특별 설정
UPDATE supplier_configs 
SET settings = settings || jsonb_build_object(
    'collection_schedule', '0 3 * * *',  -- 매일 새벽 3시
    'batch_size', 100
)
WHERE supplier_id = (SELECT id FROM suppliers WHERE name = '오너클랜');

-- 젠트레이드 특별 설정
UPDATE supplier_configs 
SET settings = settings || jsonb_build_object(
    'collection_schedule', '0 4 * * *',  -- 매일 새벽 4시
    'batch_size', 50
)
WHERE supplier_id = (SELECT id FROM suppliers WHERE name = '젠트레이드');

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_scheduler_history_job_id ON scheduler_execution_history(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduler_history_started_at ON scheduler_execution_history(started_at);
CREATE INDEX IF NOT EXISTS idx_collection_status_status ON supplier_collection_status(status);

-- 수집 통계 뷰
CREATE OR REPLACE VIEW supplier_collection_stats AS
SELECT 
    s.name as supplier_name,
    COUNT(DISTINCT sp.id) as total_products,
    COUNT(DISTINCT CASE WHEN sp.status = 'active' THEN sp.id END) as active_products,
    MAX(sp.collected_at) as last_collection,
    AVG(scl.duration_seconds) as avg_duration_seconds,
    COUNT(CASE WHEN scl.status = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN scl.status = 'failed' THEN 1 END) as fail_count,
    COUNT(scl.id) as total_collections
FROM suppliers s
LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
LEFT JOIN supplier_collection_logs scl ON s.id = scl.supplier_id
    AND scl.started_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY s.id, s.name;

COMMENT ON TABLE supplier_collection_status IS '공급사별 현재 수집 상태 (중복 실행 방지)';
COMMENT ON TABLE scheduler_execution_history IS '스케줄러 실행 히스토리';
COMMENT ON VIEW supplier_collection_stats IS '공급사별 수집 통계';