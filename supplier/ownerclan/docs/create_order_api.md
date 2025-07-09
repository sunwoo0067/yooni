# Ownerclan 새 주문 등록 API 명세서

본 문서는 오너클랜의 GraphQL API를 통해 새로운 주문을 등록하는 방법을 설명합니다.

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

`create_order.py` 스크립트는 주문 정보가 담긴 JSON 파일을 입력으로 받습니다. JSON 파일의 구조는 `OrderInput` 타입에 맞춰야 합니다.

### 주요 입력 필드

- `sender` (object): 보내는 사람 정보. (생략 가능, 생략 시 기본값 사용)
  - `name` (string, required)
  - `phoneNumber` (string, required)
  - `email` (string)
- `recipient` (object, required): 받는 사람 정보.
  - `name` (string, required)
  - `phoneNumber` (string, required)
  - `destinationAddress` (object, required)
    - `addr1` (string, required)
    - `addr2` (string)
    - `postalCode` (string)
- `products` (array, required): 주문할 상품 목록.
  - `quantity` (int, required)
  - `itemKey` (string, required): 오너클랜 상품 키
  - `optionAttributes` (array of strings): 상품 옵션
- `note` (string): 원장주문코드
- `sellerNote` (string): 주문관리코드
- `ordererNote` (string): 배송 요청 사항

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

스크립트는 `createOrder` mutation을 사용합니다.

```graphql
mutation CreateOrder($input: OrderInput!) {
    createOrder(input: $input) {
        key
        // ... 주문 상세 정보
    }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `data.createOrder` 필드에 생성된 주문 정보(배열)가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다.

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# sample_order.json 파일을 이용해 새로운 주문 생성
python supplier/ownerclan/create_order.py --input-file supplier/ownerclan/sample_order.json
```
