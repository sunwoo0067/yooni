#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈 테스트
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

# 경로 설정
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 공통 모듈 사용
from common.test_utils import TestFixtures, TestAssertions, MockCoupangAPI
from common.config import config

# settlement 모듈 import
from .settlement_client import SettlementClient
from .models import SettlementSearchParams
from .validators import validate_vendor_id, validate_revenue_recognition_year_month, is_valid_vendor_id


class TestSettlementClientBasic(unittest.TestCase):
    """SettlementClient 기본 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_fixtures = TestFixtures()
        self.vendor_id = self.test_fixtures.get_sample_vendor_id()
    
    @patch.object(SettlementClient, '__init__', return_value=None)
    def test_client_initialization(self, mock_init):
        """클라이언트 초기화 테스트"""
        client = SettlementClient()
        self.assertIsNotNone(client)
        mock_init.assert_called_once()
    
    @patch.object(SettlementClient, '__init__', return_value=None)
    def test_api_name(self, mock_init):
        """API 이름 반환 테스트"""
        client = SettlementClient()
        client.get_api_name = SettlementClient.get_api_name.__get__(client, SettlementClient)
        self.assertEqual(client.get_api_name(), "지급내역 조회 API")


class TestSettlementValidators(unittest.TestCase):
    """Settlement 검증 함수 테스트"""
    
    def test_validate_vendor_id_valid_cases(self):
        """유효한 벤더 ID 테스트"""
        valid_cases = ["A01409684", "A12345678", "A00000001"]
        
        for vendor_id in valid_cases:
            with self.subTest(vendor_id=vendor_id):
                result = validate_vendor_id(vendor_id)
                self.assertEqual(result, vendor_id)
    
    def test_validate_vendor_id_invalid_cases(self):
        """유효하지 않은 벤더 ID 테스트"""
        invalid_cases = ["", "B01409684", "A0140968", None, 123]
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaises(ValueError):
                    validate_vendor_id(invalid_value)
    
    def test_validate_year_month_valid_cases(self):
        """유효한 매출인식월 테스트"""
        valid_cases = ["2025-07", "2025-06", "2024-12"]
        
        for year_month in valid_cases:
            with self.subTest(year_month=year_month):
                result = validate_revenue_recognition_year_month(year_month)
                self.assertEqual(result, year_month)
    
    def test_validate_year_month_invalid_cases(self):
        """유효하지 않은 매출인식월 테스트"""
        invalid_cases = ["", "2025-13", "25-07", "2025/07", None, 123]
        
        for invalid_value in invalid_cases:
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaises(ValueError):
                    validate_revenue_recognition_year_month(invalid_value)
    
    def test_is_valid_vendor_id_consistency(self):
        """is_valid_vendor_id와 validate_vendor_id 일관성 테스트"""
        test_cases = ["A01409684", "B01409684", "invalid", None, ""]
        
        for test_value in test_cases:
            with self.subTest(test_value=test_value):
                is_valid_result = is_valid_vendor_id(test_value)
                
                try:
                    validate_vendor_id(test_value)
                    validate_result = True
                except ValueError:
                    validate_result = False
                
                self.assertEqual(is_valid_result, validate_result)


def run_settlement_tests():
    """지급내역 테스트 실행"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestSettlementClientBasic))
    test_suite.addTest(loader.loadTestsFromTestCase(TestSettlementValidators))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 요약
    print("\n" + "="*80)
    print("💳 지급내역 조회 테스트 결과:")
    print(f"   실행: {result.testsRun}개")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"   실패: {len(result.failures)}개")
    print(f"   오류: {len(result.errors)}개")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n📊 성공률: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_settlement_tests()