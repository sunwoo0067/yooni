# Ownerclan 주문 취소 API 명세서

본 문서는 오너클랜의 GraphQL API를 통해 '결제 완료' 상태의 주문을 취소하는 방법을 설명합니다.

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

`cancel_order.py` 스크립트는 다음 명령줄 인자를 지원합니다.

| 파라미터 | 타입   | 필수 | 설명                       |
| -------- | ------ | ---- | -------------------------- |
| `key`    | string | 예   | 취소할 주문의 `key`입니다. |

## 5. GraphQL Mutation 구조

스크립트는 `cancelOrder` mutation을 사용합니다.

```graphql
mutation CancelOrder($key: ID!) {
    cancelOrder(key: $key) {
        key
        status
        // ... 기타 주문 상세 정보
    }
}
```

`variables`에는 취소할 주문의 `key`를 전달합니다.

```json
{
  "key": "2025070921571383606A"
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `data.cancelOrder` 필드에 `status`가 `cancelled`로 변경된 주문 정보가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다. (예: 이미 배송 시작된 주문을 취소하려는 경우)

### 성공 응답 예시
```json
{
  "data": {
    "cancelOrder": {
      "key": "2025070921571383606A",
      "status": "cancelled",
      // ...
    }
  }
}
```

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# 1. 취소할 주문을 먼저 생성합니다.
# python supplier/ownerclan/create_order.py --input-file supplier/ownerclan/sample_order.json
# (위 명령의 결과에서 주문 key를 확인합니다)

# 2. 확인된 key로 주문을 취소합니다.
python supplier/ownerclan/cancel_order.py <YOUR_ORDER_KEY>
```
