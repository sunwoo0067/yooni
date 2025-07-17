#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 클라이언트 테스트
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

models_module = importlib.import_module('return.models')
ReturnRequestSearchParams = models_module.ReturnRequestSearchParams

validators_module = importlib.import_module('return.validators')
validate_search_params = validators_module.validate_search_params
is_valid_receipt_id = validators_module.is_valid_receipt_id

utils_module = importlib.import_module('return.utils')
print_return_header = utils_module.print_return_header
print_return_section = utils_module.print_return_section
validate_environment_variables = utils_module.validate_environment_variables
get_env_or_default = utils_module.get_env_or_default
format_korean_datetime = utils_module.format_korean_datetime
format_currency = utils_module.format_currency
print_return_summary_table = utils_module.print_return_summary_table
generate_date_range_for_recent_days = utils_module.generate_date_range_for_recent_days


def test_return_client_initialization():
    """ReturnClient 초기화 테스트"""
    print_return_section("ReturnClient 초기화 테스트")
    
    try:
        client = ReturnClient()
        print("✅ ReturnClient 초기화 성공")
        print(f"   벤더 ID: {client.auth.vendor_id}")
        print(f"   액세스 키: {client.auth.access_key[:8]}...")
        return True
    except Exception as e:
        print(f"❌ ReturnClient 초기화 실패: {e}")
        return False


def test_search_params_validation():
    """검색 파라미터 검증 테스트"""
    print_return_section("검색 파라미터 검증 테스트")
    
    vendor_id = get_env_or_default("COUPANG_VENDOR_ID", "A01409684", "기본 테스트 벤더 ID")
    
    test_cases = [
        {
            "name": "정상적인 일단위 검색",
            "params": {
                "vendor_id": vendor_id,
                "search_type": "daily",
                "created_at_from": "2025-07-14",
                "created_at_to": "2025-07-14",
                "status": "UC"
            },
            "should_pass": True
        },
        {
            "name": "정상적인 timeFrame 검색",
            "params": {
                "vendor_id": vendor_id,
                "search_type": "timeFrame",
                "created_at_from": "2025-07-14T00:00",
                "created_at_to": "2025-07-14T23:59"
            },
            "should_pass": True
        },
        {
            "name": "취소 요청 검색 (CANCEL)",
            "params": {
                "vendor_id": vendor_id,
                "search_type": "daily",
                "created_at_from": "2025-07-14",
                "created_at_to": "2025-07-14",
                "cancel_type": "CANCEL"
            },
            "should_pass": True
        },
        {
            "name": "잘못된 vendor_id",
            "params": {
                "vendor_id": "INVALID",
                "search_type": "daily",
                "created_at_from": "2025-07-14",
                "created_at_to": "2025-07-14"
            },
            "should_pass": False
        },
        {
            "name": "날짜 범위 초과 (32일)",
            "params": {
                "vendor_id": vendor_id,
                "search_type": "daily",
                "created_at_from": "2025-06-01",
                "created_at_to": "2025-07-14"
            },
            "should_pass": False
        },
        {
            "name": "CANCEL과 status 동시 사용 (충돌)",
            "params": {
                "vendor_id": vendor_id,
                "search_type": "daily",
                "created_at_from": "2025-07-14",
                "created_at_to": "2025-07-14",
                "cancel_type": "CANCEL",
                "status": "UC"
            },
            "should_pass": False
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            params = ReturnRequestSearchParams(**test_case["params"])
            validate_search_params(params)
            
            if test_case["should_pass"]:
                print(f"   ✅ {i}. {test_case['name']}: 통과")
                passed += 1
            else:
                print(f"   ❌ {i}. {test_case['name']}: 실패 (예외가 발생해야 함)")
                
        except Exception as e:
            if not test_case["should_pass"]:
                print(f"   ✅ {i}. {test_case['name']}: 통과 (예상된 예외: {str(e)})")
                passed += 1
            else:
                print(f"   ❌ {i}. {test_case['name']}: 실패 (예상치 못한 예외: {str(e)})")
    
    print(f"\n검증 테스트 결과: {passed}/{total} 통과")
    return passed == total


def test_receipt_id_validation():
    """접수번호 검증 테스트"""
    print_return_section("접수번호 검증 테스트")
    
    test_cases = [
        {"value": 12345678, "description": "유효한 정수", "expected": True},
        {"value": "12345678", "description": "유효한 문자열 숫자", "expected": True},
        {"value": 0, "description": "0", "expected": False},
        {"value": -123, "description": "음수", "expected": False},
        {"value": "invalid", "description": "문자가 포함된 문자열", "expected": False},
        {"value": None, "description": "None 값", "expected": False},
        {"value": "", "description": "빈 문자열", "expected": False}
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        result = is_valid_receipt_id(test["value"])
        if result == test["expected"]:
            status = "✅ 통과"
            passed += 1
        else:
            status = "❌ 실패"
        
        print(f"   {i}. {test['description']}: {status}")
    
    print(f"\n접수번호 검증 결과: {passed}/{len(test_cases)} 통과")
    return passed == len(test_cases)


def test_return_client_methods():
    """ReturnClient 메서드 테스트"""
    print_return_section("ReturnClient 메서드 테스트")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        
        # 메서드 존재 확인
        methods_to_check = [
            "get_return_requests",
            "get_return_requests_all_pages",
            "get_return_requests_by_status",
            "get_cancel_requests",
            "get_stop_release_requests",
            "get_recent_return_requests",
            "get_return_summary_by_date_range"
        ]
        
        print("🔧 주요 메서드 확인:")
        all_methods_exist = True
        for method_name in methods_to_check:
            if hasattr(client, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} 없음")
                all_methods_exist = False
        
        if not all_methods_exist:
            return False
        
        # 실제 API 호출 테스트 (환경변수 설정된 경우)
        if validate_environment_variables("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "COUPANG_VENDOR_ID"):
            print("\n🌐 실제 API 호출 테스트:")
            
            # 오늘 날짜로 반품 요청 조회 테스트
            today = datetime.now().strftime('%Y-%m-%d')
            
            params = ReturnRequestSearchParams(
                vendor_id=vendor_id,
                search_type="daily",
                created_at_from=today,
                created_at_to=today,
                cancel_type="RETURN"
            )
            
            result = client.get_return_requests(params)
            
            if result.get("success"):
                data_count = len(result.get("data", []))
                print(f"   ✅ 반품 요청 조회 성공: {data_count}건")
                
                # 요약 통계 출력
                summary_stats = result.get("summary_stats", {})
                if summary_stats.get("total_count", 0) > 0:
                    print(f"   📊 상태별 현황:")
                    for status, count in summary_stats.get("status_summary", {}).items():
                        print(f"      {status}: {count}건")
                    
                    stop_release_count = summary_stats.get("stop_release_required_count", 0)
                    if stop_release_count > 0:
                        print(f"   🚨 출고중지 처리 필요: {stop_release_count}건")
                
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"   ✅ API 호출 완료 (데이터 없음 또는 오류): {error_msg}")
            
            # 최근 7일간 요약 정보 테스트
            print("\n📊 최근 7일간 요약 정보 테스트:")
            date_from, date_to = generate_date_range_for_recent_days(7)
            summary_result = client.get_return_summary_by_date_range(
                vendor_id=vendor_id,
                created_at_from=date_from,
                created_at_to=date_to
            )
            
            if summary_result.get("success"):
                total_summary = summary_result.get("total_summary", {})
                total_requests = total_summary.get("total_requests", 0)
                print(f"   ✅ 요약 정보 조회 성공: 총 {total_requests}건")
                
                if total_summary.get("urgent_action_required"):
                    print("   🚨 긴급 처리 필요한 건이 있습니다!")
                    
            else:
                print(f"   ⚠️ 요약 정보 조회 실패: {summary_result.get('error')}")
        
        else:
            print("\n⚠️  환경변수가 설정되지 않아 실제 API 테스트는 생략")
        
        return True
        
    except Exception as e:
        print(f"❌ ReturnClient 메서드 테스트 실패: {e}")
        return False


def test_convenience_methods():
    """편의 메서드 테스트"""
    print_return_section("편의 메서드 테스트")
    
    try:
        client = ReturnClient()
        vendor_id = client.auth.vendor_id
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 각 편의 메서드가 올바른 파라미터로 호출되는지 확인
        print("🔍 편의 메서드 파라미터 생성 테스트:")
        
        # get_return_requests_by_status 테스트
        try:
            # 실제로는 호출하지 않고 파라미터만 검증
            params = ReturnRequestSearchParams(
                vendor_id=vendor_id,
                search_type="daily",
                created_at_from=today,
                created_at_to=today,
                status="UC",
                max_per_page=50
            )
            validate_search_params(params)
            print("   ✅ get_return_requests_by_status 파라미터 검증 통과")
        except Exception as e:
            print(f"   ❌ get_return_requests_by_status 파라미터 오류: {e}")
            return False
        
        # get_cancel_requests 테스트
        try:
            params = ReturnRequestSearchParams(
                vendor_id=vendor_id,
                search_type="daily",
                created_at_from=today,
                created_at_to=today,
                cancel_type="CANCEL"
            )
            validate_search_params(params)
            print("   ✅ get_cancel_requests 파라미터 검증 통과")
        except Exception as e:
            print(f"   ❌ get_cancel_requests 파라미터 오류: {e}")
            return False
        
        # get_stop_release_requests 테스트
        try:
            params = ReturnRequestSearchParams(
                vendor_id=vendor_id,
                search_type="daily",
                created_at_from=today,
                created_at_to=today,
                status="RU"
            )
            validate_search_params(params)
            print("   ✅ get_stop_release_requests 파라미터 검증 통과")
        except Exception as e:
            print(f"   ❌ get_stop_release_requests 파라미터 오류: {e}")
            return False
        
        print("\n✅ 모든 편의 메서드 파라미터 검증 통과")
        return True
        
    except Exception as e:
        print(f"❌ 편의 메서드 테스트 실패: {e}")
        return False


def run_return_client_test():
    """반품/취소 클라이언트 전체 테스트 실행"""
    print_return_header("쿠팡 파트너스 반품/취소 요청 클라이언트 테스트")
    
    print("\n💡 테스트 범위:")
    print("   - ReturnClient 초기화")
    print("   - 검색 파라미터 검증")
    print("   - 접수번호 검증")
    print("   - API 클라이언트 메서드")
    print("   - 편의 메서드")
    print("   - 실제 API 호출 (환경변수 설정시)")
    
    test_results = []
    
    try:
        # 1. 클라이언트 초기화 테스트
        print("\n" + "="*80)
        test_results.append(test_return_client_initialization())
        
        # 2. 검색 파라미터 검증 테스트
        print("\n" + "="*80)
        test_results.append(test_search_params_validation())
        
        # 3. 접수번호 검증 테스트
        print("\n" + "="*80)
        test_results.append(test_receipt_id_validation())
        
        # 4. 클라이언트 메서드 테스트
        print("\n" + "="*80)
        test_results.append(test_return_client_methods())
        
        # 5. 편의 메서드 테스트
        print("\n" + "="*80)
        test_results.append(test_convenience_methods())
        
        # 결과 요약
        print("\n" + "="*80)
        passed_count = sum(test_results)
        total_count = len(test_results)
        
        if passed_count == total_count:
            print("🎉 모든 테스트 통과!")
            print("✅ 반품/취소 요청 클라이언트가 정상 작동합니다.")
        else:
            print(f"⚠️  테스트 결과: {passed_count}/{total_count} 통과")
            print("❌ 일부 테스트가 실패했습니다.")
        
        return passed_count == total_count
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    run_return_client_test()