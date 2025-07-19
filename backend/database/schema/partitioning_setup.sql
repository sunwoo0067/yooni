-- 데이터베이스 파티셔닝 설정
-- 500만 레코드 이상 처리를 위한 테이블 파티셔닝 구조

-- ============================================
-- 1. market_orders 테이블 파티셔닝 (월별 범위 파티셔닝)
-- ============================================

-- 기존 테이블 백업
-- CREATE TABLE market_orders_backup AS SELECT * FROM market_orders;

-- 파티션 테이블 생성
CREATE TABLE IF NOT EXISTS market_orders_partitioned (
    LIKE market_orders INCLUDING ALL
) PARTITION BY RANGE (order_date);

-- 파티션 자동 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partition_orders()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    -- 향후 3개월까지 미리 생성
    FOR i IN -12..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'market_orders_' || to_char(start_date, 'YYYY_MM');
        
        -- 파티션이 없으면 생성
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF market_orders_partitioned 
                FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            
            -- 파티션별 인덱스 생성
            EXECUTE format('CREATE INDEX idx_%I_market_account ON %I(market_account_id)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_status ON %I(order_status)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_buyer ON %I(buyer_email)', partition_name, partition_name);
            
            RAISE NOTICE 'Created partition: %', partition_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 파티션 생성 실행
SELECT create_monthly_partition_orders();

-- ============================================
-- 2. market_products 테이블 파티셔닝 (마켓별 리스트 파티셔닝)
-- ============================================

-- 파티션 테이블 생성
CREATE TABLE IF NOT EXISTS market_products_partitioned (
    LIKE market_products INCLUDING ALL
) PARTITION BY LIST (market_code);

-- 마켓별 파티션 생성
DO $$
DECLARE
    market_codes text[] := ARRAY['coupang', 'naver', 'eleven', 'gmarket', 'auction'];
    market text;
BEGIN
    FOREACH market IN ARRAY market_codes
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'market_products_' || market
        ) THEN
            EXECUTE format(
                'CREATE TABLE market_products_%I PARTITION OF market_products_partitioned 
                FOR VALUES IN (%L)',
                market, market
            );
            
            -- 파티션별 인덱스
            EXECUTE format('CREATE INDEX idx_market_products_%I_sku ON market_products_%I(sku)', market, market);
            EXECUTE format('CREATE INDEX idx_market_products_%I_status ON market_products_%I(status)', market, market);
            EXECUTE format('CREATE INDEX idx_market_products_%I_updated ON market_products_%I(updated_at)', market, market);
        END IF;
    END LOOP;
END $$;

-- 기타 마켓을 위한 기본 파티션
CREATE TABLE IF NOT EXISTS market_products_default 
PARTITION OF market_products_partitioned DEFAULT;

-- ============================================
-- 3. market_raw_data 테이블 파티셔닝 (월별 범위 파티셔닝)
-- ============================================

-- 파티션 테이블 생성
CREATE TABLE IF NOT EXISTS market_raw_data_partitioned (
    id BIGSERIAL NOT NULL,
    market_code VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT false,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 월별 파티션 자동 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partition_raw_data()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    FOR i IN -6..1 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'market_raw_data_' || to_char(start_date, 'YYYY_MM');
        
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF market_raw_data_partitioned 
                FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            
            -- 인덱스
            EXECUTE format('CREATE INDEX idx_%I_market ON %I(market_code)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_type ON %I(data_type)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_processed ON %I(processed) WHERE NOT processed', partition_name, partition_name);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 파티션 생성 실행
SELECT create_monthly_partition_raw_data();

-- ============================================
-- 4. job_executions 테이블 파티셔닝 (월별 범위 파티셔닝)
-- ============================================

-- 파티션 테이블 생성
CREATE TABLE IF NOT EXISTS job_executions_partitioned (
    LIKE job_executions INCLUDING ALL,
    PRIMARY KEY (id, started_at)
) PARTITION BY RANGE (started_at);

-- 파티션 자동 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partition_job_executions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    FOR i IN -3..1 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'job_executions_' || to_char(start_date, 'YYYY_MM');
        
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF job_executions_partitioned 
                FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            
            -- 인덱스
            EXECUTE format('CREATE INDEX idx_%I_job ON %I(job_id)', partition_name, partition_name);
            EXECUTE format('CREATE INDEX idx_%I_status ON %I(status)', partition_name, partition_name);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 파티션 생성 실행
SELECT create_monthly_partition_job_executions();

-- ============================================
-- 5. 파티션 유지보수 함수
-- ============================================

-- 오래된 파티션 삭제 함수
CREATE OR REPLACE FUNCTION drop_old_partitions(
    table_name text,
    months_to_keep integer DEFAULT 12
)
RETURNS void AS $$
DECLARE
    partition record;
    cutoff_date date;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE - (months_to_keep || ' months')::interval);
    
    FOR partition IN
        SELECT 
            c.relname as partition_name,
            pg_get_expr(c.relpartbound, c.oid) as partition_bound
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
        AND c.relispartition = true
        AND c.relname LIKE table_name || '_%'
    LOOP
        -- 파티션 날짜 추출 및 확인
        IF partition.partition_bound ~ '\d{4}_\d{2}' THEN
            IF partition.partition_bound::date < cutoff_date THEN
                EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', partition.partition_name);
                RAISE NOTICE 'Dropped old partition: %', partition.partition_name;
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 파티션 통계 업데이트 함수
CREATE OR REPLACE FUNCTION update_partition_stats()
RETURNS void AS $$
DECLARE
    partition record;
BEGIN
    FOR partition IN
        SELECT 
            n.nspname || '.' || c.relname as table_name
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
        AND c.relispartition = true
    LOOP
        EXECUTE format('ANALYZE %s', partition.table_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. 파티션 모니터링 뷰
-- ============================================

CREATE OR REPLACE VIEW v_partition_info AS
SELECT 
    n.nspname as schema_name,
    c.relname as table_name,
    p.relname as partition_name,
    pg_size_pretty(pg_relation_size(p.oid)) as partition_size,
    pg_stat_get_live_tuples(p.oid) as row_count,
    pg_get_expr(p.relpartbound, p.oid) as partition_bound
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_inherits i ON i.inhparent = c.oid
JOIN pg_class p ON p.oid = i.inhrelid
WHERE c.relkind = 'p'  -- partitioned table
ORDER BY n.nspname, c.relname, p.relname;

-- ============================================
-- 7. 자동 파티션 생성 스케줄 작업
-- ============================================

-- 월별 파티션 자동 생성을 위한 스케줄 작업 추가
INSERT INTO schedule_jobs (
    name, 
    job_type, 
    status, 
    specific_times, 
    parameters
) VALUES (
    '파티션 자동 생성',
    'database_maintenance',
    'active',
    ARRAY['01:00:00'::time],  -- 매일 새벽 1시
    '{
        "action": "create_partitions",
        "tables": ["market_orders", "market_raw_data", "job_executions"],
        "months_ahead": 3
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- 오래된 파티션 정리 작업
INSERT INTO schedule_jobs (
    name, 
    job_type, 
    status, 
    specific_times, 
    parameters
) VALUES (
    '오래된 파티션 정리',
    'database_maintenance',
    'active',
    ARRAY['02:00:00'::time],  -- 매일 새벽 2시
    '{
        "action": "cleanup_partitions",
        "retention_months": {
            "market_orders": 24,
            "market_raw_data": 6,
            "job_executions": 3
        }
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- ============================================
-- 8. 파티션 전환 가이드
-- ============================================

-- 기존 데이터를 파티션 테이블로 이동하는 예시
-- 실제 실행 시 트랜잭션과 잠금을 고려해야 함

/*
-- market_orders 데이터 이동 예시
BEGIN;

-- 1. 데이터 복사
INSERT INTO market_orders_partitioned 
SELECT * FROM market_orders;

-- 2. 제약조건 및 트리거 복사
-- (생략 - 실제 상황에 맞게 조정)

-- 3. 테이블 이름 변경
ALTER TABLE market_orders RENAME TO market_orders_old;
ALTER TABLE market_orders_partitioned RENAME TO market_orders;

-- 4. 권한 설정
-- (생략 - 필요에 따라 추가)

COMMIT;
*/

-- ============================================
-- 9. 파티션 성능 모니터링 함수
-- ============================================

CREATE OR REPLACE FUNCTION partition_performance_report()
RETURNS TABLE (
    parent_table text,
    partition_count bigint,
    total_size text,
    total_rows bigint,
    avg_partition_size text,
    oldest_partition text,
    newest_partition text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.relname::text as parent_table,
        COUNT(p.oid)::bigint as partition_count,
        pg_size_pretty(SUM(pg_relation_size(p.oid))) as total_size,
        SUM(pg_stat_get_live_tuples(p.oid))::bigint as total_rows,
        pg_size_pretty(AVG(pg_relation_size(p.oid))::bigint) as avg_partition_size,
        MIN(p.relname)::text as oldest_partition,
        MAX(p.relname)::text as newest_partition
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_inherits i ON i.inhparent = c.oid
    JOIN pg_class p ON p.oid = i.inhrelid
    WHERE c.relkind = 'p'
    AND n.nspname = 'public'
    GROUP BY c.relname
    ORDER BY c.relname;
END;
$$ LANGUAGE plpgsql;