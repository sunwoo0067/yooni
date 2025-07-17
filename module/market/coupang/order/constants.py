#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관련 상수
"""

# API 기본 정보
BASE_URL = "https://api-gateway.coupang.com"

# API 경로들
ORDER_SHEETS_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets"
ORDER_SHEET_DETAIL_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}"
ORDER_SHEET_BY_ORDER_ID_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/{}/ordersheets"
ORDER_SHEET_HISTORY_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/history"
ORDER_PROCESSING_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/processing"
INVOICE_UPLOAD_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/invoice"
STOP_SHIPPING_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/stop-shipment"
ALREADY_SHIPPED_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/shipped"
ORDER_CANCEL_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/item/order-cancel"
COMPLETE_DELIVERY_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/ordersheets/{}/complete-delivery"

# 발주서 상태 코드
ORDER_STATUS = {
    "ACCEPT": "결제완료",
    "INSTRUCT": "상품준비중",
    "DEPARTURE": "배송지시", 
    "DELIVERING": "배송중",
    "FINAL_DELIVERY": "배송완료",
    "NONE_TRACKING": "업체 직접 배송(배송 연동 미적용), 추적불가"
}

# 배송비 종류
DELIVERY_CHARGE_TYPES = {
    "유료": "유료배송",
    "무료": "무료배송"
}

# 배송 유형
SHIPMENT_TYPES = {
    "THIRD_PARTY": "제3자 배송",
    "CGF": "쿠팡 풀필먼트",
    "CGF_LITE": "쿠팡 풀필먼트 라이트"
}

# 택배사 코드
DELIVERY_COMPANIES = {
    "CJ 대한통운": "CJ대한통운",
    "한진택배": "한진택배",
    "로젠택배": "로젠택배",
    "우체국택배": "우체국택배",
    "롯데택배": "롯데택배"
}

# 검색 타입
SEARCH_TYPES = {
    "timeFrame": "분단위 전체",
    "daily": "일단위 페이징"
}

# API 응답 코드
RESPONSE_CODES = {
    "200": "성공",
    "400": "요청변수확인",
    "401": "인증실패",
    "403": "권한없음",
    "500": "서버오류"
}

# 결제 위치
REFER_TYPES = {
    "아이폰앱": "iPhone App",
    "안드로이드앱": "Android App", 
    "PC웹": "PC Web",
    "모바일웹": "Mobile Web"
}

# 제한값들
MAX_DATE_RANGE_DAYS = 31  # 최대 조회 기간 (일)
MAX_PER_PAGE = 50  # 페이지당 최대 조회 요청 값
DEFAULT_PER_PAGE = 50  # 기본 페이지당 조회 요청 값

# 정규식 패턴들
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'  # yyyy-mm-dd
DATETIME_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'  # yyyy-MM-dd'T'HH:mm:ss
VENDOR_ID_PATTERN = r'^A\d{8}$'  # A00012345 형태

# 오류 메시지
ERROR_MESSAGES = {
    "INVALID_VENDOR_ID": "올바른 판매자 ID(vendorId)를 입력했는지 확인합니다. 예) A00012345",
    "DATE_RANGE_TOO_LONG": "조회기간이 31일 이내 인지 확인합니다.",
    "INVALID_DATE_FORMAT": "날짜 형식이 올바르지 않습니다. yyyy-mm-dd 형태로 입력해주세요.",
    "INVALID_STATUS": "올바른 발주서 상태를 입력해주세요.",
    "INVALID_MAX_PER_PAGE": f"페이지당 최대 조회 요청 값은 1-{MAX_PER_PAGE} 사이여야 합니다.",
    "INVALID_SHIPMENT_BOX_ID": "올바른 배송번호(shipmentBoxId)를 입력해주세요. Number 타입이어야 합니다.",
    "INVALID_ORDER_ID": "올바른 주문번호(orderId)를 입력해주세요. Number 타입이어야 합니다.",
    "ORDER_CANCELED_OR_RETURNED": "해당 주문이 취소 또는 반품되었습니다.",
    "ORDER_NOT_FOUND": "해당 발주서를 찾을 수 없습니다.",
    "INVALID_ORDER_NUMBER": "유효하지 않은 주문번호입니다.",
    "UNAUTHORIZED_ORDER_ACCESS": "다른 판매자의 주문을 조회할 수 없습니다.",
    "INVALID_INVOICE_NUMBER": "올바른 송장번호를 입력해주세요.",
    "INVALID_DELIVERY_COMPANY": "올바른 택배사 코드를 입력해주세요.",
    "INVALID_VENDOR_ITEM_ID": "올바른 상품 ID를 입력해주세요.",
    "INVALID_REASON": "올바른 취소/중지 사유를 입력해주세요."
}

# 택배사 코드 (송장 업로드용)
DELIVERY_COMPANY_CODES = {
    "01": "CJ대한통운",
    "02": "한진택배",
    "03": "롯데택배",
    "04": "로젠택배",
    "05": "우체국택배",
    "99": "기타(직접입력)"
}

# 상품준비중 처리 가능 상태
PROCESSING_AVAILABLE_STATUS = ["ACCEPT", "INSTRUCT"]

# 송장업로드 가능 상태  
INVOICE_UPLOAD_AVAILABLE_STATUS = ["INSTRUCT"]

# 출고중지 가능 상태
STOP_SHIPPING_AVAILABLE_STATUS = ["INSTRUCT"]

# 이미출고 처리 가능 상태
ALREADY_SHIPPED_AVAILABLE_STATUS = ["INSTRUCT"]

# 장기미배송 완료 처리 가능 상태
COMPLETE_DELIVERY_AVAILABLE_STATUS = ["DELIVERING"]