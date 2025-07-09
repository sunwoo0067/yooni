# Ownerclan 주문 취소 요청 API 명세서

본 문서는 오너클랜의 GraphQL API를 통해 '배송 준비중(preparing)' 상태인 주문의 취소를 요청하는 방법을 설명합니다.

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

`request_order_cancellation.py` 스크립트는 다음 명령줄 인자를 지원합니다.

| 파라미터   | 타입   | 필수 | 설명                               |
| ---------- | ------ | ---- | ---------------------------------- |
| `--key`    | string | 예   | 취소 요청할 주문의 `key`입니다.    |
| `--reason` | string | 예   | 주문 취소 요청 사유입니다.         |

## 5. GraphQL Mutation 구조

스크립트는 `requestOrderCancellation` mutation을 사용합니다.

```graphql
mutation RequestOrderCancellation($key: ID!, $input: RequestOrderCancellationInput!) {
    requestOrderCancellation(key: $key, input: $input) {
        key
        status
        // ... 기타 주문 상세 정보
    }
}
```

`variables`에는 취소할 주문의 `key`와 취소 사유(`cancelReason`)를 포함한 `input` 객체를 전달합니다.

```json
{
  "key": "SOME_ORDER_KEY_IN_PREPARING_STATUS",
  "input": {
    "cancelReason": "고객 변심으로 인한 취소 요청"
  }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `data.requestOrderCancellation` 필드에 `status`가 `cancellationRequested`로 변경된 주문 정보가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다. (예: '배송 준비중'이 아닌 상태의 주문을 취소 요청하는 경우)

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

**참고**: 이 스크립트는 '배송 준비중(preparing)' 상태의 주문에만 사용할 수 있습니다. 해당 상태의 주문 `key`가 필요합니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# 특정 주문(key)에 대해 취소를 요청합니다.
python supplier/ownerclan/request_order_cancellation.py --key <YOUR_ORDER_KEY> --reason "고객 변심"
```
