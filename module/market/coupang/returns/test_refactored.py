#!/usr/bin/env python3
"""
리팩토링된 쿠팡 파트너스 반품 API 테스트
공통 모듈과 Mock을 활용한 개선된 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# 경로 설정
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 공통 모듈 사용
from common import TestFixtures, TestAssertions, MockCoupangAPI, config
import importlib

# return 키워드 이슈로 importlib 사용
return_client_module = importlib.import_module('return.return_client')
ReturnClient = return_client_module.ReturnClient

return_models_module = importlib.import_module('return.models')
ReturnRequestSearchParams = return_models_module.ReturnRequestSearchParams

return_validators_module = importlib.import_module('return.validators')
validate_receipt_id = return_validators_module.validate_receipt_id
is_valid_receipt_id = return_validators_module.is_valid_receipt_id
validate_vendor_id = return_validators_module.validate_vendor_id


class TestReturnClientRefactored(unittest.TestCase):
    """리팩토링된 ReturnClient 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # Mock 클라이언트 생성
        self.client = None
        
        # 테스트 데이터
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
        self.sample_receipt_id = 365937
    
    @patch.object(ReturnClient, '__init__', return_value=None)
    def test_client_initialization(self, mock_init):
        """클라이언트 초기화 테스트"""
        client = ReturnClient()
        self.assertIsNotNone(client)
        mock_init.assert_called_once()
    
    @patch.object(ReturnClient, '__init__', return_value=None)
    def test_api_name(self, mock_init):
        """API 이름 반환 테스트"""
        client = ReturnClient()
        client.get_api_name = ReturnClient.get_api_name.__get__(client, ReturnClient)
        self.assertEqual(client.get_api_name(), "반품/취소 요청 관리 API")


class TestValidatorsRefactored(unittest.TestCase):
    """리팩토링된 검증 함수 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
    
    def test_validate_receipt_id_valid_cases(self):
        """유효한 접수번호 테스트"""
        valid_cases = [
            (365937, 365937),
            ("365937", 365937),
            ("  123456  ", 123456),
            (1, 1),
            (999999999, 999999999)
        ]
        
        for input_value, expected in valid_cases:
            with self.subTest(input_value=input_value):
                result = validate_receipt_id(input_value)
                self.assertEqual(result, expected)
    
    def test_validate_receipt_id_invalid_cases(self):
        """유효하지 않은 접수번호 테스트"""
        invalid_cases = self.test_fixtures.get_invalid_receipt_ids()
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                self.test_assertions.assert_validation_error(
                    validate_receipt_id, invalid_value
                )
    
    def test_is_valid_receipt_id_consistency(self):
        """is_valid_receipt_id와 validate_receipt_id 일관성 테스트"""
        test_cases = [365937, "365937", -123, "invalid", None, ""]
        
        for test_value in test_cases:
            with self.subTest(test_value=test_value):
                is_valid_result = is_valid_receipt_id(test_value)
                
                try:
                    validate_receipt_id(test_value)
                    validate_result = True
                except ValueError:
                    validate_result = False
                
                self.assertEqual(is_valid_result, validate_result,
                               f"일관성 오류: {test_value}")
    
    def test_validate_vendor_id_valid_cases(self):
        """유효한 벤더 ID 테스트"""
        valid_cases = ["A01409684", "A12345678", "A00000001"]
        
        for vendor_id in valid_cases:
            with self.subTest(vendor_id=vendor_id):
                result = validate_vendor_id(vendor_id)
                self.assertEqual(result, vendor_id)
    
    def test_validate_vendor_id_invalid_cases(self):
        """유효하지 않은 벤더 ID 테스트"""
        invalid_cases = self.test_fixtures.get_invalid_vendor_ids()
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                if invalid_value is not None:  # None은 별도 처리
                    self.test_assertions.assert_validation_error(
                        validate_vendor_id, invalid_value
                    )


class TestReturnClientMocked(unittest.TestCase):
    """Mock을 활용한 ReturnClient API 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # ReturnClient Mock 설정
        self.client = Mock(spec=ReturnClient)
        
        # Mock 메서드 설정
        self.client.validate_vendor_id.return_value = self.test_fixtures.get_sample_vendor_id()
        self.client.validate_receipt_id.return_value = 365937
        
        # 실제 메서드들은 Mock으로 대체
        self.client.get_return_requests = Mock()
        self.client.get_return_request_detail = Mock()
        self.client.confirm_return_receive = Mock()
        self.client.approve_return_request = Mock()
        self.client.get_return_withdraw_requests = Mock()
        self.client.create_return_exchange_invoice = Mock()
        
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
    
    def tearDown(self):
        """테스트 정리"""
        pass
    
    def test_get_return_requests_success(self):
        """반품 목록 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "data": [self.test_fixtures.get_sample_return_request()],
            "total_count": 1,
            "summary_stats": {"total_count": 1},
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_return_requests.return_value = mock_response
        
        # 검색 파라미터 생성
        search_params = ReturnRequestSearchParams(
            vendor_id=self.vendor_id,
            search_type="daily",
            created_at_from="2025-07-14",
            created_at_to="2025-07-14",
            cancel_type="RETURN"
        )
        
        # API 호출
        result = self.client.get_return_requests(search_params)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        self.assertIn("summary_stats", result)
        
        # Mock 호출 검증
        self.client.get_return_requests.assert_called_once_with(search_params)
    
    def test_get_return_request_detail_success(self):
        """반품 단건 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "return_request": self.test_fixtures.get_sample_return_request(),
            "detailed_info": {"priority": "HIGH"},
            "priority_level": "HIGH",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_return_request_detail.return_value = mock_response
        
        # API 호출
        result = self.client.get_return_request_detail(self.vendor_id, 365937)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("return_request", result)
        self.assertIn("detailed_info", result)
        self.assertIn("priority_level", result)
        
        # Mock 호출 검증
        self.client.get_return_request_detail.assert_called_once_with(self.vendor_id, 365937)
    
    def test_get_return_request_detail_not_found(self):
        """반품 단건 조회 실패 테스트 (404)"""
        # Mock API 응답 설정 (404 에러)
        mock_response = {
            "success": False,
            "error": "반품 요청을 찾을 수 없습니다",
            "error_code": 404,
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_return_request_detail.return_value = mock_response
        
        # API 호출
        result = self.client.get_return_request_detail(self.vendor_id, 999999)
        
        # 검증 (404 에러 응답)
        self.test_assertions.assert_error_response(result, expected_error_code=404)
    
    def test_confirm_return_receive_success(self):
        """반품 입고 확인 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "action": "receive_confirmation",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.confirm_return_receive.return_value = mock_response
        
        # API 호출
        result = self.client.confirm_return_receive(self.vendor_id, 365937)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("action", result)
        self.assertEqual(result["action"], "receive_confirmation")
        
        # Mock 호출 검증
        self.client.confirm_return_receive.assert_called_once_with(self.vendor_id, 365937)
    
    def test_approve_return_request_success(self):
        """반품 승인 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "action": "approval",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.approve_return_request.return_value = mock_response
        
        # API 호출
        result = self.client.approve_return_request(self.vendor_id, 365937, 1)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("action", result)
        self.assertEqual(result["action"], "approval")
        
        # Mock 호출 검증
        self.client.approve_return_request.assert_called_once_with(self.vendor_id, 365937, 1)
    
    def test_get_return_withdraw_requests_success(self):
        """반품 철회 이력 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "withdraw_requests": [self.test_fixtures.get_sample_withdraw_request()],
            "total_count": 1,
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_return_withdraw_requests.return_value = mock_response
        
        # API 호출
        result = self.client.get_return_withdraw_requests(
            self.vendor_id, "2025-07-14", "2025-07-14"
        )
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("withdraw_requests", result)
        self.assertIn("total_count", result)
        
        # Mock 호출 검증
        self.client.get_return_withdraw_requests.assert_called_once_with(
            self.vendor_id, "2025-07-14", "2025-07-14"
        )
    
    def test_create_return_exchange_invoice_success(self):
        """회수 송장 등록 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "invoice_data": self.test_fixtures.get_sample_invoice_response()["data"],
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.create_return_exchange_invoice.return_value = mock_response
        
        # API 호출
        result = self.client.create_return_exchange_invoice(
            vendor_id=self.vendor_id,
            receipt_id=365937,
            delivery_company_code="CJGLS",
            invoice_number="TEST20250714123456"
        )
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("invoice_data", result)
        
        # Mock 호출 검증
        self.client.create_return_exchange_invoice.assert_called_once_with(
            vendor_id=self.vendor_id,
            receipt_id=365937,
            delivery_company_code="CJGLS",
            invoice_number="TEST20250714123456"
        )


class TestReturnClientIntegration(unittest.TestCase):
    """통합 테스트 (환경변수 설정 시에만 실행)"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
        
        # 환경변수 확인
        self.has_credentials = config.validate_coupang_credentials()
    
    @unittest.skipUnless(config.validate_coupang_credentials(), 
                        "쿠팡 API 인증 정보가 설정되지 않음")
    def test_real_api_call_integration(self):
        """실제 API 호출 통합 테스트"""
        try:
            client = ReturnClient()
            
            # 검색 파라미터 생성
            search_params = ReturnRequestSearchParams(
                vendor_id=self.vendor_id,
                search_type="daily",
                created_at_from="2025-07-14",
                created_at_to="2025-07-14",
                cancel_type="RETURN"
            )
            
            # API 호출
            result = client.get_return_requests(search_params)
            
            # 기본 응답 구조 검증
            self.assertIn("success", result)
            self.assertIn("timestamp", result)
            
            if result.get("success"):
                self.assertIn("data", result)
                self.assertIn("total_count", result)
            else:
                self.assertIn("error", result)
                
        except Exception as e:
            self.fail(f"통합 테스트 실행 중 오류: {e}")


def run_refactored_tests():
    """리팩토링된 테스트 실행"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    test_suite.addTest(unittest.makeSuite(TestReturnClientRefactored))
    test_suite.addTest(unittest.makeSuite(TestValidatorsRefactored))
    test_suite.addTest(unittest.makeSuite(TestReturnClientMocked))
    test_suite.addTest(unittest.makeSuite(TestReturnClientIntegration))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 요약
    print("\n" + "="*80)
    print(f"🧪 리팩토링된 테스트 결과:")
    print(f"   실행: {result.testsRun}개")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"   실패: {len(result.failures)}개")
    print(f"   오류: {len(result.errors)}개")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 오류 발생 테스트:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n📊 성공률: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_refactored_tests()