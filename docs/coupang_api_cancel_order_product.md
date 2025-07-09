# 주문 상품 취소 처리 (CANCEL_ORDER_PROCESSING)

[결제완료] 또는 [상품준비중] 상태에 있는 상품을 취소하기 위한 API 입니다. (나머지 상태에 적용 시 에러 발생)
- **[결제완료]** 상태에 있는 상품에 대해서는 즉시 취소로 작동합니다.
- **[상품준비중]** 상태의 상품에 대해서는 출고중지를 시킵니다.

하나의 주문번호 안에 서로 다른 묶음배송번호(shipmentBoxId)가 존재하는 경우 shipmentBoxId 별로 각각 취소요청해야 정상적으로 처리가 됩니다.

> ※ **주의**: 주문 상품 취소 처리 API의 사용은 판매자 점수(주문이행)를 하락시키게 되므로, 재고와 가격 관리를 통해 사용을 지양해주시기 바랍니다.

---

## 1. API 기본 정보

- **HTTP Method**: `POST`
- **Endpoint**: `/v2/providers/openapi/apis/api/v5/vendors/{vendorId}/orders/{orderId}/cancel`
- **API Name**: `CANCEL_ORDER_PROCESSING`

### Example Endpoint
`https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v5/vendors/A00012345/orders/2000006593044/cancel`

---

## 2. 요청(Request)

### 2.1. Path Parameters

| Name       | Required | Type   | Description                                |
|------------|----------|--------|--------------------------------------------|
| `vendorId` | O        | String | 판매자 ID (쿠팡에서 발급한 고유 코드)      |
| `orderId`  | O        | Number | 주문 번호                                  |

### 2.2. Body Parameters

| Name               | Required | Type    | Description                                                                                                                                |
|--------------------|----------|---------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `orderId`          | O        | Number  | 주문 번호 (path variable과 동일)                                                                                                           |
| `vendorItemIds`    | O        | Array   | 취소할 상품의 옵션 ID(vendorItemId) 배열                                                                                                   |
| `receiptCounts`    | O        | Array   | 취소할 상품 개수 배열 (값은 항상 0보다 큼, `vendorItemIds`와 쌍으로 입력)                                                                  |
| `bigCancelCode`    | O        | String  | 주문상품 취소 사유 중 대분류 사유 코드 (`CANERR`)                                                                                          |
| `middleCancelCode` | O        | String  | 주문상품 취소 사유 중 중분류 사유 코드 (`CCTTER`, `CCPNER`, `CCPRER` 등)                                                                    |
| `vendorId`         | O        | String  | 업체 ID (path variable과 동일)                                                                                                             |
| `userId`           | O        | String  | 업체의 쿠팡 Wing 로그인 ID                                                                                                                 |

**참고**: [상품준비중] 상태의 상품 취소(출고중지완료) 시에는 입력값과 상관없이 사유 카테고리가 각각 "배송불만", "품절"로 고정되며, 상세 사유는 "파트너 API 강제 취소"로 기록됩니다.

### 2.3. Request Example

```json
{
  "orderId": 2000006593044,
  "vendorItemIds": [
    3145181064,
    3145181065,
    3145181067
  ],
  "receiptCounts": [
    1,
    2,
    1
  ],
  "bigCancelCode": "CANERR",
  "middleCancelCode": "CCTTER",
  "userId": "wing_login_id_123",
  "vendorId": "A00123456"
}
```

---

## 3. 응답(Response)

### 3.1. Response Body

| Name    | Type           | Description                                    |
|---------|----------------|------------------------------------------------|
| `code`    | String         | 응답 코드 (200: 성공, 400: 실패)               |
| `message` | String         | 실패 사유 및 에러 메시지                       |
| `data`    | `CancelResponse` | 성공 및 실패한 취소건에 대한 상세 정보         |

#### `CancelResponse` Object

| Name                  | Type          | Description                                |
|-----------------------|---------------|--------------------------------------------|
| `receiptMap`          | Object        | 접수 ID를 key로 갖는 접수 상세 정보        |
| `orderId`             | Number        | 주문번호                                   |
| `failedVendorItemIds` | Array<Number> | 취소에 실패한 `vendorItemId` 목록          |

#### `ReceiptMap` Entry Object

| Name          | Type          | Description                                |
|---------------|---------------|--------------------------------------------|
| `receiptId`   | Number        | 접수 ID                                    |
| `receiptType` | String        | `CANCEL` (즉시취소) 또는 `STOP_SHIPMENT` (출고중지) |
| `vendorItemIds` | Array<Number> | 해당 접수 ID로 처리된 상품 번호 목록       |
| `totalCount`  | Number        | 해당 접수 ID로 처리된 총 상품 개수         |

### 3.2. Response Examples

**Example 1: 전체 성공**
```json
{
  "code": "200",
  "message": "[요청번호] 43b97579-bcb5-4260-84cb-9a4a9063db71 \r\n",
  "data": {
    "receiptMap": {
      "181627233": {
        "receiptId": 181627233,
        "receiptType": "CANCEL",
        "vendorItemIds": [ 70071284034 ],
        "totalCount": 1
      }
    },
    "orderId": 23000059824637,
    "failedVendorItemIds": []
  }
}
```

**Example 2: 부분 성공**
```json
{
  "code": "200",
  "message": "[요청번호] cdea5b4b-34e9-4bec-bbd9-061e358e46a0 \r\n[3145181064]<= 취소 가능한 개수보다 요청한 개수가 더 많습니다.",
  "data": {
    "receiptMap": {
      "44698107": {
        "receiptId": 44698107,
        "receiptType": "STOP_SHIPMENT",
        "vendorItemIds": [ 3145181065, 3145181067 ],
        "totalCount": 3
      }
    },
    "orderId": 2000006593044,
    "failedVendorItemIds": [ 3145181064 ]
  }
}
```

**Example 3: 전체 실패**
```json
{
  "code": "400",
  "message": "[요청번호] 5d803ea1-e61d-44bd-a56d-44f3528f5136 \r\n [3145181067, 3145181065, 3145181064]<= 취소 가능한 개수보다 요청한 개수가 더 많습니다",
  "data": {
    "receiptMap": {},
    "orderId": 23000059824637,
    "failedVendorItemIds": [ 3145181067, 3145181065, 3145181064 ]
  }
}
```

---

## 4. 에러 사양(Error Spec)

| HTTP Status | Error Message                                      | 해결 방법                                                                                             |
|-------------|----------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 400         | 주문 ID를 입력해 주세요.                           | `orderId`를 올바로 입력했는지 확인합니다.                                                             |
| 400         | 취소할 벤더아이템 아이디 목록을 입력해주세요.      | `vendorItemIds`에 값을 올바로 입력했는지 확인합니다.                                                  |
| 400         | 취소할 아이템 개수 목록을 입력해주세요.            | `receiptCounts`에 값을 올바로 입력했는지 확인합니다.                                                  |
| 400         | 요청한 상품 개수와 취소 개수를 확인해주세요.       | `vendorItemIds`와 `receiptCounts` 배열의 개수가 일치하는지 확인합니다.                                |
| 400         | 취소사유 대분류 코드를 입력해주세요.               | `bigCancelCode`를 `CANERR`로 입력했는지 확인합니다.                                                   |
| 400         | 취소사유 중분류 코드를 입력해주세요.               | `middleCancelCode`를 `CCTTER`, `CCPNER`, `CCPRER` 중 하나로 입력했는지 확인합니다.                    |
| 400         | 업체 ID를 입력해주세요.                            | `vendorId`를 올바로 입력했는지 확인합니다.                                                            |
| 400         | 업체 ID에 맞는 올바른 유저 ID를 입력해주세요.      | `vendorId`에 속한 올바른 Wing의 `userId`를 입력했는지 확인합니다.                                       |
| 400         | 주문 정보가 없습니다.                              | 요청한 주문/상품 정보가 유효한지 확인합니다.                                                          |
| 400         | 취소 가능한 개수보다 요청한 개수가 더 많습니다.    | 취소 가능 수량을 확인하고 재시도합니다.                                                               |
| 400         | 해당 벤더아이템이 결제완료/상품지시 중 상태가 아닙니다. | 주문 상태를 확인하고, 취소 가능한 상태일 때 요청합니다.                                               |
| 400         | 요청한 업체의 상품이 아닙니다.                     | 해당 `vendorId`의 상품이 맞는지 확인합니다.                                                           |
| 400         | 출고정지 완료 처리에 실패했습니다.                 | 주문 상태를 확인하고 중복 요청이 아닌지 확인합니다.                                                   |
| 400         | 내부 오류가 발생하였습니다.                        | 입력값을 재확인하고 잠시 후 다시 시도합니다. 문제가 지속되면 쿠팡에 문의합니다.                       |
