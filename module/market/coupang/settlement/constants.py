#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈 상수 정의
"""

# API 엔드포인트
SETTLEMENT_HISTORIES_API_PATH = "/v2/providers/marketplace_openapi/apis/api/v1/settlement-histories"

# 정산 유형
SETTLEMENT_TYPE = {
    "MONTHLY": "월 정산 내역",
    "WEEKLY": "주 정산 내역",
    "DAILY": "일 정산 내역",
    "ADDITIONAL": "추가 지급",
    "RESERVE": "최종액 지급"
}

# 지급 상태
SETTLEMENT_STATUS = {
    "DONE": "지급 완료",
    "SUBJECT": "지급 예정"
}

# 타임아웃 설정
DEFAULT_TIMEOUT_SECONDS = 30
EXTENDED_TIMEOUT_SECONDS = 60

# 에러 메시지
ERROR_MESSAGES = {
    # 기본 검증 오류
    "INVALID_VENDOR_ID": "올바른 판매자 ID를 입력해주세요. (A로 시작하는 9자리)",
    "INVALID_YEAR_MONTH_FORMAT": "매출인식월 형식이 올바르지 않습니다. (YYYY-MM)",
    "INVALID_YEAR_MONTH_RANGE": "해당월까지만 조회할 수 있습니다.",
    "YEAR_MONTH_TOO_OLD": "너무 오래된 매출인식월입니다.",
    "YEAR_MONTH_FUTURE": "미래의 매출인식월은 조회할 수 없습니다.",
    
    # API 호출 오류
    "API_REQUEST_FAILED": "지급내역 조회 API 호출에 실패했습니다.",
    "API_RESPONSE_INVALID": "API 응답 형식이 올바르지 않습니다.",
    "API_TIMEOUT": "API 호출 시간이 초과되었습니다.",
    "API_RATE_LIMIT": "API 호출 횟수 제한에 도달했습니다.",
    
    # 데이터 처리 오류
    "EMPTY_RESPONSE": "조회된 지급내역 데이터가 없습니다.",
    "INVALID_SETTLEMENT_DATA": "지급내역 데이터 형식이 올바르지 않습니다.",
    "CALCULATION_ERROR": "지급내역 계산 중 오류가 발생했습니다.",
    
    # 환경 설정 오류
    "MISSING_CREDENTIALS": "쿠팡 API 인증 정보가 설정되지 않았습니다.",
    "INVALID_CONFIG": "설정 파일이 올바르지 않습니다.",
}

# 성공 메시지
SUCCESS_MESSAGES = {
    "SETTLEMENT_HISTORY_SUCCESS": "지급내역 조회 성공",
    "SETTLEMENT_SUMMARY_SUCCESS": "지급내역 요약 조회 성공",
    "SETTLEMENT_CALCULATION_SUCCESS": "지급내역 계산 완료",
}

# 검증 정규식 패턴
VENDOR_ID_PATTERN = r"^A\d{8}$"  # A로 시작하는 9자리
YEAR_MONTH_PATTERN = r"^\d{4}-\d{2}$"  # YYYY-MM

# 지급내역 계산용 필드
SETTLEMENT_CALCULATION_FIELDS = [
    "total_sale",               # 총판매액
    "service_fee",              # 판매수수료
    "settlement_target_amount", # 정산대상액
    "settlement_amount",        # 지급액
    "last_amount",              # 최종액
    "final_amount",            # 최종지급액
    "pending_released_amount",  # 보류(해제)금액
]

# 지급내역 필수 필드
REQUIRED_SETTLEMENT_FIELDS = [
    "settlement_type",                    # 정산유형
    "settlement_date",                   # 정산(예정)일
    "revenue_recognition_year_month",    # 매출인식월
    "total_sale",                       # 총판매액
    "service_fee",                      # 판매수수료
    "settlement_target_amount",         # 정산대상액
    "settlement_amount",                # 지급액
    "final_amount",                     # 최종지급액
    "status"                           # 지급 상태
]

# 차감 항목 필드
DEDUCTION_FIELDS = [
    "dedicated_delivery_amount",    # 전담택배비
    "seller_service_fee",          # 판매자서비스이용료
    "courantee_fee",               # 쿠런티이용료
    "courantee_customer_reward",   # 쿠런티보상금
    "deduction_amount",            # 정산차감
    "debt_of_last_week",           # 전주채권
    "seller_discount_coupon",      # 판매자 할인쿠폰(즉시할인)
    "downloadable_coupon",         # 판매자 할인쿠폰(다운로드)
    "store_fee_discount"           # 스토어이용료할인금액
]

# 지급내역 분석 관련 상수
SETTLEMENT_ANALYSIS_CATEGORIES = {
    "HIGH_SETTLEMENT": "고지급",      # 평균 지급액의 2배 이상
    "MEDIUM_SETTLEMENT": "중지급",    # 평균 지급액의 0.5~2배
    "LOW_SETTLEMENT": "저지급",       # 평균 지급액의 0.5배 미만
}

# 경고 임계값
WARNING_THRESHOLDS = {
    "HIGH_SERVICE_FEE_RATIO": 20,    # 판매수수료 비율 20% 이상 시 경고
    "HIGH_DEDUCTION_RATIO": 10,      # 차감액 비율 10% 이상 시 경고
    "LOW_SETTLEMENT_RATIO": 0.5,     # 정산액이 총판매액의 50% 미만 시 경고
}

# 날짜 형식
YEAR_MONTH_FORMAT = "%Y-%m"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# 기본 설정값
DEFAULT_ANALYSIS_MONTHS = 3      # 기본 분석 개월 수
MAX_ANALYSIS_MONTHS = 12        # 최대 분석 개월 수

# 지급내역 요약 보고서 설정
SUMMARY_REPORT_CONFIG = {
    "include_charts": True,       # 차트 포함 여부
    "include_trends": True,       # 트렌드 분석 포함 여부
    "include_recommendations": True,  # 추천사항 포함 여부
    "max_months": 12,            # 최대 분석 개월 수
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
    "SETTLEMENT": "💳",
    "CALENDAR": "📅",
    "CHART": "📊",
    "SUMMARY": "📋",
    "BANK": "🏦"
}

# 은행 코드 매핑 (일부)
BANK_CODES = {
    "001": "한국은행",
    "002": "산업은행",
    "003": "기업은행",
    "004": "국민은행",
    "005": "하나은행",
    "007": "수협중앙회",
    "008": "수출입은행",
    "011": "농협은행",
    "012": "농협회원조합",
    "020": "우리은행",
    "023": "SC제일은행",
    "027": "한국씨티은행",
    "031": "대구은행",
    "032": "부산은행",
    "034": "광주은행",
    "035": "제주은행",
    "037": "전북은행",
    "039": "경남은행",
    "045": "새마을금고",
    "048": "신협중앙회",
    "050": "상호저축은행",
    "052": "모간스탠리은행",
    "054": "HSBC은행",
    "055": "도이치은행",
    "057": "제이피모간체이스은행",
    "058": "미즈호은행",
    "059": "미쓰비시도쿄UFJ은행",
    "060": "BOA은행",
    "061": "비엔피파리바은행",
    "062": "중국공상은행",
    "063": "중국은행",
    "064": "산림조합중앙회",
    "065": "대화은행",
    "071": "우체국",
    "076": "신용보증기금",
    "077": "기술보증기금",
    "081": "하나은행",
    "088": "신한은행",
    "089": "케이뱅크",
    "090": "카카오뱅크",
    "092": "토스뱅크"
}