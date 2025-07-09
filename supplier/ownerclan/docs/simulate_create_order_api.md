# Ownerclan 테스트 주문 (시뮬레이션) API 명세서

본 문서는 오너클랜의 GraphQL API를 통해 실제 주문을 생성하지 않고, 예상되는 상품 금액과 배송비 정보를 조회하는 방법을 설명합니다.

## 1. 엔드포인트

| 환경         | URL                                       |
| ------------ | ----------------------------------------- |
| **Production** | `https://api.ownerclan.com/v1/graphql`    |

> 현재 모든 구현은 **프로덕션(Production)** 환경을 기준으로 합니다.

## 2. HTTP 메서드

`POST`

## 3. 인증

- **Type**: `Bearer` 토큰
- **Header**: `Authorization: Bearer <YOUR_JWT_TOKEN>`

토큰은 `supplier/ownerclan/utils/auth.py`의 `get_ownerclan_token()` 함수를 통해 발급받을 수 있습니다.

## 4. 파라미터

`simulate_create_order.py` 스크립트는 `create_order.py`와 동일한 주문 정보 JSON 파일을 입력으로 받습니다.

### JSON 파일 예시 (`sample_order.json`)

```json
{
    "sender": {
        "name": "보내는이",
        "phoneNumber": "010-1234-5678",
        "email": "b00679540@gmail.com"
    },
    "recipient": {
        "name": "받는이",
        "phoneNumber": "010-8765-4321",
        "destinationAddress": {
            "addr1": "서울 금천구 가산디지털1로 128",
            "addr2": "808호",
            "postalCode": "08507"
        }
    },
    "products": [
        {
            "quantity": 1,
            "itemKey": "WFHVCDV",
            "optionAttributes": []
        }
    ],
    "note": "테스트 원장주문코드",
    "sellerNote": "테스트 주문관리코드",
    "ordererNote": "테스트 배송시 요청사항"
}
```

## 5. GraphQL Mutation 구조

스크립트는 `simulateCreateOrder` mutation을 사용합니다.

```graphql
mutation SimulateCreateOrder($input: OrderInput!) {
    simulateCreateOrder(input: $input) {
        itemAmounts {
            amount
            itemKey
        }
        shippingAmount
        extraShippingFeeExists
    }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `data.simulateCreateOrder` 필드에 예상 비용 정보가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다.

### 성공 응답 예시
```json
{
  "data": {
    "simulateCreateOrder": [
      {
        "itemAmounts": [
          {
            "amount": 3160,
            "itemKey": "WFHVCDV"
          }
        ],
        "shippingAmount": 3000,
        "extraShippingFeeExists": false
      }
    ]
  }
}
```

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# sample_order.json 파일을 이용해 주문 생성 시뮬레이션 실행
python supplier/ownerclan/simulate_create_order.py --input-file supplier/ownerclan/sample_order.json
```
