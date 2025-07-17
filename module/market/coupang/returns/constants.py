#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 관련 상수
"""

# API 기본 정보
BASE_URL = "https://api-gateway.coupang.com"

# API 경로들
RETURN_REQUESTS_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnRequests"
RETURN_REQUEST_DETAIL_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnRequests/{}"
RETURN_RECEIVE_CONFIRMATION_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnRequests/{}/receiveConfirmation"
RETURN_APPROVAL_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnRequests/{}/approval"
RETURN_WITHDRAW_REQUESTS_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnWithdrawRequests"
RETURN_WITHDRAW_BY_IDS_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/returnWithdrawList"
RETURN_EXCHANGE_INVOICE_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/return-exchange-invoices/manual"

# 반품/취소 상태 코드
RETURN_STATUS = {
    "RU": "출고중지요청",
    "UC": "반품접수", 
    "CC": "반품완료",
    "PR": "쿠팡확인요청"
}

# 반품/취소 진행 상태
RECEIPT_STATUS = {
    "RELEASE_STOP_UNCHECKED": "출고중지요청",
    "RETURNS_UNCHECKED": "반품접수",
    "VENDOR_WAREHOUSE_CONFIRM": "입고완료",
    "REQUEST_COUPANG_CHECK": "쿠팡확인요청",
    "RETURNS_COMPLETED": "반품완료"
}

# 취소 유형
CANCEL_TYPE = {
    "RETURN": "반품주문조회",
    "CANCEL": "취소주문조회"
}

# 검색 타입
SEARCH_TYPES = {
    "timeFrame": "분단위 전체",
    "daily": "일단위 페이징"
}

# 출고중지처리상태
RELEASE_STOP_STATUS = {
    "미처리": "처리 대기중",
    "처리(이미출고)": "이미 출고된 상품",
    "처리(출고중지)": "출고 중지 처리됨",
    "자동처리(이미출고)": "자동으로 이미출고 처리됨",
    "비대상": "출고중지 대상이 아님"
}

# 상품출고여부
RELEASE_STATUS = {
    "Y": "출고됨",
    "N": "미출고",
    "S": "출고중지됨", 
    "A": "이미출고됨"
}

# 귀책타입
FAULT_BY_TYPE = {
    "COUPANG": "쿠팡 과실",
    "VENDOR": "협력사(셀러) 과실",
    "CUSTOMER": "고객 과실",
    "WMS": "물류 과실",
    "GENERAL": "일반"
}

# 완료 확인 종류
COMPLETE_CONFIRM_TYPE = {
    "VENDOR_CONFIRM": "파트너 확인",
    "UNDEFINED": "미확인",
    "CS_CONFIRM": "CS 대리확인",
    "CS_LOSS_CONFIRM": "CS 손실확인"
}

# 택배사 코드
DELIVERY_COMPANY_CODES = {
    "CJGLS": "CJ대한통운",
    "HANJIN": "한진택배", 
    "LOTTE": "롯데택배",
    "LOGEN": "로젠택배",
    "KPOST": "우체국택배"
}

# 제한값들
MAX_DATE_RANGE_DAYS = 31  # 최대 조회 기간 (일)
MAX_PER_PAGE = 50  # 페이지당 최대 조회 요청 값
DEFAULT_PER_PAGE = 50  # 기본 페이지당 조회 요청 값

# 정규식 패턴들
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'  # yyyy-mm-dd
DATETIME_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$'  # yyyy-MM-ddTHH:mm
VENDOR_ID_PATTERN = r'^A\d{8}$'  # A00012345 형태

# 오류 메시지
ERROR_MESSAGES = {
    "INVALID_VENDOR_ID": "올바른 판매자 ID(vendorId)를 입력했는지 확인합니다. 예) A00012345",
    "DATE_RANGE_TOO_LONG": "조회기간이 31일 이내 인지 확인합니다.",
    "INVALID_DATE_FORMAT": "날짜 형식이 올바르지 않습니다. yyyy-mm-dd 또는 yyyy-mm-ddTHH:mm 형태로 입력해주세요.",
    "INVALID_STATUS": "올바른 반품 상태를 입력해주세요.",
    "INVALID_CANCEL_TYPE": "올바른 취소 유형을 입력해주세요. (RETURN 또는 CANCEL)",
    "INVALID_SEARCH_TYPE": "올바른 검색 타입을 입력해주세요. (timeFrame)",
    "INVALID_MAX_PER_PAGE": f"페이지당 최대 조회 요청 값은 1-{MAX_PER_PAGE} 사이여야 합니다.",
    "ORDER_ID_REQUIRED": "반품상태(status) 값 입력이 없을 경우 주문번호(orderId) 입력은 필수입니다.",
    "INVALID_ORDER_ID": "올바른 주문번호(orderId)를 입력해주세요. Number 타입이어야 합니다.",
    "TIMEFRAME_DATETIME_FORMAT": "timeFrame 검색 시 날짜는 yyyy-MM-ddTHH:mm 형식이어야 합니다.",
    "CANCEL_TYPE_STATUS_CONFLICT": "cancelType=CANCEL일 경우 status 파라메터를 사용할 수 없습니다.",
    "TIMEFRAME_PAGINATION_CONFLICT": "timeFrame 검색 시 nextToken, maxPerPage, orderId 파라메터를 사용할 수 없습니다."
}

# API 응답 코드
RESPONSE_CODES = {
    "200": "성공",
    "400": "요청변수확인",
    "401": "인증실패", 
    "403": "권한없음",
    "412": "서버오류(타임아웃)",
    "500": "서버오류"
}

# 반품 사유 카테고리 (샘플)
CANCEL_REASON_CATEGORIES = {
    "고객변심": "단순변심, 필요없어짐 등",
    "상품불량": "파손, 오염, 기능이상 등",
    "배송문제": "배송지연, 배송누락 등",
    "주문실수": "중복주문, 잘못주문 등"
}

# 회수종류
RETURN_DELIVERY_TYPES = {
    "전담택배": "쿠팡 전담 택배사 회수",
    "연동택배": "연동된 택배사 회수", 
    "수기관리": "수동 관리",
    "": "회수 대상 없음"
}

# 반품/교환 처리 타입
RETURN_EXCHANGE_DELIVERY_TYPE = {
    "RETURN": "반품",
    "EXCHANGE": "교환"
}

# 반품 귀책 타입 (철회 이력용)
REFUND_DELIVERY_DUTY = {
    "COM": "업체",
    "CUS": "고객", 
    "COU": "쿠팡"
}

# 반품 처리 가능 상태들
RECEIPT_STATUS_FOR_RECEIVE_CONFIRMATION = ["RETURNS_UNCHECKED"]  # 입고확인 가능
RECEIPT_STATUS_FOR_APPROVAL = ["VENDOR_WAREHOUSE_CONFIRM"]  # 승인 가능

# 반품 철회 조회 제한값
MAX_WITHDRAW_DATE_RANGE_DAYS = 7  # 최대 조회 기간 (일)
MAX_WITHDRAW_PER_PAGE = 100  # 페이지당 최대 조회 수
DEFAULT_WITHDRAW_PER_PAGE = 10  # 기본 페이지당 조회 수
MAX_CANCEL_IDS_PER_REQUEST = 50  # 한 번에 조회 가능한 최대 접수번호 수