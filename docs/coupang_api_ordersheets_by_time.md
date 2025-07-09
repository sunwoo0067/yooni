# Coupang Open API: 발주서 목록 조회 (분단위 전체)

## 개요
발주서 목록을 24시간 이내의 분단위 구간으로 조회합니다. `searchType=timeFrame` 파라미터가 필수적입니다.

- **Path**: `GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets`
- **Example Endpoint**: `https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/A00012345/ordersheets?createdAtFrom=2017-09-29T00:00&createdAtTo=2017-09-29T23:59&searchType=timeFrame&status=DEPARTURE`

### 주요 특징
- **조회 기간**: 최대 24시간 이내로만 조회 가능합니다.
- **날짜 형식**: `yyyy-mm-ddTHH:MM` 형식으로 시작 및 종료 일시를 지정해야 합니다.
- **페이징 없음**: 이 API는 페이징을 지원하지 않고, 지정된 시간 범위 내의 모든 데이터를 한 번에 반환합니다.
- **용도**: 실시간으로 발생하는 주문을 확인하는 데 적합합니다.

---

## Request Parameters

### Path Segment Parameter
| Name     | Required | Type   | Description                                        |
|----------|----------|--------|----------------------------------------------------|
| vendorId | O        | String | 판매자 ID (쿠팡에서 발급한 고유 코드, 예: A00012345) |

### Query String Parameter
| Name          | Required | Type   | Description                                                                                                                              |
|---------------|----------|--------|------------------------------------------------------------------------------------------------------------------------------------------|
| createdAtFrom | O        | String | 검색 시작일시 (yyyy-mm-ddTHH:MM, 예: 2018-07-01T01:23)                                                                                    |
| createdAtTo   | O        | String | 검색 종료일시 (yyyy-mm-ddTHH:MM, 예: 2018-07-01T15:50). 시작일시로부터 24시간 이내여야 함.                                                    |
| status        | O        | String | 발주서 상태 (`ACCEPT`, `INSTRUCT`, `DEPARTURE`, `DELIVERING`, `FINAL_DELIVERY`, `NONE_TRACKING`)                                           |
| searchType    | O        | String | `timeFrame`으로 반드시 설정해야 분단위 조회가 수행됩니다.                                                                                |

---

## Response Message

응답 메시지의 구조와 필드는 '발주서 목록 조회(일단위 페이징)' API와 동일합니다.

### `data` 객체 필드
| Name                  | Type    | Description                                                                                                                                                           |
|-----------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| shipmentBoxId         | Number  | 배송번호(묶음배송번호)                                                                                                                                                |
| orderId               | Number  | 주문번호                                                                                                                                                              |
| ...                   | ...     | (이하 필드는 일단위 페이징 API와 동일)                                                                                                                                |

---

## Error Spec

| HTTP 상태 코드 | 오류 메시지                             | 해결 방법                                      |
|----------------|-----------------------------------------|------------------------------------------------|
| 400            | Invalid vendor ID                       | 올바른 판매자 ID(vendorId)를 입력했는지 확인.  |
| 400            | endTime-startTime range should less than 0 day | 조회 기간이 24시간 이내인지 확인.              |
