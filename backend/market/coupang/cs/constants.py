#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 상수 정의
"""

# API 엔드포인트
ONLINE_INQUIRIES_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/onlineInquiries"
INQUIRY_REPLY_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/onlineInquiries/{}/replies"

# 고객센터 문의 API 엔드포인트
CALL_CENTER_INQUIRIES_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/callCenterInquiries"
CALL_CENTER_INQUIRY_DETAIL_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/callCenterInquiries/{}"
CALL_CENTER_INQUIRY_REPLY_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/callCenterInquiries/{}/replies"
CALL_CENTER_INQUIRY_CONFIRM_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/callCenterInquiries/{}/confirms"

# 답변 상태
ANSWERED_TYPE = {
    "ALL": "전체보기",
    "ANSWERED": "답변완료", 
    "NOANSWER": "미답변"
}

# 고객센터 문의 상태
PARTNER_COUNSELING_STATUS = {
    "NONE": "전체",
    "ANSWER": "답변완료", 
    "NO_ANSWER": "미답변",
    "TRANSFER": "미확인"
}

# 문의 상태
INQUIRY_STATUS = {
    "PROGRESS": "진행중",
    "COMPLETE": "완료"
}

# CS 파트너 상담 상태
CS_PARTNER_COUNSELING_STATUS = {
    "REQUEST_ANSWER": "답변요청",
    "ANSWERED": "답변완료"
}

# 파트너 이관 상태
PARTNER_TRANSFER_STATUS = {
    "NONE": "대상아님",
    "REQUEST_ANSWER": "답변요청",
    "ANSWERED": "답변완료"
}

# 파트너 이관 완료 사유
PARTNER_TRANSFER_COMPLETE_REASON = {
    "NONE": "없음",
    "DISPUTE_PROCESS": "직권처리",
    "DISPUTE_PROCESS_COMPLETE": "판매자확인",
    "CANCEL": "이관취소"
}

# 답변 타입
ANSWER_TYPE = {
    "CS_AGENT": "상담사",
    "VENDOR": "판매자"
}

# 날짜 형식 패턴
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'

# 벤더 ID 패턴  
VENDOR_ID_PATTERN = r'^A\d{8}$'

# 조회 기간 제한 (최대 7일)
MAX_DATE_RANGE_DAYS = 7

# 페이지네이션 설정
DEFAULT_PAGE_NUM = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
MIN_PAGE_SIZE = 1

# 고객센터 문의 페이지네이션 설정
CC_DEFAULT_PAGE_SIZE = 10
CC_MAX_PAGE_SIZE = 30
CC_MIN_PAGE_SIZE = 1

# 에러 메시지
ERROR_MESSAGES = {
    "INVALID_VENDOR_ID": "올바른 판매자 ID(vendorId)를 입력했는지 확인합니다. 예) A00012345",
    "INVALID_DATE_FORMAT": "날짜 형식이 yyyy-MM-dd 인지 확인합니다.",
    "DATE_RANGE_TOO_LONG": "조회기간이 7일 이하 인지 확인합니다.",
    "START_AFTER_END": "조회 시작일이 종료일보다 늦을 수 없습니다.",
    "INVALID_ANSWERED_TYPE": "답변 상태는 ALL, ANSWERED, NOANSWER 중 하나여야 합니다.",
    "INVALID_PAGE_NUM": "페이지 번호는 1 이상이어야 합니다.",
    "INVALID_PAGE_SIZE": f"페이지 크기는 {MIN_PAGE_SIZE}~{MAX_PAGE_SIZE} 사이여야 합니다.",
    "TIMEOUT_ERROR": "설정한 조회기간(1일), 페이지 크기값(10)으로 재설정 후 재요청 합니다.",
    "INQUIRY_ID_REQUIRED": "문의 ID가 필요합니다.",
    "INVALID_INQUIRY_ID": "올바른 문의 ID를 입력해주세요. Number 타입이어야 합니다.",
    "INVALID_REPLY_CONTENT": "답변 내용을 입력해주세요.",
    "INVALID_REPLY_BY": "응답자 셀러포탈(WING) 아이디를 입력해주세요.",
    "DUPLICATE_REPLY": "동일한 inquiryId에 중복으로 답변을 입력했는지 확인합니다.",
    "DELETED_INQUIRY": "삭제된 상품문의에는 더 이상 답변할 수 없습니다.",
    "INVALID_JSON_FORMAT": "답변내용(content)을 JSON 형식에 맞게 작성했는지 확인합니다.",
    "INVALID_WING_ID": "replyBy 파라메터 값으로 올바른 셀러포탈(WING) 아이디를 입력했는지 확인합니다.",
    "INVALID_COUNSELING_STATUS": "문의 상태는 NONE, ANSWER, NO_ANSWER, TRANSFER 중 하나여야 합니다.",
    "INVALID_VENDOR_ITEM_ID": "올바른 옵션 ID(vendorItemId)를 입력해주세요.",
    "INVALID_ORDER_ID": "올바른 주문번호(orderId)를 입력해주세요.",
    "INVALID_PAGE_SIZE_CC": "페이지 크기는 1~30 사이여야 합니다.",
    "INQUIRY_NOT_FOUND": "문의를 찾을 수 없습니다.",
    "INQUIRY_CANNOT_ANSWER": "답변할 수 없는 문의입니다. 상태를 확인해주세요.",
    "CONTENT_LENGTH_ERROR": "답변 내용은 2자 이상 1000자 이하여야 합니다.",
    "PARENT_ANSWER_ID_REQUIRED": "부모 이관글 ID(parentAnswerId)가 필요합니다.",
    "INVALID_USER_ID": "올바르지 않은 사용자 ID입니다.",
    "INQUIRY_CLOSED": "상담이 종료된 문의입니다.",
    "CONFIRM_BY_REQUIRED": "확인자 ID(confirmBy)가 필요합니다."
}

# HTTP 헤더
EXTENDED_TIMEOUT_HEADER = "X-EXTENDED-TIMEOUT"
DEFAULT_TIMEOUT_SECONDS = 30
EXTENDED_TIMEOUT_SECONDS = 60