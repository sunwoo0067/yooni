#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 공통 유틸리티
"""

import os
import sys
from typing import Dict, Any, Optional


def setup_project_path():
    """프로젝트 루트를 Python 경로에 추가"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..', '..')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def format_api_response(
    success: bool,
    data: Optional[Any] = None,
    message: str = "",
    error: str = "",
    code: str = "",
    original_response: Optional[Dict[str, Any]] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    API 응답을 일관된 형식으로 포맷팅
    
    Args:
        success: 성공 여부
        data: 응답 데이터
        message: 성공 메시지
        error: 오류 메시지
        code: 응답 코드
        original_response: 원본 응답
        **extra_fields: 추가 필드들
        
    Returns:
        Dict[str, Any]: 포맷팅된 응답
    """
    response = {
        "success": success,
        "originalResponse": original_response
    }
    
    if success:
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
    else:
        if error:
            response["error"] = error
        if code:
            response["code"] = code
    
    # 추가 필드들 추가
    response.update(extra_fields)
    
    return response


def handle_api_success(api_response: Dict[str, Any], default_message: str = "", **extra_fields) -> Dict[str, Any]:
    """
    성공 API 응답 처리
    
    Args:
        api_response: API 원본 응답
        default_message: 기본 메시지
        **extra_fields: 추가 필드들
        
    Returns:
        Dict[str, Any]: 처리된 응답
    """
    return format_api_response(
        success=True,
        data=api_response.get("data", {}),
        message=api_response.get("message", default_message),
        original_response=api_response,
        **extra_fields
    )


def handle_api_error(api_response: Dict[str, Any], default_error: str = "알 수 없는 오류") -> Dict[str, Any]:
    """
    오류 API 응답 처리
    
    Args:
        api_response: API 원본 응답
        default_error: 기본 오류 메시지
        
    Returns:
        Dict[str, Any]: 처리된 응답
    """
    return format_api_response(
        success=False,
        error=api_response.get("message", default_error),
        code=api_response.get("code"),
        original_response=api_response
    )


def handle_exception_error(exception: Exception, operation: str) -> Dict[str, Any]:
    """
    예외 처리
    
    Args:
        exception: 발생한 예외
        operation: 수행 중이던 작업
        
    Returns:
        Dict[str, Any]: 처리된 응답
    """
    return format_api_response(
        success=False,
        error=f"{operation} 실패: {str(exception)}",
        original_response=None
    )


def print_test_header(title: str, width: int = 60):
    """테스트 헤더 출력"""
    print("=" * width)
    print(f"🚀 {title}")
    print("=" * width)


def print_test_section(title: str, width: int = 50):
    """테스트 섹션 헤더 출력"""
    print(f"\n" + "=" * width)
    print(f"📋 {title}")
    print("=" * width)


def print_api_request_info(api_name: str, **params):
    """API 요청 정보 출력"""
    print(f"\n📤 {api_name} API 요청 중...")
    for key, value in params.items():
        print(f"   {key}: {value}")


def print_api_result(result: Dict[str, Any], success_message: str = "", failure_message: str = ""):
    """API 결과 출력"""
    if result.get("success"):
        print(f"\n✅ {success_message or '성공!'}")
        # 결과 세부 정보 출력
        for key, value in result.items():
            if key not in ["success", "originalResponse"] and value is not None:
                print(f"   📝 {key}: {value}")
    else:
        print(f"\n❌ {failure_message or '실패:'}")
        print(f"   🚨 오류: {result.get('error')}")
        if result.get('code'):
            print(f"   📊 코드: {result.get('code')}")


def get_env_or_default(env_var: str, default_value: str, description: str = "") -> str:
    """환경변수 값을 가져오거나 기본값 반환"""
    value = os.getenv(env_var, default_value)
    if value == default_value and description:
        print(f"⚠️  {env_var} 환경변수가 설정되지 않아 기본값 사용: {description}")
    return value


def validate_environment_variables(*required_vars: str) -> bool:
    """필수 환경변수들이 설정되어 있는지 확인"""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 환경변수 설정이 필요합니다:")
        for var in missing_vars:
            print(f"   export {var}=your_value")
        return False
    
    return True