#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 모듈 상수 정의
"""

# API 엔드포인트
REVENUE_HISTORY_API_PATH = "/v2/providers/openapi/apis/api/v1/revenue-history"

# 매출 타입
SALE_TYPE = {
    "SALE": "판매",
    "REFUND": "환불"
}

# 세금 타입
TAX_TYPE = {
    "TAX": "과세",
    "TAX_FREE": "비과세"
}

# 페이지네이션 설정
DEFAULT_MAX_PER_PAGE = 20
MIN_MAX_PER_PAGE = 1
MAX_MAX_PER_PAGE = 100

# 날짜 범위 제한
MAX_DATE_RANGE_DAYS = 31  # 31일 최대
MIN_DATE_RANGE_DAYS = 1   # 1일 최소

# 타임아웃 설정
DEFAULT_TIMEOUT_SECONDS = 30
EXTENDED_TIMEOUT_SECONDS = 60

# 에러 메시지
ERROR_MESSAGES = {
    # 기본 검증 오류
    "INVALID_VENDOR_ID": "올바른 판매자 ID를 입력해주세요. (A로 시작하는 9자리)",
    "INVALID_DATE_FORMAT": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)",
    "INVALID_DATE_RANGE": "조회 시작일이 종료일보다 늦을 수 없습니다.",
    "INVALID_RECOGNITION_DATE_RANGE": "매출 인식일 범위가 올바르지 않습니다.",
    "DATE_RANGE_TOO_LONG": f"조회 기간은 최대 {MAX_DATE_RANGE_DAYS}일까지 가능합니다.",
    "DATE_RANGE_TOO_SHORT": f"조회 기간은 최소 {MIN_DATE_RANGE_DAYS}일 이상이어야 합니다.",
    
    # 매출 검색 파라미터 오류
    "INVALID_MAX_PER_PAGE": f"페이지당 조회 개수는 {MIN_MAX_PER_PAGE}~{MAX_MAX_PER_PAGE} 사이여야 합니다.",
    "INVALID_TOKEN": "페이지네이션 토큰이 올바르지 않습니다.",
    "INVALID_RECOGNITION_DATE": "매출 인식일이 올바르지 않습니다.",
    
    # API 호출 오류
    "API_REQUEST_FAILED": "매출내역 조회 API 호출에 실패했습니다.",
    "API_RESPONSE_INVALID": "API 응답 형식이 올바르지 않습니다.",
    "API_TIMEOUT": "API 호출 시간이 초과되었습니다.",
    "API_RATE_LIMIT": "API 호출 횟수 제한에 도달했습니다.",
    
    # 데이터 처리 오류
    "EMPTY_RESPONSE": "조회된 매출 데이터가 없습니다.",
    "INVALID_REVENUE_DATA": "매출 데이터 형식이 올바르지 않습니다.",
    "CALCULATION_ERROR": "매출 계산 중 오류가 발생했습니다.",
    
    # 환경 설정 오류
    "MISSING_CREDENTIALS": "쿠팡 API 인증 정보가 설정되지 않았습니다.",
    "INVALID_CONFIG": "설정 파일이 올바르지 않습니다.",
}

# 성공 메시지
SUCCESS_MESSAGES = {
    "REVENUE_HISTORY_SUCCESS": "매출내역 조회 성공",
    "REVENUE_SUMMARY_SUCCESS": "매출 요약 조회 성공",
    "REVENUE_CALCULATION_SUCCESS": "매출 계산 완료",
}

# 검증 정규식 패턴
VENDOR_ID_PATTERN = r"^A\d{8}$"  # A로 시작하는 9자리
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"  # YYYY-MM-DD
TOKEN_PATTERN = r"^[A-Za-z0-9+/=]*$"  # Base64 토큰 패턴

# 통계 계산용 필드
REVENUE_CALCULATION_FIELDS = [
    "settlement_amount",      # 정산금액
    "service_fee",           # 서비스 수수료
    "vat",                   # 부가세
    "sale_amount",           # 판매금액
    "refund_amount",         # 환불금액
    "commission",            # 수수료
]

# 매출 데이터 필수 필드
REQUIRED_REVENUE_FIELDS = [
    "vendor_item_id",        # 판매자 상품 ID
    "item_name",             # 상품명
    "recognition_date",      # 매출 인식일
    "sale_type",             # 매출 타입 (SALE/REFUND)
    "settlement_amount",     # 정산금액
]

# 매출 분석 관련 상수
REVENUE_ANALYSIS_CATEGORIES = {
    "HIGH_REVENUE": "고매출",     # 평균 매출의 2배 이상
    "MEDIUM_REVENUE": "중매출",   # 평균 매출의 0.5~2배
    "LOW_REVENUE": "저매출",      # 평균 매출의 0.5배 미만
}

# 경고 임계값
WARNING_THRESHOLDS = {
    "LARGE_DATE_RANGE": 20,      # 20일 이상 조회 시 경고
    "HIGH_PAGE_SIZE": 50,        # 50개 이상 페이지 크기 시 경고
    "LOW_REVENUE_RATIO": 0.1,    # 매출의 10% 이하일 때 경고
}

# 날짜 형식
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
API_DATE_FORMAT = "%Y-%m-%d"

# 기본 설정값
DEFAULT_SEARCH_DAYS = 7          # 기본 검색 기간
DEFAULT_RECENT_DAYS = 30         # 기본 최근 기간
DEFAULT_MONTHLY_PERIOD = 1       # 기본 월별 기간

# 매출 요약 보고서 설정
SUMMARY_REPORT_CONFIG = {
    "include_charts": True,       # 차트 포함 여부
    "include_trends": True,       # 트렌드 분석 포함 여부
    "include_recommendations": True,  # 추천사항 포함 여부
    "max_top_items": 10,         # 상위 아이템 최대 개수
}

# HTTP 상태 코드
HTTP_STATUS_CODES = {
    200: "성공",
    400: "잘못된 요청",
    401: "인증 실패", 
    403: "접근 권한 없음",
    404: "리소스를 찾을 수 없음",
    429: "요청 횟수 제한 초과",
    500: "서버 내부 오류",
    503: "서비스 이용 불가"
}

# 로깅 메시지 이모지
LOG_EMOJIS = {
    "SUCCESS": "✅",
    "ERROR": "❌", 
    "WARNING": "⚠️",
    "INFO": "ℹ️",
    "PROCESSING": "🔄",
    "REVENUE": "💰",
    "CALENDAR": "📅",
    "CHART": "📊",
    "SUMMARY": "📋"
}