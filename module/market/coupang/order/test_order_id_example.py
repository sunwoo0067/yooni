#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 주문번호별 조회 기능 테스트
orderId 검증 및 API 호출 테스트
"""

import os
import sys

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
from order.validators import validate_order_id, is_valid_order_id
from order.utils import (
    print_order_header, print_order_section,
    validate_environment_variables, get_env_or_default
)


def test_order_id_validation():
    """주문번호 검증 함수 테스트"""
    print_order_section("주문번호 검증 함수 테스트")
    
    test_cases = [
        {"value": "9100041863244", "description": "유효한 문자열 숫자", "expected": True},
        {"value": 9100041863244, "description": "유효한 정수", "expected": True},
        {"value": "123456789", "description": "짧은 숫자 문자열", "expected": True},
        {"value": 123456789, "description": "짧은 정수", "expected": True},
        {"value": "invalid123", "description": "문자가 포함된 문자열", "expected": False},
        {"value": "abc123def", "description": "앞뒤 문자가 있는 문자열", "expected": False},
        {"value": "-123", "description": "음수 문자열", "expected": False},
        {"value": -123, "description": "음수 정수", "expected": False},
        {"value": "0", "description": "0 문자열", "expected": False},
        {"value": 0, "description": "0 정수", "expected": False},
        {"value": None, "description": "None 값", "expected": False},
        {"value": "", "description": "빈 문자열", "expected": False},
        {"value": "  ", "description": "공백 문자열", "expected": False},
    ]
    
    print("🔍 is_valid_order_id() 함수 테스트:")
    for i, test in enumerate(test_cases, 1):
        try:
            result = is_valid_order_id(test["value"])
            status = "✅ 통과" if result == test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status}")
            if result != test["expected"]:
                print(f"       예상: {test['expected']}, 실제: {result}")
        except Exception as e:
            status = "✅ 통과" if not test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status} (예외: {type(e).__name__})")
    
    print("\n🔍 validate_order_id() 함수 테스트:")
    for i, test in enumerate(test_cases, 1):
        try:
            validated_value = validate_order_id(test["value"])
            if test["expected"]:
                print(f"   {i:2d}. {test['description']}: ✅ 통과 (결과: {validated_value})")
            else:
                print(f"   {i:2d}. {test['description']}: ❌ 실패 (예외가 발생해야 함)")
        except Exception as e:
            if not test["expected"]:
                print(f"   {i:2d}. {test['description']}: ✅ 통과 (예외: {str(e)})")
            else:
                print(f"   {i:2d}. {test['description']}: ❌ 실패 (예상치 못한 예외: {str(e)})")


def test_order_by_id_response_model():
    """OrderSheetByOrderIdResponse 모델 테스트"""
    print_order_section("OrderSheetByOrderIdResponse 모델 테스트")
    
    # 샘플 API 응답 데이터 (분리배송 시뮬레이션)
    sample_response = {
        "code": 200,
        "message": "OK",
        "data": [
            {
                "shipmentBoxId": 642538971006401429,
                "orderId": 9100041863244,
                "orderedAt": "2024-04-08T22:54:46",
                "orderer": {
                    "name": "이*주",
                    "email": "",
                    "safeNumber": "0502-***6-3501",
                    "ordererNumber": None
                },
                "paidAt": "2024-04-08T22:54:56",
                "status": "INSTRUCT",
                "shippingPrice": 3000,
                "remotePrice": 0,
                "remoteArea": False,
                "parcelPrintMessage": "문 앞",
                "splitShipping": True,
                "ableSplitShipping": True,
                "receiver": {
                    "name": "이*주",
                    "safeNumber": "0502-***6-3501",
                    "receiverNumber": None,
                    "addr1": "서울시 강남구",
                    "addr2": "테헤란로 123번지",
                    "postCode": "12345"
                },
                "orderItems": [
                    {
                        "vendorItemPackageId": 0,
                        "vendorItemPackageName": "상품1",
                        "productId": 7313251147,
                        "vendorItemId": 85872453655,
                        "vendorItemName": "상품1, 2개",
                        "shippingCount": 2,
                        "salesPrice": 20000,
                        "orderPrice": 40000,
                        "discountPrice": 0,
                        "instantCouponDiscount": 0,
                        "downloadableCouponDiscount": 0,
                        "coupangDiscount": 0,
                        "externalVendorSkuCode": "",
                        "etcInfoHeader": None,
                        "etcInfoValue": None,
                        "etcInfoValues": None,
                        "sellerProductId": 14091699106,
                        "sellerProductName": "상품1",
                        "sellerProductItemName": "2개 세트",  # 불일치 의도
                        "firstSellerProductItemName": "2개 세트",
                        "cancelCount": 0,
                        "holdCountForCancel": 0,
                        "estimatedShippingDate": "2024-04-09",
                        "plannedShippingDate": "",
                        "invoiceNumberUploadDate": None,
                        "extraProperties": {},
                        "pricingBadge": False,
                        "usedProduct": False,
                        "confirmDate": None,
                        "deliveryChargeTypeName": "유료",
                        "upBundleVendorItemId": None,
                        "upBundleVendorItemName": None,
                        "upBundleSize": None,
                        "upBundleItem": False,
                        "canceled": False
                    }
                ],
                "overseaShippingInfoDto": {
                    "personalCustomsClearanceCode": "",
                    "ordererSsn": "",
                    "ordererPhoneNumber": ""
                },
                "deliveryCompanyName": "CJ대한통운",
                "invoiceNumber": None,
                "inTrasitDateTime": None,
                "deliveredDate": None,
                "refer": "안드로이드앱",
                "shipmentType": "THIRD_PARTY"
            },
            {
                "shipmentBoxId": 642538971006401430,
                "orderId": 9100041863244,
                "orderedAt": "2024-04-08T22:54:46",
                "orderer": {
                    "name": "이*주",
                    "email": "",
                    "safeNumber": "0502-***6-3501",
                    "ordererNumber": None
                },
                "paidAt": "2024-04-08T22:54:56",
                "status": "DEPARTURE",
                "shippingPrice": 0,
                "remotePrice": 0,
                "remoteArea": False,
                "parcelPrintMessage": "문 앞",
                "splitShipping": True,
                "ableSplitShipping": True,
                "receiver": {
                    "name": "이*주",
                    "safeNumber": "0502-***6-3501",
                    "receiverNumber": None,
                    "addr1": "서울시 강남구",
                    "addr2": "테헤란로 123번지",
                    "postCode": "12345"
                },
                "orderItems": [
                    {
                        "vendorItemPackageId": 0,
                        "vendorItemPackageName": "상품2",
                        "productId": 7313251148,
                        "vendorItemId": 85872453656,
                        "vendorItemName": "상품2, 1개",
                        "shippingCount": 1,
                        "salesPrice": 30000,
                        "orderPrice": 30000,
                        "discountPrice": 0,
                        "instantCouponDiscount": 0,
                        "downloadableCouponDiscount": 0,
                        "coupangDiscount": 0,
                        "externalVendorSkuCode": "",
                        "etcInfoHeader": None,
                        "etcInfoValue": None,
                        "etcInfoValues": None,
                        "sellerProductId": 14091699107,
                        "sellerProductName": "상품2",
                        "sellerProductItemName": "1개",
                        "firstSellerProductItemName": "1개",
                        "cancelCount": 0,
                        "holdCountForCancel": 0,
                        "estimatedShippingDate": "2024-04-09",
                        "plannedShippingDate": "",
                        "invoiceNumberUploadDate": "2024-04-09T19:15:38",
                        "extraProperties": {},
                        "pricingBadge": False,
                        "usedProduct": False,
                        "confirmDate": None,
                        "deliveryChargeTypeName": "무료",
                        "upBundleVendorItemId": None,
                        "upBundleVendorItemName": None,
                        "upBundleSize": None,
                        "upBundleItem": False,
                        "canceled": False
                    }
                ],
                "overseaShippingInfoDto": {
                    "personalCustomsClearanceCode": "",
                    "ordererSsn": "",
                    "ordererPhoneNumber": ""
                },
                "deliveryCompanyName": "한진택배",
                "invoiceNumber": "***00402084",
                "inTrasitDateTime": "2024-04-09 22:41:00",
                "deliveredDate": None,
                "refer": "안드로이드앱",
                "shipmentType": "THIRD_PARTY"
            }
        ]
    }
    
    try:
        # 모델 생성 테스트
        order_response = OrderSheetByOrderIdResponse.from_dict(sample_response)
        print("✅ OrderSheetByOrderIdResponse 모델 생성 성공")
        
        # 기본 정보 테스트
        total_count = order_response.get_total_count()
        print(f"✅ 총 발주서 수: {total_count}개")
        
        order_id = order_response.get_order_id()
        print(f"✅ 주문번호: {order_id}")
        
        shipment_box_ids = order_response.get_shipment_box_ids()
        print(f"✅ 배송번호 목록: {shipment_box_ids}")
        
        # 분리배송 확인
        is_split = order_response.is_split_shipping()
        print(f"✅ 분리배송 여부: {'예' if is_split else '아니오'}")
        
        # 수취인 정보 테스트
        receiver_info = order_response.get_receiver_info_summary()
        print(f"✅ 수취인 정보 추출 성공: {receiver_info['name']}")
        
        # 상품명 검증 테스트
        product_validation = order_response.get_product_name_validation_summary()
        print(f"✅ 상품명 검증 요약 추출 성공")
        print(f"   총 상품: {product_validation['totalItems']}개")
        print(f"   불일치: {product_validation['mismatchCount']}개")
        print(f"   불일치율: {product_validation['mismatchRate']}%")
        
        # 상품명 불일치 확인
        has_mismatch = order_response.has_product_name_mismatch()
        print(f"✅ 상품명 불일치 확인: {'있음' if has_mismatch else '없음'}")
        
        # 상태별 요약
        status_summary = order_response.get_status_summary()
        print(f"✅ 상태별 요약: {status_summary}")
        
        # 배송 요약 정보
        shipping_summaries = order_response.get_shipping_summary()
        print(f"✅ 배송 요약 정보 추출 성공: {len(shipping_summaries)}개")
        
        # 총 주문 금액
        total_amount = order_response.get_total_order_amount()
        print(f"✅ 총 주문 금액: {total_amount:,}원")
        
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {str(e)}")


def test_order_client_methods():
    """OrderClient 메서드 테스트"""
    print_order_section("OrderClient 메서드 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = OrderClient()
        print("✅ OrderClient 초기화 성공")
        
        # 메서드 존재 확인
        methods_to_check = [
            "get_order_sheets_by_order_id",
            "get_order_sheets_by_order_id_with_validation",
            "_generate_order_id_warnings"
        ]
        
        for method_name in methods_to_check:
            if hasattr(client, method_name):
                print(f"✅ {method_name} 메서드 존재 확인")
            else:
                print(f"❌ {method_name} 메서드 없음")
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 vendor_id 테스트
        try:
            client.get_order_sheets_by_order_id("INVALID", "123456789")
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 order_id 테스트
        try:
            client.get_order_sheets_by_order_id(vendor_id, "invalid_id")
            print("❌ 잘못된 order_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 order_id 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 주문번호 (실제로는 존재하지 않을 가능성 높음)
            test_order_id = "123456789"
            
            result = client.get_order_sheets_by_order_id(vendor_id, test_order_id)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                total_count = result.get("total_count", 0)
                print(f"   발주서 수: {total_count}개")
            else:
                print(f"✅ API 호출 실패 (예상된 결과): {result.get('error')}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
            
    except Exception as e:
        print(f"❌ OrderClient 테스트 실패: {str(e)}")


def test_split_shipping_scenarios():
    """분리배송 시나리오 테스트"""
    print_order_section("분리배송 시나리오 테스트")
    
    print("🔍 분리배송 판별 로직 테스트:")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "단일 발주서 (일반 배송)",
            "data": [{"splitShipping": False}],
            "expected": False
        },
        {
            "name": "단일 발주서 (분리배송 플래그)",
            "data": [{"splitShipping": True}],
            "expected": True
        },
        {
            "name": "복수 발주서 (분리배송)",
            "data": [{"splitShipping": False}, {"splitShipping": False}],
            "expected": True
        },
        {
            "name": "복수 발주서 + 분리배송 플래그",
            "data": [{"splitShipping": True}, {"splitShipping": True}],
            "expected": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # OrderSheet 객체 시뮬레이션을 위한 최소 데이터 생성
            mock_data = {"code": 200, "message": "OK", "data": []}
            
            for j, sheet_data in enumerate(test_case["data"]):
                mock_sheet = {
                    "shipmentBoxId": 1000 + j,
                    "orderId": 999,
                    "orderedAt": "2024-04-08T22:54:46",
                    "orderer": {"name": "테스트", "email": "", "safeNumber": "010-1234-5678"},
                    "paidAt": "2024-04-08T22:54:56",
                    "status": "ACCEPT",
                    "shippingPrice": 0,
                    "remotePrice": 0,
                    "remoteArea": False,
                    "splitShipping": sheet_data["splitShipping"],
                    "ableSplitShipping": False,
                    "receiver": {"name": "테스트", "safeNumber": "010-1234-5678", "addr1": "서울", "addr2": "강남", "postCode": "12345"},
                    "orderItems": [{
                        "vendorItemId": 1, "vendorItemName": "테스트상품", "shippingCount": 1,
                        "salesPrice": 1000, "orderPrice": 1000, "discountPrice": 0,
                        "sellerProductId": 1, "sellerProductName": "테스트상품", "sellerProductItemName": "1개",
                        "cancelCount": 0, "holdCountForCancel": 0
                    }],
                    "overseaShippingInfoDto": {}
                }
                mock_data["data"].append(mock_sheet)
            
            # 모델 생성 및 테스트
            order_response = OrderSheetByOrderIdResponse.from_dict(mock_data)
            result = order_response.is_split_shipping()
            
            status = "✅ 통과" if result == test_case["expected"] else "❌ 실패"
            print(f"   {i}. {test_case['name']}: {status}")
            if result != test_case["expected"]:
                print(f"      예상: {test_case['expected']}, 실제: {result}")
            
        except Exception as e:
            print(f"   {i}. {test_case['name']}: ❌ 오류 ({str(e)})")


def run_order_id_test():
    """발주서 주문번호별 조회 기능 전체 테스트"""
    print_order_header("쿠팡 파트너스 발주서 주문번호별 조회 기능 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - 주문번호(orderId) 검증 함수")
    print("   - OrderSheetByOrderIdResponse 모델")
    print("   - 분리배송 판별 로직")
    print("   - OrderClient 메서드")
    print("   - API 호출 및 응답 처리")
    
    try:
        # 1. 주문번호 검증 테스트
        print("\n" + "="*80)
        test_order_id_validation()
        
        # 2. 모델 테스트
        print("\n" + "="*80)
        test_order_by_id_response_model()
        
        # 3. 분리배송 시나리오 테스트
        print("\n" + "="*80)
        test_split_shipping_scenarios()
        
        # 4. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_order_client_methods()
        
        print("\n" + "="*80)
        print("🎉 발주서 주문번호별 조회 기능 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    run_order_id_test()