# 쿠팡 필수 구매 옵션 가이드

## 개요
쿠팡 파트너스 API를 통해 상품을 등록할 때 필요한 필수 구매 옵션의 검증 및 가이드를 제공합니다.

## 주요 기능

### 1. 옵션 검증 (`CoupangOptionValidator`)

#### 필수 구매 옵션 검증
```python
from market.coupang import CoupangOptionValidator

validator = CoupangOptionValidator()

# 검증할 상품 옵션
product_options = [
    {
        "attributeTypeName": "수량",
        "attributeValue": "1", 
        "attributeUnit": "개"
    }
]

# 검증 실행
result = validator.validate_required_options(78877, product_options)
print(f"검증 결과: {result['isValid']}")
```

#### 검증 결과 구조
```json
{
    "isValid": true,
    "errors": [],
    "warnings": [], 
    "requiredOptions": [...],
    "providedOptions": [...],
    "missingOptions": [],
    "invalidOptions": []
}
```

### 2. 옵션 설정 가이드

#### 카테고리별 옵션 가이드 조회
```python
guide = validator.get_option_guide(78877)

# 필수 옵션 확인
mandatory_options = guide['mandatoryOptions']

# 구매 옵션 확인
purchase_options = guide['purchaseOptions']

# 그룹 옵션 확인
group_options = guide['groupOptions']
```

#### 가이드 구조
```json
{
    "categoryCode": 78877,
    "isSingleItemAllowed": true,
    "mandatoryOptions": [...],
    "optionalOptions": [...],
    "purchaseOptions": [...],
    "searchOptions": [...],
    "groupOptions": {...},
    "unitGuide": {...},
    "allowedConditions": [...]
}
```

### 3. 권장 옵션 조합

#### 조합 제안
```python
combinations = validator.suggest_option_combinations(78877)

for combo in combinations:
    print(f"조합명: {combo['name']}")
    print(f"복잡도: {combo['complexity']}")
    print(f"옵션 수: {len(combo['options'])}")
```

#### 조합 유형
- **기본 필수 조합**: 필수 구매 옵션만 포함
- **권장 조합**: 필수 + 주요 선택 옵션
- **전체 조합**: 모든 구매 옵션 포함

### 4. 그룹 옵션 충돌 검사

#### 충돌 검사
```python
selected_options = ["색상", "사이즈", "용량"]
conflict_result = validator.check_group_option_conflicts(78877, selected_options)

if conflict_result['hasConflicts']:
    for conflict in conflict_result['conflicts']:
        print(f"충돌: {conflict['message']}")
```

## 데이터 타입 검증

### 지원 타입
- **STRING**: 문자열
- **NUMBER**: 숫자 (정수/실수)
- **DATE**: 날짜 (YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD)

### 단위 검증
허용된 단위 목록 확인:
```python
guide = validator.get_option_guide(78877)
unit_guide = guide['unitGuide']

for attr_name, unit_info in unit_guide.items():
    print(f"{attr_name}: {unit_info['allowedUnits']}")
```

## 중요 참고사항

### 2024년 10월 10일 변경사항
- 필수 구매옵션 입력 시 데이터 형식 엄격 검증
- 자유 구매옵션 구성 시 노출 제한 적용

### 그룹 옵션 규칙
- 동일 그룹 번호를 가진 옵션 중 **하나만** 선택 가능
- 필수 그룹의 경우 반드시 하나는 선택해야 함

### 상품 상태별 허용 여부
```python
conditions = validator.get_option_guide(78877)['allowedConditions']
# 예: ['NEW', 'REFURBISHED', 'USED_BEST', 'USED_GOOD', 'USED_NORMAL']
```

## 사용 예제

### 완전한 검증 워크플로우
```python
from market.coupang import CoupangOptionValidator

def validate_product_options(category_code, product_options):
    validator = CoupangOptionValidator()
    
    # 1. 기본 옵션 검증
    validation = validator.validate_required_options(category_code, product_options)
    
    if not validation['isValid']:
        print("❌ 옵션 검증 실패:")
        for error in validation['errors']:
            print(f"  - {error}")
        return False
    
    # 2. 그룹 충돌 검사
    option_names = [opt['attributeTypeName'] for opt in product_options]
    conflicts = validator.check_group_option_conflicts(category_code, option_names)
    
    if conflicts['hasConflicts']:
        print("❌ 그룹 옵션 충돌:")
        for conflict in conflicts['conflicts']:
            print(f"  - {conflict['message']}")
        return False
    
    print("✅ 모든 검증 통과")
    return True

# 사용 예
product_options = [
    {"attributeTypeName": "수량", "attributeValue": "1", "attributeUnit": "개"},
    {"attributeTypeName": "색상", "attributeValue": "검은색"}
]

is_valid = validate_product_options(78877, product_options)
```

## 오류 해결 가이드

### 일반적인 오류들

1. **필수 옵션 누락**
   ```
   오류: 필수 구매 옵션 '수량'이 누락되었습니다.
   해결: 해당 옵션을 product_options에 추가
   ```

2. **데이터 타입 불일치**
   ```
   오류: 옵션 '수량'의 값 'abc'가 예상 타입 'NUMBER'과 맞지 않습니다.
   해결: 숫자 값으로 변경 (예: "1", "10.5")
   ```

3. **그룹 옵션 충돌**
   ```
   오류: 그룹 1에서는 하나의 옵션만 선택 가능합니다: 색상, 컬러
   해결: 그룹 내에서 하나의 옵션만 선택
   ```

4. **허용되지 않는 단위**
   ```
   경고: 옵션 '무게'의 단위 'pound'가 허용된 단위 목록에 없습니다.
   해결: 허용된 단위 사용 (예: kg, g, mg)
   ```

## 테스트 실행

```bash
# 기본 테스트
python market/coupang/category/option_guide_example.py

# 개별 기능 테스트
python -c "
from market.coupang import CoupangOptionValidator
validator = CoupangOptionValidator()
guide = validator.get_option_guide(78877)
print(f'카테고리 {guide[\"categoryCode\"]} 가이드 조회 성공')
"
```