-- 워크플로우 관련 테이블 생성

-- 워크플로우 정의 테이블
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    trigger_type VARCHAR(50) NOT NULL, -- 'event', 'schedule', 'manual'
    config JSONB NOT NULL, -- 워크플로우 설정 (YAML/JSON)
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 워크플로우 규칙 테이블
CREATE TABLE IF NOT EXISTS workflow_rules (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    rule_order INTEGER NOT NULL,
    condition_type VARCHAR(50) NOT NULL, -- 'threshold', 'comparison', 'time_based', 'custom'
    condition_config JSONB NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'notification', 'api_call', 'database_update', 'workflow_trigger'
    action_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 워크플로우 실행 이력
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflow_definitions(id),
    trigger_source VARCHAR(100), -- 이벤트 소스
    trigger_data JSONB,
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    result JSONB,
    error_message TEXT
);

-- 워크플로우 스텝 실행 이력
CREATE TABLE IF NOT EXISTS workflow_step_executions (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id) ON DELETE CASCADE,
    rule_id INTEGER REFERENCES workflow_rules(id),
    step_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT
);

-- 이벤트 트리거 정의
CREATE TABLE IF NOT EXISTS event_triggers (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    workflow_id INTEGER REFERENCES workflow_definitions(id),
    filter_config JSONB, -- 이벤트 필터링 조건
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_type, event_source, workflow_id)
);

-- 워크플로우 템플릿
CREATE TABLE IF NOT EXISTS workflow_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    description TEXT,
    template_config JSONB NOT NULL,
    icon VARCHAR(50),
    is_public BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at);
CREATE INDEX idx_workflow_step_executions_execution_id ON workflow_step_executions(execution_id);
CREATE INDEX idx_event_triggers_event_type ON event_triggers(event_type, event_source);

-- 기본 워크플로우 템플릿 삽입
INSERT INTO workflow_templates (name, category, description, template_config, icon) VALUES
('재고 부족 알림', 'inventory', '재고가 설정된 임계치 이하로 떨어지면 알림을 보냅니다.', 
 '{"trigger": {"type": "event", "source": "inventory.low_stock"}, "rules": [{"condition": {"type": "threshold", "field": "stock_quantity", "operator": "<=", "value": 10}, "action": {"type": "notification", "channel": "email", "template": "low_stock_alert"}}]}',
 'package'),
 
('신규 주문 처리', 'order', '신규 주문이 들어오면 자동으로 검증하고 처리합니다.',
 '{"trigger": {"type": "event", "source": "order.created"}, "rules": [{"condition": {"type": "always"}, "action": {"type": "api_call", "endpoint": "/api/orders/validate"}}, {"condition": {"type": "field_check", "field": "validation_status", "value": "passed"}, "action": {"type": "database_update", "table": "orders", "set": {"status": "processing"}}}]}',
 'shopping-cart'),
 
('일일 매출 리포트', 'reporting', '매일 자정에 일일 매출 리포트를 생성하고 이메일로 발송합니다.',
 '{"trigger": {"type": "schedule", "cron": "0 0 * * *"}, "rules": [{"condition": {"type": "always"}, "action": {"type": "api_call", "endpoint": "/api/reports/daily-sales"}}, {"condition": {"type": "always"}, "action": {"type": "notification", "channel": "email", "template": "daily_sales_report"}}]}',
 'file-text'),
 
('가격 자동 조정', 'pricing', '경쟁사 가격 변동 시 자동으로 가격을 조정합니다.',
 '{"trigger": {"type": "event", "source": "competitor.price_change"}, "rules": [{"condition": {"type": "comparison", "field": "competitor_price", "operator": "<", "compare_field": "our_price", "margin": 0.95}, "action": {"type": "api_call", "endpoint": "/api/products/adjust-price", "params": {"strategy": "match_competitor", "margin": 0.98}}}]}',
 'trending-up');