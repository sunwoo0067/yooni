# Coupang Open API: 발주서 단건 조회 (shipmentBoxId)

## 개요
`shipmentBoxId`를 이용하여 발주서 단건을 조회합니다. 이 API는 상품 준비 중 배송지 변경과 같은 최신 주문 상태를 확인하는 데 필수적입니다.

- **Path**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets/{shipmentBoxId}`
- **Example Endpoint**: `https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/A00000001/ordersheets/642538971006401429`

### 주요 특징
- **배송지 재확인**: 결제완료 상태에서 고객이 배송지를 변경할 수 있으므로, 상품준비중 처리 이후 이 API를 통해 배송지 정보("receiver")가 변경되었는지 반드시 재확인해야 합니다.
- **상품 정보 확인**: 출고 전, "sellerProductName + sellerProductItemName"과 "vendorItemName"의 정보가 일치하는지 확인해야 합니다.

---

## Request Parameters

### Path Segment Parameter
| Name          | Required | Type   | Description                                      |
|---------------|----------|--------|--------------------------------------------------|
| vendorId      | O        | String | 판매자 ID (쿠팡에서 발급한 고유 코드)            |
| shipmentBoxId | O        | Number | 배송번호(묶음배송번호), 목록 조회 API를 통해 획득 |

---

## Response Message

응답 메시지의 구조와 필드는 '발주서 목록 조회' API와 거의 동일하나, `data` 필드가 단일 객체라는 점이 다릅니다.

### `data` 객체 필드
| Name                  | Type    | Description                                      |
|-----------------------|---------|--------------------------------------------------|
| shipmentBoxId         | Number  | 배송번호(묶음배송번호)                           |
| orderId               | Number  | 주문번호                                         |
| ...                   | ...     | (이하 필드는 목록 조회 API와 동일)               |

---

## Error Spec

| HTTP 상태 코드 | 오류 메시지                             | 해결 방법                                                               |
|----------------|-----------------------------------------|-------------------------------------------------------------------------|
| 400            | 해당 주문이 취소 또는 반품되었습니다.   | 반품/취소 요청 목록 조회 API를 통해 확인하고, 해당 주문을 반복 호출하지 않도록 처리. |
| 400            | Invalid vendor ID                       | 올바른 판매자 ID(vendorId)를 입력했는지 확인.                             |
