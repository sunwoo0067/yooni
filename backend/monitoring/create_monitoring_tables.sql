-- 성능 모니터링 관련 테이블

-- 성능 메트릭 저장 테이블
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metrics_data JSONB NOT NULL,
    performance_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 시간별 집계 데이터
CREATE TABLE IF NOT EXISTS performance_hourly_stats (
    id SERIAL PRIMARY KEY,
    hour_timestamp TIMESTAMP NOT NULL,
    avg_cpu_percent DECIMAL(5,2),
    avg_memory_percent DECIMAL(5,2),
    avg_query_time_ms DECIMAL(10,2),
    avg_collection_rate DECIMAL(10,2),
    total_collections INTEGER,
    failed_collections INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hour_timestamp)
);

-- 성능 경고 로그
CREATE TABLE IF NOT EXISTS performance_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- cpu_high, memory_high, slow_query, etc
    severity VARCHAR(20) NOT NULL, -- info, warning, critical
    message TEXT,
    metrics JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 최적화 실행 이력
CREATE TABLE IF NOT EXISTS optimization_history (
    id SERIAL PRIMARY KEY,
    optimization_type VARCHAR(50) NOT NULL, -- index, vacuum, partition, etc
    target_table VARCHAR(100),
    before_metrics JSONB,
    after_metrics JSONB,
    improvement_percent DECIMAL(5,2),
    executed_by VARCHAR(100),
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_performance_metrics_score ON performance_metrics(performance_score);
CREATE INDEX idx_performance_hourly_hour ON performance_hourly_stats(hour_timestamp DESC);
CREATE INDEX idx_performance_alerts_created ON performance_alerts(created_at DESC) WHERE acknowledged = FALSE;
CREATE INDEX idx_optimization_history_type ON optimization_history(optimization_type, created_at DESC);

-- 성능 대시보드용 뷰
CREATE OR REPLACE VIEW performance_dashboard AS
SELECT 
    -- 최근 메트릭
    (SELECT performance_score FROM performance_metrics ORDER BY timestamp DESC LIMIT 1) as current_score,
    (SELECT metrics_data->>'cpu_percent' FROM performance_metrics ORDER BY timestamp DESC LIMIT 1) as current_cpu,
    (SELECT metrics_data->>'memory_percent' FROM performance_metrics ORDER BY timestamp DESC LIMIT 1) as current_memory,
    (SELECT metrics_data->>'collection_rate' FROM performance_metrics ORDER BY timestamp DESC LIMIT 1) as current_collection_rate,
    
    -- 1시간 평균
    (SELECT AVG(performance_score) FROM performance_metrics WHERE timestamp > NOW() - INTERVAL '1 hour') as avg_score_1h,
    (SELECT AVG(CAST(metrics_data->>'cpu_percent' AS DECIMAL)) FROM performance_metrics WHERE timestamp > NOW() - INTERVAL '1 hour') as avg_cpu_1h,
    
    -- 경고 수
    (SELECT COUNT(*) FROM performance_alerts WHERE created_at > NOW() - INTERVAL '24 hours' AND acknowledged = FALSE) as active_alerts,
    (SELECT COUNT(*) FROM performance_alerts WHERE created_at > NOW() - INTERVAL '24 hours' AND severity = 'critical') as critical_alerts,
    
    -- 수집 통계
    (SELECT COUNT(*) FROM supplier_collection_logs WHERE started_at > NOW() - INTERVAL '24 hours') as collections_24h,
    (SELECT COUNT(*) FROM supplier_collection_logs WHERE started_at > NOW() - INTERVAL '24 hours' AND status = 'failed') as failed_24h;

-- 병목 지점 분석 뷰
CREATE OR REPLACE VIEW performance_bottlenecks AS
WITH recent_metrics AS (
    SELECT 
        metrics_data,
        performance_score,
        timestamp
    FROM performance_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour'
)
SELECT 
    CASE 
        WHEN AVG(CAST(metrics_data->>'cpu_percent' AS DECIMAL)) > 80 THEN 'CPU'
        WHEN AVG(CAST(metrics_data->>'memory_percent' AS DECIMAL)) > 85 THEN 'Memory'
        WHEN AVG(CAST(metrics_data->>'avg_query_time_ms' AS DECIMAL)) > 100 THEN 'Database'
        WHEN AVG(CAST(metrics_data->>'collection_rate' AS DECIMAL)) < 50 THEN 'Collection'
        ELSE 'None'
    END as bottleneck_type,
    AVG(CAST(metrics_data->>'cpu_percent' AS DECIMAL)) as avg_cpu,
    AVG(CAST(metrics_data->>'memory_percent' AS DECIMAL)) as avg_memory,
    AVG(CAST(metrics_data->>'avg_query_time_ms' AS DECIMAL)) as avg_query_time,
    AVG(CAST(metrics_data->>'collection_rate' AS DECIMAL)) as avg_collection_rate,
    AVG(performance_score) as avg_performance_score
FROM recent_metrics;

-- 시간별 성능 추이 함수
CREATE OR REPLACE FUNCTION update_performance_hourly_stats()
RETURNS void AS $$
BEGIN
    INSERT INTO performance_hourly_stats (
        hour_timestamp,
        avg_cpu_percent,
        avg_memory_percent,
        avg_query_time_ms,
        avg_collection_rate,
        total_collections,
        failed_collections
    )
    SELECT 
        date_trunc('hour', NOW() - INTERVAL '1 hour') as hour_timestamp,
        AVG(CAST(metrics_data->>'cpu_percent' AS DECIMAL)) as avg_cpu_percent,
        AVG(CAST(metrics_data->>'memory_percent' AS DECIMAL)) as avg_memory_percent,
        AVG(CAST(metrics_data->>'avg_query_time_ms' AS DECIMAL)) as avg_query_time_ms,
        AVG(CAST(metrics_data->>'collection_rate' AS DECIMAL)) as avg_collection_rate,
        (SELECT COUNT(*) FROM supplier_collection_logs 
         WHERE started_at >= date_trunc('hour', NOW() - INTERVAL '1 hour')
         AND started_at < date_trunc('hour', NOW())) as total_collections,
        (SELECT COUNT(*) FROM supplier_collection_logs 
         WHERE started_at >= date_trunc('hour', NOW() - INTERVAL '1 hour')
         AND started_at < date_trunc('hour', NOW())
         AND status = 'failed') as failed_collections
    FROM performance_metrics
    WHERE timestamp >= date_trunc('hour', NOW() - INTERVAL '1 hour')
    AND timestamp < date_trunc('hour', NOW())
    ON CONFLICT (hour_timestamp) DO UPDATE SET
        avg_cpu_percent = EXCLUDED.avg_cpu_percent,
        avg_memory_percent = EXCLUDED.avg_memory_percent,
        avg_query_time_ms = EXCLUDED.avg_query_time_ms,
        avg_collection_rate = EXCLUDED.avg_collection_rate,
        total_collections = EXCLUDED.total_collections,
        failed_collections = EXCLUDED.failed_collections;
END;
$$ LANGUAGE plpgsql;

-- 자동 정리 함수 (30일 이상 된 데이터 삭제)
CREATE OR REPLACE FUNCTION cleanup_old_performance_data()
RETURNS void AS $$
BEGIN
    DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM performance_alerts WHERE created_at < NOW() - INTERVAL '90 days' AND acknowledged = TRUE;
    DELETE FROM optimization_history WHERE created_at < NOW() - INTERVAL '180 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE performance_metrics IS '실시간 성능 메트릭 저장';
COMMENT ON TABLE performance_hourly_stats IS '시간별 성능 통계';
COMMENT ON TABLE performance_alerts IS '성능 경고 로그';
COMMENT ON TABLE optimization_history IS '최적화 실행 이력';