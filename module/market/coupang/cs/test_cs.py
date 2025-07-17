#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 클라이언트 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# 경로 설정
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 공통 모듈 사용
from common.test_utils import TestFixtures, TestAssertions, MockCoupangAPI
from common.config import config

# cs 모듈 import
from .cs_client import CSClient
from .models import InquirySearchParams, CustomerInquiry
from .validators import (
    validate_vendor_id, validate_date_format, validate_date_range,
    validate_answered_type, validate_inquiry_id, is_valid_inquiry_id,
    validate_timeout_settings
)


class TestCSClientRefactored(unittest.TestCase):
    """리팩토링된 CSClient 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # 테스트 데이터
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
        self.sample_inquiry_id = 12345
    
    @patch.object(CSClient, '__init__', return_value=None)
    def test_client_initialization(self, mock_init):
        """클라이언트 초기화 테스트"""
        client = CSClient()
        self.assertIsNotNone(client)
        mock_init.assert_called_once()
    
    @patch.object(CSClient, '__init__', return_value=None)
    def test_api_name(self, mock_init):
        """API 이름 반환 테스트"""
        client = CSClient()
        client.get_api_name = CSClient.get_api_name.__get__(client, CSClient)
        self.assertEqual(client.get_api_name(), "고객문의(CS) 관리 API")


class TestCSValidatorsRefactored(unittest.TestCase):
    """리팩토링된 CS 검증 함수 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
    
    def test_validate_vendor_id_valid_cases(self):
        """유효한 벤더 ID 테스트"""
        valid_cases = ["A01409684", "A12345678", "A00000001"]
        
        for vendor_id in valid_cases:
            with self.subTest(vendor_id=vendor_id):
                result = validate_vendor_id(vendor_id)
                self.assertEqual(result, vendor_id)
    
    def test_validate_vendor_id_invalid_cases(self):
        """유효하지 않은 벤더 ID 테스트"""
        invalid_cases = ["", "B01409684", "A0140968", "A014096844", None, 123, []]
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                self.test_assertions.assert_validation_error(
                    validate_vendor_id, invalid_value
                )
    
    def test_validate_date_format_valid_cases(self):
        """유효한 날짜 형식 테스트"""
        valid_cases = [
            ("2025-07-14", "조회시작일"),
            ("2025-01-01", "조회종료일"),
            ("2024-12-31", "테스트날짜")
        ]
        
        for date_str, field_name in valid_cases:
            with self.subTest(date_str=date_str):
                result = validate_date_format(date_str, field_name)
                self.assertEqual(result, date_str)
    
    def test_validate_date_format_invalid_cases(self):
        """유효하지 않은 날짜 형식 테스트"""
        invalid_cases = [
            ("", "조회시작일"),
            ("2025-7-14", "조회시작일"),  # 0 패딩 없음
            ("25-07-14", "조회시작일"),   # 연도 2자리
            ("2025/07/14", "조회시작일"), # 잘못된 구분자
            ("2025-13-01", "조회시작일"), # 잘못된 월
            ("2025-02-30", "조회시작일"), # 잘못된 일
            (None, "조회시작일"),
            (123, "조회시작일")
        ]
        
        for invalid_date, field_name in invalid_cases:
            with self.subTest(invalid_date=invalid_date):
                self.test_assertions.assert_validation_error(
                    validate_date_format, invalid_date, field_name
                )
    
    def test_validate_date_range_valid_cases(self):
        """유효한 날짜 범위 테스트"""
        valid_cases = [
            ("2025-07-14", "2025-07-14"),  # 같은 날
            ("2025-07-14", "2025-07-15"),  # 1일 차이
            ("2025-07-14", "2025-07-21"),  # 7일 차이 (최대)
        ]
        
        for start_date, end_date in valid_cases:
            with self.subTest(start_date=start_date, end_date=end_date):
                result_start, result_end = validate_date_range(start_date, end_date)
                self.assertEqual(result_start, start_date)
                self.assertEqual(result_end, end_date)
    
    def test_validate_date_range_invalid_cases(self):
        """유효하지 않은 날짜 범위 테스트"""
        invalid_cases = [
            ("2025-07-15", "2025-07-14"),  # 시작일이 종료일보다 늦음
            ("2025-07-14", "2025-07-22"),  # 7일 초과
            ("2025-07-01", "2025-07-30"),  # 29일 차이
        ]
        
        for start_date, end_date in invalid_cases:
            with self.subTest(start_date=start_date, end_date=end_date):
                self.test_assertions.assert_validation_error(
                    validate_date_range, start_date, end_date
                )
    
    def test_validate_answered_type_valid_cases(self):
        """유효한 답변 상태 테스트"""
        valid_cases = ["ALL", "ANSWERED", "NOANSWER"]
        
        for answered_type in valid_cases:
            with self.subTest(answered_type=answered_type):
                result = validate_answered_type(answered_type)
                self.assertEqual(result, answered_type)
    
    def test_validate_answered_type_invalid_cases(self):
        """유효하지 않은 답변 상태 테스트"""
        invalid_cases = ["", "INVALID", "COMPLETE", None, 123, []]
        
        for invalid_type in invalid_cases:
            with self.subTest(invalid_type=invalid_type):
                self.test_assertions.assert_validation_error(
                    validate_answered_type, invalid_type
                )
    
    def test_validate_inquiry_id_valid_cases(self):
        """유효한 문의 ID 테스트"""
        valid_cases = [
            (12345, 12345),
            ("12345", 12345),
            ("  67890  ", 67890),
            (1, 1),
            (999999999, 999999999)
        ]
        
        for input_value, expected in valid_cases:
            with self.subTest(input_value=input_value):
                result = validate_inquiry_id(input_value)
                self.assertEqual(result, expected)
    
    def test_validate_inquiry_id_invalid_cases(self):
        """유효하지 않은 문의 ID 테스트"""
        invalid_cases = ["", "invalid", -123, 0, None, "123abc", [], {}]
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                self.test_assertions.assert_validation_error(
                    validate_inquiry_id, invalid_value
                )
    
    def test_is_valid_inquiry_id_consistency(self):
        """is_valid_inquiry_id와 validate_inquiry_id 일관성 테스트"""
        test_cases = [12345, "12345", -123, "invalid", None, ""]
        
        for test_value in test_cases:
            with self.subTest(test_value=test_value):
                is_valid_result = is_valid_inquiry_id(test_value)
                
                try:
                    validate_inquiry_id(test_value)
                    validate_result = True
                except ValueError:
                    validate_result = False
                
                self.assertEqual(is_valid_result, validate_result,
                               f"일관성 오류: {test_value}")
    
    def test_validate_timeout_settings(self):
        """타임아웃 설정 검증 테스트"""
        test_cases = [
            (10, 1, False),  # 안전한 설정
            (50, 7, True),   # 위험한 설정 (큰 페이지 크기 + 긴 기간)
            (30, 5, True),   # 중간 위험
            (5, 2, False),   # 안전한 설정
        ]
        
        for page_size, date_range_days, expected_risky in test_cases:
            with self.subTest(page_size=page_size, date_range_days=date_range_days):
                result = validate_timeout_settings(page_size, date_range_days)
                
                self.assertIn("is_risky", result)
                self.assertIn("warnings", result)
                self.assertIn("timeout_seconds", result)
                self.assertEqual(result["is_risky"], expected_risky)


class TestCSClientMocked(unittest.TestCase):
    """Mock을 활용한 CSClient API 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.test_assertions = TestAssertions()
        self.mock_api = MockCoupangAPI()
        
        # CSClient Mock 설정
        self.client = Mock(spec=CSClient)
        
        # Mock 메서드 설정
        self.client.get_customer_inquiries = Mock()
        self.client.get_inquiries_by_date_range = Mock()
        self.client.get_today_inquiries = Mock()
        self.client.get_unanswered_inquiries = Mock()
        self.client.create_inquiry_analysis_report = Mock()
        
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
    
    def tearDown(self):
        """테스트 정리"""
        pass
    
    def test_get_customer_inquiries_success(self):
        """고객문의 목록 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "data": [self.get_sample_customer_inquiry()],
            "total_count": 1,
            "summary_stats": {"total_count": 1, "answered_count": 0, "unanswered_count": 1},
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_customer_inquiries.return_value = mock_response
        
        # 검색 파라미터 생성
        search_params = InquirySearchParams(
            vendor_id=self.vendor_id,
            answered_type="ALL",
            inquiry_start_at="2025-07-14",
            inquiry_end_at="2025-07-14"
        )
        
        # API 호출
        result = self.client.get_customer_inquiries(search_params)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        self.assertIn("summary_stats", result)
        
        # Mock 호출 검증
        self.client.get_customer_inquiries.assert_called_once_with(search_params)
    
    def test_get_today_inquiries_success(self):
        """오늘의 고객문의 조회 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "data": [self.get_sample_customer_inquiry()],
            "total_count": 1,
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_today_inquiries.return_value = mock_response
        
        # API 호출
        result = self.client.get_today_inquiries(self.vendor_id, "ALL")
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        
        # Mock 호출 검증
        self.client.get_today_inquiries.assert_called_once_with(self.vendor_id, "ALL")
    
    def test_get_unanswered_inquiries_success(self):
        """미답변 고객문의 조회 성공 테스트"""
        # Mock API 응답 설정
        unanswered_inquiry = self.get_sample_customer_inquiry()
        unanswered_inquiry["is_answered"] = False
        
        mock_response = {
            "success": True,
            "data": [unanswered_inquiry],
            "total_count": 1,
            "message": "미답변 고객문의 조회 성공 (1건)",
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.get_unanswered_inquiries.return_value = mock_response
        
        # API 호출
        result = self.client.get_unanswered_inquiries(self.vendor_id, 7)
        
        # 검증
        self.test_assertions.assert_success_response(result, expected_data_count=1)
        self.assertIn("total_count", result)
        
        # Mock 호출 검증
        self.client.get_unanswered_inquiries.assert_called_once_with(self.vendor_id, 7)
    
    def test_create_inquiry_analysis_report_success(self):
        """고객문의 분석 보고서 생성 성공 테스트"""
        # Mock API 응답 설정
        mock_response = {
            "success": True,
            "analysis_report": {
                "summary": "총 1건의 고객문의 분석 완료",
                "overall_status": "🟢 우수",
                "key_metrics": {
                    "total_inquiries": 1,
                    "answered_count": 0,
                    "unanswered_count": 1,
                    "answer_rate": 0.0
                },
                "recommendations": ["미답변 문의 비율을 낮추기 위한 대응 계획이 필요합니다"]
            },
            "timestamp": "2025-07-14T08:50:45.236462"
        }
        self.client.create_inquiry_analysis_report.return_value = mock_response
        
        # API 호출
        result = self.client.create_inquiry_analysis_report(self.vendor_id, 7)
        
        # 검증
        self.test_assertions.assert_success_response(result)
        self.assertIn("analysis_report", result)
        
        # Mock 호출 검증
        self.client.create_inquiry_analysis_report.assert_called_once_with(self.vendor_id, 7)
    
    def get_sample_customer_inquiry(self) -> Dict[str, Any]:
        """샘플 고객문의 데이터"""
        return {
            "inquiry_id": 12345,
            "product_id": 678901,
            "seller_product_id": 234567,
            "seller_item_id": 890123,
            "vendor_item_id": 456789,
            "content": "상품 크기 문의드립니다",
            "inquiry_at": "2025-07-14 10:30:00",
            "order_ids": [],
            "buyer_email": "test@example.com",
            "comment_dto_list": [],
            "is_answered": False,
            "answer_count": 0,
            "latest_answer_at": None
        }


class TestCSClientIntegration(unittest.TestCase):
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
            client = CSClient()
            
            # 검색 파라미터 생성 (오늘 하루) - .env에서 vendor_id 자동 로드
            search_params = InquirySearchParams(
                vendor_id=client.vendor_id,
                answered_type="ALL",
                inquiry_start_at="2025-07-14",
                inquiry_end_at="2025-07-14"
            )
            
            # API 호출
            result = client.get_customer_inquiries(search_params)
            
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


def run_cs_tests():
    """고객문의 테스트 실행"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestCSClientRefactored))
    test_suite.addTest(loader.loadTestsFromTestCase(TestCSValidatorsRefactored))
    test_suite.addTest(loader.loadTestsFromTestCase(TestCSClientMocked))
    test_suite.addTest(loader.loadTestsFromTestCase(TestCSClientIntegration))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 요약
    print("\n" + "="*80)
    print(f"🧪 고객문의(CS) 테스트 결과:")
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
    run_cs_tests()