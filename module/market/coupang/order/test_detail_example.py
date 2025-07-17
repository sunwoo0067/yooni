#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 단건 조회 기능 테스트
shipmentBoxId 검증 및 API 호출 테스트
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
from order.models import OrderSheetDetailResponse
from order.validators import validate_shipment_box_id, is_valid_shipment_box_id
from order.utils import (
    print_order_header, print_order_section,
    validate_environment_variables, get_env_or_default
)


def test_shipment_box_id_validation():
    """배송번호 검증 함수 테스트"""
    print_order_section("배송번호 검증 함수 테스트")
    
    test_cases = [
        {"value": "642538971006401429", "description": "유효한 문자열 숫자", "expected": True},
        {"value": 642538971006401429, "description": "유효한 정수", "expected": True},
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
    
    print("🔍 is_valid_shipment_box_id() 함수 테스트:")
    for i, test in enumerate(test_cases, 1):
        try:
            result = is_valid_shipment_box_id(test["value"])
            status = "✅ 통과" if result == test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status}")
            if result != test["expected"]:
                print(f"       예상: {test['expected']}, 실제: {result}")
        except Exception as e:
            status = "✅ 통과" if not test["expected"] else "❌ 실패"
            print(f"   {i:2d}. {test['description']}: {status} (예외: {type(e).__name__})")
    
    print("\n🔍 validate_shipment_box_id() 함수 테스트:")
    for i, test in enumerate(test_cases, 1):
        try:
            validated_value = validate_shipment_box_id(test["value"])
            if test["expected"]:
                print(f"   {i:2d}. {test['description']}: ✅ 통과 (결과: {validated_value})")
            else:
                print(f"   {i:2d}. {test['description']}: ❌ 실패 (예외가 발생해야 함)")
        except Exception as e:
            if not test["expected"]:
                print(f"   {i:2d}. {test['description']}: ✅ 통과 (예외: {str(e)})")
            else:
                print(f"   {i:2d}. {test['description']}: ❌ 실패 (예상치 못한 예외: {str(e)})")


def test_order_detail_response_model():
    """OrderSheetDetailResponse 모델 테스트"""
    print_order_section("OrderSheetDetailResponse 모델 테스트")
    
    # 샘플 API 응답 데이터 (쿠팡 API 명세서 예제 기반)
    sample_response = {
        "code": 200,
        "message": "OK",
        "data": {
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
            "status": "FINAL_DELIVERY",
            "shippingPrice": 0,
            "remotePrice": 0,
            "remoteArea": False,
            "parcelPrintMessage": "문 앞",
            "splitShipping": False,
            "ableSplitShipping": False,
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
                    "vendorItemPackageName": "신서리티 델타 구운 캐슈넛",
                    "productId": 7313251147,
                    "vendorItemId": 85872453655,
                    "vendorItemName": "신서리티 델타 구운 캐슈넛, 5개, 160g",
                    "shippingCount": 1,
                    "salesPrice": 41000,
                    "orderPrice": 41000,
                    "discountPrice": 0,
                    "instantCouponDiscount": 0,
                    "downloadableCouponDiscount": 0,
                    "coupangDiscount": 0,
                    "externalVendorSkuCode": "",
                    "etcInfoHeader": None,
                    "etcInfoValue": None,
                    "etcInfoValues": None,
                    "sellerProductId": 14091699106,
                    "sellerProductName": "신서리티 델타 구운 캐슈넛 160g",
                    "sellerProductItemName": "5개",
                    "firstSellerProductItemName": "5개",
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
                    "upBundleVendorItemId": 88049657337,
                    "upBundleVendorItemName": "신서리티 델타 구운 캐슈넛, 5개, 160g",
                    "upBundleSize": 5,
                    "upBundleItem": True,
                    "canceled": False
                }
            ],
            "overseaShippingInfoDto": {
                "personalCustomsClearanceCode": "",
                "ordererSsn": "",
                "ordererPhoneNumber": ""
            },
            "deliveryCompanyName": "로젠택배",
            "invoiceNumber": "***00402083",
            "inTrasitDateTime": "2024-04-09 22:41:00",
            "deliveredDate": "2024-04-11 09:57:00",
            "refer": "안드로이드앱",
            "shipmentType": "THIRD_PARTY"
        }
    }
    
    try:
        # 모델 생성 테스트
        detail_response = OrderSheetDetailResponse.from_dict(sample_response)
        print("✅ OrderSheetDetailResponse 모델 생성 성공")
        
        # 수취인 정보 테스트
        receiver_info = detail_response.get_receiver_info()
        print(f"✅ 수취인 정보 추출 성공: {receiver_info['name']}")
        
        # 상품명 검증 테스트
        product_validation = detail_response.get_product_name_validation_info()
        print(f"✅ 상품명 검증 정보 추출 성공: {len(product_validation)}개 상품")
        
        for i, validation in enumerate(product_validation, 1):
            seller_name = validation["sellerFullName"]
            vendor_name = validation["vendorItemName"]
            is_matched = validation["isMatched"]
            
            print(f"   {i}. 옵션ID {validation['vendorItemId']}")
            print(f"      등록명: {seller_name}")
            print(f"      노출명: {vendor_name}")
            print(f"      일치여부: {'✅ 일치' if is_matched else '❌ 불일치'}")
        
        # 상품명 불일치 확인
        has_mismatch = detail_response.has_product_name_mismatch()
        print(f"✅ 상품명 불일치 확인: {'있음' if has_mismatch else '없음'}")
        
        # 배송 요약 정보
        shipping_summary = detail_response.get_shipping_summary()
        print(f"✅ 배송 요약 정보 추출 성공: {shipping_summary['deliveryCompanyName']}")
        
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
            "get_order_sheet_detail",
            "get_order_sheet_with_validation",
            "_generate_detail_warnings"
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
            client.get_order_sheet_detail("INVALID", "123456789")
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 shipment_box_id 테스트
        try:
            client.get_order_sheet_detail(vendor_id, "invalid_id")
            print("❌ 잘못된 shipment_box_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 shipment_box_id 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 배송번호 (실제로는 존재하지 않을 가능성 높음)
            test_shipment_box_id = "123456789"
            
            result = client.get_order_sheet_detail(vendor_id, test_shipment_box_id)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
            else:
                print(f"✅ API 호출 실패 (예상된 결과): {result.get('error')}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
            
    except Exception as e:
        print(f"❌ OrderClient 테스트 실패: {str(e)}")


def run_detail_test():
    """발주서 단건 조회 기능 전체 테스트"""
    print_order_header("쿠팡 파트너스 발주서 단건 조회 기능 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - 배송번호(shipmentBoxId) 검증 함수")
    print("   - OrderSheetDetailResponse 모델")
    print("   - OrderClient 메서드")
    print("   - API 호출 및 응답 처리")
    
    try:
        # 1. 배송번호 검증 테스트
        print("\n" + "="*80)
        test_shipment_box_id_validation()
        
        # 2. 모델 테스트
        print("\n" + "="*80)
        test_order_detail_response_model()
        
        # 3. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_order_client_methods()
        
        print("\n" + "="*80)
        print("🎉 발주서 단건 조회 기능 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    run_detail_test()