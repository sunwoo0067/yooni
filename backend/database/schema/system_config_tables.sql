-- 시스템 설정 테이블 (환경변수 DB 관리)

-- 1. 시스템 설정 테이블
CREATE TABLE IF NOT EXISTS system_configs (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,  -- database, api, system, feature 등
    key VARCHAR(255) NOT NULL,
    value TEXT,
    encrypted BOOLEAN DEFAULT false,  -- 암호화 여부
    description TEXT,
    data_type VARCHAR(50) DEFAULT 'string',  -- string, integer, boolean, json
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    UNIQUE(category, key)
);

-- 2. 설정 히스토리 테이블 (변경 이력 추적)
CREATE TABLE IF NOT EXISTS system_config_history (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES system_configs(id),
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100),
    change_reason TEXT
);

-- 3. 설정 그룹 테이블 (관련 설정들을 그룹화)
CREATE TABLE IF NOT EXISTS system_config_groups (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 설정-그룹 매핑 테이블
CREATE TABLE IF NOT EXISTS system_config_group_mappings (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES system_configs(id),
    group_id INTEGER REFERENCES system_config_groups(id),
    display_order INTEGER DEFAULT 0,
    UNIQUE(config_id, group_id)
);

-- 인덱스 생성
CREATE INDEX idx_system_configs_category ON system_configs(category);
CREATE INDEX idx_system_configs_key ON system_configs(key);
CREATE INDEX idx_system_configs_active ON system_configs(is_active);
CREATE INDEX idx_system_config_history_config ON system_config_history(config_id);
CREATE INDEX idx_system_config_history_changed ON system_config_history(changed_at);

-- 트리거: 설정 변경 시 히스토리 자동 기록
CREATE OR REPLACE FUNCTION record_config_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.value IS DISTINCT FROM NEW.value THEN
        INSERT INTO system_config_history (
            config_id, category, key, old_value, new_value, changed_by
        ) VALUES (
            NEW.id, NEW.category, NEW.key, OLD.value, NEW.value, NEW.updated_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER config_change_trigger
AFTER UPDATE ON system_configs
FOR EACH ROW
EXECUTE FUNCTION record_config_change();

-- 기본 설정 그룹 생성
INSERT INTO system_config_groups (group_name, description, display_order) VALUES
    ('database', '데이터베이스 연결 설정', 1),
    ('api_keys', 'API 인증 정보', 2),
    ('marketplace', '마켓플레이스 설정', 3),
    ('collection', '수집 스케줄 설정', 4),
    ('notification', '알림 설정', 5),
    ('system', '시스템 전역 설정', 6)
ON CONFLICT (group_name) DO NOTHING;

-- 기본 설정 값 삽입
INSERT INTO system_configs (category, key, value, description, data_type) VALUES
    -- 데이터베이스 설정
    ('database', 'DB_HOST', 'localhost', '데이터베이스 호스트', 'string'),
    ('database', 'DB_PORT', '5434', '데이터베이스 포트', 'integer'),
    ('database', 'DB_NAME', 'yoonni', '데이터베이스 이름', 'string'),
    ('database', 'DB_USER', 'postgres', '데이터베이스 사용자', 'string'),
    ('database', 'DB_CONNECTION_POOL_SIZE', '20', '연결 풀 크기', 'integer'),
    
    -- 시스템 설정
    ('system', 'LOG_LEVEL', 'INFO', '로그 레벨 (DEBUG, INFO, WARNING, ERROR)', 'string'),
    ('system', 'TIMEZONE', 'Asia/Seoul', '시스템 타임존', 'string'),
    ('system', 'MAINTENANCE_MODE', 'false', '유지보수 모드', 'boolean'),
    
    -- 수집 설정
    ('collection', 'DEFAULT_COLLECTION_INTERVAL', '3600', '기본 수집 주기 (초)', 'integer'),
    ('collection', 'MAX_RETRY_COUNT', '3', '최대 재시도 횟수', 'integer'),
    ('collection', 'RETRY_DELAY', '60', '재시도 대기 시간 (초)', 'integer'),
    
    -- 알림 설정
    ('notification', 'ENABLE_EMAIL_NOTIFICATION', 'true', '이메일 알림 활성화', 'boolean'),
    ('notification', 'ENABLE_SLACK_NOTIFICATION', 'false', 'Slack 알림 활성화', 'boolean'),
    ('notification', 'LOW_STOCK_THRESHOLD', '10', '재고 부족 알림 임계값', 'integer')
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    data_type = EXCLUDED.data_type;

-- 설정 조회 함수
CREATE OR REPLACE FUNCTION get_config(p_category VARCHAR, p_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    v_value TEXT;
BEGIN
    SELECT value INTO v_value
    FROM system_configs
    WHERE category = p_category 
    AND key = p_key 
    AND is_active = true;
    
    RETURN v_value;
END;
$$ LANGUAGE plpgsql;

-- 설정 업데이트 함수
CREATE OR REPLACE FUNCTION set_config(
    p_category VARCHAR, 
    p_key VARCHAR, 
    p_value TEXT,
    p_user VARCHAR DEFAULT 'system'
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE system_configs
    SET value = p_value,
        updated_at = CURRENT_TIMESTAMP,
        updated_by = p_user
    WHERE category = p_category 
    AND key = p_key;
    
    IF NOT FOUND THEN
        INSERT INTO system_configs (category, key, value, created_by, updated_by)
        VALUES (p_category, p_key, p_value, p_user, p_user);
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;