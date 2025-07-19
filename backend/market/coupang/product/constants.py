#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 관련 상수
"""

# API 기본 정보
BASE_URL = "https://api-gateway.coupang.com"

# API 경로들
PRODUCT_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
PRODUCT_GET_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}"
PRODUCT_PARTIAL_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}/partial"
PRODUCT_PARTIAL_UPDATE_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}/partial"
PRODUCT_APPROVAL_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}/approvals"
PRODUCT_INFLOW_STATUS_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/inflow-status"
PRODUCT_TIME_FRAME_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame"
PRODUCT_STATUS_HISTORY_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{}/histories"
PRODUCT_BY_EXTERNAL_SKU_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/external-vendor-sku-codes/{}"
VENDOR_ITEM_INVENTORY_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/inventories"
VENDOR_ITEM_QUANTITY_UPDATE_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/quantities/{}"
VENDOR_ITEM_PRICE_UPDATE_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/prices/{}"
VENDOR_ITEM_SALES_RESUME_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/sales/resume"
VENDOR_ITEM_SALES_STOP_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/sales/stop"
VENDOR_ITEM_ORIGINAL_PRICE_UPDATE_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/original-prices/{}"
VENDOR_ITEM_AUTO_GENERATED_OPT_IN_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/auto-generated/opt-in"
VENDOR_ITEM_AUTO_GENERATED_OPT_OUT_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{}/auto-generated/opt-out"
SELLER_AUTO_GENERATED_OPT_IN_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller/auto-generated/opt-in"
SELLER_AUTO_GENERATED_OPT_OUT_API_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller/auto-generated/opt-out"
CATEGORY_RECOMMENDATION_API_PATH = "/v2/providers/openapi/apis/api/v1/categorization/predict"

# 배송방법 코드
DELIVERY_METHODS = {
    "SEQUENCIAL": "일반배송",
    "COLD_FRESH": "신선냉동",
    "MAKE_ORDER": "주문제작"
}

# 배송비 종류
DELIVERY_CHARGE_TYPES = {
    "FREE": "무료배송",
    "NOT_FREE": "유료배송", 
    "CONDITIONAL_FREE": "조건부무료배송",
    "CHARGE_RECEIVED": "착불"
}

# 택배사 코드 (일부)
DELIVERY_COMPANIES = {
    "CJGLS": "CJ대한통운",
    "LOTTE": "롯데택배",
    "HANJIN": "한진택배",
    "KGB": "로젠택배",
    "EPOST": "우체국택배",
    "KDEXP": "경동택배"
}

# 상품 상태 코드
PRODUCT_STATUS = {
    "IN_REVIEW": "심사중",
    "SAVED": "임시저장",
    "APPROVING": "승인대기중", 
    "APPROVED": "승인완료",
    "PARTIAL_APPROVED": "부분승인완료",
    "DENIED": "승인반려",
    "DELETED": "상품삭제"
}

# 이미지 타입
IMAGE_TYPES = {
    "REPRESENTATION": "대표이미지",
    "DETAIL": "기타이미지",
    "USED_PRODUCT": "중고상태이미지"
}

# 컨텐츠 타입
CONTENT_TYPES = {
    "TEXT": "텍스트",
    "IMAGE": "이미지",
    "VIDEO": "비디오"
}

# 인증 타입 (예시)
CERTIFICATION_TYPES = {
    "KC_SAFETY": "KC 안전인증",
    "CE": "CE 인증",
    "FCC": "FCC 인증",
    "FDA": "FDA 승인"
}

# 카테고리별 필수 속성 예시
CATEGORY_REQUIRED_ATTRIBUTES = {
    56137: ["용량", "브랜드", "원산지"],  # 화장품 예시
    # 다른 카테고리들...
}

# 고시정보 카테고리 예시
NOTICE_CATEGORIES = {
    "화장품": ["용량 또는 중량", "제품 주요 사양", "사용법", "주의사항"],
    "의류": ["소재", "색상", "치수", "세탁방법", "제조자"],
    "전자제품": ["품명 및 모델명", "KC 인증 필 유무", "정격전압", "소비전력"],
    # 다른 카테고리들...
}

# API 응답 코드
RESPONSE_CODES = {
    "SUCCESS": "성공",
    "ERROR": "오류"
}

# 배송 관련 기본값
DEFAULT_DELIVERY_CHARGE = 0
DEFAULT_RETURN_CHARGE = 3000
DEFAULT_FREE_SHIP_AMOUNT = 0

# 제한값들
MAX_PRODUCT_NAME_LENGTH = 100
MAX_SELLER_PRODUCT_NAME_LENGTH = 20
MAX_SEARCH_TAG_COUNT = 10
MAX_IMAGE_COUNT = 10
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1
MAX_TIME_FRAME_MINUTES = 10

# 정규식 패턴들
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
DATETIME_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
VENDOR_ID_PATTERN = r'^A\d{8}$'