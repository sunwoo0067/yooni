-- public.ownerclan_categories definition

CREATE TABLE IF NOT EXISTS public.ownerclan_categories (
    "key" TEXT NOT NULL PRIMARY KEY,
    id TEXT NULL,
    name TEXT NULL,
    "fullName" TEXT NULL,
    "parentKey" TEXT NULL, -- 최상위 카테고리의 경우 NULL이 될 수 있음
    attributes JSONB NULL,
    "lastSyncedAt" TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT ownerclan_categories_parent_fk FOREIGN KEY ("parentKey") REFERENCES public.ownerclan_categories("key") ON DELETE SET NULL
);

COMMENT ON TABLE public.ownerclan_categories IS '오너클랜 상품 카테고리 정보';
COMMENT ON COLUMN public.ownerclan_categories.key IS '카테고리 키 (오너클랜 코드)';
COMMENT ON COLUMN public.ownerclan_categories.id IS '카테고리 API ID';
COMMENT ON COLUMN public.ownerclan_categories.name IS '카테고리 이름';
COMMENT ON COLUMN public.ownerclan_categories."fullName" IS '전체 경로를 포함한 카테고리 이름';
COMMENT ON COLUMN public.ownerclan_categories."parentKey" IS '상위 카테고리 키 (ownerclan_categories.key 참조)';
COMMENT ON COLUMN public.ownerclan_categories.attributes IS '카테고리 속성 정보';
COMMENT ON COLUMN public.ownerclan_categories."lastSyncedAt" IS '마지막 동기화 시각';

-- 루트 카테고리 추가 (존재하지 않을 경우)
INSERT INTO public.ownerclan_categories ("key", name, "fullName")
VALUES ('00000000', 'ROOT', 'ROOT')
ON CONFLICT ("key") DO NOTHING;
