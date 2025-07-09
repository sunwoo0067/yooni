# Coupang API: 장기미배송 배송완료 처리 (Complete Long-Term Undelivery)

송장 등록 후 1달이 경과하였으나 배송추적 결과를 확인할 수 없는 건에 대해 배송완료로 상태를 변경하는 API입니다.

**주의사항:**
- 정산된 주문에 대한 미배송으로 고객 분쟁 발생 시, 분쟁 처리 비용은 판매자가 부담해야 하므로 정확한 확인이 필요합니다.
- 배송지시(DEPARTURE) 이후 30일이 지난 배송지시, 배송중 상태인 주문만 처리 가능합니다.

---

## 1. API 기본 정보

- **HTTP Method**: `POST`
- **Endpoint**: `/v2/providers/openapi/apis/api/v4/vendors/{vendorId}/completeLongTermUndelivery`
- **API Name**: `UPDATE_INVOICE_DELIVERY_BY_INVOICE_NO`

### Example Endpoint
`https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/A00012345/completeLongTermUndelivery`

---

## 2. 요청(Request)

### 2.1. Path Parameters

| Name     | Required | Type   | Description |
|----------|----------|--------|-------------|
| `vendorId` | O        | String | 판매자 ID     |

### 2.2. Body Parameters

| Name            | Required | Type   | Description  |
|-----------------|----------|--------|--------------|
| `shipmentBoxId` | O        | Number | 묶음배송번호 |
| `invoiceNumber` | O        | String | 운송장번호   |

### 2.3. Request Example

```json
{
  "shipmentBoxId": 123456789012345678,
  "invoiceNumber": "505124853844"
}
```

---

## 3. 응답(Response)

### 3.1. Response Body

| Name      | Type    | Description                  |
|-----------|---------|------------------------------|
| `code`    | String  | 서버 응답 상태 정보 (e.g., "200") |
| `message` | String  | 상세 정보 (e.g., "SUCCESS")    |
| `data`    | Boolean | 처리 결과 (true/false)       |

### 3.2. Response Example (Success)

```json
{
  "code": "200",
  "message": "SUCCESS",
  "data": true
}
```

---

## 4. 에러 사양(Error Spec)

| HTTP Status | Error Message                               | Solution                                                                                                   |
|-------------|---------------------------------------------|------------------------------------------------------------------------------------------------------------|
| 400         | 배송완료 처리 실패. 배송상태: INSTRUCT        | 상품준비중(INSTRUCT) 상태의 주문은 처리할 수 없습니다. 배송지시 이후 상태의 주문만 가능합니다.               |
| 400         | 배송완료 처리 실패. 배송상태: DEPARTURE       | 올바른 송장번호인지 확인하고, 배송지시 후 30일이 지났는지 확인합니다. (최대 32일 소요될 수 있음)             |
| 400         | 배송완료 처리 실패. 배송상태: NONE_TRACKING   | 업체직송(NONE_TRACKING) 상태의 주문은 처리할 수 없습니다.                                                    |
