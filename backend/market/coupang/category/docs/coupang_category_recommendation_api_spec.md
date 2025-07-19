# 쿠팡 파트너스 API - 카테고리 추천 명세서

## 개요
쿠팡 카테고리 추천 API는 판매자가 보유한 상품정보(상품명, 브랜드, 속성 등)를 입력하면, 해당 정보와 가장 일치하는 쿠팡 카테고리(displayCategoryCode)를 찾아서 제안해주는 머신러닝 기반 서비스입니다.

### 특징
- 과거 등록된 상품의 쿠팡 카테고리를 학습한 머신러닝 모델 기반
- 카테고리별 수수료가 상이하므로 선택 시 주의 필요
- 정확한 정보 입력이 중요 (부정확한 정보 시 잘못된 추천 가능)

### 추천 결과 예시
| 입력 정보 | 제안 결과 |
|-----------|-----------|
| [유한양행] 유한젠 가루세제 1kg 용기(살균표백제)x10개 | 생활용품>세제>세탁세제>표백제>분말형 (5depth leaf catecode: 63955) |
| [유한양행] 유한젠 액체세제 1.8L 리필 (살균표백제) | 생활용품>세제>세탁세제>표백제>액상형 (5depth leaf catecode: 63954) |
| [유한양행] 유한락스 파워젤 1L (살균/악취제거)x10개 | 생활용품>세제>청소세제>락스/살균소독제 (4depth leaf catecode: 63922) |

## API 엔드포인트

### 카테고리 추천
- **Method**: POST
- **Path**: `/v2/providers/openapi/apis/api/v1/categorization/predict`
- **Base URL**: `https://api-gateway.coupang.com`
- **Full URL**: `https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v1/categorization/predict`

### Example
```
POST https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v1/categorization/predict
```

## 요청 파라미터

### Request Headers
```http
Content-Type: application/json;charset=UTF-8
Authorization: CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={timestamp}, signature={signature}
```

### Body Parameters
| Name | Required | Type | Description |
|------|----------|------|-------------|
| productName | ✅ 필수 | String | 상품명 |
| productDescription | ❌ 선택 | String | 상품에 대한 상세설명 |
| brand | ❌ 선택 | String | 브랜드 |
| attributes | ❌ 선택 | Object | 상품속성정보 (예: 사이즈, 색상, 소재 등) |
| sellerSkuCode | ❌ 선택 | String | 판매자상품코드(업체상품코드) |

### Request Example
```json
{
  "productName": "코데즈컴바인 양트임싱글코트",
  "productDescription": "모니터 해상도, 밝기, 컴퓨터 사양 등에 따라 실물과 약간의 색상차이가 있을 수 있습니다. 캐주얼하지만 큐티한디자인이 돋보이는 싱글코트에요 약간박시한핏이라 여유있고 편하게 스타일링하기 좋은 캐주얼 싱글코트입니다.",
  "brand": "코데즈컴바인",
  "attributes": {
    "제품 소재": "모달:53.8 폴리:43.2 레이온:2.4 면:0.6",
    "색상": "베이지,네이비",
    "제조국": "한국"
  },
  "sellerSkuCode": "123123"
}
```

## 응답 메시지

### Response Structure
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "autoCategorizationPredictionResultType": "SUCCESS",
    "predictedCategoryId": "63950",
    "predictedCategoryName": "일반 섬유유연제",
    "comment": null
  }
}
```

### Response Fields

#### Root Level
| Name | Type | Description |
|------|------|-------------|
| code | Number | HTTP Status Code |
| message | String | HTTP Status message |
| data | Object | 추천 결과 데이터 |

#### Data Object
| Name | Type | Description |
|------|------|-------------|
| autoCategorizationPredictionResultType | String | 결과 타입 (SUCCESS, FAILURE, INSUFFICIENT_INFORMATION) |
| predictedCategoryId | String | 추천 카테고리ID (displayCategoryCode) |
| predictedCategoryName | String | 추천 카테고리 명 |
| comment | String | 추가 코멘트 (선택적) |

### 결과 타입 설명
- **SUCCESS**: 카테고리 추천 성공
- **FAILURE**: 카테고리 추천 실패
- **INSUFFICIENT_INFORMATION**: 정보 부족으로 추천 불가

## 상품명 작성 가이드

### 📝 좋은 상품명 작성법

#### 1. 상세하고 명확한 정보 포함
- ✅ **좋은 예시**: "라운드티셔츠 남성 긴팔 맨투맨 gn 95 aden 그린 계열"
- ❌ **나쁜 예시**: "라운드티셔츠 gn 95 aden 그린 계열"

**개선점**: 남성용/여성용/남녀공용 구분, 긴팔/반팔 구분, 맨투맨/후드 등 세부 타입 명시

#### 2. 하나의 상품에 집중
- ✅ **좋은 예시**: "애견 강아지 자동 리드줄"
- ❌ **나쁜 예시**: "애견 캐리어 애견 장난감 애견 의류 리드줄"

**개선점**: 딜 형식 상품명 지양, 검색 키워드와 상품명 구분

#### 3. 모호한 키워드 지양
- ✅ **좋은 예시**: "[유한양행] 유한젠 가루세제 1kg 용기(살균표백제)x10개"
- ❌ **나쁜 예시**: "[유한양행] 유한젠 가루/액체 (살균표백제)"

**개선점**: 분말형/액상형 등 명확한 형태 구분

### 🎯 카테고리별 상품명 팁

#### 패션 의류
- 성별 구분 필수: 남성용/여성용/남녀공용
- 세부 타입: 맨투맨/후드/크롭/오버핏 등
- 계절: 긴팔/반팔/겨울용/여름용 등

#### 생활용품
- 형태: 가루/액체/젤/스프레이 등
- 용량: 정확한 용량과 단위
- 용도: 세탁용/청소용/살균용 등

#### 전자제품
- 사양: 용량, 크기, 기능
- 브랜드와 모델명
- 색상 및 디자인

## 오류 명세

### HTTP 상태 코드 및 오류 메시지

| HTTP 상태 코드 | 오류 메시지 | 해결 방법 |
|---------------|------------|----------|
| 400 | Input product name should not be empty! | 상품명(productName) 입력 확인 |
| 500 | Internal Server Error | productName 파라미터 입력 누락 확인 |
| 500 | Error occurred when communicating with seller_intelligence domain service | 일정시간 후 재호출 또는 입력값 수정 |
| 500 | Fail to communicate with the downstream domain services | 일정시간 후 재호출 또는 입력값 수정 |
| 500 | Fail to communicate with the listing domain to retrieve category name | 일정시간 후 재호출 또는 입력값 수정 |
| 500 | Receive error message from the downstream domain services | 일정시간 후 재호출 또는 입력값 수정 |

## 활용 워크플로우

### 1. 기본 카테고리 추천
```json
{
  "productName": "삼성 갤럭시 스마트폰 케이스 투명 실리콘"
}
```

### 2. 상세 정보 포함 추천
```json
{
  "productName": "나이키 에어맥스 남성 운동화 270 화이트",
  "brand": "나이키",
  "attributes": {
    "색상": "화이트",
    "사이즈": "250mm",
    "소재": "합성피혁"
  }
}
```

### 3. 추천 결과 활용
```python
# 추천받은 카테고리로 메타정보 조회
category_id = response['data']['predictedCategoryId']
metadata = category_client.get_category_metadata(category_id)
```

## 주의사항

### ⚠️ 중요 고려사항
1. **수수료 차이**: 카테고리별 수수료가 다르므로 신중한 선택 필요
2. **추천 결과 검증**: AI 추천이므로 최종 선택은 판매자 판단
3. **정확한 정보 입력**: 부정확한 정보 시 잘못된 추천 가능
4. **책임 제한**: 쿠팡은 잘못된 추천으로 인한 불이익 책임지지 않음

### 💡 모범 사례
- 상품의 핵심 특징을 명확히 기술
- 브랜드명과 모델명 포함
- 용량, 사이즈 등 구체적 수치 포함
- 용도와 대상 고객 명시
- 색상, 소재 등 주요 속성 포함

## API 이름
**GET_PRODUCT_AUTO_CATEGORY** - 상품 자동 카테고리 추천