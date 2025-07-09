# 이미출고 처리 (STOP_RETURN_REQUEST_BY_RECEIPT)

고객이 주문을 취소하여 반품요청목록 조회 시 상태가 출고중지요청(`RELEASE_STOP_UNCHECKED`) 또는 반품접수미확인(`RETURNS_UNCHECKED`)이면서 `releaseStatus`가 "N"일 경우에 사용합니다. 이미 판매자가 상품을 발송한 상태일 때 이 API를 호출하여 '이미출고' 상태로 변경하고 송장 정보를 등록합니다.

**주의:** 고객의 출고중지요청에도 불구하고 상품을 출고했다면 왕복 반품 배송비는 판매자의 귀책입니다.

## 요청

### Path

`PATCH /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/returnRequests/{receiptId}/completedShipment`

### Example Endpoint

`https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/A00012345/returnRequests/12346897/completedShipment`

### Path Segment Parameter

| Name        | Required | Type   | Description                                      |
|-------------|----------|--------|--------------------------------------------------|
| `vendorId`  | O        | String | 판매자 ID (쿠팡에서 업체에게 발급한 고유 코드) 예) A00012345 |
| `receiptId` | O        | Number | 접수 ID                                          |

### Body Parameter

| Name                  | Required | Type   | Description                                      |
|-----------------------|----------|--------|--------------------------------------------------|
| `vendorId`            | O        | String | 판매자 ID (쿠팡에서 업체에게 발급한 고유 코드) 예) A00012345 |
| `receiptId`           | O        | Number | 접수 ID                                          |
| `deliveryCompanyCode` | O        | String | 택배사 코드 (예: `KDEXP`)                      |
| `invoiceNumber`       | O        | String | 송장번호                                         |

### Request Example

```json
{
  "vendorId": "TESTVENDORID",
  "receiptId": 12346897,
  "deliveryCompanyCode": "KDEXP",
  "invoiceNumber": "70432743577"
}
```

## 응답

### Response Message

| Name          | Type   | Description                                |
|---------------|--------|--------------------------------------------|
| `code`        | String | 서버 응답 코드                             |
| `message`     | String | 서버 응답 메세지                           |
| `data`        | Object | **`resultCode`**: `String` - SUCCESS/FAIL<br>**`resultMessage`**: `String` - 결과 메세지 |

### Response Example

```json
{
  "code": "200",
  "message": "OK",
  "data": {
    "resultCode": "SUCCESS",
    "resultMessage": "이미출고 상태변경이 성공하였습니다."
  }
}
```

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지                                                                                             | 해결 방법                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| 400 (요청변수확인)         | 이미 저장된 송장번호가 있어 송장번호 등록이 불가능합니다. (동일송장번호 업로드 조건 : 수취인정보 동일) | 등록한 송장번호가 이미 쿠팡에 등록된 번호인지 확인합니다.                     |
| 400 (요청변수확인)         | 송장번호가 유효하지 않습니다.                                                                           | 입력한 송장번호(`invoiceNumber`)가 올바른 값인지 확인합니다.                  |
