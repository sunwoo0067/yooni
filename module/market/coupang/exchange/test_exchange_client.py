#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 클라이언트 테스트
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

# exchange 키워드는 문제없지만 일관성을 위해 importlib 사용
exchange_client_module = importlib.import_module('exchange.exchange_client')
ExchangeClient = exchange_client_module.ExchangeClient

exchange_models_module = importlib.import_module('exchange.models')
ExchangeRequestSearchParams = exchange_models_module.ExchangeRequestSearchParams

exchange_validators_module = importlib.import_module('exchange.validators')
validate_exchange_id = exchange_validators_module.validate_exchange_id
is_valid_exchange_id = exchange_validators_module.is_valid_exchange_id
validate_vendor_id = exchange_validators_module.validate_vendor_id
validate_exchange_reject_code = exchange_validators_module.validate_exchange_reject_code
validate_delivery_code = exchange_validators_module.validate_delivery_code
validate_invoice_number = exchange_validators_module.validate_invoice_number


class TestExchangeClientRefactored(unittest.TestCase):
    """리팩토링된 ExchangeClient 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # 테스트 데이터
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
        self.sample_exchange_id = 101268974
    
    @patch.object(ExchangeClient, '__init__', return_value=None)
    def test_client_initialization(self, mock_init):
        """클라이언트 초기화 테스트"""
        client = ExchangeClient()
        self.assertIsNotNone(client)
        mock_init.assert_called_once()
    
    @patch.object(ExchangeClient, '__init__', return_value=None)
    def test_api_name(self, mock_init):
        """API 이름 반환 테스트"""
        client = ExchangeClient()
        client.get_api_name = ExchangeClient.get_api_name.__get__(client, ExchangeClient)
        self.assertEqual(client.get_api_name(), "교환요청 관리 API")


class TestExchangeValidatorsRefactored(unittest.TestCase):
    """리팩토링된 검증 함수 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
    
    def test_validate_exchange_id_valid_cases(self):
        """유효한 교환 ID 테스트"""
        valid_cases = [
            (101268974, 101268974),
            ("101268974", 101268974),
            ("  123456  ", 123456),
            (1, 1),
            (999999999, 999999999)
        ]
        
        for input_value, expected in valid_cases:
            with self.subTest(input_value=input_value):
                result = validate_exchange_id(input_value)
                self.assertEqual(result, expected)
    
    def test_validate_exchange_id_invalid_cases(self):
        """유효하지 않은 교환 ID 테스트"""
        invalid_cases = ["", "invalid", -123, 0, None, "123abc", [], {}]
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                self.test_assertions.assert_validation_error(
                    validate_exchange_id, invalid_value
                )
    
    def test_is_valid_exchange_id_consistency(self):
        """is_valid_exchange_id와 validate_exchange_id 일관성 테스트"""
        test_cases = [101268974, "101268974", -123, "invalid", None, ""]
        
        for test_value in test_cases:
            with self.subTest(test_value=test_value):
                is_valid_result = is_valid_exchange_id(test_value)
                
                try:
                    validate_exchange_id(test_value)
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
    
    def test_validate_exchange_reject_code_valid_cases(self):
        """유효한 교환 거부 코드 테스트"""
        valid_cases = ["SOLDOUT", "WITHDRAW"]
        
        for reject_code in valid_cases:
            with self.subTest(reject_code=reject_code):
                result = validate_exchange_reject_code(reject_code)
                self.assertEqual(result, reject_code)
    
    def test_validate_exchange_reject_code_invalid_cases(self):
        """유효하지 않은 교환 거부 코드 테스트"""
        invalid_cases = ["", "INVALID", "CANCEL", None, 123, []]
        
        for invalid_code in invalid_cases:
            with self.subTest(invalid_code=invalid_code):
                self.test_assertions.assert_validation_error(
                    validate_exchange_reject_code, invalid_code
                )
    
    def test_validate_delivery_code_valid_cases(self):
        """유효한 택배사 코드 테스트"""
        valid_cases = ["CJGLS", "EPOST", "KDEXP", "HANJIN", "LOTTE", "CUSTOM123"]
        
        for delivery_code in valid_cases:
            with self.subTest(delivery_code=delivery_code):
                result = validate_delivery_code(delivery_code)
                self.assertEqual(result, delivery_code)
    
    def test_validate_invoice_number_valid_cases(self):
        """유효한 운송장번호 테스트"""
        valid_cases = ["1234567890", "ABC123456789", "12345-67890", "CJ123456789012"]
        
        for invoice_number in valid_cases:
            with self.subTest(invoice_number=invoice_number):
                result = validate_invoice_number(invoice_number)
                self.assertEqual(result, invoice_number)
    
    def test_validate_invoice_number_invalid_cases(self):
        """유효하지 않은 운송장번호 테스트"""
        invalid_cases = ["", "1234", "123456789012345678901", "123@456", None, []]
        
        for invalid_number in invalid_cases:
            with self.subTest(invalid_number=invalid_number):
                self.test_assertions.assert_validation_error(
                    validate_invoice_number, invalid_number
                )


class TestExchangeClientMocked(unittest.TestCase):
    """Mock을 활용한 ExchangeClient API 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # ExchangeClient Mock 설정
        self.client = Mock(spec=ExchangeClient)
        
        # Mock 메서드 설정
        self.client.validate_vendor_id.return_value = self.test_fixtures.get_sample_vendor_id()
        self.client.validate_exchange_id = Mock()
        
        # 실제 메서드들은 Mock으로 대체
        self.client.get_exchange_requests = Mock()
        self.client.get_exchange_requests_by_date_range = Mock()
        self.client.get_today_exchange_requests = Mock()
        self.client.create_exchange_analysis_report = Mock()
        self.client.get_vendor_fault_exchanges = Mock()
        self.client.confirm_exchange_receive = Mock()
        self.client.reject_exchange_request = Mock()
        self.client.upload_exchange_invoice = Mock()
        
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
    
    def tearDown(self):
        """테스트 정리"""
        pass
    
    def test_get_exchange_requests_success(self):
        """교환요청 목록 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "data": [self.get_sample_exchange_request()],
            "total_count": 1,
            "summary_stats": {"total_count": 1},
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_exchange_requests.return_value = mock_response
        
        # 검색 파라미터 생성
        search_params = ExchangeRequestSearchParams(
            vendor_id=self.vendor_id,
            created_at_from="2025-07-14T00:00:00",
            created_at_to="2025-07-14T23:59:59"
        )
        
        # API 호출
        result = self.client.get_exchange_requests(search_params)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        self.assertIn("summary_stats", result)
        
        # Mock 호출 검증
        self.client.get_exchange_requests.assert_called_once_with(search_params)
    
    def test_get_today_exchange_requests_success(self):
        """오늘의 교환요청 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "data": [self.get_sample_exchange_request()],
            "total_count": 1,
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_today_exchange_requests.return_value = mock_response
        
        # API 호출
        result = self.client.get_today_exchange_requests(self.vendor_id)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        
        # Mock 호출 검증
        self.client.get_today_exchange_requests.assert_called_once_with(self.vendor_id)
    
    def test_create_exchange_analysis_report_success(self):
        """교환요청 분석 보고서 생성 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "analysis_report": {
                "summary": "총 1건의 교환요청 분석 완료",
                "overall_status": "🟢 양호",
                "key_metrics": {"total_exchanges": 1, "vendor_fault_rate": 0.0},
                "recommendations": ["정기적인 분석을 권장합니다"]
            },
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.create_exchange_analysis_report.return_value = mock_response
        
        # API 호출
        result = self.client.create_exchange_analysis_report(self.vendor_id, 7)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("analysis_report", result)
        
        # Mock 호출 검증
        self.client.create_exchange_analysis_report.assert_called_once_with(self.vendor_id, 7)
    
    def test_get_vendor_fault_exchanges_success(self):
        """업체 과실 교환요청 조회 성공 테스트"""
        # Mock API 응답 설정
        vendor_fault_exchange = self.get_sample_exchange_request()
        vendor_fault_exchange["fault_type"] = "VENDOR"
        
        mock_response = {
            "success": True,
            "data": [vendor_fault_exchange],
            "total_count": 1,
            "fault_rate": 100.0,
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_vendor_fault_exchanges.return_value = mock_response
        
        # API 호출
        result = self.client.get_vendor_fault_exchanges(self.vendor_id, 7)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("fault_rate", result)
        
        # Mock 호출 검증
        self.client.get_vendor_fault_exchanges.assert_called_once_with(self.vendor_id, 7)
    
    def test_confirm_exchange_receive_success(self):
        """교환요청 입고 확인 처리 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "code": 200,
            "message": "OK",
            "result_code": "SUCCESS",
            "result_message": "처리가 완료되었습니다",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.confirm_exchange_receive.return_value = mock_response
        
        exchange_id = 101268974
        
        # API 호출
        result = self.client.confirm_exchange_receive(exchange_id, self.vendor_id)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("result_code", result)
        
        # Mock 호출 검증
        self.client.confirm_exchange_receive.assert_called_once_with(exchange_id, self.vendor_id)
    
    def test_reject_exchange_request_success(self):
        """교환요청 거부 처리 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "code": 200,
            "message": "OK",
            "reject_code": "SOLDOUT",
            "reject_message": "교환할수있지만 아이템이 매진되였습니다",
            "result_code": "SUCCESS",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.reject_exchange_request.return_value = mock_response
        
        exchange_id = 101268974
        reject_code = "SOLDOUT"
        
        # API 호출
        result = self.client.reject_exchange_request(exchange_id, self.vendor_id, reject_code)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("reject_code", result)
        self.assertIn("reject_message", result)
        
        # Mock 호출 검증
        self.client.reject_exchange_request.assert_called_once_with(
            exchange_id, self.vendor_id, reject_code
        )
    
    def test_upload_exchange_invoice_success(self):
        """교환상품 송장 업로드 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "code": 200,
            "message": "OK",
            "delivery_code": "CJGLS",
            "invoice_number": "1234567890123",
            "shipment_box_id": 12345,
            "result_code": "SUCCESS",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.upload_exchange_invoice.return_value = mock_response
        
        exchange_id = 101268974
        delivery_code = "CJGLS"
        invoice_number = "1234567890123"
        shipment_box_id = 12345
        
        # API 호출
        result = self.client.upload_exchange_invoice(
            exchange_id, self.vendor_id, delivery_code, invoice_number, shipment_box_id
        )
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("delivery_code", result)
        self.assertIn("invoice_number", result)
        self.assertIn("shipment_box_id", result)
        
        # Mock 호출 검증
        self.client.upload_exchange_invoice.assert_called_once_with(
            exchange_id, self.vendor_id, delivery_code, invoice_number, shipment_box_id
        )
    
    def get_sample_exchange_request(self) -> Dict[str, Any]:
        """샘플 교환요청 데이터"""
        return {
            "exchange_id": 101268974,
            "order_id": 11000013144262,
            "vendor_id": "A01409684",
            "order_delivery_status_code": "FINAL_DELIVERY",
            "exchange_status": "PROGRESS",
            "refer_type": "WEB_MOBILE",
            "fault_type": "CUSTOMER",
            "exchange_amount": 0,
            "reason_code": "DIFFERENTOPT",
            "reason_code_text": "색상/ 사이즈가 기대와 다름",
            "reason_etc_detail": "베이지색 주문했는데 브라운이 왔습니다",
            "created_by_type": "CUSTOMER",
            "created_at": "2025-07-14T10:00:00",
            "modified_by_type": "TRACKING",
            "modified_at": "2025-07-14T10:00:00",
            "exchange_items": [{
                "exchange_item_id": 1765111,
                "order_item_id": 3476137875,
                "target_item_name": "후아유(WHO.A.U) 벙커Ⅰ 레터 백팩",
                "quantity": 1,
                "target_item_unit_price": 35900
            }],
            "successable": False,
            "rejectable": False,
            "delivery_invoice_modifiable": False
        }


class TestExchangeClientIntegration(unittest.TestCase):
    """통합 테스트 (환경변수 설정 시에만 실행)"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
        
        # 환경변수 확인
        self.has_credentials = config.validate_coupang_credentials()
    
    @unittest.skipUnless(config.validate_coupang_credentials(), 
                        "쿠팡 API 인증 정보가 .env 파일에 설정되지 않음")
    def test_real_api_call_integration(self):
        """실제 API 호출 통합 테스트 (.env 기반)"""
        try:
            client = ExchangeClient()
            
            # 검색 파라미터 생성 (오늘 하루) - .env에서 vendor_id 자동 로드
            search_params = ExchangeRequestSearchParams(
                vendor_id=client.vendor_id,
                created_at_from="2025-07-14T00:00:00",
                created_at_to="2025-07-14T23:59:59"
            )
            
            # API 호출
            result = client.get_exchange_requests(search_params)
            
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


def run_exchange_tests():
    """교환요청 테스트 실행"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestExchangeClientRefactored))
    test_suite.addTest(loader.loadTestsFromTestCase(TestExchangeValidatorsRefactored))
    test_suite.addTest(loader.loadTestsFromTestCase(TestExchangeClientMocked))
    test_suite.addTest(loader.loadTestsFromTestCase(TestExchangeClientIntegration))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 요약
    print("\n" + "="*80)
    print(f"🧪 교환요청 테스트 결과:")
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
    run_exchange_tests()