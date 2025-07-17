-- 공급사 멀티계정 관리를 위한 테이블
CREATE TABLE IF NOT EXISTS supplier_accounts (
  id SERIAL PRIMARY KEY,
  supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
  account_name VARCHAR(100) NOT NULL,
  api_key VARCHAR(255),
  api_secret VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_supplier_accounts_supplier_id ON supplier_accounts(supplier_id);

-- suppliers 테이블에 필요한 컬럼 추가 (없는 경우)
ALTER TABLE suppliers 
ADD COLUMN IF NOT EXISTS contact_info VARCHAR(255),
ADD COLUMN IF NOT EXISTS business_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS address TEXT;