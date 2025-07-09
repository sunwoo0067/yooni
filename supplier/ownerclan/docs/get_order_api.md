# Ownerclan 단일 주문 조회 API 명세서

본 문서는 오너클랜의 단일 주문 정보를 GraphQL API를 통해 조회하는 방법을 설명합니다.

## 1. 엔드포인트

| 환경         | URL                                       |
| ------------ | ----------------------------------------- |
| **Production** | `https://api.ownerclan.com/v1/graphql`    |
| Sandbox      | `https://api-sandbox.ownerclan.com/v1/graphql` |

> 현재 모든 구현은 **프로덕션(Production)** 환경을 기준으로 합니다.

## 2. HTTP 메서드

`GET`

## 3. 인증

- **Type**: `Bearer` 토큰
- **Header**: `Authorization: Bearer <YOUR_JWT_TOKEN>`

토큰은 `supplier/ownerclan/utils/auth.py`의 `get_ownerclan_token()` 함수를 통해 발급받을 수 있습니다.

## 4. 쿼리 파라미터

| 파라미터 | 타입   | 설명                                      |
| -------- | ------ | ----------------------------------------- |
| `query`  | string | 실행할 GraphQL 쿼리 문. URL 인코딩 필요. |

## 5. GraphQL 쿼리

단일 주문을 조회하기 위한 기본 쿼리 구조입니다. `key`에 조회할 실제 주문 코드를 입력합니다.

```graphql
query {
  order(key: "<ORDER_KEY>") {
    key
    id
    products {
      quantity
      price
      shippingType
      itemKey
      itemOptionInfo {
        optionAttributes {
          name
          value
        }
        price
      }
      trackingNumber
      shippingCompanyCode
      shippedDate
      additionalAttributes {
        key
        value
      }
      taxFree
    }
    status
    shippingInfo {
      sender {
        name
        phoneNumber
        email
      }
      recipient {
        name
        phoneNumber
        destinationAddress {
          addr1
          addr2
          postalCode
        }
      }
      shippingFee
    }
    createdAt
    updatedAt
    note
    ordererNote
    sellerNote
    isBeingMediated
    adjustments {
      reason
      price
      taxFree
    }
    transactions {
      key
      id
      kind
      status
      amount {
        currency
        value
      }
      createdAt
      updatedAt
      closedAt
      note
    }
  }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: 요청한 `data` 필드에 주문 정보가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다.

### 성공 예시

```json
{
  "data": {
    "order": {
      "key": "실제 주문 키",
      "id": "API ID",
      // ... 기타 주문 정보
    }
  }
}
```

### 실패 예시 (주문 정보 없음)

```json
{
  "errors": [
    {
      "message": "주문 정보를 찾을 수 없습니다.",
      "path": ["order"],
      "field": "key",
      "originalValue": "\"존재하지 않는 주문 키\""
    }
  ],
  "data": {
    "order": null
  }
}
```

## 7. 파이썬 예제 코드

프로젝트 내 `supplier/ownerclan/get_order.py` 스크립트를 사용하여 특정 주문을 조회할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# 사용법: python get_order.py <조회할_주문_KEY>
python supplier/ownerclan/get_order.py 20240101ABCDE
```
