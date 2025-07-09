-- ownerclan_items 테이블에 content 컬럼을 추가하는 마이그레이션 스크립트

ALTER TABLE public.ownerclan_items
ADD COLUMN IF NOT EXISTS content TEXT;

COMMENT ON COLUMN public.ownerclan_items.content IS '상품 상세 정보 (HTML)';
