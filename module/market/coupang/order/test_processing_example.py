#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 주문 처리 기능 테스트
상품준비중, 송장업로드, 출고중지, 이미출고, 취소, 장기미배송완료 처리 데모
"""

import os
import sys
from datetime import datetime

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# .env 파일 경로 설정
from dotenv import load_dotenv
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from order.order_client import OrderClient
from order.validators import (
    validate_delivery_company_code, validate_invoice_number,
    validate_vendor_item_id, validate_reason
)
from order.utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, validate_environment_variables,
    get_env_or_default
)


def test_processing_validators():
    """주문 처리 관련 검증 함수 테스트"""
    print_order_section("주문 처리 검증 함수 테스트")
    
    print("🔍 택배사 코드 검증 테스트:")
    test_cases = [
        {"value": "01", "description": "CJ대한통운", "expected": True},
        {"value": "02", "description": "한진택배", "expected": True},
        {"value": "99", "description": "기타", "expected": True},
        {"value": "00", "description": "잘못된 코드", "expected": False},
        {"value": "invalid", "description": "문자 코드", "expected": False},
        {"value": None, "description": "None 값", "expected": False},
    ]
    
    for i, test in enumerate(test_cases, 1):
        try:
            result = validate_delivery_company_code(test["value"])
            status = "✅ 통과" if test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status}")
        except Exception as e:
            status = "✅ 통과" if not test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status} (예외: {type(e).__name__})")
    
    print("\n🔍 송장번호 검증 테스트:")
    invoice_test_cases = [
        {"value": "1234567890", "description": "정상 송장번호", "expected": True},
        {"value": "ABC123DEF456", "description": "영숫자 송장번호", "expected": True},
        {"value": "", "description": "빈 문자열", "expected": False},
        {"value": "   ", "description": "공백 문자열", "expected": False},
        {"value": None, "description": "None 값", "expected": False},
    ]
    
    for i, test in enumerate(invoice_test_cases, 1):
        try:
            result = validate_invoice_number(test["value"])
            status = "✅ 통과" if test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status}")
        except Exception as e:
            status = "✅ 통과" if not test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status} (예외: {type(e).__name__})")


def test_processing_client_methods():
    """OrderClient 주문 처리 메서드 테스트"""
    print_order_section("OrderClient 주문 처리 메서드 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = OrderClient()
        print("✅ OrderClient 초기화 성공")
        
        # 주문 처리 메서드들 존재 확인
        processing_methods = [
            "process_order_to_instruct",
            "upload_invoice",
            "stop_shipping",
            "mark_as_already_shipped",
            "cancel_order_item",
            "complete_long_term_undelivered"
        ]
        
        for method_name in processing_methods:
            if hasattr(client, method_name):
                print(f"✅ {method_name} 메서드 존재 확인")
            else:
                print(f"❌ {method_name} 메서드 없음")
        
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 vendor_id 테스트
        try:
            client.process_order_to_instruct("INVALID", "123456789")
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 배송번호 테스트
        try:
            client.upload_invoice(vendor_id, "invalid_id", "01", "123456789")
            print("❌ 잘못된 shipment_box_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 shipment_box_id 검증 성공: {str(e)}")
        
        # 잘못된 택배사 코드 테스트
        try:
            client.upload_invoice(vendor_id, "123456789", "INVALID", "123456789")
            print("❌ 잘못된 delivery_company_code 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 delivery_company_code 검증 성공: {str(e)}")
            
    except Exception as e:
        print(f"❌ OrderClient 테스트 실패: {str(e)}")


def example_process_to_instruct():
    """상품준비중 처리 예제"""
    print_order_section("상품준비중 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 shipmentBoxId (ACCEPT 상태여야 함)
    shipment_box_id = "642538971006401429"  # 예시 ID
    
    print_api_request_info(
        "상품준비중 처리",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/processing",
        처리조건="ACCEPT(결제완료) 상태에서만 가능"
    )
    
    # API 호출
    result = client.process_order_to_instruct(vendor_id, shipment_box_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 상품준비중 처리 완료")
        
        new_status = result.get("new_status", "")
        print(f"   📦 새로운 상태: {new_status}")
        
        # 처리 결과 정보
        processing_result = result.get("processing_result", {})
        if processing_result.get("success"):
            print(f"   ✅ 처리 성공: {processing_result.get('message')}")
        
        # 주의사항
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
    else:
        print("\n❌ 상품준비중 처리 실패")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_upload_invoice():
    """송장업로드 처리 예제"""
    print_order_section("송장업로드 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 파라미터 (INSTRUCT 상태여야 함)
    shipment_box_id = "642538971006401429"  # 예시 ID
    delivery_company_code = "01"  # CJ대한통운
    invoice_number = "1234567890123"  # 예시 송장번호
    
    print_api_request_info(
        "송장업로드 처리",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        택배사코드=delivery_company_code,
        송장번호=invoice_number,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/invoice",
        처리조건="INSTRUCT(상품준비중) 상태에서만 가능"
    )
    
    # API 호출
    result = client.upload_invoice(vendor_id, shipment_box_id, delivery_company_code, invoice_number)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 송장업로드 처리 완료")
        
        new_status = result.get("new_status", "")
        delivery_company_name = result.get("delivery_company_name", "")
        uploaded_invoice = result.get("invoice_number", "")
        
        print(f"   📦 새로운 상태: {new_status}")
        print(f"   🚚 택배사: {delivery_company_name}")
        print(f"   📋 송장번호: {uploaded_invoice}")
        
        # 처리 결과 정보
        processing_result = result.get("processing_result", {})
        if processing_result.get("success"):
            print(f"   ✅ 처리 성공: {processing_result.get('message')}")
        
        # 주의사항
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
    else:
        print("\n❌ 송장업로드 처리 실패")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_stop_shipping():
    """출고중지완료 처리 예제"""
    print_order_section("출고중지완료 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 파라미터 (INSTRUCT 상태여야 함)
    shipment_box_id = "642538971006401429"  # 예시 ID
    reason = "재고 부족으로 인한 출고 불가"  # 출고중지 사유
    
    print_api_request_info(
        "출고중지완료 처리",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        중지사유=reason,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/stop-shipment",
        처리조건="INSTRUCT(상품준비중) 상태에서만 가능"
    )
    
    # API 호출
    result = client.stop_shipping(vendor_id, shipment_box_id, reason)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 출고중지완료 처리 완료")
        
        new_status = result.get("new_status", "")
        stop_reason = result.get("reason", "")
        
        print(f"   📦 새로운 상태: {new_status}")
        print(f"   📝 중지 사유: {stop_reason}")
        
        # 처리 결과 정보
        processing_result = result.get("processing_result", {})
        if processing_result.get("success"):
            print(f"   ✅ 처리 성공: {processing_result.get('message')}")
        
        # 주의사항
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
    else:
        print("\n❌ 출고중지완료 처리 실패")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_cancel_order_item():
    """주문 상품 취소 처리 예제"""
    print_order_section("주문 상품 취소 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 파라미터
    vendor_item_id = "85872453655"  # 예시 상품 ID
    reason = "상품 품절로 인한 판매자 취소"  # 취소 사유
    
    print_api_request_info(
        "주문 상품 취소 처리",
        판매자ID=vendor_id,
        상품ID=vendor_item_id,
        취소사유=reason,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/item/order-cancel",
        처리조건="판매자 귀책 사유로 취소"
    )
    
    # API 호출
    result = client.cancel_order_item(vendor_id, vendor_item_id, reason)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 주문 상품 취소 처리 완료")
        
        canceled_item_id = result.get("vendor_item_id", "")
        cancel_reason = result.get("reason", "")
        
        print(f"   📦 취소된 상품 ID: {canceled_item_id}")
        print(f"   📝 취소 사유: {cancel_reason}")
        
        # 처리 결과 정보
        processing_result = result.get("processing_result", {})
        if processing_result.get("success"):
            print(f"   ✅ 처리 성공: {processing_result.get('message')}")
        
        # 주의사항
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
    else:
        print("\n❌ 주문 상품 취소 처리 실패")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_complete_long_term_undelivered():
    """장기미배송 배송완료 처리 예제"""
    print_order_section("장기미배송 배송완료 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 shipmentBoxId (DELIVERING 상태여야 함)
    shipment_box_id = "642538971006401429"  # 예시 ID
    
    print_api_request_info(
        "장기미배송 배송완료 처리",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/complete-delivery",
        처리조건="DELIVERING(배송중) 상태에서만 가능"
    )
    
    # API 호출
    result = client.complete_long_term_undelivered(vendor_id, shipment_box_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 장기미배송 배송완료 처리 완료")
        
        new_status = result.get("new_status", "")
        print(f"   📦 새로운 상태: {new_status}")
        
        # 처리 결과 정보
        processing_result = result.get("processing_result", {})
        if processing_result.get("success"):
            print(f"   ✅ 처리 성공: {processing_result.get('message')}")
        
        # 주의사항
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
    else:
        print("\n❌ 장기미배송 배송완료 처리 실패")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
    
    return result


def run_processing_examples():
    """모든 주문 처리 예제 실행"""
    print_order_header("쿠팡 파트너스 주문 처리 기능 예제")
    
    print("\n💡 주문 처리 API 특징:")
    print("   - 상태별로 처리 가능한 작업이 다름")
    print("   - ACCEPT → INSTRUCT → DEPARTURE → DELIVERING → FINAL_DELIVERY")
    print("   - 각 단계별 필요한 정보와 제약사항 존재")
    print("   - 처리 후 되돌릴 수 없는 작업들이 있음")
    print("   - 고객에게 자동 안내 메시지 발송")
    
    try:
        # 1. 검증 함수 테스트
        print("\n" + "="*80)
        test_processing_validators()
        
        # 2. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_processing_client_methods()
        
        # 3. 상품준비중 처리 예제
        print("\n" + "="*80)
        example_process_to_instruct()
        
        # 4. 송장업로드 처리 예제
        print("\n" + "="*80)
        example_upload_invoice()
        
        # 5. 출고중지완료 처리 예제
        print("\n" + "="*80)
        example_stop_shipping()
        
        # 6. 주문 상품 취소 처리 예제
        print("\n" + "="*80)
        example_cancel_order_item()
        
        # 7. 장기미배송 배송완료 처리 예제
        print("\n" + "="*80)
        example_complete_long_term_undelivered()
        
        print("\n" + "="*80)
        print("🎉 모든 주문 처리 기능 예제 실행 완료!")
        
        print("\n💡 실제 운영 시 주의사항:")
        print("   - 각 API는 특정 상태에서만 호출 가능")
        print("   - 송장번호는 정확히 입력 (변경 시 추가 비용)")
        print("   - 취소/중지 사유는 구체적으로 입력")
        print("   - 처리 후 고객에게 자동 안내")
        print("   - 일부 처리는 되돌릴 수 없음")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    # 개발자 모드: 기본 예제만 실행
    print("🔧 개발자 모드: 상품준비중 처리 예제만 실행")
    example_process_to_instruct()
    
    # 전체 예제 실행을 원할 경우 아래 주석 해제
    # run_processing_examples()