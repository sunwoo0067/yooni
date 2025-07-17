#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 배송상태 변경 히스토리 조회 기능 테스트
shipmentBoxId를 이용한 배송상태 변경 히스토리 조회 데모
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
from order.models import OrderSheetHistoryResponse, DeliveryHistoryItem
from order.utils import (
    print_order_header, print_order_section, print_api_request_info,
    print_order_result, validate_environment_variables,
    get_env_or_default
)


def test_history_response_model():
    """OrderSheetHistoryResponse 모델 테스트"""
    print_order_section("OrderSheetHistoryResponse 모델 테스트")
    
    # 샘플 API 응답 데이터 (배송상태 변경 히스토리)
    sample_response = {
        "code": 200,
        "message": "OK",
        "data": {
            "shipmentBoxId": 642538971006401429,
            "orderId": 9100041863244,
            "currentStatus": "DELIVERING",
            "deliveryCompanyName": "CJ대한통운",
            "invoiceNumber": "1234567890",
            "history": [
                {
                    "status": "ACCEPT",
                    "statusDescription": "결제완료",
                    "changedAt": "2024-04-08T22:54:56",
                    "location": None,
                    "trackingInfo": None
                },
                {
                    "status": "INSTRUCT",
                    "statusDescription": "상품준비중",
                    "changedAt": "2024-04-09T09:15:30",
                    "location": None,
                    "trackingInfo": None
                },
                {
                    "status": "DEPARTURE",
                    "statusDescription": "배송지시",
                    "changedAt": "2024-04-09T15:22:45",
                    "location": "서울물류센터",
                    "trackingInfo": "송장번호 등록"
                },
                {
                    "status": "DELIVERING",
                    "statusDescription": "배송중",
                    "changedAt": "2024-04-10T08:30:12",
                    "location": "강남지점",
                    "trackingInfo": "배송 중"
                }
            ]
        }
    }
    
    try:
        # 모델 생성 테스트
        history_response = OrderSheetHistoryResponse.from_dict(sample_response)
        print("✅ OrderSheetHistoryResponse 모델 생성 성공")
        
        # 기본 정보 테스트
        print(f"✅ 배송번호: {history_response.shipment_box_id}")
        print(f"✅ 주문번호: {history_response.order_id}")
        print(f"✅ 현재 상태: {history_response.current_status}")
        print(f"✅ 택배사: {history_response.delivery_company_name}")
        print(f"✅ 송장번호: {history_response.invoice_number}")
        
        # 배송추적 가능 여부
        has_tracking = history_response.has_delivery_tracking()
        print(f"✅ 배송추적 가능: {'예' if has_tracking else '아니오'}")
        
        # 상태 변경 횟수
        status_changes_count = history_response.get_status_changes_count()
        print(f"✅ 상태 변경 횟수: {status_changes_count}회")
        
        # 최신 상태 정보
        latest_status = history_response.get_latest_status()
        if latest_status:
            print(f"✅ 최신 상태: {latest_status.status} - {latest_status.status_description}")
            print(f"   변경일시: {latest_status.changed_at}")
            print(f"   위치: {latest_status.location or '정보 없음'}")
        
        # 히스토리 출력
        print(f"\n📋 배송상태 변경 히스토리:")
        for i, item in enumerate(history_response.history, 1):
            print(f"   {i}. {item.status} - {item.status_description}")
            print(f"      일시: {item.changed_at}")
            if item.location:
                print(f"      위치: {item.location}")
            if item.tracking_info:
                print(f"      추적정보: {item.tracking_info}")
        
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {str(e)}")


def test_history_client_methods():
    """OrderClient 배송상태 히스토리 조회 메서드 테스트"""
    print_order_section("OrderClient 배송상태 히스토리 조회 메서드 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = OrderClient()
        print("✅ OrderClient 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(client, "get_order_sheet_history"):
            print("✅ get_order_sheet_history 메서드 존재 확인")
        else:
            print("❌ get_order_sheet_history 메서드 없음")
            return
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 vendor_id 테스트
        try:
            client.get_order_sheet_history("INVALID", "123456789")
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 shipment_box_id 테스트
        try:
            client.get_order_sheet_history(vendor_id, "invalid_id")
            print("❌ 잘못된 shipment_box_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 shipment_box_id 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 배송번호 (실제로는 존재하지 않을 가능성 높음)
            test_shipment_box_id = "123456789"
            
            result = client.get_order_sheet_history(vendor_id, test_shipment_box_id)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                has_tracking = result.get("has_delivery_tracking", False)
                history_count = result.get("history_count", 0)
                print(f"   배송추적: {'가능' if has_tracking else '불가능'}")
                print(f"   히스토리 수: {history_count}개")
            else:
                print(f"✅ API 호출 실패 (예상된 결과): {result.get('error')}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
            
    except Exception as e:
        print(f"❌ OrderClient 테스트 실패: {str(e)}")


def example_history_basic():
    """기본 배송상태 변경 히스토리 조회 예제"""
    print_order_section("배송상태 변경 히스토리 조회 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 테스트용 shipmentBoxId (실제 운영 시에는 발주서 목록에서 가져온 값 사용)
    shipment_box_id = "642538971006401429"  # 예시 ID
    
    print_api_request_info(
        "배송상태 변경 히스토리 조회",
        판매자ID=vendor_id,
        배송번호=shipment_box_id,
        API경로=f"/v2/providers/openapi/apis/api/v4/vendors/{vendor_id}/ordersheets/{shipment_box_id}/history"
    )
    
    # API 호출
    result = client.get_order_sheet_history(vendor_id, shipment_box_id)
    
    # 결과 출력
    if result.get("success"):
        print("\n✅ 배송상태 변경 히스토리 조회 성공")
        
        # 기본 정보
        current_status = result.get("current_status", "")
        delivery_company = result.get("delivery_company_name", "")
        invoice_number = result.get("invoice_number", "")
        has_tracking = result.get("has_delivery_tracking", False)
        history_count = result.get("history_count", 0)
        
        print(f"   📦 현재 상태: {current_status}")
        print(f"   🚚 택배사: {delivery_company or '미지정'}")
        print(f"   📋 송장번호: {invoice_number or '미등록'}")
        print(f"   🔍 배송추적: {'가능' if has_tracking else '불가능'}")
        print(f"   📊 상태 변경 횟수: {history_count}회")
        
        # 최신 상태 정보
        latest_status = result.get("latest_status")
        if latest_status:
            print(f"\n   🕐 최신 상태 정보:")
            print(f"      상태: {latest_status.get('status')} - {latest_status.get('statusDescription')}")
            print(f"      일시: {latest_status.get('changedAt')}")
            if latest_status.get('location'):
                print(f"      위치: {latest_status.get('location')}")
        
        # 히스토리 상세
        history = result.get("history", [])
        if history:
            print(f"\n   📋 배송상태 변경 히스토리:")
            for i, item in enumerate(history, 1):
                print(f"      {i}. {item.get('status')} - {item.get('statusDescription')}")
                print(f"         일시: {item.get('changedAt')}")
                if item.get('location'):
                    print(f"         위치: {item.get('location')}")
                if item.get('trackingInfo'):
                    print(f"         추적정보: {item.get('trackingInfo')}")
        
    else:
        print("\n❌ 배송상태 변경 히스토리 조회 실패")
        print(f"   🚨 오류: {result.get('error')}")
        if result.get('code'):
            print(f"   📊 코드: {result.get('code')}")
    
    return result


def example_history_error_handling():
    """배송상태 히스토리 조회 오류 처리 예제"""
    print_order_section("배송상태 히스토리 조회 오류 처리 예제")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    client = OrderClient()
    
    # 존재하지 않는 배송번호 조회 시뮬레이션
    non_existent_shipment_box_id = "999999999999999999"
    
    print_api_request_info(
        "존재하지 않는 배송번호 히스토리 조회",
        판매자ID=vendor_id,
        배송번호=non_existent_shipment_box_id,
        예상결과="400 오류 또는 빈 응답"
    )
    
    result = client.get_order_sheet_history(vendor_id, non_existent_shipment_box_id)
    
    if result.get("success"):
        print("\n✅ 조회 성공 (예상과 다름)")
        history_count = result.get("history_count", 0)
        print(f"   히스토리 수: {history_count}개")
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
            elif "유효하지 않은 배송번호" in error_message:
                print(f"   💡 대응방안: 정상적인 배송번호인지 재확인 필요")
            elif "다른 판매자의 주문" in error_message:
                print(f"   💡 대응방안: 판매자 ID 확인 필요")
            else:
                print(f"   💡 대응방안: 배송번호 재확인 또는 발주서 목록에서 조회")
        elif error_code == 403:
            print(f"   💡 대응방안: 권한 없음, 판매자 ID 및 인증 정보 확인 필요")


def run_history_test():
    """배송상태 변경 히스토리 조회 기능 전체 테스트"""
    print_order_header("쿠팡 파트너스 배송상태 변경 히스토리 조회 기능 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - OrderSheetHistoryResponse 모델")
    print("   - 배송추적 가능 여부 판별")
    print("   - OrderClient 메서드")
    print("   - API 호출 및 응답 처리")
    print("   - 오류 처리")
    
    try:
        # 1. 모델 테스트
        print("\n" + "="*80)
        test_history_response_model()
        
        # 2. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_history_client_methods()
        
        # 3. 기본 조회 예제
        print("\n" + "="*80)
        example_history_basic()
        
        # 4. 오류 처리 예제
        print("\n" + "="*80)
        example_history_error_handling()
        
        print("\n" + "="*80)
        print("🎉 배송상태 변경 히스토리 조회 기능 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    run_history_test()