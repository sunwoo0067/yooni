#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 상수 정의
"""

# API 엔드포인트
EXCHANGE_REQUESTS_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/exchangeRequests"
EXCHANGE_RECEIVE_CONFIRMATION_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/exchangeRequests/{}/receiveConfirmation"
EXCHANGE_REJECTION_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/exchangeRequests/{}/rejection"
EXCHANGE_INVOICE_UPLOAD_API_PATH = "/v2/providers/openapi/apis/api/v4/vendors/{}/exchangeRequests/{}/invoices"

# 교환 상태
EXCHANGE_STATUS = {
    "RECEIPT": "접수",
    "PROGRESS": "진행", 
    "SUCCESS": "완료",
    "REJECT": "불가",
    "CANCEL": "철회"
}

# 주문 배송 상태
EXCHANGE_ORDER_DELIVERY_STATUS = {
    "ACCEPT": "결재완료",
    "INSTRUCT": "상품준비중",
    "DEPARTURE": "배송지시", 
    "DELIVERING": "배송중",
    "FINAL_DELIVERY": "배송완료",
    "NONE_TRACKING": "업체 직접 배송(배송 연동 미적용), 추적불가"
}

# 접수 경로
EXCHANGE_REFER_TYPE = {
    "VENDOR": "벤더",
    "CS_CENTER": "CS",
    "WEB_PC": "웹 PC", 
    "WEB_MOBILE": "웹 모바일"
}

# 귀책 (배송비 부담 주체)
EXCHANGE_FAULT_TYPE = {
    "COUPANG": "쿠팡과실",
    "VENDOR": "업체과실",
    "CUSTOMER": "고객과실",
    "WMS": "물류과실",
    "GENERAL": "일반"
}

# 등록자/수정자 유형
EXCHANGE_CREATED_BY_TYPE = {
    "CUSTOMER": "고객",
    "COUNSELOR": "상담사", 
    "COUPANG": "내부직원",
    "VENDOR": "업체",
    "ETC": "기타",
    "TRACKING": "배송추적"
}

# 배송 상태
EXCHANGE_DELIVERY_STATUS = {
    "BeforeDirection": "배송연동 전",
    "CompleteDirection": "배송연동",
    "Delivering": "배송중",
    "CompleteDelivery": "배송완료",
    "DirectionFail": "배송연동실패",
    "VendorDirect": "업체직송",
    "Fail": "배송실패",
    "Withdraw": "교환배송철회",
    "NoneData": "정보없음"
}

# 회수 상태
EXCHANGE_COLLECT_STATUS = {
    "BeforeDirection": "회수연동 전",
    "CompleteDirection": "회수연동",
    "Delivering": "회수중",
    "CompleteCollect": "업체전달완료",
    "DirectionFail": "회수연동실패",
    "Fail": "회수실패", 
    "Withdraw": "교환회수철회",
    "NoCollect": "회수 불필요",
    "NoneData": "정보없음"
}

# 택배사 코드 (주요)
DELIVERY_COMPANY_CODES = {
    "CJGLS": "CJ대한통운",
    "EPOST": "우체국택배",
    "KDEXP": "경동택배",
    "HANJIN": "한진택배",
    "LOTTE": "롯데택배"
}

# 교환 거부 코드
EXCHANGE_REJECT_CODES = {
    "SOLDOUT": "교환할수있지만 아이템이 매진되였습니다",
    "WITHDRAW": "교환요청이 철회되였습니다 (고객님이 요청함)"
}

# VOC 코드 (교환/반품/취소 공통)
VOC_CODES = {
    # 고객 변심 / 실수
    "CHANGEMIND": {"text": "필요 없어짐 (단순 변심)", "fault": "CUS"},
    "NOLONGERNEED": {"text": "필요 없어짐", "fault": "CUS"},
    "DIFFERENTOPT": {"text": "색상/ 사이즈가 기대와 다름(같은 상품의 다른 옵션으로 교환)", "fault": "CUS"},
    "DONTLIKESIZECOLOR": {"text": "색상, 사이즈가 기대와 다름", "fault": "CUS"},
    "CHEAPER": {"text": "다른 사이트의 가격이 더 저렴함", "fault": "CUS"},
    "WRONGOPT": {"text": "상품의 옵션 선택을 잘못함", "fault": "CUS"},
    "DELIVERYLATER": {"text": "배송 예정일이 예상보다 늦음", "fault": "COM"},
    "WRONGADDRESS": {"text": "배송지 입력 실수", "fault": "CUS"},
    "REORDER": {"text": "상품을 추가하여 재주문", "fault": "CUS"},
    "OTHERS": {"text": "기타", "fault": "CUS"},
    "OTHERS_CHANGEMIND": {"text": "그외 (단순변심)", "fault": "CUS"},
    
    # 상품이 도착하지 않음
    "DELIVERYSTOP": {"text": "배송흐름이 멈춤", "fault": "COM"},
    "CARRIERLOST": {"text": "택배사 상품 분실", "fault": "COM"},
    "LOST": {"text": "배송주소 오배송(원인파악 불가 포함)", "fault": "COM"},
    "PARTIALMISS": {"text": "주문상품 중 일부가 배송되지 않음", "fault": "COM"},
    "COMPOMISS": {"text": "상품의 구성품, 부속품이 제대로 들어있지 않음", "fault": "COM"},
    "LATEDELIVERED": {"text": "상품이 늦게 배송됨", "fault": "COM"},
    "SKUOOSRESHIP": {"text": "SKU OOS로 나머지 상품 재출고", "fault": "COM"},
    "DELIVERYSTUCK": {"text": "배송 상태가 멈춰 있음", "fault": "COM"},
    "LIKELYDELAY": {"text": "배송지연이 예상됨", "fault": "COM"},
    
    # 상품에 문제가 있음
    "DAMAGED": {"text": "상품이 파손되어 배송됨", "fault": "COM"},
    "DEFECT": {"text": "상품 결함/기능에 이상이 있음", "fault": "COM"},
    "INACCURATE": {"text": "실제 상품이 상품 설명에 써있는 것과 다름", "fault": "COM"},
    "BOTHDAMAGED": {"text": "포장과 상품 모두 훼손됨", "fault": "COM"},
    "SHIPBOXOK": {"text": "포장은 괜찮으나 상품이 파손됨", "fault": "COM"},
    "UNABLEBOOK": {"text": "티켓 상품 예약 불가능", "fault": "COM"},
    "TICKETNOUSE": {"text": "티켓 상품 지점 휴업/ 폐점으로 사용 불가능", "fault": "COM"},
    "PRICEERROR": {"text": "잘못된 가격 기재", "fault": "COM"},
    "ITEMNAMEERR": {"text": "잘못된 상품명 기재", "fault": "COM"},
    "OTHERS_PRODUCT": {"text": "그외 (상품문제)", "fault": "COM"},
    
    # 다른 상품이 배송됨
    "WRONGDELIVERY": {"text": "내가 주문한 상품과 아예 다른 상품이 배송됨", "fault": "COM"},
    "WRONGSIZECOL": {"text": "내가 주문한 상품과 다른 색상/사이즈의 상품이 배송됨", "fault": "COM"},
    "OTHERS_DELIVERY": {"text": "그외 (배송문제)", "fault": "COM"},
    
    # 본사 / 업체 취소
    "OOSSELLER": {"text": "업체로부터 품절되었다고 연락 받음", "fault": "COM"},
    "UNUSEDTICKET": {"text": "티켓 상품의 미사용 환불 취소", "fault": "CUS"},
    "DUPLICATE": {"text": "Abusing 의심 중복구매 취소", "fault": "COM"},
    "SKUOOSCAN": {"text": "SKU OOS 취소", "fault": "COM"},
    
    # 시스템에러
    "SYSTEMERROR": {"text": "시스템 오류", "fault": "COU/COM"},
    "SYSTEMINFO_ERROR": {"text": "상품 정보가 잘못 노출됨(쿠팡 시스템 오류)", "fault": "COU"},
    "EXITERROR": {"text": "주문 이탈", "fault": "COU/COM"},
    "PAYERROR": {"text": "결제 오류", "fault": "COU/COM"},
    "PARTNERERROR": {"text": "제휴사이트 오류", "fault": "COU/COM"},
    "REGISTERROR": {"text": "쿠폰 등록 오류", "fault": "COU/COM"},
    "NOTPURCHASABLE": {"text": "구매 불가능", "fault": "COU/COM"}
}

# 날짜 형식 패턴
DATETIME_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'

# 벤더 ID 패턴  
VENDOR_ID_PATTERN = r'^A\d{8}$'

# 검색 기간 제한 (최대 7일)
MAX_DATE_RANGE_DAYS = 7

# 페이지당 최대 조회 수
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 10

# 에러 메시지
ERROR_MESSAGES = {
    "INVALID_VENDOR_ID": "올바른 판매자 ID(vendorId)를 입력했는지 확인합니다. 예) A00012345",
    "INVALID_DATETIME_FORMAT": "검색 시작일/종료일의 입력형식이 yyyy-MM-ddTHH:mm:ss 인지 확인합니다.",
    "DATE_RANGE_TOO_LONG": "조회기간이 7일 이하 인지 확인합니다.",
    "START_AFTER_END": "검색 종료일이 검색 시작일 보다 빠른 날짜로 설정 되었는지 확인합니다.",
    "INVALID_STATUS": "올바른 교환 상태를 입력해주세요.",
    "INVALID_ORDER_ID": "올바른 주문번호를 입력해주세요. Number 타입이어야 합니다.",
    "INVALID_MAX_PER_PAGE": f"페이지당 최대 조회 수는 1~{MAX_PER_PAGE} 사이여야 합니다.",
    "INVALID_EXCHANGE_ID": "올바른 교환 접수번호를 입력해주세요. Number 타입이어야 합니다.",
    "INVALID_REJECT_CODE": "교환거절코드는 SOLDOUT 또는 WITHDRAW만 입력할 수 있습니다.",
    "INVALID_DELIVERY_CODE": "올바른 택배사 코드를 입력해주세요.",
    "INVALID_INVOICE_NUMBER": "올바른 운송장번호를 입력해주세요.",
    "INVALID_SHIPMENT_BOX_ID": "올바른 배송번호를 입력해주세요. Number 타입이어야 합니다."
}