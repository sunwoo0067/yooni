# Ownerclan 주문 메모 업데이트 API 명세서

본 문서는 오너클랜의 GraphQL API를 통해 기존 주문의 원장주문코드(note)와 주문관리메모(sellerNote)를 업데이트하는 방법을 설명합니다.

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

`update_order_notes.py` 스크립트는 다음 명령줄 인자를 지원합니다.

| 파라미터        | 타입   | 필수 | 설명                                       |
| --------------- | ------ | ---- | ------------------------------------------ |
| `--key`         | string | 예   | 메모를 수정할 주문의 `key`입니다.          |
| `--note`        | string | 아니오 | 새로운 원장주문코드(note)입니다.           |
| `--seller-note` | string | 아니오 | 새로운 주문관리메모(sellerNote)입니다.     |

**주의**: `note` 또는 `seller-note` 중 적어도 하나는 반드시 제공해야 합니다.

## 5. GraphQL Mutation 구조

스크립트는 `updateOrderNotes` mutation을 사용하며, 주문 `key`를 동적으로 쿼리에 삽입합니다.

```graphql
mutation UpdateOrderNotes($input: OrderUpdateNotesInput!) {
    updateOrderNotes(key: "{order_key}", input: $input) {
        key
        note
        sellerNote
        // ... 기타 주문 상세 정보
    }
}
```

`input` 변수에는 `note` 또는 `sellerNotes` 필드가 포함됩니다.

```json
{
  "input": {
    "note": "수정된 원장주문코드",
    "sellerNotes": [{"sellerNote": "수정된 주문관리코드"}]
  }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `data.updateOrderNotes` 필드에 업데이트된 주문 정보가 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다.

**참고**: `updateOrderNotes`의 직접적인 응답은 캐시된 데이터를 반환할 수 있습니다. 업데이트된 내용을 가장 정확하게 확인하려면, 이 API 호출 후 `get_order.py`로 해당 주문을 다시 조회하는 것이 좋습니다.

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# 특정 주문(key)의 note와 sellerNote를 모두 업데이트
python supplier/ownerclan/update_order_notes.py --key 2025070921325143457A --note '수정된 원장주문코드' --seller-note '수정된 주문관리코드'

# note만 업데이트
python supplier/ownerclan/update_order_notes.py --key 2025070921325143457A --note '새로운 원장주문코드'

# sellerNote만 업데이트
python supplier/ownerclan/update_order_notes.py --key 2025070921325143457A --seller-note '새로운 주문관리코드'
```
