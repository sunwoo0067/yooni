# Ownerclan 복수 주문 조회 API 명세서

본 문서는 오너클랜의 여러 주문 내역을 GraphQL API를 통해 조회하는 방법을 설명합니다.

## 1. 엔드포인트

| 환경         | URL                                       |
| ------------ | ----------------------------------------- |
| **Production** | `https://api.ownerclan.com/v1/graphql`    |

> 현재 모든 구현은 **프로덕션(Production)** 환경을 기준으로 합니다.

## 2. HTTP 메서드

`GET`

## 3. 인증

- **Type**: `Bearer` 토큰
- **Header**: `Authorization: Bearer <YOUR_JWT_TOKEN>`

토큰은 `supplier/ownerclan/utils/auth.py`의 `get_ownerclan_token()` 함수를 통해 발급받을 수 있습니다.

## 4. 파라미터

`list_orders.py` 스크립트는 다음 명령줄 인자를 지원합니다.

### Pagination 관련

| 파라미터 | 타입   | 설명                                               |
| -------- | ------ | -------------------------------------------------- |
| `--after`  | string | 이 cursor 값 이후의 주문만 조회합니다.             |
| `--first`  | int    | 조회할 주문의 최대 개수입니다.                     |

### 검색 관련

| 파라미터          | 타입   | 설명                                               |
| ----------------- | ------ | -------------------------------------------------- |
| `--dateFrom`      | string | 주문 생성일 시작 (ISO 8601 형식: `YYYY-MM-DDTHH:MM:SS`) |
| `--dateTo`        | string | 주문 생성일 종료 (ISO 8601 형식: `YYYY-MM-DDTHH:MM:SS`) |
| `--note`          | string | 원장주문코드(note)에 포함된 값으로 검색합니다.     |
| `--sellerNote`    | string | 주문 관리 코드(sellerNote)에 포함된 값으로 검색합니다. |
| `--status`        | string | 특정 주문 상태의 주문만 조회합니다.                |
| `--shippedAfter`  | string | 송장 입력일 시작 (ISO 8601 형식: `YYYY-MM-DDTHH:MM:SS`) |
| `--shippedBefore` | string | 송장 입력일 종료 (ISO 8601 형식: `YYYY-MM-DDTHH:MM:SS`) |

**참고**: 기간 관련 파라미터는 90일 이내로 지정해야 합니다. 아무 조건도 주지 않으면 기본적으로 최근 90일간의 데이터를 조회합니다.

## 5. GraphQL 쿼리 구조

스크립트는 입력된 파라미터를 기반으로 아래와 같은 구조의 쿼리를 동적으로 생성합니다.

```graphql
query {
  allOrders(first: 5, dateTo: "...") {
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    edges {
      cursor
      node {
        // ... 주문 상세 정보
      }
    }
  }
}
```

## 6. 응답

- **성공 시 (`200 OK`)**: `pageInfo`와 주문 목록(`edges`)이 포함된 JSON 객체를 반환합니다.
- **실패 시**: `errors` 필드에 오류 정보가 담긴 JSON 객체를 반환합니다.

## 7. 파이썬 스크립트 사용 예시

프로젝트 루트 디렉터리에서 다음 명령을 실행하여 사용할 수 있습니다.

```bash
# .env 파일에 OWNERCLAN_USERNAME, OWNERCLAN_PASSWORD 설정 필요

# 최근 90일간의 주문 중 처음 5개를 조회
python supplier/ownerclan/list_orders.py --first 5

# 특정 기간 동안 '결제완료' 상태인 주문 10개를 조회
python supplier/ownerclan/list_orders.py --status PAYMENT_COMPLETED --first 10 --dateFrom "2025-07-01T00:00:00" --dateTo "2025-07-09T23:59:59"

# 특정 주문 관리 코드가 포함된 주문 조회
python supplier/ownerclan/list_orders.py --sellerNote "MyMemo123"
```
