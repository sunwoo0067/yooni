# 쿠팡 파트너스 API - 카테고리 메타정보 조회 명세서

## 개요
노출 카테고리코드(displayCategoryCode)를 이용하여 해당 카테고리에 속한 고시정보, 옵션, 구비서류, 인증정보 목록 등을 조회합니다.

상품 생성 시, 쿠팡에서 규정하고 있는 각 카테고리의 메타 정보와 일치하는 항목으로 상품 생성 전문을 구성해야 합니다.

## API 엔드포인트

### 카테고리 메타정보 조회
- **Method**: GET
- **Path**: `/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/{displayCategoryCode}`
- **Base URL**: `https://api-gateway.coupang.com`
- **Full URL**: `https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/{displayCategoryCode}`

### Example
```
GET https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/78877
```

## 요청 파라미터

### Path Parameters
| Name | Required | Type | Description |
|------|----------|------|-------------|
| displayCategoryCode | O | Number | 노출카테고리코드 |

### Request Example
```http
GET /v2/providers/seller_api/apis/api/v1/marketplace/meta/category-related-metas/display-category-codes/78877
Content-Type: application/json;charset=UTF-8
Authorization: CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={timestamp}, signature={signature}
```

## 응답 메시지

### Response Structure
```json
{
  "code": "SUCCESS|ERROR",
  "message": "결과 메세지",
  "data": {
    "isAllowSingleItem": boolean,
    "attributes": [...],
    "noticeCategories": [...],
    "requiredDocumentNames": [...],
    "certifications": [...],
    "allowedOfferConditions": [...]
  }
}
```

### Response Fields

#### Root Level
| Name | Type | Description |
|------|------|-------------|
| code | Number | 결과코드 (SUCCESS/ERROR) |
| message | String | 결과 메세지 |
| data | Object | 카테고리 메타정보 |

#### Data Object
| Name | Type | Description |
|------|------|-------------|
| isAllowSingleItem | Boolean | 단일상품 등록 가능 여부 (true/false) |
| attributes | Array | 카테고리 옵션목록 (구매옵션/검색옵션) |
| noticeCategories | Array | 상품고시정보목록 |
| requiredDocumentNames | Array | 구비서류목록 |
| certifications | Array | 상품 인증 정보 |
| allowedOfferConditions | Array | 허용된 상품 상태 |

#### Attributes Array
| Name | Type | Description |
|------|------|-------------|
| attributeTypeName | String | 옵션타입명 |
| required | String | 필수여부 (MANDATORY: 필수, OPTIONAL: 선택) |
| dataType | String | 데이터형식 (STRING: 문자열, NUMBER: 숫자, DATE: 날짜) |
| basicUnit | String | 기본단위 |
| usableUnits | Array | 사용가능한단위값목록 |
| groupNumber | String | 그룹속성값 (NONE: 그룹속성 아님, 1 or 2: 그룹 속성임) |
| exposed | String | 구매옵션/검색옵션 구분값 (EXPOSED: 구매옵션, NONE: 검색옵션) |

#### Notice Categories Array
| Name | Type | Description |
|------|------|-------------|
| noticeCategoryName | String | 상품고시정보카테고리명 |
| noticeCategoryDetailNames | Array | 상품고시정보카테고리상세목록 |
| └ noticeCategoryDetailName | String | 상품고시정보카테고리상세명 |
| └ required | String | 필수여부 (MANDATORY: 필수, OPTIONAL: 선택) |

#### Required Document Names Array
| Name | Type | Description |
|------|------|-------------|
| templateName | String | 구비서류명 |
| required | String | 구비서류필수여부 (MANDATORY: 필수, OPTIONAL: 선택) |

#### Certifications Array
| Name | Type | Description |
|------|------|-------------|
| certificationType | String | 상품등록/수정 시 certificationType에 입력 |
| name | String | 인증 정보 이름 |
| dataType | String | 인증 정보 타입 (CODE: 인증기관에서 발급받은 코드 입력, NONE: 코드 입력 불필요) |
| required | String | 필수여부 (MANDATORY: 필수, RECOMMEND: 추천, OPTIONAL: 선택) |

#### Allowed Offer Conditions Array
허용된 상품 상태 값들:
- `NEW`: 새 상품
- `REFURBISHED`: 리퍼
- `USED_BEST`: 중고(최상)
- `USED_GOOD`: 중고(상)
- `USED_NORMAL`: 중고(중)

## 응답 예제

<details>
<summary>Full Response Example</summary>

```json
{
  "code": "SUCCESS",
  "message": "",
  "data": {
    "isAllowSingleItem": true,
    "attributes": [
      {
        "attributeTypeName": "수량",
        "dataType": "NUMBER",
        "basicUnit": "개",
        "usableUnits": [
          "개", "개입", "매", "매입", "팩", "입", "장", "병", 
          "인용", "인분", "box", "Ea", "포", "캔", "박스", "스틱", 
          "권", "set", "세트", "조", "캡슐", "통", "정", "봉", "마리"
        ],
        "required": "OPTIONAL",
        "groupNumber": "NONE",
        "exposed": "EXPOSED"
      },
      {
        "attributeTypeName": "자동차거치용품 거치대고정",
        "dataType": "STRING",
        "basicUnit": "없음",
        "usableUnits": [],
        "required": "OPTIONAL",
        "groupNumber": "NONE",
        "exposed": "NONE"
      }
    ],
    "noticeCategories": [
      {
        "noticeCategoryName": "자동차용품(자동차부품/기타 자동차용품)",
        "noticeCategoryDetailNames": [
          {
            "noticeCategoryDetailName": "품명 및 모델명",
            "required": "MANDATORY"
          },
          {
            "noticeCategoryDetailName": "출시년월",
            "required": "MANDATORY"
          }
        ]
      }
    ],
    "requiredDocumentNames": [
      {
        "templateName": "기타인증서류",
        "required": "OPTIONAL"
      }
    ],
    "certifications": [
      {
        "certificationType": "NOT_REQUIRED",
        "name": "인증대상아님",
        "dataType": "NONE",
        "required": "OPTIONAL"
      }
    ],
    "allowedOfferConditions": [
      "NEW",
      "REFURBISHED",
      "USED_BEST",
      "USED_GOOD",
      "USED_NORMAL"
    ]
  }
}
```

</details>

## 오류 명세

### HTTP 상태 코드 및 오류 메시지

| HTTP 상태 코드 | 오류 메시지 | 해결 방법 |
|---------------|------------|----------|
| 400 | 관리카테고리를 찾을 수 없는 노출카테고리코드 입니다. 담당MD에게 확인하고 유효한 노출카테고리를 입력해주세요. | 올바른 노출카테고리코드를 입력했는지 확인 |
| 400 | 전시카테고리코드는 숫자형으로 입력해주세요. | 노출(전시)카테고리코드는 숫자로만 입력 가능 |

## 중요 참고사항

### 구매옵션 관련
- **2024년 10월 10일부터** 필수 구매옵션 입력 시 데이터 형식에 맞게 입력해야 정상적으로 상품등록이 가능
- **2024년 10월 10일부터** 자유 구매옵션 구성을 할 경우 노출에 제한됨
- 상품 판매 승인 이전: attributes의 추가, 변경, 삭제 가능
- 상품 판매 승인 이후: attributes의 추가만 가능, 삭제/변경 불가

### 단위 관련
- 길이(cm): cm, mm, m, km
- 길이(인치): in, ft, yd
- 무게(g): mg, g, kg, t, oz, lb
- 부피(ml): cc, ml, L
- 데이터 용량(GB): KB, MB, GB, TB
- 수량(개): 개, 개입, 매, 매입, 팩, 입, 장, 병, 인용, 인분, box, Ea, 포, 캔, 박스, 스틱, 권, set, 세트, 캡슐, 통, 정, 봉, 마리

### 특수 케이스
- **음료 카테고리**에서는 `basicUnit` 필드를 사용하지 않음

## 관련 가이드
- 노출 카테고리코드 조회 방법
- 필수 구매옵션 및 허용값 확인 방법
- 구매옵션 자유 입력 가이드 (20201012 변경사항)