-- 공급사 설정 테이블
CREATE TABLE IF NOT EXISTS supplier_configs (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    api_type VARCHAR(50) NOT NULL, -- 'graphql', 'rest', 'crawling'
    api_endpoint TEXT,
    api_key TEXT,
    api_secret TEXT,
    collection_enabled BOOLEAN DEFAULT true,
    collection_schedule VARCHAR(20) DEFAULT 'manual', -- 'manual', 'hourly', 'daily', 'realtime'
    schedule_time TIME,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id)
);

-- 수집 로그 테이블
CREATE TABLE IF NOT EXISTS collection_logs (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'partial'
    total_products INTEGER DEFAULT 0,
    new_products INTEGER DEFAULT 0,
    updated_products INTEGER DEFAULT 0,
    failed_products INTEGER DEFAULT 0,
    error_message TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 수집 스케줄 테이블
CREATE TABLE IF NOT EXISTS collection_schedules (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    schedule_type VARCHAR(20) NOT NULL, -- 'manual', 'hourly', 'daily', 'realtime'
    hour INTEGER CHECK (hour >= 0 AND hour < 24),
    minute INTEGER CHECK (minute >= 0 AND minute < 60),
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id)
);

-- 인덱스 생성
CREATE INDEX idx_collection_logs_supplier_id ON collection_logs(supplier_id);
CREATE INDEX idx_collection_logs_started_at ON collection_logs(started_at DESC);
CREATE INDEX idx_collection_logs_status ON collection_logs(status);

-- 기본 공급사 설정 데이터 입력
INSERT INTO supplier_configs (supplier_id, api_type, api_endpoint, collection_enabled, collection_schedule, schedule_time)
VALUES 
    (1, 'graphql', 'https://api.ownerclan.com/v1/graphql', true, 'daily', '02:00:00'),
    (2, 'rest', 'https://api.zentrade.com/v1', true, 'hourly', NULL),
    (3, 'crawling', 'https://domemae.com', false, 'manual', NULL)
ON CONFLICT (supplier_id) DO NOTHING;