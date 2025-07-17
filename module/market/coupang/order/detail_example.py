#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 단건 조회 예제
shipmentBoxId를 이용한 발주서 상세 조회 데모
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
from order.models import OrderSheetDetailResponse
from order.utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, print_order_sheet_details, validate_environment_variables,
    get_env_or_default
)


def example_order_detail_basic():
    """기본 발주서 단건 조회 예제"""
    print_order_section("발주서 단건 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 shipmentBoxId (실제 운영 시에는 발주서 목록에서 가져온 값 사용)
    shipment_box_id = "642538971006401429"  # 예시 ID
    
    print_api_request_info(
        "발주서 단건 조회",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}"
    )
    
    # API 호출
    result = client.get_order_sheet_detail(vendor_id, shipment_box_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 발주서 단건 조회 성공")
        
        # 기본 정보
        order_data = result.get("data", {})
        print(f"   📦 주문번호: {order_data.get('orderId')}")
        print(f"   📅 주문일시: {order_data.get('orderedAt')}")
        print(f"   📊 상태: {order_data.get('status')}")
        
        # 배송지 정보 (변경 확인용)
        receiver_info = result.get("receiver_info", {})
        print(f"\n   📍 수취인 정보:")
        print(f"      이름: {receiver_info.get('name')}")
        print(f"      주소: {receiver_info.get('addr1')} {receiver_info.get('addr2')}")
        print(f"      연락처: {receiver_info.get('safeNumber')}")
        
        # 상품명 검증 정보
        product_validation = result.get("product_validation_info", [])
        has_mismatch = result.get("has_product_name_mismatch", False)
        print(f"\n   🔍 상품명 검증 결과:")
        if has_mismatch:
            print("      ⚠️  상품명 불일치 발견!")
            for info in product_validation:
                if not info["isMatched"]:
                    print(f"         - 옵션ID: {info['vendorItemId']}")
                    print(f"         - 등록명: {info['sellerFullName']}")
                    print(f"         - 노출명: {info['vendorItemName']}")
        else:
            print("      ✅ 모든 상품명이 일치합니다")
        
        # 경고 메시지
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
        # 배송 요약
        shipping_summary = result.get("shipping_summary", {})
        print(f"\n   🚛 배송 정보:")
        print(f"      택배사: {shipping_summary.get('deliveryCompanyName', '미지정')}")
        print(f"      운송장번호: {shipping_summary.get('invoiceNumber', '미등록')}")
        print(f"      출고일: {shipping_summary.get('inTrasitDateTime', '미출고')}")
        
    else:
        print("\n❌ 발주서 단건 조회 실패")
        print(f"   🚨 오류: {result.get('error')}")
        if result.get('code'):
            print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_order_detail_with_validation():
    """발주서 단건 조회 + 자동 검증 예제"""
    print_order_section("발주서 단건 조회 + 자동 검증 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 shipmentBoxId
    shipment_box_id = "642538971006401429"  # 예시 ID
    
    print_api_request_info(
        "발주서 단건 조회 + 자동 검증",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        검증기능="배송지 변경 확인, 상품명 일치 확인, 출고 준비도 확인"
    )
    
    # API 호출 (자동 검증 포함)
    result = client.get_order_sheet_with_validation(vendor_id, shipment_box_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 발주서 단건 조회 + 검증 완료")
        
        # 검증 결과
        validation_result = result.get("validation_result", {})
        print(f"\n   📋 자동 검증 결과:")
        print(f"      배송지 변경 경고: {'⚠️  예' if validation_result.get('address_change_warning') else '✅ 아니오'}")
        print(f"      상품명 불일치 경고: {'⚠️  예' if validation_result.get('product_mismatch_warning') else '✅ 아니오'}")
        print(f"      출고 준비 완료: {'✅ 예' if validation_result.get('shipping_ready') else '❌ 아니오'}")
        
        # 검증 요약
        validation_summary = validation_result.get("validation_summary", [])
        if validation_summary:
            print(f"\n   📝 검증 요약:")
            for item in validation_summary:
                print(f"      - {item}")
        
        # 출고 가능 여부 판단
        if validation_result.get("shipping_ready"):
            print(f"\n   🚀 출고 가능 상태입니다!")
        else:
            print(f"\n   🛑 출고 보류 필요!")
            print(f"      👉 상품명 불일치 확인 후 온라인 문의 접수 필요")
    else:
        print("\n❌ 발주서 단건 조회 실패")
        print(f"   🚨 오류: {result.get('error')}")
    
    return result


def example_order_detail_validation_scenarios():
    """다양한 검증 시나리오 예제"""
    print_order_section("발주서 검증 시나리오 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 시나리오별 테스트
    test_scenarios = [
        {
            "name": "정상 배송번호",
            "shipment_box_id": "642538971006401429",
            "description": "유효한 배송번호로 조회"
        },
        {
            "name": "숫자 문자열 배송번호",
            "shipment_box_id": "123456789",
            "description": "문자열 형태의 숫자 배송번호"
        },
        {
            "name": "잘못된 배송번호 (문자포함)",
            "shipment_box_id": "invalid123abc",
            "description": "잘못된 형식의 배송번호 (오류 예상)"
        },
        {
            "name": "음수 배송번호",
            "shipment_box_id": "-123",
            "description": "음수 배송번호 (오류 예상)"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 시나리오 {i}: {scenario['name']}")
        print(f"   설명: {scenario['description']}")
        print(f"   배송번호: {scenario['shipment_box_id']}")
        
        try:
            result = client.get_order_sheet_detail(vendor_id, scenario['shipment_box_id'])
            
            if result.get("success"):
                print(f"   ✅ 조회 성공")
                order_data = result.get("data", {})
                print(f"      주문번호: {order_data.get('orderId', 'N/A')}")
                print(f"      상태: {order_data.get('status', 'N/A')}")
            else:
                print(f"   ❌ 조회 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 예외 발생: {str(e)}")


def example_order_detail_error_handling():
    """오류 처리 예제"""
    print_order_section("발주서 단건 조회 오류 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 존재하지 않는 발주서 조회 시뮬레이션
    non_existent_shipment_box_id = "999999999999999999"
    
    print_api_request_info(
        "존재하지 않는 발주서 조회",
        판매자ID=vendor_id,
        배송번호=non_existent_shipment_box_id,
        예상결과="404 오류 또는 빈 응답"
    )
    
    result = client.get_order_sheet_detail(vendor_id, non_existent_shipment_box_id)
    
    if result.get("success"):
        print("\n✅ 조회 성공 (예상과 다름)")
    else:
        print("\n❌ 조회 실패 (예상된 결과)")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
        
        # 오류 코드별 대응 방안 제시
        error_code = result.get('code')
        if error_code == 400:
            print(f"   💡 대응방안: 배송번호 확인 또는 반품/취소 상태 확인")
        elif error_code == 404:
            print(f"   💡 대응방안: 존재하지 않는 발주서, 배송번호 재확인 필요")
        elif error_code == 403:
            print(f"   💡 대응방안: 권한 없음, 판매자 ID 확인 필요")


def run_detail_examples():
    """모든 발주서 단건 조회 예제 실행"""
    print_order_header("쿠팡 파트너스 발주서 단건 조회 예제")
    
    print("\n💡 발주서 단건 조회 API 특징:")
    print("   - shipmentBoxId로 특정 발주서 상세 조회")
    print("   - 배송지 변경 확인 (ACCEPT, INSTRUCT 상태)")
    print("   - 상품명 일치 확인 (출고 전 필수)")
    print("   - 실시간 배송 정보 확인")
    
    try:
        # 1. 기본 단건 조회
        print("\n" + "="*80)
        example_order_detail_basic()
        
        # 2. 자동 검증 포함 조회
        print("\n" + "="*80)
        example_order_detail_with_validation()
        
        # 3. 검증 시나리오 테스트
        print("\n" + "="*80)
        example_order_detail_validation_scenarios()
        
        # 4. 오류 처리 예제
        print("\n" + "="*80)
        example_order_detail_error_handling()
        
        print("\n" + "="*80)
        print("🎉 모든 발주서 단건 조회 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    # 개발자 모드: 기본 예제만 실행
    print("🔧 개발자 모드: 기본 발주서 단건 조회 예제만 실행")
    example_order_detail_basic()
    
    # 전체 예제 실행을 원할 경우 아래 주석 해제
    # run_detail_examples()