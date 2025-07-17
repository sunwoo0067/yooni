#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 발주서 관리 테스트
발주서 목록 조회 API 테스트 코드
"""

import unittest
from unittest.mock import Mock, patch
import os
import sys
from datetime import datetime, timedelta

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from .order_client import OrderClient
from .models import OrderSheetSearchParams, OrderSheetListResponse, OrderSheet, Orderer, Receiver, OrderItem
from .validators import validate_search_params, validate_vendor_id, validate_date_range
from .utils import (
    format_api_response, handle_api_success, handle_api_error, 
    calculate_order_summary, format_currency, format_datetime
)
from .constants import ORDER_STATUS, MAX_DATE_RANGE_DAYS


class TestOrderSheetSearchParams(unittest.TestCase):
    """발주서 검색 파라미터 테스트"""
    
    def setUp(self):
        self.valid_params = OrderSheetSearchParams(
            vendor_id="A12345678",
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT"
        )
    
    def test_to_query_params(self):
        """쿼리 파라미터 변환 테스트"""
        query_string = self.valid_params.to_query_params()
        
        self.assertIn("createdAtFrom=2024-01-01", query_string)
        self.assertIn("createdAtTo=2024-01-02", query_string)
        self.assertIn("status=ACCEPT", query_string)
    
    def test_to_query_params_with_optional_fields(self):
        """선택적 필드 포함 쿼리 파라미터 테스트"""
        params = OrderSheetSearchParams(
            vendor_id="A12345678",
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT",
            next_token="test_token",
            max_per_page=20,
            search_type="timeFrame"
        )
        
        query_string = params.to_query_params()
        
        self.assertIn("nextToken=test_token", query_string)
        self.assertIn("maxPerPage=20", query_string)
        self.assertIn("searchType=timeFrame", query_string)
    
    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        result = self.valid_params.to_dict()
        
        self.assertEqual(result["vendorId"], "A12345678")
        self.assertEqual(result["createdAtFrom"], "2024-01-01")
        self.assertEqual(result["createdAtTo"], "2024-01-02")
        self.assertEqual(result["status"], "ACCEPT")


class TestValidators(unittest.TestCase):
    """검증 함수 테스트"""
    
    def test_validate_vendor_id_valid(self):
        """유효한 판매자 ID 검증 테스트"""
        # 정상적인 경우는 예외가 발생하지 않아야 함
        try:
            validate_vendor_id("A12345678")
        except ValueError:
            self.fail("유효한 판매자 ID에서 예외가 발생했습니다")
    
    def test_validate_vendor_id_invalid(self):
        """유효하지 않은 판매자 ID 검증 테스트"""
        invalid_ids = ["", "12345678", "B12345678", "A1234567", "A123456789"]
        
        for vendor_id in invalid_ids:
            with self.assertRaises(ValueError):
                validate_vendor_id(vendor_id)
    
    def test_validate_date_range_valid(self):
        """유효한 날짜 범위 검증 테스트"""
        try:
            validate_date_range("2024-01-01", "2024-01-02")
        except ValueError:
            self.fail("유효한 날짜 범위에서 예외가 발생했습니다")
    
    def test_validate_date_range_invalid_format(self):
        """잘못된 날짜 형식 검증 테스트"""
        with self.assertRaises(ValueError):
            validate_date_range("2024/01/01", "2024-01-02")
    
    def test_validate_date_range_too_long(self):
        """날짜 범위 초과 검증 테스트"""
        start_date = "2024-01-01"
        end_date = "2024-02-15"  # 45일 차이
        
        with self.assertRaises(ValueError):
            validate_date_range(start_date, end_date)
    
    def test_validate_search_params(self):
        """검색 파라미터 전체 검증 테스트"""
        valid_params = OrderSheetSearchParams(
            vendor_id="A12345678",
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT"
        )
        
        # 정상적인 경우는 예외가 발생하지 않아야 함
        try:
            validate_search_params(valid_params)
        except ValueError:
            self.fail("유효한 검색 파라미터에서 예외가 발생했습니다")


class TestUtils(unittest.TestCase):
    """유틸리티 함수 테스트"""
    
    def test_format_api_response_success(self):
        """성공 응답 포맷팅 테스트"""
        response = format_api_response(
            success=True,
            data=["test_data"],
            message="성공"
        )
        
        self.assertTrue(response["success"])
        self.assertEqual(response["data"], ["test_data"])
        self.assertEqual(response["message"], "성공")
    
    def test_format_api_response_error(self):
        """오류 응답 포맷팅 테스트"""
        response = format_api_response(
            success=False,
            error="오류 발생",
            code="400"
        )
        
        self.assertFalse(response["success"])
        self.assertEqual(response["error"], "오류 발생")
        self.assertEqual(response["code"], "400")
    
    def test_handle_api_success(self):
        """API 성공 응답 처리 테스트"""
        api_response = {
            "code": 200,
            "data": [{"orderId": 123}],
            "message": "성공",
            "nextToken": "test_token"
        }
        
        result = handle_api_success(api_response, "기본 메시지")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], [{"orderId": 123}])
        self.assertEqual(result["next_token"], "test_token")
    
    def test_calculate_order_summary_empty(self):
        """빈 발주서 목록 요약 계산 테스트"""
        summary = calculate_order_summary([])
        
        self.assertEqual(summary["total_orders"], 0)
        self.assertEqual(summary["total_amount"], 0)
        self.assertEqual(summary["total_shipping_fee"], 0)
        self.assertEqual(summary["status_summary"], {})
        self.assertEqual(summary["delivery_company_summary"], {})
    
    def test_calculate_order_summary_with_data(self):
        """발주서 데이터 요약 계산 테스트"""
        mock_orders = [
            {
                "status": "ACCEPT",
                "shippingPrice": 3000,
                "deliveryCompanyName": "CJ 대한통운",
                "orderItems": [
                    {"orderPrice": 10000},
                    {"orderPrice": 5000}
                ]
            },
            {
                "status": "DELIVERING", 
                "shippingPrice": 0,
                "deliveryCompanyName": "한진택배",
                "orderItems": [
                    {"orderPrice": 20000}
                ]
            }
        ]
        
        summary = calculate_order_summary(mock_orders)
        
        self.assertEqual(summary["total_orders"], 2)
        self.assertEqual(summary["total_amount"], 35000)  # 10000 + 5000 + 20000
        self.assertEqual(summary["total_shipping_fee"], 3000)
        self.assertEqual(summary["status_summary"]["ACCEPT"], 1)
        self.assertEqual(summary["status_summary"]["DELIVERING"], 1)
        self.assertEqual(summary["delivery_company_summary"]["CJ 대한통운"], 1)
        self.assertEqual(summary["delivery_company_summary"]["한진택배"], 1)
    
    def test_format_currency(self):
        """금액 포맷팅 테스트"""
        self.assertEqual(format_currency(1000), "1,000원")
        self.assertEqual(format_currency(1234567), "1,234,567원")
    
    def test_format_datetime(self):
        """날짜시간 포맷팅 테스트"""
        # ISO 형식
        result = format_datetime("2024-01-01T10:30:00")
        self.assertEqual(result, "2024-01-01 10:30:00")
        
        # 이미 포맷된 형식
        result = format_datetime("2024-01-01 10:30:00")
        self.assertEqual(result, "2024-01-01 10:30:00")


class TestOrderClient(unittest.TestCase):
    """발주서 클라이언트 테스트"""
    
    def setUp(self):
        self.client = OrderClient("test_access", "test_secret")
        self.valid_params = OrderSheetSearchParams(
            vendor_id="A12345678",
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT"
        )
    
    @patch.object(OrderClient, '_make_request')
    def test_get_order_sheets_success(self, mock_request):
        """발주서 목록 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = {
            "code": 200,
            "data": [
                {
                    "orderId": 123,
                    "status": "ACCEPT",
                    "orderedAt": "2024-01-01T10:00:00",
                    "shippingPrice": 3000,
                    "orderer": {
                        "name": "홍길동",
                        "email": "test@test.com",
                        "safeNumber": "010-****-1234"
                    },
                    "receiver": {
                        "name": "김철수",
                        "safeNumber": "010-****-5678",
                        "addr1": "서울시 강남구",
                        "addr2": "테스트동 123",
                        "postCode": "12345"
                    },
                    "orderItems": [
                        {
                            "vendorItemId": 1001,
                            "vendorItemName": "테스트 상품",
                            "shippingCount": 2,
                            "salesPrice": 10000,
                            "orderPrice": 20000,
                            "discountPrice": 0,
                            "sellerProductId": 2001,
                            "sellerProductName": "판매자 상품",
                            "sellerProductItemName": "판매자 옵션",
                            "cancelCount": 0,
                            "holdCountForCancel": 0
                        }
                    ],
                    "shipmentBoxId": 999,
                    "paidAt": "2024-01-01T10:05:00",
                    "remotePrice": 0,
                    "remoteArea": False,
                    "splitShipping": False,
                    "ableSplitShipping": True
                }
            ],
            "nextToken": "test_next_token"
        }
        mock_request.return_value = mock_response
        
        # API 호출
        result = self.client.get_order_sheets(self.valid_params)
        
        # 검증
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["next_token"], "test_next_token")
        
        # Mock 호출 확인
        mock_request.assert_called_once()
    
    @patch.object(OrderClient, '_make_request')
    def test_get_order_sheets_error(self, mock_request):
        """발주서 목록 조회 오류 테스트"""
        # Mock 오류 응답 설정
        mock_response = {
            "code": 400,
            "message": "잘못된 요청",
            "data": None
        }
        mock_request.return_value = mock_response
        
        # API 호출
        result = self.client.get_order_sheets(self.valid_params)
        
        # 검증
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_get_order_sheets_invalid_params(self):
        """잘못된 파라미터로 발주서 조회 테스트"""
        invalid_params = OrderSheetSearchParams(
            vendor_id="invalid",  # 잘못된 형식
            created_at_from="2024-01-01",
            created_at_to="2024-01-02",
            status="ACCEPT"
        )
        
        # 검증 오류가 발생해야 함
        with self.assertRaises(ValueError):
            self.client.get_order_sheets(invalid_params)
    
    @patch.object(OrderClient, 'get_order_sheets')
    def test_get_order_sheets_all_pages(self, mock_get_sheets):
        """전체 페이지 발주서 조회 테스트"""
        # Mock 응답 시나리오: 2페이지 데이터
        mock_responses = [
            {
                "success": True,
                "data": [{"orderId": 1}, {"orderId": 2}],
                "next_token": "page2_token"
            },
            {
                "success": True,
                "data": [{"orderId": 3}],
                "next_token": None  # 마지막 페이지
            }
        ]
        mock_get_sheets.side_effect = mock_responses
        
        # API 호출
        result = self.client.get_order_sheets_all_pages(self.valid_params)
        
        # 검증
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 3)  # 총 3개 발주서
        self.assertEqual(result["page_count"], 2)  # 2페이지
        self.assertFalse(result["has_next_page"])
        
        # Mock 호출 횟수 확인
        self.assertEqual(mock_get_sheets.call_count, 2)
    
    def test_get_order_sheets_by_status(self):
        """상태별 발주서 조회 편의 메서드 테스트"""
        with patch.object(self.client, 'get_order_sheets_all_pages') as mock_all_pages:
            mock_all_pages.return_value = {"success": True, "data": []}
            
            # API 호출
            result = self.client.get_order_sheets_by_status(
                vendor_id="A12345678",
                created_at_from="2024-01-01",
                created_at_to="2024-01-02",
                status="DELIVERING",
                max_per_page=20
            )
            
            # Mock 호출 확인
            mock_all_pages.assert_called_once()
            
            # 전달된 파라미터 확인
            call_args = mock_all_pages.call_args[0][0]
            self.assertEqual(call_args.vendor_id, "A12345678")
            self.assertEqual(call_args.status, "DELIVERING")
            self.assertEqual(call_args.max_per_page, 20)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def setUp(self):
        self.client = OrderClient()
    
    def test_workflow_basic_to_detailed(self):
        """기본 조회에서 상세 조회까지 워크플로우 테스트"""
        # 실제 API 호출 없이 시뮬레이션
        with patch.object(self.client, '_make_request') as mock_request:
            # 성공 응답 설정
            mock_request.return_value = {
                "code": 200,
                "data": [
                    {
                        "orderId": 123,
                        "status": "ACCEPT",
                        "orderedAt": "2024-01-01T10:00:00",
                        "shippingPrice": 3000,
                        "orderer": {
                            "name": "홍길동",
                            "email": "test@test.com", 
                            "safeNumber": "010-****-1234"
                        },
                        "receiver": {
                            "name": "김철수",
                            "safeNumber": "010-****-5678",
                            "addr1": "서울시 강남구",
                            "addr2": "테스트동 123",
                            "postCode": "12345"
                        },
                        "orderItems": [],
                        "shipmentBoxId": 999,
                        "paidAt": "2024-01-01T10:05:00",
                        "remotePrice": 0,
                        "remoteArea": False,
                        "splitShipping": False,
                        "ableSplitShipping": True
                    }
                ]
            }
            
            # 1. 기본 조회
            params = OrderSheetSearchParams(
                vendor_id="A12345678",
                created_at_from="2024-01-01",
                created_at_to="2024-01-02",
                status="ACCEPT"
            )
            
            result = self.client.get_order_sheets(params)
            
            # 검증
            self.assertTrue(result["success"])
            self.assertEqual(len(result["data"]), 1)
            
            # 2. 상세 정보 확인
            order_sheet = result["data"][0]
            self.assertEqual(order_sheet["orderId"], 123)
            self.assertEqual(order_sheet["status"], "ACCEPT")


def run_tests():
    """테스트 실행"""
    print("🧪 쿠팡 파트너스 발주서 API 테스트 시작")
    print("=" * 80)
    
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestOrderSheetSearchParams,
        TestValidators,
        TestUtils,
        TestOrderClient,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 출력
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ 모든 테스트가 통과했습니다!")
    else:
        print(f"❌ 테스트 실패: {len(result.failures)}개 실패, {len(result.errors)}개 오류")
        
        if result.failures:
            print("\n📋 실패한 테스트:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback}")
        
        if result.errors:
            print("\n🚨 오류가 발생한 테스트:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback}")
    
    print(f"\n📊 테스트 결과: {result.testsRun}개 실행, {len(result.failures)}개 실패, {len(result.errors)}개 오류")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 개별 테스트 클래스 실행 예제
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        print("🔧 개발자 모드: 단일 테스트 클래스 실행")
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        # 전체 테스트 실행
        success = run_tests()
        sys.exit(0 if success else 1)