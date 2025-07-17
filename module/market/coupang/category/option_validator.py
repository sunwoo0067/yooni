#!/usr/bin/env python3
"""
쿠팡 필수 구매 옵션 검증 및 가이드 모듈
"""

from typing import Dict, List, Optional, Any, Tuple
from .category_client import CoupangCategoryClient


class CoupangOptionValidator:
    """쿠팡 구매 옵션 검증 및 가이드 클래스"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 vendor_id: Optional[str] = None):
        """
        옵션 검증기 초기화
        
        Args:
            access_key: 쿠팡 액세스 키
            secret_key: 쿠팡 시크릿 키  
            vendor_id: 쿠팡 벤더 ID
        """
        self.category_client = CoupangCategoryClient(access_key, secret_key, vendor_id)
    
    def validate_required_options(self, display_category_code: int, 
                                product_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        필수 구매 옵션 검증 (PDF 가이드 기반)
        
        Args:
            display_category_code: 노출카테고리코드
            product_options: 상품에 설정된 옵션 리스트
                예시: [{"attributeTypeName": "수량", "attributeValue": "1", "attributeUnit": "개"}]
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        try:
            # 카테고리 메타정보 조회
            category_attrs = self.category_client.get_category_attributes(display_category_code)
            
            # 필수 구매 옵션 필터링 (MANDATORY + EXPOSED)
            required_purchase_options = [
                attr for attr in category_attrs 
                if attr.get('required') == 'MANDATORY' and attr.get('exposed') == 'EXPOSED'
            ]
            
            validation_result = {
                "isValid": True,
                "errors": [],
                "warnings": [],
                "groupWarnings": [],
                "requiredOptions": required_purchase_options,
                "providedOptions": product_options,
                "missingOptions": [],
                "invalidOptions": [],
                "groupValidation": {}
            }
            
            # 카테고리 속성을 이름으로 매핑
            attr_map = {attr['attributeTypeName']: attr for attr in category_attrs}
            
            # 제공된 옵션을 이름으로 매핑
            provided_options_map = {opt.get('attributeTypeName'): opt for opt in product_options}
            provided_option_names = set(provided_options_map.keys())
            
            # 1. 필수 옵션 누락 검증
            for required_opt in required_purchase_options:
                opt_name = required_opt.get('attributeTypeName')
                
                if opt_name not in provided_option_names:
                    validation_result["errors"].append(
                        f"필수 구매 옵션 '{opt_name}' (타입: {required_opt.get('dataType')})이 누락되었습니다."
                    )
                    validation_result["missingOptions"].append(required_opt)
                    validation_result["isValid"] = False
            
            # 2. 그룹 옵션 검증 (PDF 예시 반영)
            group_validation = self._validate_group_options(category_attrs, provided_option_names)
            validation_result["groupValidation"] = group_validation
            
            if group_validation.get("hasErrors"):
                validation_result["errors"].extend(group_validation["errors"])
                validation_result["isValid"] = False
            
            if group_validation.get("hasWarnings"):
                validation_result["groupWarnings"].extend(group_validation["warnings"])
            
            # 3. 제공된 옵션의 세부 검증
            for provided_opt in product_options:
                opt_name = provided_opt.get('attributeTypeName')
                opt_value = provided_opt.get('attributeValue')
                opt_unit = provided_opt.get('attributeUnit')
                
                if opt_name in attr_map:
                    attr_info = attr_map[opt_name]
                    
                    # 3-1. 데이터 타입 검증
                    expected_type = attr_info.get('dataType')
                    if not self._validate_data_type(opt_value, expected_type):
                        validation_result["errors"].append(
                            f"옵션 '{opt_name}'의 값 '{opt_value}'가 예상 타입 '{expected_type}'과 맞지 않습니다. "
                            f"(예: {self._get_type_example(expected_type)})"
                        )
                        validation_result["invalidOptions"].append(provided_opt)
                        validation_result["isValid"] = False
                    
                    # 3-2. 단위 검증 (PDF 예시 기반)
                    if opt_unit:
                        unit_validation = self._validate_unit(opt_name, opt_unit, attr_info)
                        if not unit_validation["isValid"]:
                            validation_result["errors"].append(unit_validation["message"])
                            validation_result["isValid"] = False
                        elif unit_validation.get("warning"):
                            validation_result["warnings"].append(unit_validation["warning"])
                    elif attr_info.get('usableUnits') and len(attr_info['usableUnits']) > 0:
                        # 단위가 필요한 옵션인데 단위가 없는 경우
                        basic_unit = attr_info.get('basicUnit', '없음')
                        if basic_unit != '없음':
                            validation_result["warnings"].append(
                                f"옵션 '{opt_name}'에 단위를 지정하는 것이 권장됩니다. "
                                f"기본 단위: {basic_unit}, 허용 단위: {', '.join(attr_info['usableUnits'][:5])}"
                            )
                else:
                    validation_result["warnings"].append(
                        f"카테고리에 정의되지 않은 옵션 '{opt_name}'입니다."
                    )
            
            return validation_result
            
        except Exception as e:
            return {
                "isValid": False,
                "error": f"검증 중 오류 발생: {str(e)}",
                "errors": [str(e)],
                "warnings": [],
                "groupWarnings": [],
                "requiredOptions": [],
                "providedOptions": product_options,
                "missingOptions": [],
                "invalidOptions": [],
                "groupValidation": {}
            }
    
    def _validate_data_type(self, value: Any, expected_type: str) -> bool:
        """
        데이터 타입 검증
        
        Args:
            value: 검증할 값
            expected_type: 예상 타입 (STRING, NUMBER, DATE)
            
        Returns:
            bool: 검증 통과 여부
        """
        if expected_type == "STRING":
            return isinstance(value, str)
        elif expected_type == "NUMBER":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == "DATE":
            # 날짜 형식 검증 (YYYY-MM-DD 등)
            import re
            if isinstance(value, str):
                # 간단한 날짜 패턴 검증
                date_patterns = [
                    r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                    r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
                    r'^\d{4}\.\d{2}\.\d{2}$'  # YYYY.MM.DD
                ]
                return any(re.match(pattern, value) for pattern in date_patterns)
            return False
        else:
            return True  # 알 수 없는 타입은 통과
    
    def _validate_group_options(self, category_attrs: List[Dict], provided_option_names: set) -> Dict[str, Any]:
        """
        그룹 옵션 검증 (PDF 예시 기반)
        
        PDF 예시에서 "개당 용량"과 "개당 중량"은 둘 다 groupNumber "1"
        이는 둘 중 하나만 선택해야 함을 의미
        
        Args:
            category_attrs: 카테고리 속성 정보
            provided_option_names: 제공된 옵션명 집합
            
        Returns:
            Dict[str, Any]: 그룹 검증 결과
        """
        group_options = {}
        validation_result = {
            "hasErrors": False,
            "hasWarnings": False,
            "errors": [],
            "warnings": [],
            "groupAnalysis": {}
        }
        
        # 그룹별로 옵션 분류
        for attr in category_attrs:
            group_num = attr.get('groupNumber', 'NONE')
            if group_num != 'NONE':
                if group_num not in group_options:
                    group_options[group_num] = []
                group_options[group_num].append(attr)
        
        # 각 그룹 검증
        for group_num, group_attrs in group_options.items():
            # 그룹 내에서 선택된 옵션들
            selected_in_group = []
            required_in_group = []
            exposed_in_group = []
            
            for attr in group_attrs:
                attr_name = attr['attributeTypeName']
                
                if attr_name in provided_option_names:
                    selected_in_group.append(attr)
                
                if attr.get('required') == 'MANDATORY':
                    required_in_group.append(attr)
                
                if attr.get('exposed') == 'EXPOSED':
                    exposed_in_group.append(attr)
            
            group_analysis = {
                "groupNumber": group_num,
                "totalOptions": len(group_attrs),
                "selectedOptions": [attr['attributeTypeName'] for attr in selected_in_group],
                "requiredOptions": [attr['attributeTypeName'] for attr in required_in_group],
                "exposedOptions": [attr['attributeTypeName'] for attr in exposed_in_group]
            }
            
            validation_result["groupAnalysis"][group_num] = group_analysis
            
            # 그룹 검증 규칙 적용
            if len(selected_in_group) > 1:
                # 오류: 그룹 내에서 여러 옵션 선택
                selected_names = [attr['attributeTypeName'] for attr in selected_in_group]
                validation_result["errors"].append(
                    f"그룹 {group_num}에서는 하나의 옵션만 선택할 수 있습니다. "
                    f"선택된 옵션: {', '.join(selected_names)} "
                    f"(예: '개당 용량' 또는 '개당 중량' 중 하나만 선택)"
                )
                validation_result["hasErrors"] = True
            
            elif len(selected_in_group) == 0 and required_in_group:
                # 경고: 필수 그룹이지만 아무것도 선택하지 않음
                required_names = [attr['attributeTypeName'] for attr in required_in_group]
                if any(attr.get('exposed') == 'EXPOSED' for attr in required_in_group):
                    validation_result["warnings"].append(
                        f"그룹 {group_num}에서 필수 옵션을 선택해야 합니다. "
                        f"선택 가능한 옵션: {', '.join(required_names)}"
                    )
                    validation_result["hasWarnings"] = True
        
        return validation_result
    
    def _validate_unit(self, option_name: str, unit: str, attr_info: Dict) -> Dict[str, Any]:
        """
        단위 검증 (PDF 예시 기반)
        
        PDF 예시:
        - 수량: basicUnit="개", usableUnits=["개", "세트", "박스", "매"]
        - 개당 용량: basicUnit="ml", usableUnits=["cc", "ml", "L"]
        - 개당 중량: basicUnit="없음", usableUnits=["mg", "g", "kg", "t", "oz", "lb"]
        
        Args:
            option_name: 옵션명
            unit: 제공된 단위
            attr_info: 속성 정보
            
        Returns:
            Dict[str, Any]: 단위 검증 결과
        """
        basic_unit = attr_info.get('basicUnit', '없음')
        usable_units = attr_info.get('usableUnits', [])
        
        if not usable_units:
            # 단위가 정의되지 않은 경우
            return {
                "isValid": True,
                "warning": f"옵션 '{option_name}'에 단위 정보가 정의되지 않았습니다."
            }
        
        if unit in usable_units:
            # 허용된 단위 사용
            result = {"isValid": True}
            
            if unit != basic_unit and basic_unit != '없음':
                result["warning"] = (
                    f"옵션 '{option_name}'의 기본 단위는 '{basic_unit}'입니다. "
                    f"'{unit}' 사용 시 정확한 환산값을 확인하세요."
                )
            
            return result
        else:
            # 허용되지 않은 단위 사용
            return {
                "isValid": False,
                "message": (
                    f"옵션 '{option_name}'의 단위 '{unit}'가 허용되지 않습니다. "
                    f"허용 단위: {', '.join(usable_units)} (기본: {basic_unit})"
                )
            }
    
    def _get_type_example(self, data_type: str) -> str:
        """
        데이터 타입별 예시 값 반환
        
        Args:
            data_type: 데이터 타입 (STRING, NUMBER, DATE)
            
        Returns:
            str: 예시 값
        """
        examples = {
            "STRING": "문자열 (예: '검은색', '플라스틱')",
            "NUMBER": "숫자 (예: '1', '10.5', '100')",
            "DATE": "날짜 (예: '2024-01-01', '2024/01/01')"
        }
        return examples.get(data_type, "해당 타입의 값")
    
    def get_option_guide(self, display_category_code: int) -> Dict[str, Any]:
        """
        카테고리별 옵션 설정 가이드 생성
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            Dict[str, Any]: 옵션 설정 가이드
        """
        try:
            # 카테고리 메타정보 조회
            metadata = self.category_client.get_category_metadata(display_category_code)
            data = metadata.get('data', {})
            
            guide = {
                "categoryCode": display_category_code,
                "isSingleItemAllowed": data.get('isAllowSingleItem', False),
                "mandatoryOptions": [],
                "optionalOptions": [],
                "purchaseOptions": [],
                "searchOptions": [],
                "groupOptions": {},
                "unitGuide": {},
                "allowedConditions": data.get('allowedOfferConditions', [])
            }
            
            # 속성별 분류
            attributes = data.get('attributes', [])
            for attr in attributes:
                attr_name = attr.get('attributeTypeName')
                is_required = attr.get('required') == 'MANDATORY'
                is_exposed = attr.get('exposed') == 'EXPOSED'
                group_num = attr.get('groupNumber', 'NONE')
                
                attr_info = {
                    "name": attr_name,
                    "dataType": attr.get('dataType'),
                    "basicUnit": attr.get('basicUnit'),
                    "usableUnits": attr.get('usableUnits', []),
                    "required": attr.get('required'),
                    "exposed": attr.get('exposed'),
                    "groupNumber": group_num
                }
                
                # 필수/선택 분류
                if is_required:
                    guide["mandatoryOptions"].append(attr_info)
                else:
                    guide["optionalOptions"].append(attr_info)
                
                # 구매옵션/검색옵션 분류
                if is_exposed:
                    guide["purchaseOptions"].append(attr_info)
                else:
                    guide["searchOptions"].append(attr_info)
                
                # 그룹 옵션 처리
                if group_num != 'NONE':
                    if group_num not in guide["groupOptions"]:
                        guide["groupOptions"][group_num] = []
                    guide["groupOptions"][group_num].append(attr_info)
                
                # 단위 가이드
                if attr.get('usableUnits'):
                    guide["unitGuide"][attr_name] = {
                        "basicUnit": attr.get('basicUnit'),
                        "allowedUnits": attr.get('usableUnits')
                    }
            
            return guide
            
        except Exception as e:
            return {
                "error": f"가이드 생성 중 오류 발생: {str(e)}",
                "categoryCode": display_category_code
            }
    
    def suggest_option_combinations(self, display_category_code: int) -> List[Dict[str, Any]]:
        """
        권장 옵션 조합 제안 (PDF 가이드 기반)
        
        PDF 예시를 기반으로 실제적인 조합을 제안:
        - 수량 (필수)
        - 개당 용량 OR 개당 중량 (그룹 1에서 선택)
        
        Args:
            display_category_code: 노출카테고리코드
            
        Returns:
            List[Dict[str, Any]]: 권장 옵션 조합 리스트
        """
        try:
            # 카테고리 속성 정보 조회
            category_attrs = self.category_client.get_category_attributes(display_category_code)
            
            # 옵션 분류
            mandatory_exposed = []  # 필수 구매 옵션
            optional_exposed = []   # 선택 구매 옵션
            group_options = {}      # 그룹별 옵션
            
            for attr in category_attrs:
                if attr.get('exposed') == 'EXPOSED':
                    if attr.get('required') == 'MANDATORY':
                        mandatory_exposed.append(attr)
                    else:
                        optional_exposed.append(attr)
                    
                    # 그룹 옵션 분류
                    group_num = attr.get('groupNumber', 'NONE')
                    if group_num != 'NONE':
                        if group_num not in group_options:
                            group_options[group_num] = []
                        group_options[group_num].append(attr)
            
            combinations = []
            
            # 조합 1: 기본 필수 조합 (PDF 예시: 수량만)
            if mandatory_exposed:
                combinations.append({
                    "name": "기본 필수 조합",
                    "description": "필수 구매 옵션만 포함 (예: 수량)",
                    "options": mandatory_exposed,
                    "complexity": "낮음",
                    "example": "수량: 1개",
                    "groupsIncluded": [],
                    "estimatedVariants": 1
                })
            
            # 조합 2: 그룹 옵션 포함 조합 (PDF 예시: 수량 + 개당 용량)
            for group_num, group_attrs in group_options.items():
                exposed_in_group = [attr for attr in group_attrs if attr.get('exposed') == 'EXPOSED']
                
                if exposed_in_group:
                    # 그룹에서 첫 번째 옵션을 예시로 선택
                    example_attr = exposed_in_group[0]
                    group_combination = mandatory_exposed + [example_attr]
                    
                    group_names = [attr['attributeTypeName'] for attr in exposed_in_group]
                    
                    combinations.append({
                        "name": f"그룹 {group_num} 포함 조합",
                        "description": f"필수 옵션 + 그룹 {group_num} 선택 (예: {example_attr['attributeTypeName']})",
                        "options": group_combination,
                        "complexity": "보통",
                        "example": f"수량: 1개 + {example_attr['attributeTypeName']}: 500{example_attr.get('basicUnit', '')}",
                        "groupsIncluded": [group_num],
                        "groupChoices": group_names,
                        "estimatedVariants": len(exposed_in_group)
                    })
            
            # 조합 3: 완전 조합 (모든 그룹에서 하나씩 + 기타 선택 옵션)
            if group_options or optional_exposed:
                complete_options = mandatory_exposed.copy()
                included_groups = []
                example_parts = ["수량: 1개"]
                
                # 각 그룹에서 하나씩 추가
                for group_num, group_attrs in group_options.items():
                    exposed_in_group = [attr for attr in group_attrs if attr.get('exposed') == 'EXPOSED']
                    if exposed_in_group:
                        example_attr = exposed_in_group[0]
                        complete_options.append(example_attr)
                        included_groups.append(group_num)
                        example_parts.append(f"{example_attr['attributeTypeName']}: 500{example_attr.get('basicUnit', '')}")
                
                # 주요 선택 옵션 추가
                important_optional = [
                    attr for attr in optional_exposed
                    if any(keyword in attr['attributeTypeName'].lower() 
                          for keyword in ['색상', '컬러', '사이즈', '크기', '재질', 'material'])
                    and attr.get('groupNumber', 'NONE') == 'NONE'  # 그룹에 속하지 않은 것만
                ]
                
                if important_optional:
                    complete_options.extend(important_optional[:2])  # 최대 2개만
                    for attr in important_optional[:2]:
                        example_parts.append(f"{attr['attributeTypeName']}: 예시값")
                
                if len(complete_options) > len(mandatory_exposed):
                    total_variants = 1
                    for group_num in included_groups:
                        group_size = len([attr for attr in group_options[group_num] 
                                        if attr.get('exposed') == 'EXPOSED'])
                        total_variants *= group_size
                    
                    combinations.append({
                        "name": "완전 조합",
                        "description": "필수 옵션 + 모든 그룹 + 주요 선택 옵션",
                        "options": complete_options,
                        "complexity": "높음",
                        "example": " + ".join(example_parts),
                        "groupsIncluded": included_groups,
                        "estimatedVariants": total_variants,
                        "warning": "상품 변형이 많아질 수 있습니다"
                    })
            
            # 조합이 없는 경우 기본 메시지
            if not combinations:
                combinations.append({
                    "name": "옵션 없음",
                    "description": "이 카테고리에는 구매 옵션이 정의되지 않았습니다",
                    "options": [],
                    "complexity": "없음",
                    "example": "옵션 선택 불가",
                    "groupsIncluded": [],
                    "estimatedVariants": 1
                })
            
            return combinations
            
        except Exception as e:
            return [{
                "error": f"조합 제안 중 오류 발생: {str(e)}",
                "categoryCode": display_category_code,
                "name": "오류",
                "description": "조합 분석 실패",
                "options": [],
                "complexity": "오류"
            }]
    
    def check_group_option_conflicts(self, display_category_code: int, 
                                   selected_options: List[str]) -> Dict[str, Any]:
        """
        그룹 옵션 충돌 검사
        
        Args:
            display_category_code: 노출카테고리코드
            selected_options: 선택된 옵션명 리스트
            
        Returns:
            Dict[str, Any]: 충돌 검사 결과
        """
        try:
            guide = self.get_option_guide(display_category_code)
            group_options = guide.get("groupOptions", {})
            
            conflicts = []
            warnings = []
            
            for group_num, options in group_options.items():
                selected_in_group = [
                    opt["name"] for opt in options 
                    if opt["name"] in selected_options
                ]
                
                if len(selected_in_group) > 1:
                    conflicts.append({
                        "groupNumber": group_num,
                        "conflictingOptions": selected_in_group,
                        "message": f"그룹 {group_num}에서는 하나의 옵션만 선택 가능합니다: {', '.join(selected_in_group)}"
                    })
                elif len(selected_in_group) == 0:
                    # 필수 그룹인지 확인
                    required_in_group = [opt for opt in options if opt.get("required") == "MANDATORY"]
                    if required_in_group:
                        warnings.append({
                            "groupNumber": group_num,
                            "message": f"그룹 {group_num}에서 필수 옵션을 선택해야 합니다: {', '.join([opt['name'] for opt in required_in_group])}"
                        })
            
            return {
                "hasConflicts": len(conflicts) > 0,
                "conflicts": conflicts,
                "warnings": warnings,
                "isValid": len(conflicts) == 0
            }
            
        except Exception as e:
            return {
                "error": f"그룹 옵션 검사 중 오류 발생: {str(e)}",
                "hasConflicts": True,
                "isValid": False
            }