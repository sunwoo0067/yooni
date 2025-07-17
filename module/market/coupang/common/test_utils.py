#!/usr/bin/env python3
"""
쿠팡 API 테스트 유틸리티
"""

import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock


class MockCoupangAPI:
    """공통 Mock API 클래스"""
    
    @staticmethod
    def create_success_response(data: Any = None, code: int = 200, 
                               message: str = "OK") -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "code": code,
            "message": message,
            "data": data or []
        }
    
    @staticmethod
    def create_error_response(code: int = 400, 
                             message: str = "Bad Request") -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "code": code,
            "message": message
        }
    
    @staticmethod
    def create_mock_client(api_responses: Dict[str, Any]) -> Mock:
        """Mock 클라이언트 생성"""
        mock_client = Mock()
        
        # API 응답 설정
        for method_name, response in api_responses.items():
            mock_method = Mock(return_value=response)
            setattr(mock_client, method_name, mock_method)
        
        return mock_client
    
    @staticmethod
    def create_network_error():
        """네트워크 에러 시뮬레이션"""
        import urllib.error
        return urllib.error.URLError("Network unreachable")
    
    @staticmethod
    def create_http_error(code: int = 500, reason: str = "Internal Server Error"):
        """HTTP 에러 시뮬레이션"""
        import urllib.error
        return urllib.error.HTTPError(
            url="https://api-gateway.coupang.com/test",
            code=code,
            msg=reason,
            hdrs={},
            fp=None
        )


class TestFixtures:
    """공통 테스트 픽스처"""
    
    @staticmethod
    def get_sample_vendor_id() -> str:
        """샘플 벤더 ID"""
        return "A01409684"
    
    @staticmethod
    def get_sample_return_request() -> Dict[str, Any]:
        """샘플 반품 요청 데이터"""
        return {
            "receiptId": 365937,
            "orderId": 500004398,
            "paymentId": 700003957,
            "receiptType": "반품",
            "receiptStatus": "RETURNS_UNCHECKED",
            "createdAt": "2025-07-13T10:00:00",
            "modifiedAt": "2025-07-13T10:00:00",
            "requesterName": "테스트 사용자",
            "requesterPhoneNumber": "010-****-1234",
            "requesterRealPhoneNumber": None,
            "requesterAddress": "서울시 강남구",
            "requesterAddressDetail": "테스트 주소",
            "requesterZipCode": "12345",
            "cancelReasonCategory1": "고객변심",
            "cancelReasonCategory2": "단순변심",
            "cancelReason": "테스트 사유",
            "cancelCountSum": 1,
            "returnDeliveryId": 12345,
            "returnDeliveryType": "연동택배",
            "releaseStopStatus": "미처리",
            "enclosePrice": 0,
            "faultByType": "CUSTOMER",
            "preRefund": False,
            "completeConfirmType": "UNDEFINED",
            "completeConfirmDate": "",
            "returnItems": [],
            "returnDeliveryDtos": [],
            "reasonCode": "CHANGEMIND",
            "reasonCodeText": "필요 없어짐 (단순 변심)",
            "returnShippingCharge": -3000
        }
    
    @staticmethod
    def get_sample_return_list_response() -> Dict[str, Any]:
        """샘플 반품 목록 응답"""
        sample_request = TestFixtures.get_sample_return_request()
        return MockCoupangAPI.create_success_response([sample_request])
    
    @staticmethod
    def get_sample_return_detail_response() -> Dict[str, Any]:
        """샘플 반품 상세 응답"""
        sample_request = TestFixtures.get_sample_return_request()
        return MockCoupangAPI.create_success_response([sample_request])
    
    @staticmethod
    def get_sample_withdraw_request() -> Dict[str, Any]:
        """샘플 반품 철회 요청"""
        return {
            "cancelId": 116607450,
            "orderId": 29000024470847,
            "vendorId": "A01409684",
            "refundDeliveryDuty": "COM",
            "createdAt": "2025-07-13T10:00:00",
            "vendorItemIds": [3838728011]
        }
    
    @staticmethod
    def get_sample_withdraw_response() -> Dict[str, Any]:
        """샘플 반품 철회 응답"""
        sample_withdraw = TestFixtures.get_sample_withdraw_request()
        return MockCoupangAPI.create_success_response([sample_withdraw])
    
    @staticmethod
    def get_sample_invoice_response() -> Dict[str, Any]:
        """샘플 송장 등록 응답"""
        invoice_data = {
            "deliveryCompanyCode": "CJGLS",
            "invoiceNumber": "TEST20250714123456",
            "invoiceNumberId": 26125633,
            "receiptId": 365937,
            "regNumber": "1234568",
            "returnDeliveryId": 25726758,
            "returnExchangeDeliveryType": "RETURN"
        }
        return MockCoupangAPI.create_success_response(invoice_data)
    
    @staticmethod
    def get_invalid_vendor_ids() -> List[str]:
        """유효하지 않은 벤더 ID 목록"""
        return [
            "",
            "INVALID",
            "A123",  # 너무 짧음
            "B01409684",  # A로 시작하지 않음
            "A0140968",  # 8자리
            "A014096840",  # 10자리
            None
        ]
    
    @staticmethod
    def get_invalid_receipt_ids() -> List[Any]:
        """유효하지 않은 접수번호 목록"""
        return [
            "",
            "invalid",
            -123,
            0,
            None,
            "123abc",
            [],
            {}
        ]
    
    @staticmethod
    def get_test_date_ranges() -> List[Dict[str, str]]:
        """테스트용 날짜 범위"""
        return [
            {"from": "2025-07-14", "to": "2025-07-14"},  # 당일
            {"from": "2025-07-08", "to": "2025-07-14"},  # 7일
            {"from": "2025-07-01", "to": "2025-07-07"},   # 과거 7일
        ]


class TestAssertions:
    """테스트 검증 유틸리티"""
    
    @staticmethod
    def assert_success_response(result: Dict[str, Any], 
                               expected_data_count: Optional[int] = None):
        """성공 응답 검증"""
        assert result.get("success") is True, f"예상: 성공, 실제: {result}"
        assert "timestamp" in result, "타임스탬프가 없습니다"
        
        if expected_data_count is not None:
            data = result.get("data", [])
            assert len(data) == expected_data_count, \
                f"예상 데이터 수: {expected_data_count}, 실제: {len(data)}"
    
    @staticmethod
    def assert_error_response(result: Dict[str, Any], 
                             expected_error_code: Optional[int] = None):
        """에러 응답 검증"""
        assert result.get("success") is False, f"예상: 실패, 실제: {result}"
        assert "error" in result, "에러 메시지가 없습니다"
        assert "timestamp" in result, "타임스탬프가 없습니다"
        
        if expected_error_code is not None:
            error_code = result.get("error_code")
            assert error_code == expected_error_code, \
                f"예상 에러 코드: {expected_error_code}, 실제: {error_code}"
    
    @staticmethod
    def assert_validation_error(func, *args, **kwargs):
        """검증 에러 발생 확인"""
        try:
            func(*args, **kwargs)
            assert False, "ValidationError가 발생해야 합니다"
        except (ValueError, TypeError) as e:
            # 예상된 검증 에러
            pass
        except Exception as e:
            assert False, f"예상: ValidationError, 실제: {type(e).__name__}: {e}"