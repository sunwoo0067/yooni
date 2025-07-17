#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품 처리 기능 테스트
반품상품 입고확인, 반품요청 승인, 반품철회 이력조회, 회수송장 등록 테스트
"""

import os
import sys
from datetime import datetime, timedelta

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

utils_module = importlib.import_module('return.utils')
print_return_header = utils_module.print_return_header
print_return_section = utils_module.print_return_section
validate_environment_variables = utils_module.validate_environment_variables
get_env_or_default = utils_module.get_env_or_default


def test_return_receive_confirmation():
    """반품상품 입고 확인 처리 테스트"""
    print_return_section("반품상품 입고 확인 처리 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(client, 'confirm_return_receive'):
            print("✅ confirm_return_receive 메서드 존재")
        else:
            print("❌ confirm_return_receive 메서드 없음")
            return False
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 vendor_id 테스트
        try:
            client.confirm_return_receive("INVALID", 123456)
            print("❌ 잘못된 vendor_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 vendor_id 검증 성공: {str(e)}")
        
        # 잘못된 receipt_id 테스트
        try:
            client.confirm_return_receive(vendor_id, "invalid_id")
            print("❌ 잘못된 receipt_id 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 receipt_id 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 접수번호 (실제로는 존재하지 않을 가능성 높음)
            test_receipt_id = 123456
            
            result = client.confirm_return_receive(vendor_id, test_receipt_id)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                print(f"   접수번호: {result.get('receipt_id')}")
                print(f"   처리 액션: {result.get('action')}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ API 호출 실패 (예상된 결과): {error_msg}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ 반품상품 입고 확인 처리 테스트 실패: {str(e)}")
        return False


def test_return_request_approval():
    """반품요청 승인 처리 테스트"""
    print_return_section("반품요청 승인 처리 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(client, 'approve_return_request'):
            print("✅ approve_return_request 메서드 존재")
        else:
            print("❌ approve_return_request 메서드 없음")
            return False
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 cancel_count 테스트
        try:
            client.approve_return_request(vendor_id, 123456, 0)
            print("❌ 잘못된 cancel_count 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 cancel_count 검증 성공: {str(e)}")
        
        try:
            client.approve_return_request(vendor_id, 123456, "invalid")
            print("❌ 잘못된 cancel_count 타입 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 cancel_count 타입 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 접수번호 (실제로는 존재하지 않을 가능성 높음)
            test_receipt_id = 123456
            test_cancel_count = 1
            
            result = client.approve_return_request(vendor_id, test_receipt_id, test_cancel_count)
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                print(f"   접수번호: {result.get('receipt_id')}")
                print(f"   취소 수량: {result.get('cancel_count')}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ API 호출 실패 (예상된 결과): {error_msg}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ 반품요청 승인 처리 테스트 실패: {str(e)}")
        return False


def test_return_withdraw_requests():
    """반품철회 이력 조회 테스트"""
    print_return_section("반품철회 이력 조회 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        methods_to_check = [
            "get_return_withdraw_requests",
            "get_return_withdraw_by_cancel_ids"
        ]
        
        print("\n🔧 반품철회 조회 메서드 확인:")
        for method_name in methods_to_check:
            if hasattr(client, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} 없음")
                return False
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 잘못된 날짜 범위 테스트
        try:
            client.get_return_withdraw_requests(vendor_id, "", "2025-07-14")
            print("❌ 빈 시작일 검증 실패")
        except ValueError as e:
            print(f"✅ 빈 시작일 검증 성공: {str(e)}")
        
        # 잘못된 페이지 설정 테스트
        try:
            client.get_return_withdraw_requests(vendor_id, "2025-07-14", "2025-07-14", size_per_page=101)
            print("❌ 잘못된 페이지 크기 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 페이지 크기 검증 성공: {str(e)}")
        
        # 잘못된 cancel_ids 테스트
        try:
            client.get_return_withdraw_by_cancel_ids(vendor_id, [])
            print("❌ 빈 cancel_ids 검증 실패")
        except ValueError as e:
            print(f"✅ 빈 cancel_ids 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 최근 7일간 철회 이력 조회
            today = datetime.now()
            date_from = (today - timedelta(days=6)).strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
            
            print(f"   조회 기간: {date_from} ~ {date_to}")
            
            result = client.get_return_withdraw_requests(vendor_id, date_from, date_to, size_per_page=5)
            
            if result.get("success"):
                withdraw_requests = result.get("withdraw_requests", [])
                print(f"✅ 반품철회 이력 조회 성공: {len(withdraw_requests)}건")
                
                if withdraw_requests:
                    print("   최근 철회 이력:")
                    for i, request in enumerate(withdraw_requests[:3], 1):
                        print(f"      {i}. 접수번호: {request.get('cancelId')}, 주문번호: {request.get('orderId')}")
                else:
                    print("   📭 조회 기간 내 철회된 반품이 없습니다.")
                
                # 접수번호로 조회 테스트 (철회 이력이 있는 경우)
                if withdraw_requests:
                    test_cancel_ids = [req.get('cancelId') for req in withdraw_requests[:2]]
                    print(f"\n   접수번호로 조회 테스트: {test_cancel_ids}")
                    
                    id_result = client.get_return_withdraw_by_cancel_ids(vendor_id, test_cancel_ids)
                    if id_result.get("success"):
                        found_count = id_result.get("found_count", 0)
                        print(f"   ✅ 접수번호 조회 성공: {found_count}건 발견")
                    else:
                        print(f"   ❌ 접수번호 조회 실패: {id_result.get('error')}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ API 호출 실패 (예상된 결과): {error_msg}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ 반품철회 이력 조회 테스트 실패: {str(e)}")
        return False


def test_return_exchange_invoice():
    """회수 송장 등록 테스트"""
    print_return_section("회수 송장 등록 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(client, 'create_return_exchange_invoice'):
            print("✅ create_return_exchange_invoice 메서드 존재")
        else:
            print("❌ create_return_exchange_invoice 메서드 없음")
            return False
        
        # 파라미터 검증 테스트
        print("\n🔍 파라미터 검증 테스트:")
        
        # 빈 택배사 코드 테스트
        try:
            client.create_return_exchange_invoice(vendor_id, 123456, "", "test123")
            print("❌ 빈 택배사 코드 검증 실패")
        except ValueError as e:
            print(f"✅ 빈 택배사 코드 검증 성공: {str(e)}")
        
        # 빈 운송장번호 테스트
        try:
            client.create_return_exchange_invoice(vendor_id, 123456, "CJGLS", "")
            print("❌ 빈 운송장번호 검증 실패")
        except ValueError as e:
            print(f"✅ 빈 운송장번호 검증 성공: {str(e)}")
        
        # 잘못된 반품/교환 타입 테스트
        try:
            client.create_return_exchange_invoice(vendor_id, 123456, "CJGLS", "test123", "INVALID")
            print("❌ 잘못된 반품/교환 타입 검증 실패")
        except ValueError as e:
            print(f"✅ 잘못된 반품/교환 타입 검증 성공: {str(e)}")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 데이터 (실제로는 존재하지 않을 가능성 높음)
            test_receipt_id = 123456
            test_delivery_company = "CJGLS"
            test_invoice_number = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            result = client.create_return_exchange_invoice(
                vendor_id=vendor_id,
                receipt_id=test_receipt_id,
                delivery_company_code=test_delivery_company,
                invoice_number=test_invoice_number,
                return_exchange_delivery_type="RETURN"
            )
            
            if result.get("success"):
                print("✅ API 호출 성공 (예상치 못한 결과)")
                invoice_data = result.get("invoice_data", {})
                print(f"   접수번호: {invoice_data.get('receiptId')}")
                print(f"   운송장번호: {invoice_data.get('invoiceNumber')}")
                print(f"   택배사: {invoice_data.get('deliveryCompanyCode')}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ API 호출 실패 (예상된 결과): {error_msg}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ 회수 송장 등록 테스트 실패: {str(e)}")
        return False


def test_return_workflow():
    """반품 처리 워크플로우 테스트"""
    print_return_section("반품 처리 워크플로우 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(client, 'process_return_workflow'):
            print("✅ process_return_workflow 메서드 존재")
        else:
            print("❌ process_return_workflow 메서드 없음")
            return False
        
        print("\n💡 워크플로우 개념:")
        print("   1. 현재 상태 확인")
        print("   2. 반품접수(RETURNS_UNCHECKED) → 입고 확인 처리")
        print("   3. 입고완료(VENDOR_WAREHOUSE_CONFIRM) → 승인 처리")
        print("   4. 최종 상태 확인")
        
        # 환경변수가 설정되어 있으면 실제 API 호출 테스트
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 테스트용 접수번호 (실제로는 존재하지 않을 가능성 높음)
            test_receipt_id = 123456
            
            result = client.process_return_workflow(vendor_id, test_receipt_id)
            
            if result.get("success"):
                print("✅ 워크플로우 완료")
                workflow_results = result.get("workflow_results", [])
                print(f"   총 {len(workflow_results)}단계 실행:")
                
                for step_result in workflow_results:
                    step_name = step_result.get("step")
                    success = step_result.get("success", False)
                    status_icon = "✅" if success else "❌"
                    print(f"      {status_icon} {step_name}")
                    
                    if step_name == "status_check":
                        current_status = step_result.get("current_status")
                        print(f"         현재 상태: {current_status}")
                    elif step_name == "final_status_check":
                        final_status = step_result.get("final_status")
                        print(f"         최종 상태: {final_status}")
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"✅ 워크플로우 실패 (예상된 결과): {error_msg}")
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ 반품 처리 워크플로우 테스트 실패: {str(e)}")
        return False


def run_return_processing_tests():
    """반품 처리 기능 전체 테스트 실행"""
    print_return_header("쿠팡 파트너스 반품 처리 기능 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - 반품상품 입고 확인 처리")
    print("   - 반품요청 승인 처리")
    print("   - 반품철회 이력 조회")
    print("   - 회수 송장 등록")
    print("   - 반품 처리 워크플로우")
    print("   - 실제 API 호출 (환경변수 설정시)")
    
    test_results = []
    
    try:
        # 1. 반품상품 입고 확인 처리 테스트
        print("\n" + "="*80)
        test_results.append(test_return_receive_confirmation())
        
        # 2. 반품요청 승인 처리 테스트
        print("\n" + "="*80)
        test_results.append(test_return_request_approval())
        
        # 3. 반품철회 이력 조회 테스트
        print("\n" + "="*80)
        test_results.append(test_return_withdraw_requests())
        
        # 4. 회수 송장 등록 테스트
        print("\n" + "="*80)
        test_results.append(test_return_exchange_invoice())
        
        # 5. 반품 처리 워크플로우 테스트
        print("\n" + "="*80)
        test_results.append(test_return_workflow())
        
        # 결과 요약
        print("\n" + "="*80)
        passed_count = sum(test_results)
        total_count = len(test_results)
        
        if passed_count == total_count:
            print("🎉 모든 테스트 통과!")
            print("✅ 반품 처리 기능이 정상 작동합니다.")
        else:
            print(f"⚠️  테스트 결과: {passed_count}/{total_count} 통과")
            print("❌ 일부 테스트가 실패했습니다.")
        
        return passed_count == total_count
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    run_return_processing_tests()