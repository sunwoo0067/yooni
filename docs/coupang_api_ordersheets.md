# Coupang Open API: 발주서 목록 조회 (일단위 페이징)

## 개요
발주서 목록을 하루 단위 페이징 형태로 조회합니다.

- **Path**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets`
- **Example Endpoint**: `https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/A00012345/ordersheets?createdAtFrom=2017-10-10&createdAtTo=2017-10-11&maxPerPage=2&status=INSTRUCT`

### 주요 특징
- **배송지 변경**: 결제완료 상태에서 고객이 배송지를 변경할 수 있으므로, 상품준비중 처리 이후 배송지 정보("receiver") 재확인이 필요합니다. (발주서 단건 조회 API 사용 권장)
- **타임아웃**: 주문 건이 많을 경우 타임아웃이 발생할 수 있습니다.
- **반품/취소**: 반품완료건은 이 API로 조회 불가하며, '반품/취소 요청 목록 조회' API를 사용해야 합니다.
- **상품 정보 확인**: 출고 전, "sellerProductName + sellerProductItemName"과 "vendorItemName"의 정보가 일치하는지 반드시 확인해야 합니다.

---

## Request Parameters

### Path Segment Parameter
| Name     | Required | Type   | Description                                        |
|----------|----------|--------|----------------------------------------------------|
| vendorId | O        | String | 판매자 ID (쿠팡에서 발급한 고유 코드, 예: A00012345) |

### Query String Parameter
| Name          | Required | Type   | Description                                                                                                                              |
|---------------|----------|--------|------------------------------------------------------------------------------------------------------------------------------------------|
| createdAtFrom | O        | String | 검색 시작일시 (yyyy-mm-dd, 예: 2018-07-01)                                                                                                 |
| createdAtTo   | O        | String | 검색 종료일시 (yyyy-mm-dd, 예: 2018-07-31). 최대 31일까지 조회 가능.                                                                        |
| status        | O        | String | 발주서 상태 (`ACCEPT`, `INSTRUCT`, `DEPARTURE`, `DELIVERING`, `FINAL_DELIVERY`, `NONE_TRACKING`)                                           |
| nextToken     |          | String | 다음 페이지 조회를 위한 token 값. 첫 페이지 조회 시에는 불필요.                                                                          |
| maxPerPage    |          | Number | 페이지당 최대 조회 요청 값. (default = 50)                                                                                               |
| searchType    |          | String | `timeFrame`으로 설정 시 '발주서 목록 조회(분단위 전체)'로 수행됨. 그 외에는 '일단위 페이징'으로 수행.                                         |

---

## Response Message

### 기본 구조
```json
{
  "code": 200,
  "message": "OK",
  "data": [ ... ],
  "nextToken": "448537989"
}
```

### `data` 객체 필드
| Name                  | Type    | Description                                                                                                                                                           |
|-----------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| shipmentBoxId         | Number  | 배송번호(묶음배송번호)                                                                                                                                                |
| orderId               | Number  | 주문번호                                                                                                                                                              |
| orderedAt             | String  | 주문일시 (yyyy-MM-dd'T'HH:mm:ss)                                                                                                                                      |
| orderer               | Object  | 주문자 정보 (`name`, `email`, `safeNumber`)                                                                                                                           |
| paidAt                | String  | 결제일시 (yyyy-MM-dd'T'HH:mm:ss)                                                                                                                                      |
| status                | String  | 발주서 상태                                                                                                                                                           |
| shippingPrice         | Number  | 배송비                                                                                                                                                                |
| remotePrice           | Number  | 도서산간배송비                                                                                                                                                        |
| parcelPrintMessage    | String  | 배송메세지                                                                                                                                                            |
| receiver              | Object  | 수취인 정보 (`name`, `safeNumber`, `addr1`, `addr2`, `postCode`)                                                                                                        |
| orderItems            | Array   | 주문 상품 목록 (상세 내용은 아래 `orderItems` 객체 필드 참조)                                                                                                         |
| deliveryCompanyName   | String  | 택배사 (예: CJ 대한통운, 한진택배)                                                                                                                                    |
| invoiceNumber         | String  | 운송장번호                                                                                                                                                            |
| inTrasitDateTime      | String  | 출고일(발송일) (yyyy-MM-dd HH:mm:ss)                                                                                                                                  |
| deliveredDate         | String  | 배송완료일 (yyyy-MM-dd HH:mm:ss)                                                                                                                                      |
| nextToken             | String  | 다음 페이지 요청 시 필요한 token 값. 마지막 페이지는 빈 값.                                                                                                           |

### `orderItems` 객체 필드
| Name                  | Type    | Description                                                                                                                                                           |
|-----------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| vendorItemId          | Number  | 옵션ID                                                                                                                                                                |
| vendorItemName        | String  | 노출상품명                                                                                                                                                            |
| shippingCount         | Number  | 주문 수량. 발주 가능 수량 = `shippingCount` - (`holdCountForCancel` + `cancelCount`)                                                                                   |
| salesPrice            | Number  | 개당 상품 가격                                                                                                                                                        |
| orderPrice            | Number  | 결제 가격 (`salesPrice` * `shippingCount`)                                                                                                                            |
| discountPrice         | Number  | 총 할인 가격                                                                                                                                                          |
| sellerProductId       | Number  | 등록상품ID                                                                                                                                                            |
| sellerProductName     | String  | 등록상품명                                                                                                                                                            |
| sellerProductItemName | String  | 등록옵션명                                                                                                                                                            |
| canceled              | Boolean | 주문 취소 여부                                                                                                                                                        |

---

## Error Spec

| HTTP 상태 코드 | 오류 메시지                             | 해결 방법                                      |
|----------------|-----------------------------------------|------------------------------------------------|
| 400            | Invalid vendor ID                       | 올바른 판매자 ID(vendorId)를 입력했는지 확인.  |
| 400            | endTime-startTime range should less than31. | 조회 기간이 31일 이내인지 확인.                |
