# 발주서 단건 조회 (orderId)

`orderId`를 이용하여 발주서 단건을 조회하는 API입니다.

**중요 사항:**
- 결제완료 상태에서 고객이 배송지를 변경할 수 있으므로, **상품준비중** 처리 이후에 꼭 본 API를 통해 배송지 정보(`receiver`)가 변경되었는지 확인 및 업데이트해야 합니다.
- 출고 전, `sellerProductName + sellerProductItemName`과 `vendorItemName`의 정보가 일치하는지 반드시 확인해야 합니다.

---

## 요청 명세

- **Path**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/{orderId}/ordersheets`
- **API Name**: `GET_ORDERSHEET_BY_ORDERID`

### Path Segment Parameters

| Name     | Required | Type   | Description                                                                 |
|----------|----------|--------|-----------------------------------------------------------------------------|
| `vendorId` | O        | String | 업체코드 (쿠팡에서 발급한 고유 코드)                                        |
| `orderId`  | O        | Number | 주문번호 (발주서 목록 조회 API를 통해 획득)                                 |

### Request Body

- Not required.

---

## 응답 명세

응답 `data` 필드는 주문 정보를 담고 있는 객체의 배열입니다. 주요 필드는 다음과 같습니다:

- `shipmentBoxId`: 배송번호
- `orderId`: 주문번호
- `orderedAt`: 주문일시
- `orderer`: 주문자 정보 (이름, 안심번호 등)
- `paidAt`: 결제일시
- `status`: 발주서 상태 (e.g., `ACCEPT`, `FINAL_DELIVERY`)
- `receiver`: 수취인 정보 (이름, 주소, 안심번호 등)
- `orderItems`: 주문 상품 목록 (상품명, 수량, 가격, 할인 정보 등)
- `deliveryCompanyName`: 택배사
- `invoiceNumber`: 운송장번호

### Response Example

```json
{
  "code": 200,
  "message": "OK",
  "data": [
    {
      "shipmentBoxId": 642538976401429,
      "orderId": 9100041863244,
      "orderedAt": "2024-04-08T22:54:46",
      "orderer": {
        "name": "이*주",
        "safeNumber": "0502-***6-3501"
      },
      "paidAt": "2024-04-08T22:54:56",
      "status": "FINAL_DELIVERY",
      "receiver": {
        "name": "이*주",
        "addr1": "***",
        "addr2": "***"
      },
      "orderItems": [
        {
          "vendorItemId": 85872453655,
          "vendorItemName": "신서리티 델타 구운 캐슈넛, 5개, 160g",
          "shippingCount": 1,
          "salesPrice": 41000
        }
      ]
    }
  ]
}
```

---

## 오류 코드

| HTTP 상태 코드 | 오류 메시지                             |
|----------------|-----------------------------------------|
| 400            | 해당 주문이 취소 또는 반품 되었습니다.  |
| 400            | 유효하지 않은 주문번호 입니다.          |
| 400            | 다른 판매자의 주문을 조회할 수 없습니다.|
