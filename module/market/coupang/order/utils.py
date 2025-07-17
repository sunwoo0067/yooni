#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 관련 공통 유틸리티
"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime


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
        data=api_response.get("data", []),
        message=api_response.get("message", default_message),
        original_response=api_response,
        next_token=api_response.get("nextToken"),
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
        code=str(api_response.get("code", "")),
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


def print_order_header(title: str, width: int = 80):
    """주문 관련 테스트 헤더 출력"""
    print("=" * width)
    print(f"🛒 {title}")
    print("=" * width)


def print_order_section(title: str, width: int = 60):
    """주문 관련 테스트 섹션 헤더 출력"""
    print(f"\n" + "=" * width)
    print(f"📋 {title}")
    print("=" * width)


def print_api_request_info(api_name: str, **params):
    """API 요청 정보 출력"""
    print(f"\n📤 {api_name} API 요청 중...")
    for key, value in params.items():
        print(f"   {key}: {value}")


def print_order_result(result: Dict[str, Any], success_message: str = "", failure_message: str = ""):
    """주문 API 결과 출력"""
    if result.get("success"):
        print(f"\n✅ {success_message or '성공!'}")
        
        # 발주서 목록 출력
        data = result.get("data", [])
        if isinstance(data, list) and data:
            print(f"   📦 조회된 발주서 수: {len(data)}개")
            
            # 상태별 요약
            status_summary = {}
            for order in data:
                status = order.get("status", "UNKNOWN")
                status_summary[status] = status_summary.get(status, 0) + 1
            
            print(f"   📊 상태별 요약:")
            for status, count in status_summary.items():
                print(f"      - {status}: {count}개")
        
        # 다음 페이지 토큰
        next_token = result.get("next_token")
        if next_token:
            print(f"   🔗 다음 페이지 토큰: {next_token}")
        else:
            print(f"   📄 마지막 페이지입니다")
            
    else:
        print(f"\n❌ {failure_message or '실패:'}")
        print(f"   🚨 오류: {result.get('error')}")
        if result.get('code'):
            print(f"   📊 코드: {result.get('code')}")


def print_order_sheet_details(order_sheet: Dict[str, Any]):
    """발주서 상세 정보 출력"""
    print(f"\n📦 발주서 상세 정보:")
    print(f"   🆔 주문번호: {order_sheet.get('orderId')}")
    print(f"   📅 주문일시: {order_sheet.get('orderedAt')}")
    print(f"   📊 상태: {order_sheet.get('status')}")
    print(f"   💰 배송비: {order_sheet.get('shippingPrice'):,}원")
    
    # 주문자 정보
    orderer = order_sheet.get('orderer', {})
    print(f"   👤 주문자: {orderer.get('name')} ({orderer.get('safeNumber')})")
    
    # 수취인 정보
    receiver = order_sheet.get('receiver', {})
    print(f"   📍 수취인: {receiver.get('name')} ({receiver.get('addr1')} {receiver.get('addr2')})")
    
    # 주문 아이템들
    items = order_sheet.get('orderItems', [])
    print(f"   📋 주문 아이템 ({len(items)}개):")
    for i, item in enumerate(items, 1):
        print(f"      {i}. {item.get('vendorItemName')} - {item.get('shippingCount')}개 ({item.get('orderPrice'):,}원)")


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


def format_currency(amount: int) -> str:
    """금액 포맷팅"""
    return f"{amount:,}원"


def format_datetime(datetime_str: str) -> str:
    """날짜시간 포맷팅"""
    try:
        if 'T' in datetime_str:
            dt = datetime.fromisoformat(datetime_str.replace('T', ' '))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime_str


def calculate_order_summary(order_sheets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """발주서 목록 요약 정보 계산"""
    if not order_sheets:
        return {
            "total_orders": 0,
            "total_amount": 0,
            "total_shipping_fee": 0,
            "status_summary": {},
            "delivery_company_summary": {}
        }
    
    total_amount = 0
    total_shipping_fee = 0
    status_summary = {}
    delivery_company_summary = {}
    
    for sheet in order_sheets:
        # 총 주문 금액 계산
        order_items = sheet.get("orderItems", [])
        order_amount = sum(item.get("orderPrice", 0) for item in order_items)
        total_amount += order_amount
        
        # 배송비 계산
        total_shipping_fee += sheet.get("shippingPrice", 0)
        
        # 상태별 집계
        status = sheet.get("status", "UNKNOWN")
        status_summary[status] = status_summary.get(status, 0) + 1
        
        # 택배사별 집계
        delivery_company = sheet.get("deliveryCompanyName", "미지정")
        delivery_company_summary[delivery_company] = delivery_company_summary.get(delivery_company, 0) + 1
    
    return {
        "total_orders": len(order_sheets),
        "total_amount": total_amount,
        "total_shipping_fee": total_shipping_fee,
        "status_summary": status_summary,
        "delivery_company_summary": delivery_company_summary
    }


def print_order_summary(summary: Dict[str, Any]):
    """발주서 요약 정보 출력"""
    print(f"\n📊 발주서 요약 정보:")
    print(f"   📦 총 발주서 수: {summary['total_orders']}개")
    print(f"   💰 총 주문 금액: {format_currency(summary['total_amount'])}")
    print(f"   🚚 총 배송비: {format_currency(summary['total_shipping_fee'])}")
    
    print(f"\n   📋 상태별 현황:")
    for status, count in summary["status_summary"].items():
        print(f"      - {status}: {count}개")
    
    print(f"\n   🚛 택배사별 현황:")
    for company, count in summary["delivery_company_summary"].items():
        print(f"      - {company}: {count}개")


def create_timeframe_params_for_today(vendor_id: str, status: str, 
                                   start_hour: int = 0, end_hour: int = 23):
    """
    오늘 날짜 기준으로 분단위 전체 조회 파라미터 생성
    
    Args:
        vendor_id: 판매자 ID
        status: 발주서 상태
        start_hour: 시작 시간 (0-23)
        end_hour: 종료 시간 (0-23)
        
    Returns:
        OrderSheetTimeFrameParams: 분단위 전체 조회 파라미터
    """
    from datetime import datetime
    from .models import OrderSheetTimeFrameParams
    
    today = datetime.now().strftime("%Y-%m-%d")
    created_at_from = f"{today}T{start_hour:02d}:00"
    created_at_to = f"{today}T{end_hour:02d}:59"
    
    return OrderSheetTimeFrameParams(
        vendor_id=vendor_id,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        status=status
    )


def create_timeframe_params_for_hours(vendor_id: str, status: str, 
                                    base_datetime: str, hours: int = 12):
    """
    지정된 시간 기준으로 N시간 범위의 분단위 전체 조회 파라미터 생성
    
    Args:
        vendor_id: 판매자 ID
        status: 발주서 상태
        base_datetime: 기준 일시 (yyyy-mm-ddTHH:MM)
        hours: 조회할 시간 범위 (최대 24시간)
        
    Returns:
        OrderSheetTimeFrameParams: 분단위 전체 조회 파라미터
    """
    from datetime import datetime, timedelta
    from .models import OrderSheetTimeFrameParams
    
    if hours > 24:
        raise ValueError("분단위 전체 조회는 최대 24시간까지만 가능합니다")
    
    try:
        base_dt = datetime.strptime(base_datetime, "%Y-%m-%dT%H:%M")
        end_dt = base_dt + timedelta(hours=hours)
        
        created_at_from = base_dt.strftime("%Y-%m-%dT%H:%M")
        created_at_to = end_dt.strftime("%Y-%m-%dT%H:%M")
        
        return OrderSheetTimeFrameParams(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status=status
        )
        
    except ValueError:
        raise ValueError("날짜 형식이 올바르지 않습니다. yyyy-mm-ddTHH:MM 형식을 사용해주세요")