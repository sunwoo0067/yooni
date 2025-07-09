-- 오너클랜 상품 정보를 저장하기 위한 테이블 스키마

CREATE TABLE IF NOT EXISTS public.ownerclan_items (
    "key" TEXT PRIMARY KEY,
    "createdAt" TIMESTAMPTZ,
    "updatedAt" TIMESTAMPTZ,
    name TEXT,
    model TEXT,
    production TEXT,
    origin TEXT,
    price NUMERIC,
    "pricePolicy" TEXT,
    "fixedPrice" NUMERIC,
    category JSONB,
    "shippingFee" NUMERIC,
    "shippingType" TEXT,
    status TEXT,
    options JSONB,
    "taxFree" BOOLEAN,
    "adultOnly" BOOLEAN,
    returnable BOOLEAN,
    images JSONB,
    "guaranteedShippingPeriod" TEXT, -- 예시 데이터가 없어 TEXT로 지정, 필요시 변경
    "openmarketSellable" BOOLEAN,
    "boxQuantity" INTEGER,
    attributes JSONB,
    "returnCriteria" TEXT, -- 예시 데이터가 없어 TEXT로 지정, 필요시 변경
    metadata JSONB,
    "lastSyncedAt" TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.ownerclan_items IS '오너클랜 API를 통해 수집된 개별 상품 정보';
COMMENT ON COLUMN public.ownerclan_items."key" IS '오너클랜 상품 고유 키';
COMMENT ON COLUMN public.ownerclan_items."createdAt" IS '상품 등록 시각';
COMMENT ON COLUMN public.ownerclan_items."updatedAt" IS '상품 최종 수정 시각';
COMMENT ON COLUMN public.ownerclan_items.name IS '상품명';
COMMENT ON COLUMN public.ownerclan_items.price IS '상품 가격';
COMMENT ON COLUMN public.ownerclan_items.category IS '상품 카테고리 정보';
COMMENT ON COLUMN public.ownerclan_items.options IS '상품 옵션 정보';
COMMENT ON COLUMN public.ownerclan_items.images IS '상품 이미지 URL 목록';
COMMENT ON COLUMN public.ownerclan_items."lastSyncedAt" IS 'Supabase와 마지막으로 동기화된 시각';
