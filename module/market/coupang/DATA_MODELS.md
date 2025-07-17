# 쿠팡 파트너스 API 데이터 모델 스키마

## 개요
이 문서는 쿠팡 파트너스 API 통합 클라이언트의 모든 데이터 모델과 스키마를 정의합니다.

## 목차
- [공통 데이터 타입](#공통-데이터-타입)
- [CS 모듈 데이터 모델](#cs-모듈-데이터-모델)
- [Sales 모듈 데이터 모델](#sales-모듈-데이터-모델)
- [Settlement 모듈 데이터 모델](#settlement-모듈-데이터-모델)
- [Order 모듈 데이터 모델](#order-모듈-데이터-모델)
- [Product 모듈 데이터 모델](#product-모듈-데이터-모델)
- [Returns 모듈 데이터 모델](#returns-모듈-데이터-모델)
- [Exchange 모듈 데이터 모델](#exchange-모듈-데이터-모델)
- [API 응답 공통 구조](#api-응답-공통-구조)

---

## 공통 데이터 타입

### 날짜/시간 형식
```python
# 날짜 형식
DATE_FORMAT = "YYYY-MM-DD"  # 예: "2025-07-14"

# 날짜-시간 형식
DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss"  # 예: "2025-07-14 15:30:45"

# 년-월 형식 (지급내역용)
YEAR_MONTH_FORMAT = "YYYY-MM"  # 예: "2025-07"
```

### 페이징 공통 구조
```python
@dataclass
class PaginationInfo:
    current_page: int
    total_pages: int
    page_size: int
    total_elements: int
    has_next: bool
    has_previous: bool
```

### API 응답 기본 구조
```python
@dataclass
class BaseAPIResponse:
    success: bool
    message: str
    error_code: Optional[str] = None
    timestamp: str = None
```

---

## CS 모듈 데이터 모델

### 1. 온라인 고객문의 관련

#### InquirySearchParams (문의 검색 파라미터)
```python
@dataclass
class InquirySearchParams:
    vendor_id: str                    # 판매자 ID (필수)
    answered_type: str = "ALL"        # 답변 상태: ALL, ANSWERED, NOANSWER
    created_at_from: str = None       # 시작일 (YYYY-MM-DD)
    created_at_to: str = None         # 종료일 (YYYY-MM-DD)
    page_num: int = 1                 # 페이지 번호 (1부터 시작)
    page_size: int = 20               # 페이지 크기 (1~100)
    timeout: int = 30                 # 타임아웃 (초)
    extended_timeout: bool = False    # 확장 타임아웃 사용 여부
    
    def to_query_params(self) -> Dict[str, Any]:
        """쿼리 파라미터 딕셔너리로 변환"""
        params = {"vendorId": self.vendor_id}
        if self.answered_type:
            params["answeredType"] = self.answered_type
        if self.created_at_from:
            params["createdAtFrom"] = self.created_at_from
        if self.created_at_to:
            params["createdAtTo"] = self.created_at_to
        if self.page_num:
            params["pageNum"] = self.page_num
        if self.page_size:
            params["pageSize"] = self.page_size
        return params
```

#### CustomerInquiry (고객문의)
```python
@dataclass
class CustomerInquiry:
    inquiry_id: int                   # 문의 ID
    customer_id: str                  # 고객 ID
    vendor_id: str                    # 판매자 ID
    vendor_item_id: str               # 판매자 상품 ID
    product_name: str                 # 상품명
    inquiry_type: str                 # 문의 유형
    inquiry_status: str               # 문의 상태
    title: str                        # 문의 제목
    content: str                      # 문의 내용
    created_at: str                   # 작성일시
    answered_at: Optional[str] = None # 답변일시
    order_id: Optional[str] = None    # 주문 ID
    
    def get_inquiry_summary(self) -> Dict[str, Any]:
        """문의 요약 정보 반환"""
        return {
            "inquiry_id": self.inquiry_id,
            "customer_id": self.customer_id,
            "title": self.title,
            "type": self.inquiry_type,
            "status": self.inquiry_status,
            "created_at": self.created_at,
            "is_answered": self.answered_at is not None
        }
```

#### InquiryComment (문의 댓글)
```python
@dataclass
class InquiryComment:
    comment_id: int                   # 댓글 ID
    inquiry_id: int                   # 문의 ID
    content: str                      # 댓글 내용
    created_at: str                   # 작성일시
    created_by: str                   # 작성자
    comment_type: str                 # 댓글 유형 (CUSTOMER, VENDOR)
```

#### InquiryReplyRequest (문의 답변 요청)
```python
@dataclass
class InquiryReplyRequest:
    content: str                      # 답변 내용 (1~1000자)
    reply_by: str                     # 응답자 WING ID
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (API 요청용)"""
        return {
            "content": self.content,
            "replyBy": self.reply_by
        }
    
    def validate(self) -> bool:
        """답변 요청 유효성 검증"""
        return (
            1 <= len(self.content) <= 1000 and
            self.reply_by and len(self.reply_by) > 0
        )
```

#### InquiryReplyResponse (문의 답변 응답)
```python
@dataclass
class InquiryReplyResponse(BaseAPIResponse):
    inquiry_id: int                   # 문의 ID
    reply_id: int                     # 답변 ID
    content: str                      # 답변 내용
    replied_at: str                   # 답변일시
    replied_by: str                   # 답변자
```

### 2. 콜센터 문의 관련

#### CallCenterInquirySearchParams (콜센터 문의 검색 파라미터)
```python
@dataclass
class CallCenterInquirySearchParams:
    vendor_id: str                           # 판매자 ID (필수)
    partner_counseling_status: str = "NONE"  # 상담 상태: NONE, ANSWER, NO_ANSWER, TRANSFER
    created_at_from: str = None              # 시작일
    created_at_to: str = None                # 종료일
    page_num: int = 1                        # 페이지 번호
    page_size: int = 20                      # 페이지 크기
```

#### CallCenterInquiry (콜센터 문의)
```python
@dataclass
class CallCenterInquiry:
    inquiry_id: int                   # 문의 ID
    vendor_id: str                    # 판매자 ID
    customer_id: str                  # 고객 ID
    inquiry_type: str                 # 문의 유형
    inquiry_status: str               # 문의 상태
    partner_counseling_status: str    # 파트너 상담 상태
    title: str                        # 문의 제목
    content: str                      # 문의 내용
    created_at: str                   # 작성일시
    order_id: Optional[str] = None    # 주문 ID
    vendor_item_id: Optional[str] = None  # 판매자 상품 ID
    product_name: Optional[str] = None    # 상품명
```

#### CallCenterReply (콜센터 답변)
```python
@dataclass
class CallCenterReply:
    reply_id: int                     # 답변 ID
    inquiry_id: int                   # 문의 ID
    content: str                      # 답변 내용
    created_at: str                   # 작성일시
    created_by: str                   # 작성자
    parent_answer_id: Optional[int] = None  # 부모 답변 ID
```

#### CallCenterInquiryReplyRequest (콜센터 문의 답변 요청)
```python
@dataclass
class CallCenterInquiryReplyRequest:
    content: str                      # 답변 내용 (2~1000자)
    reply_by: str                     # 응답자 WING ID
    parent_answer_id: int             # 부모 이관글 ID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "replyBy": self.reply_by,
            "parentAnswerId": self.parent_answer_id
        }
```

---

## Sales 모듈 데이터 모델

### RevenueSearchParams (매출 검색 파라미터)
```python
@dataclass
class RevenueSearchParams:
    vendor_id: str                    # 판매자 ID (필수)
    recognition_date_from: str        # 매출 인식 시작일 (YYYY-MM-DD)
    recognition_date_to: str          # 매출 인식 종료일 (YYYY-MM-DD)
    max_per_page: int = 20            # 페이지당 최대 개수 (1~1000)
    token: Optional[str] = None       # 페이징 토큰
    
    def to_query_params(self) -> Dict[str, Any]:
        params = {
            "vendorId": self.vendor_id,
            "recognitionDateFrom": self.recognition_date_from,
            "recognitionDateTo": self.recognition_date_to,
            "maxPerPage": self.max_per_page
        }
        if self.token:
            params["token"] = self.token
        return params
    
    def validate_date_range(self) -> bool:
        """날짜 범위 유효성 검증 (최대 31일)"""
        from datetime import datetime
        start = datetime.strptime(self.recognition_date_from, '%Y-%m-%d')
        end = datetime.strptime(self.recognition_date_to, '%Y-%m-%d')
        return (end - start).days <= 31
```

### RevenueItem (매출 항목)
```python
@dataclass
class RevenueItem:
    order_id: str                     # 주문 ID
    product_id: str                   # 상품 ID
    vendor_item_id: str               # 판매자 상품 ID
    product_name: str                 # 상품명
    order_date: str                   # 주문일
    recognition_date: str             # 매출 인식일
    sale_price: int                   # 판매가
    quantity: int                     # 수량
    commission_rate: float            # 수수료율 (%)
    commission_fee: int               # 수수료
    net_revenue: int                  # 순 매출
    sale_type: str                    # 판매 유형
    tax_type: str                     # 세금 유형
    
    def calculate_total_revenue(self) -> int:
        """총 매출 계산"""
        return self.sale_price * self.quantity
    
    def calculate_profit_margin(self) -> float:
        """수익률 계산"""
        total_revenue = self.calculate_total_revenue()
        if total_revenue == 0:
            return 0.0
        return (self.net_revenue / total_revenue) * 100
```

### DeliveryFee (배송비)
```python
@dataclass
class DeliveryFee:
    delivery_fee: int                 # 배송비
    return_delivery_fee: int          # 반품 배송비
    remote_area_delivery_fee: int     # 도서산간 배송비
```

### RevenueHistory (매출 내역)
```python
@dataclass
class RevenueHistory:
    revenue_items: List[RevenueItem]  # 매출 항목 리스트
    delivery_fee: DeliveryFee         # 배송비 정보
    total_count: int                  # 전체 건수
    
    def get_total_revenue(self) -> int:
        """총 매출 합계"""
        return sum(item.calculate_total_revenue() for item in self.revenue_items)
    
    def get_total_commission(self) -> int:
        """총 수수료 합계"""
        return sum(item.commission_fee for item in self.revenue_items)
    
    def get_total_net_revenue(self) -> int:
        """총 순 매출 합계"""
        return sum(item.net_revenue for item in self.revenue_items)
    
    def get_revenue_by_product(self) -> Dict[str, int]:
        """상품별 매출 집계"""
        product_revenue = {}
        for item in self.revenue_items:
            if item.product_name not in product_revenue:
                product_revenue[item.product_name] = 0
            product_revenue[item.product_name] += item.calculate_total_revenue()
        return product_revenue
```

### RevenueHistoryResponse (매출 내역 응답)
```python
@dataclass
class RevenueHistoryResponse(BaseAPIResponse):
    data: RevenueHistory              # 매출 내역 데이터
    next_token: Optional[str] = None  # 다음 페이지 토큰
    has_more: bool = False            # 추가 데이터 존재 여부
```

---

## Settlement 모듈 데이터 모델

### SettlementSearchParams (지급내역 검색 파라미터)
```python
@dataclass
class SettlementSearchParams:
    revenue_recognition_year_month: str  # 매출 인식 년월 (YYYY-MM)
    
    def to_query_params(self) -> Dict[str, Any]:
        return {
            "revenueRecognitionYearMonth": self.revenue_recognition_year_month
        }
    
    def validate_year_month(self) -> bool:
        """년월 형식 유효성 검증"""
        import re
        pattern = r'^\d{4}-\d{2}$'
        return bool(re.match(pattern, self.revenue_recognition_year_month))
```

### SettlementHistory (지급내역)
```python
@dataclass
class SettlementHistory:
    settlement_date: str              # 지급일
    settlement_type: str              # 지급 유형 (MONTHLY, WEEKLY, DAILY, ADDITIONAL, RESERVE)
    payment_status: str               # 지급 상태 (DONE, SUBJECT)
    settlement_amount: int            # 지급금액
    service_fee: int                  # 서비스 수수료
    vat: int                          # 부가세
    bank_name: str                    # 은행명
    account_number: str               # 계좌번호 (마스킹)
    revenue_recognition_year_month: str  # 매출 인식 년월
    
    def get_net_amount(self) -> int:
        """실제 수령액 (지급금액 - 수수료 - 부가세)"""
        return self.settlement_amount - self.service_fee - self.vat
    
    def get_fee_rate(self) -> float:
        """수수료율 계산"""
        if self.settlement_amount == 0:
            return 0.0
        return (self.service_fee / self.settlement_amount) * 100
    
    def get_masked_account(self) -> str:
        """마스킹된 계좌번호 반환"""
        if len(self.account_number) <= 4:
            return self.account_number
        return self.account_number[:2] + '*' * (len(self.account_number) - 4) + self.account_number[-2:]
    
    def is_paid(self) -> bool:
        """지급 완료 여부"""
        return self.payment_status == "DONE"
```

### SettlementHistoryResponse (지급내역 응답)
```python
@dataclass
class SettlementHistoryResponse(BaseAPIResponse):
    data: List[SettlementHistory]     # 지급내역 리스트
    total_count: int                  # 전체 건수
    year_month: str                   # 조회 년월
    
    def get_total_settlement_amount(self) -> int:
        """총 지급금액 합계"""
        return sum(item.settlement_amount for item in self.data)
    
    def get_total_service_fee(self) -> int:
        """총 서비스 수수료 합계"""
        return sum(item.service_fee for item in self.data)
    
    def get_settlements_by_type(self) -> Dict[str, List[SettlementHistory]]:
        """지급 유형별 분류"""
        settlements_by_type = {}
        for settlement in self.data:
            if settlement.settlement_type not in settlements_by_type:
                settlements_by_type[settlement.settlement_type] = []
            settlements_by_type[settlement.settlement_type].append(settlement)
        return settlements_by_type
```

---

## Order 모듈 데이터 모델

### OrderSheetSearchParams (주문서 검색 파라미터)
```python
@dataclass
class OrderSheetSearchParams:
    vendor_id: str                    # 판매자 ID
    created_at_from: str              # 시작일
    created_at_to: str                # 종료일
    status: Optional[str] = None      # 주문 상태
    page_num: int = 1                 # 페이지 번호
    page_size: int = 50               # 페이지 크기
```

### OrderSheetTimeFrameParams (주문서 시간대 파라미터)
```python
@dataclass
class OrderSheetTimeFrameParams:
    hours: int = 24                   # 조회 시간 (시간)
    
    def to_query_params(self) -> Dict[str, Any]:
        return {"hours": self.hours}
```

### Orderer (주문자 정보)
```python
@dataclass
class Orderer:
    name: str                         # 주문자명
    phone: str                        # 전화번호
    email: str                        # 이메일
    orderer_id: str                   # 주문자 ID
```

### Receiver (수령자 정보)
```python
@dataclass
class Receiver:
    name: str                         # 수령자명
    phone: str                        # 전화번호
    address1: str                     # 주소1
    address2: str                     # 주소2
    postcode: str                     # 우편번호
    receiver_id: str                  # 수령자 ID
```

### OrderItem (주문 상품)
```python
@dataclass
class OrderItem:
    vendor_item_id: str               # 판매자 상품 ID
    product_name: str                 # 상품명
    option_name: str                  # 옵션명
    quantity: int                     # 수량
    unit_price: int                   # 단가
    total_price: int                  # 총 가격
    status: str                       # 상품 상태
    shipment_box_id: Optional[str] = None  # 출고박스 ID
```

### OrderSheet (주문서)
```python
@dataclass
class OrderSheet:
    order_id: str                     # 주문 ID
    vendor_id: str                    # 판매자 ID
    order_date: str                   # 주문일
    status: str                       # 주문 상태
    orderer: Orderer                  # 주문자 정보
    receiver: Receiver                # 수령자 정보
    order_items: List[OrderItem]      # 주문 상품 리스트
    total_amount: int                 # 총 주문금액
    delivery_charge: int              # 배송비
    
    def get_total_quantity(self) -> int:
        """총 주문 수량"""
        return sum(item.quantity for item in self.order_items)
    
    def get_product_names(self) -> List[str]:
        """주문 상품명 리스트"""
        return [item.product_name for item in self.order_items]
```

---

## Product 모듈 데이터 모델

### ProductImage (상품 이미지)
```python
@dataclass
class ProductImage:
    image_url: str                    # 이미지 URL
    image_type: str                   # 이미지 유형 (REPRESENTATION, DETAIL, ADDITIONAL)
    sequence: int                     # 이미지 순서
    
    def is_main_image(self) -> bool:
        """대표 이미지 여부"""
        return self.image_type == "REPRESENTATION" and self.sequence == 1
```

### ProductAttribute (상품 속성)
```python
@dataclass
class ProductAttribute:
    attribute_type_id: str            # 속성 유형 ID
    attribute_value: str              # 속성 값
    attribute_name: str               # 속성명
```

### ProductItem (상품 옵션)
```python
@dataclass
class ProductItem:
    vendor_item_id: str               # 판매자 상품 ID
    item_name: str                    # 상품명
    original_price: int               # 정가
    sale_price: int                   # 판매가
    quantity: int                     # 재고 수량
    maximum_buy_count: int            # 최대 구매 수량
    status: str                       # 상품 상태
    
    def get_discount_rate(self) -> float:
        """할인율 계산"""
        if self.original_price == 0:
            return 0.0
        return ((self.original_price - self.sale_price) / self.original_price) * 100
```

### ProductRequest (상품 등록 요청)
```python
@dataclass
class ProductRequest:
    category_id: str                  # 카테고리 ID
    product_name: str                 # 상품명
    vendor_id: str                    # 판매자 ID
    display_category_code: str        # 진열 카테고리 코드
    images: List[ProductImage]        # 상품 이미지 리스트
    attributes: List[ProductAttribute] # 상품 속성 리스트
    items: List[ProductItem]          # 상품 옵션 리스트
    
    def validate(self) -> bool:
        """상품 등록 요청 유효성 검증"""
        return (
            bool(self.category_id) and
            bool(self.product_name) and
            bool(self.vendor_id) and
            len(self.images) > 0 and
            len(self.items) > 0
        )
```

---

## Returns 모듈 데이터 모델

### ReturnRequestSearchParams (반품 요청 검색 파라미터)
```python
@dataclass
class ReturnRequestSearchParams:
    vendor_id: str                    # 판매자 ID
    created_at_from: str              # 시작일
    created_at_to: str                # 종료일
    status: Optional[str] = None      # 반품 상태
    receipt_status: Optional[str] = None  # 접수 상태
    
    def to_query_params(self) -> Dict[str, Any]:
        params = {
            "vendorId": self.vendor_id,
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to
        }
        if self.status:
            params["status"] = self.status
        if self.receipt_status:
            params["receiptStatus"] = self.receipt_status
        return params
```

### ReturnItem (반품 상품)
```python
@dataclass
class ReturnItem:
    vendor_item_id: str               # 판매자 상품 ID
    product_name: str                 # 상품명
    option_name: str                  # 옵션명
    quantity: int                     # 반품 수량
    unit_price: int                   # 단가
    return_reason: str                # 반품 사유
    fault_by: str                     # 귀책사유 (CUSTOMER, VENDOR)
```

### ReturnRequest (반품 요청)
```python
@dataclass
class ReturnRequest:
    return_id: str                    # 반품 ID
    order_id: str                     # 주문 ID
    vendor_id: str                    # 판매자 ID
    return_type: str                  # 반품 유형
    return_status: str                # 반품 상태
    receipt_status: str               # 접수 상태
    created_at: str                   # 생성일시
    return_items: List[ReturnItem]    # 반품 상품 리스트
    total_return_amount: int          # 총 반품금액
    
    def get_total_quantity(self) -> int:
        """총 반품 수량"""
        return sum(item.quantity for item in self.return_items)
    
    def is_customer_fault(self) -> bool:
        """고객 귀책 여부"""
        return any(item.fault_by == "CUSTOMER" for item in self.return_items)
```

---

## Exchange 모듈 데이터 모델

### ExchangeRequestSearchParams (교환 요청 검색 파라미터)
```python
@dataclass
class ExchangeRequestSearchParams:
    vendor_id: str                    # 판매자 ID
    created_at_from: str              # 시작일
    created_at_to: str                # 종료일
    status: Optional[str] = None      # 교환 상태
    
    def to_query_params(self) -> Dict[str, Any]:
        params = {
            "vendorId": self.vendor_id,
            "createdAtFrom": self.created_at_from,
            "createdAtTo": self.created_at_to
        }
        if self.status:
            params["status"] = self.status
        return params
```

### ExchangeItem (교환 상품)
```python
@dataclass
class ExchangeItem:
    vendor_item_id: str               # 판매자 상품 ID
    product_name: str                 # 상품명
    option_name: str                  # 옵션명
    quantity: int                     # 교환 수량
    unit_price: int                   # 단가
    exchange_reason: str              # 교환 사유
    fault_type: str                   # 귀책 유형
```

### ExchangeAddress (교환 주소)
```python
@dataclass
class ExchangeAddress:
    name: str                         # 수령자명
    phone: str                        # 전화번호
    address1: str                     # 주소1
    address2: str                     # 주소2
    postcode: str                     # 우편번호
```

### ExchangeRequest (교환 요청)
```python
@dataclass
class ExchangeRequest:
    exchange_id: str                  # 교환 ID
    order_id: str                     # 주문 ID
    vendor_id: str                    # 판매자 ID
    exchange_status: str              # 교환 상태
    delivery_status: str              # 배송 상태
    created_at: str                   # 생성일시
    exchange_items: List[ExchangeItem] # 교환 상품 리스트
    exchange_address: ExchangeAddress  # 교환 주소
    
    def get_total_quantity(self) -> int:
        """총 교환 수량"""
        return sum(item.quantity for item in self.exchange_items)
    
    def get_exchange_reasons(self) -> List[str]:
        """교환 사유 리스트"""
        return [item.exchange_reason for item in self.exchange_items]
```

---

## API 응답 공통 구조

### 성공 응답 구조
```json
{
  "code": "SUCCESS",
  "message": "성공",
  "data": {
    // 실제 데이터
  }
}
```

### 에러 응답 구조
```json
{
  "code": "ERROR_CODE",
  "message": "에러 메시지",
  "data": null
}
```

### 페이징 응답 구조
```json
{
  "code": "SUCCESS",
  "message": "성공",
  "data": {
    "content": [
      // 데이터 배열
    ],
    "page": {
      "current": 1,
      "size": 20,
      "total_pages": 10,
      "total_elements": 200,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

---

## 데이터 검증 규칙

### 공통 검증 규칙
- 모든 ID 필드는 빈 문자열이 아니어야 함
- 날짜 형식은 정확한 형식을 따라야 함
- 페이지 번호는 1 이상이어야 함
- 금액 필드는 0 이상이어야 함

### 모듈별 특화 검증
- **CS**: 답변 내용은 1~1000자, WING ID는 필수
- **Sales**: 날짜 범위는 최대 31일
- **Settlement**: 년월 형식은 YYYY-MM
- **Order**: 시간 범위는 최대 168시간(7일)

이 데이터 모델 스키마는 모든 API 클라이언트가 일관된 데이터 구조를 사용하도록 보장하며, 타입 안정성과 데이터 무결성을 제공합니다.