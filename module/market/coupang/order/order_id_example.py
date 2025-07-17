#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 주문번호별 조회 예제
orderId를 이용한 발주서 목록 조회 데모 (분리배송 포함)
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
from order.models import OrderSheetByOrderIdResponse
from order.utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, validate_environment_variables,
    get_env_or_default
)


def example_order_by_id_basic():
    """기본 주문번호별 발주서 조회 예제"""
    print_order_section("주문번호별 발주서 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 orderId (실제 운영 시에는 발주서 목록에서 가져온 값 사용)
    order_id = "9100041863244"  # 예시 ID
    
    print_api_request_info(
        "주문번호별 발주서 조회",
        판매자ID=vendor_id,
        주문번호=order_id,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/{order_id}/ordersheets"
    )
    
    # API 호출
    result = client.get_order_sheets_by_order_id(vendor_id, order_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 주문번호별 발주서 조회 성공")
        
        # 기본 정보
        total_count = result.get("total_count", 0)
        shipment_box_ids = result.get("shipment_box_ids", [])
        is_split = result.get("is_split_shipping", False)
        
        print(f"   📦 총 발주서 수: {total_count}개")
        print(f"   🚚 분리배송 여부: {'예' if is_split else '아니오'}")
        print(f"   📋 배송번호 목록: {shipment_box_ids}")
        
        # 수취인 정보
        receiver_info = result.get("receiver_info", {})
        print(f"\n   📍 수취인 정보:")
        print(f"      이름: {receiver_info.get('name')}")
        print(f"      주소: {receiver_info.get('addr1')} {receiver_info.get('addr2')}")
        print(f"      연락처: {receiver_info.get('safeNumber')}")
        
        # 상품명 검증 정보
        product_validation = result.get("product_validation_summary", {})
        has_mismatch = result.get("has_product_name_mismatch", False)
        total_items = product_validation.get("totalItems", 0)
        mismatch_count = product_validation.get("mismatchCount", 0)
        mismatch_rate = product_validation.get("mismatchRate", 0)
        
        print(f"\n   🔍 상품명 검증 결과:")
        print(f"      총 상품 수: {total_items}개")
        if has_mismatch:
            print(f"      ⚠️  불일치 상품: {mismatch_count}개 ({mismatch_rate}%)")
        else:
            print(f"      ✅ 모든 상품명이 일치합니다")
        
        # 상태별 요약
        status_summary = result.get("status_summary", {})
        print(f"\n   📊 상태별 요약:")
        for status, count in status_summary.items():
            print(f"      {status}: {count}개")
        
        # 총 주문 금액
        total_amount = result.get("total_order_amount", 0)
        print(f"\n   💰 총 주문 금액: {total_amount:,}원")
        
        # 경고 메시지
        warnings = result.get("warnings", [])
        if warnings:
            print(f"\n   🚨 주의사항:")
            for warning in warnings:
                print(f"      {warning}")
        
        # 배송 상세 정보
        shipping_summaries = result.get("shipping_summaries", [])
        print(f"\n   🚛 배송 상세 정보:")
        for i, shipping in enumerate(shipping_summaries, 1):
            print(f"      {i}. 배송번호: {shipping.get('shipmentBoxId')}")
            print(f"         상태: {shipping.get('status')}")
            print(f"         택배사: {shipping.get('deliveryCompanyName', '미지정')}")
            print(f"         운송장: {shipping.get('invoiceNumber', '미등록')}")
            print(f"         출고일: {shipping.get('inTrasitDateTime', '미출고')}")
        
    else:
        print("\n❌ 주문번호별 발주서 조회 실패")
        print(f"   🚨 오류: {result.get('error')}")
        if result.get('code'):
            print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_order_by_id_with_validation():
    """주문번호별 발주서 조회 + 자동 검증 예제"""
    print_order_section("주문번호별 발주서 조회 + 자동 검증 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 orderId
    order_id = "9100041863244"  # 예시 ID
    
    print_api_request_info(
        "주문번호별 발주서 조회 + 자동 검증",
        판매자ID=vendor_id,
        주문번호=order_id,
        검증기능="분리배송 확인, 배송지 변경 확인, 상품명 일치 확인, 출고 준비도 확인"
    )
    
    # API 호출 (자동 검증 포함)
    result = client.get_order_sheets_by_order_id_with_validation(vendor_id, order_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 주문번호별 발주서 조회 + 검증 완료")
        
        # 기본 정보
        total_count = result.get("total_count", 0)
        is_split = result.get("is_split_shipping", False)
        print(f"   📦 총 발주서 수: {total_count}개")
        print(f"   🚚 분리배송: {'예' if is_split else '아니오'}")
        
        # 검증 결과
        validation_result = result.get("validation_result", {})
        print(f"\n   📋 자동 검증 결과:")
        print(f"      분리배송 경고: {'⚠️  예' if validation_result.get('split_shipping_warning') else '✅ 아니오'}")
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
        print("\n❌ 주문번호별 발주서 조회 실패")
        print(f"   🚨 오류: {result.get('error')}")
    
    return result


def example_order_by_id_validation_scenarios():
    """다양한 검증 시나리오 예제"""
    print_order_section("주문번호별 조회 검증 시나리오 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 시나리오별 테스트
    test_scenarios = [
        {
            "name": "정상 주문번호",
            "order_id": "9100041863244",
            "description": "유효한 주문번호로 조회"
        },
        {
            "name": "숫자 문자열 주문번호",
            "order_id": "123456789",
            "description": "문자열 형태의 숫자 주문번호"
        },
        {
            "name": "잘못된 주문번호 (문자포함)",
            "order_id": "invalid123abc",
            "description": "잘못된 형식의 주문번호 (오류 예상)"
        },
        {
            "name": "음수 주문번호",
            "order_id": "-123",
            "description": "음수 주문번호 (오류 예상)"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 시나리오 {i}: {scenario['name']}")
        print(f"   설명: {scenario['description']}")
        print(f"   주문번호: {scenario['order_id']}")
        
        try:
            result = client.get_order_sheets_by_order_id(vendor_id, scenario['order_id'])
            
            if result.get("success"):
                print(f"   ✅ 조회 성공")
                total_count = result.get("total_count", 0)
                is_split = result.get("is_split_shipping", False)
                print(f"      발주서 수: {total_count}개")
                print(f"      분리배송: {'예' if is_split else '아니오'}")
            else:
                print(f"   ❌ 조회 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 예외 발생: {str(e)}")


def example_order_by_id_error_handling():
    """오류 처리 예제"""
    print_order_section("주문번호별 조회 오류 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 존재하지 않는 주문번호 조회 시뮬레이션
    non_existent_order_id = "999999999999999999"
    
    print_api_request_info(
        "존재하지 않는 주문번호 조회",
        판매자ID=vendor_id,
        주문번호=non_existent_order_id,
        예상결과="400 오류 또는 빈 응답"
    )
    
    result = client.get_order_sheets_by_order_id(vendor_id, non_existent_order_id)
    
    if result.get("success"):
        print("\n✅ 조회 성공 (예상과 다름)")
        total_count = result.get("total_count", 0)
        print(f"   발주서 수: {total_count}개")
    else:
        print("\n❌ 조회 실패 (예상된 결과)")
        print(f"   🚨 오류: {result.get('error')}")
        print(f"   📊 코드: {result.get('code')}")
        
        # 오류 코드별 대응 방안 제시
        error_code = result.get('code')
        if error_code == 400:
            error_message = result.get('error', '')
            if "취소 또는 반품" in error_message:
                print(f"   💡 대응방안: 반품/취소 요청 목록 조회 API 통해 확인")
            elif "유효하지 않은 주문번호" in error_message:
                print(f"   💡 대응방안: 정상적인 주문번호인지 재확인 필요")
            elif "다른 판매자의 주문" in error_message:
                print(f"   💡 대응방안: 판매자 ID 확인 필요")
            else:
                print(f"   💡 대응방안: 주문번호 재확인 또는 발주서 목록에서 조회")
        elif error_code == 403:
            print(f"   💡 대응방안: 권한 없음, 판매자 ID 및 인증 정보 확인 필요")


def example_split_shipping_demo():
    """분리배송 시뮬레이션 예제"""
    print_order_section("분리배송 시뮬레이션 예제")
    
    print("💡 분리배송 예제 (시뮬레이션 데이터):")
    print("   하나의 주문번호(orderId)에 여러 배송번호(shipmentBoxId)가 존재하는 경우")
    
    # 시뮬레이션 데이터 생성
    sample_split_response = {
        "code": 200,
        "message": "OK",
        "data": [
            {
                "shipmentBoxId": 642538971006401429,
                "orderId": 9100041863244,
                "orderedAt": "2024-04-08T22:54:46",
                "status": "INSTRUCT",
                "orderItems": [{"vendorItemId": 1, "vendorItemName": "상품1", "sellerProductName": "상품1", "sellerProductItemName": "옵션1"}],
                "receiver": {"name": "홍길동", "addr1": "서울시", "addr2": "강남구"},
                "orderer": {"name": "홍길동"}
            },
            {
                "shipmentBoxId": 642538971006401430,
                "orderId": 9100041863244,
                "orderedAt": "2024-04-08T22:54:46", 
                "status": "DEPARTURE",
                "orderItems": [{"vendorItemId": 2, "vendorItemName": "상품2", "sellerProductName": "상품2", "sellerProductItemName": "옵션2"}],
                "receiver": {"name": "홍길동", "addr1": "서울시", "addr2": "강남구"},
                "orderer": {"name": "홍길동"}
            }
        ]
    }
    
    try:
        # 시뮬레이션 데이터로 모델 테스트
        order_response = OrderSheetByOrderIdResponse.from_dict(sample_split_response)
        
        print(f"\n📦 분리배송 분석 결과:")
        print(f"   주문번호: {order_response.get_order_id()}")
        print(f"   총 발주서 수: {order_response.get_total_count()}개")
        print(f"   배송번호 목록: {order_response.get_shipment_box_ids()}")
        print(f"   분리배송 여부: {'예' if order_response.is_split_shipping() else '아니오'}")
        
        # 상태별 요약
        status_summary = order_response.get_status_summary()
        print(f"\n   📊 상태별 요약:")
        for status, count in status_summary.items():
            print(f"      {status}: {count}개")
        
        # 배송 요약
        shipping_summaries = order_response.get_shipping_summary()
        print(f"\n   🚛 배송 상세:")
        for i, shipping in enumerate(shipping_summaries, 1):
            print(f"      {i}. 배송번호: {shipping['shipmentBoxId']}")
            print(f"         상태: {shipping['status']}")
        
        print(f"\n   💡 분리배송 관리 포인트:")
        print(f"      - 각 배송번호별로 개별 상태 관리 필요")
        print(f"      - 모든 발주서가 완료되어야 주문 완료")
        print(f"      - 배송지 변경은 모든 발주서에 동일하게 적용")
        
    except Exception as e:
        print(f"❌ 시뮬레이션 실패: {str(e)}")


def run_order_id_examples():
    """모든 주문번호별 발주서 조회 예제 실행"""
    print_order_header("쿠팡 파트너스 발주서 주문번호별 조회 예제")
    
    print("\n💡 주문번호별 발주서 조회 API 특징:")
    print("   - orderId로 해당 주문의 모든 발주서 조회")
    print("   - 분리배송 시 여러 shipmentBoxId 반환")
    print("   - 배송지 변경 확인 (ACCEPT, INSTRUCT 상태)")
    print("   - 상품명 일치 확인 (출고 전 필수)")
    print("   - 실시간 배송 정보 확인")
    
    try:
        # 1. 기본 주문번호별 조회
        print("\n" + "="*80)
        example_order_by_id_basic()
        
        # 2. 자동 검증 포함 조회
        print("\n" + "="*80)
        example_order_by_id_with_validation()
        
        # 3. 검증 시나리오 테스트
        print("\n" + "="*80)
        example_order_by_id_validation_scenarios()
        
        # 4. 오류 처리 예제
        print("\n" + "="*80)
        example_order_by_id_error_handling()
        
        # 5. 분리배송 시뮬레이션
        print("\n" + "="*80)
        example_split_shipping_demo()
        
        print("\n" + "="*80)
        print("🎉 모든 주문번호별 발주서 조회 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    # 개발자 모드: 기본 예제만 실행
    print("🔧 개발자 모드: 기본 주문번호별 발주서 조회 예제만 실행")
    example_order_by_id_basic()
    
    # 전체 예제 실행을 원할 경우 아래 주석 해제
    # run_order_id_examples()