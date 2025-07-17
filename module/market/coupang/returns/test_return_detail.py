#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 단건 조회 테스트
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

import importlib
return_module = importlib.import_module('return.return_client')
ReturnClient = return_module.ReturnClient

models_module = importlib.import_module('return.models')
ReturnRequestDetailResponse = models_module.ReturnRequestDetailResponse

validators_module = importlib.import_module('return.validators')
validate_receipt_id = validators_module.validate_receipt_id
is_valid_receipt_id = validators_module.is_valid_receipt_id

utils_module = importlib.import_module('return.utils')
print_return_header = utils_module.print_return_header
print_return_section = utils_module.print_return_section
validate_environment_variables = utils_module.validate_environment_variables
get_env_or_default = utils_module.get_env_or_default
format_korean_datetime = utils_module.format_korean_datetime


def test_receipt_id_validation():
    """접수번호 검증 테스트"""
    print_return_section("접수번호 검증 테스트")
    
    test_cases = [
        {"value": 365937, "description": "유효한 정수", "expected": True},
        {"value": "365937", "description": "유효한 문자열 숫자", "expected": True},
        {"value": 123456789, "description": "긴 숫자", "expected": True},
        {"value": "invalid123", "description": "문자가 포함된 문자열", "expected": False},
        {"value": -123, "description": "음수", "expected": False},
        {"value": 0, "description": "0", "expected": False},
        {"value": None, "description": "None 값", "expected": False},
        {"value": "", "description": "빈 문자열", "expected": False}
    ]
    
    print("🔍 is_valid_receipt_id() 함수 테스트:")
    passed = 0
    for i, test in enumerate(test_cases, 1):
        result = is_valid_receipt_id(test["value"])
        if result == test["expected"]:
            status = "✅ 통과"
            passed += 1
        else:
            status = "❌ 실패"
        
        print(f"   {i}. {test['description']}: {status}")
        if result != test["expected"]:
            print(f"      예상: {test['expected']}, 실제: {result}")
    
    print(f"\n🔍 validate_receipt_id() 함수 테스트:")
    for i, test in enumerate(test_cases, 1):
        try:
            validated_value = validate_receipt_id(test["value"])
            if test["expected"]:
                print(f"   {i}. {test['description']}: ✅ 통과 (결과: {validated_value})")
            else:
                print(f"   {i}. {test['description']}: ❌ 실패 (예외가 발생해야 함)")
        except Exception as e:
            if not test["expected"]:
                print(f"   {i}. {test['description']}: ✅ 통과 (예외: {str(e)})")
            else:
                print(f"   {i}. {test['description']}: ❌ 실패 (예상치 못한 예외: {str(e)})")
    
    return passed == len([t for t in test_cases if t["expected"]])


def test_detail_response_model():
    """ReturnRequestDetailResponse 모델 테스트"""
    print_return_section("ReturnRequestDetailResponse 모델 테스트")
    
    # 샘플 API 응답 데이터 (API 명세서 예제 기반)
    sample_response = {
        "code": "200",
        "message": "OK",
        "data": [
            {
                "receiptId": 365937,
                "orderId": 500004398,
                "paymentId": 700003957,
                "receiptType": "반품",
                "receiptStatus": "RELEASE_STOP_UNCHECKED",
                "createdAt": "2016-03-25T13:05:30",
                "modifiedAt": "2016-03-25T13:05:30",
                "requesterName": "임송이",
                "requesterPhoneNumber": "010-****-4043",
                "requesterRealPhoneNumber": None,
                "requesterAddress": "서울특별시 송파구 송파대로 570 (신천동)",
                "requesterAddressDetail": "Tower 730",
                "requesterZipCode": "05510",
                "cancelReasonCategory1": "고객변심",
                "cancelReasonCategory2": "단순변심(사유없음)",
                "cancelReason": "테스트",
                "cancelCountSum": 1,
                "returnDeliveryId": 40453,
                "returnDeliveryType": "연동택배",
                "releaseStopStatus": "미처리",
                "enclosePrice": 0,
                "faultByType": "CUSTOMER",
                "preRefund": False,
                "completeConfirmDate": "",
                "completeConfirmType": "미확인",
                "returnItems": [
                    {
                        "vendorItemPackageId": 0,
                        "vendorItemPackageName": "객지/한씨연대기/삼포 가는 길/섬섬옥수/몰개월의 새",
                        "vendorItemId": 3000001893,
                        "vendorItemName": "객지/한씨연대기/삼포 가는 길/섬섬옥수/몰개월의 새 1",
                        "purchaseCount": 1,
                        "cancelCount": 1,
                        "shipmentBoxId": 123456789012345678,
                        "sellerProductId": 130,
                        "sellerProductName": "객지/한씨연대기/삼포 가는 길/섬섬옥수/몰개월의 새 1",
                        "releaseStatus": "S",
                        "cancelCompleteUser": "l******"
                    }
                ],
                "returnDeliveryDtos": [
                    {
                        "deliveryCompanyCode": "DIRECT",
                        "deliveryInvoiceNo": "201807261200"
                    }
                ],
                "reasonCode": "CHANGEMIND",
                "reasonCodeText": "필요 없어짐 (단순 변심)",
                "returnShippingCharge": -3000
            }
        ]
    }
    
    try:
        # 모델 생성 테스트
        detail_response = ReturnRequestDetailResponse.from_dict(sample_response)
        print("✅ ReturnRequestDetailResponse 모델 생성 성공")
        
        # 단건 조회 결과 테스트
        return_request = detail_response.get_return_request()
        if return_request:
            print(f"✅ 반품 요청 추출 성공: 접수번호 {return_request.receipt_id}")
        else:
            print("❌ 반품 요청 추출 실패")
            return False
        
        # 상세 정보 테스트
        detailed_info = detail_response.get_detailed_info()
        if detailed_info:
            print("✅ 상세 정보 추출 성공")
            
            # 기본 정보 확인
            basic_info = detailed_info.get("basic_info", {})
            print(f"   접수번호: {basic_info.get('receipt_id')}")
            print(f"   주문번호: {basic_info.get('order_id')}")
            print(f"   상태: {basic_info.get('receipt_status')}")
            
            # 신청인 정보 확인
            requester_info = detailed_info.get("requester_info", {})
            print(f"   신청인: {requester_info.get('name')}")
            print(f"   주소: {requester_info.get('address')}")
            
            # 반품 사유 확인
            return_reason = detailed_info.get("return_reason", {})
            print(f"   사유: {return_reason.get('reason_text')}")
            
            # 처리 정보 확인
            processing_info = detailed_info.get("processing_info", {})
            print(f"   출고중지상태: {processing_info.get('release_stop_status')}")
            print(f"   귀책타입: {processing_info.get('fault_by_type')}")
            
            # 금액 정보 확인
            financial_info = detailed_info.get("financial_info", {})
            print(f"   배송비: {financial_info.get('shipping_charge_text')}")
            
        else:
            print("❌ 상세 정보 추출 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {str(e)}")
        return False


def test_return_client_detail_methods():
    """ReturnClient 단건 조회 메서드 테스트"""
    print_return_section("ReturnClient 단건 조회 메서드 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        methods_to_check = [
            "get_return_request_detail",
            "get_return_request_with_analysis"
        ]
        
        print("\n🔧 단건 조회 메서드 확인:")
        for method_name in methods_to_check:
            if hasattr(client, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} 없음")
                return False
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 vendor_id 테스트
        try:
            client.get_return_request_detail("INVALID", 123456)
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 receipt_id 테스트
        try:
            client.get_return_request_detail(vendor_id, "invalid_id")
            print("❌ 잘못된 receipt_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 receipt_id 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 접수번호 (실제로는 존재하지 않을 가능성 높음)
            test_receipt_id = 123456
            
            result = client.get_return_request_detail(vendor_id, test_receipt_id)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                detailed_info = result.get("detailed_info", {})
                if detailed_info:
                    basic_info = detailed_info.get("basic_info", {})
                    print(f"   접수번호: {basic_info.get('receipt_id')}")
                    print(f"   우선순위: {result.get('priority_level')}")
                    print(f"   출고중지 필요: {result.get('stop_release_required')}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ API 호출 실패 (예상된 결과): {error_msg}")
                
                # 분석 기능 테스트
                print("\n🔍 분석 기능 테스트:")
                analysis_result = client.get_return_request_with_analysis(vendor_id, test_receipt_id)
                if not analysis_result.get("success"):
                    print("✅ 분석 기능도 정상적으로 실패 처리됨")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ ReturnClient 단건 조회 테스트 실패: {str(e)}")
        return False


def test_priority_and_analysis():
    """우선순위 판정 및 분석 기능 테스트"""
    print_return_section("우선순위 판정 및 분석 기능 테스트")
    
    try:
        client = ReturnClient()
        
        # 샘플 ReturnRequest 생성을 위한 데이터
        sample_data = {
            "receiptId": 365937,
            "orderId": 500004398,
            "paymentId": 700003957,
            "receiptType": "RETURN",
            "receiptStatus": "RELEASE_STOP_UNCHECKED",
            "createdAt": "2025-07-13T10:00:00",
            "modifiedAt": "2025-07-13T10:00:00",
            "requesterName": "테스트 사용자",
            "requesterPhoneNumber": "010-****-1234",
            "requesterRealPhoneNumber": None,
            "requesterAddress": "서울시 강남구",
            "requesterAddressDetail": "테스트 주소",
            "requesterZipCode": "12345",
            "cancelReasonCategory1": "상품불량",
            "cancelReasonCategory2": "파손",
            "cancelReason": "배송 중 파손",
            "cancelCountSum": 1,
            "returnDeliveryId": 12345,
            "returnDeliveryType": "연동택배",
            "releaseStopStatus": "미처리",
            "enclosePrice": 0,
            "faultByType": "VENDOR",
            "preRefund": True,
            "completeConfirmType": "UNDEFINED",
            "completeConfirmDate": "",
            "returnItems": [],
            "returnDeliveryDtos": [],
            "reasonCode": "DEFECTIVE",
            "reasonCodeText": "상품 불량",
            "returnShippingCharge": -5000
        }
        
        # ReturnRequest 객체 생성
        ReturnRequest = models_module.ReturnRequest
        return_request = ReturnRequest.from_dict(sample_data)
        
        # 우선순위 테스트
        priority = client._get_processing_priority(return_request)
        print(f"✅ 우선순위 판정 테스트: {priority}")
        
        # 권장사항 테스트
        recommendations = client._get_processing_recommendations(return_request)
        print(f"✅ 처리 권장사항 생성: {len(recommendations)}개")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # 타임라인 분석 테스트
        timeline = client._analyze_processing_timeline(return_request)
        print(f"✅ 타임라인 분석: {timeline}")
        
        # 리스크 평가 테스트
        risk = client._assess_return_risk(return_request)
        print(f"✅ 리스크 평가: {risk['risk_level']} (점수: {risk['risk_score']})")
        print(f"   리스크 요인: {', '.join(risk['risk_factors'])}")
        
        # 액션 아이템 테스트
        actions = client._generate_action_items(return_request)
        print(f"✅ 액션 아이템 생성: {len(actions)}개")
        for action in actions:
            print(f"   [{action['priority']}] {action['action']}: {action['description']}")
        
        # 유사 사례 인사이트 테스트
        insight = client._get_similar_cases_insight(return_request)
        print(f"✅ 유사 사례 인사이트: {insight['reason_category']}")
        print(f"   예방 팁: {insight['prevention_tip']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 우선순위 및 분석 기능 테스트 실패: {str(e)}")
        return False


def run_return_detail_test():
    """반품/취소 요청 단건 조회 전체 테스트 실행"""
    print_return_header("쿠팡 파트너스 반품/취소 요청 단건 조회 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - 접수번호 검증 함수")
    print("   - ReturnRequestDetailResponse 모델")
    print("   - ReturnClient 단건 조회 메서드")
    print("   - 우선순위 판정 및 분석 기능")
    print("   - 실제 API 호출 (환경변수 설정시)")
    
    test_results = []
    
    try:
        # 1. 접수번호 검증 테스트
        print("\n" + "="*80)
        test_results.append(test_receipt_id_validation())
        
        # 2. 응답 모델 테스트
        print("\n" + "="*80)
        test_results.append(test_detail_response_model())
        
        # 3. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_results.append(test_return_client_detail_methods())
        
        # 4. 우선순위 및 분석 기능 테스트
        print("\n" + "="*80)
        test_results.append(test_priority_and_analysis())
        
        # 결과 요약
        print("\n" + "="*80)
        passed_count = sum(test_results)
        total_count = len(test_results)
        
        if passed_count == total_count:
            print("🎉 모든 테스트 통과!")
            print("✅ 반품/취소 요청 단건 조회 기능이 정상 작동합니다.")
        else:
            print(f"⚠️  테스트 결과: {passed_count}/{total_count} 통과")
            print("❌ 일부 테스트가 실패했습니다.")
        
        return passed_count == total_count
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    run_return_detail_test()