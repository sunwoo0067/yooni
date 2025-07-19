"""
네이버 스마트스토어 주문 관리 API
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from .base_client import NaverBaseClient

class NaverOrderClient(NaverBaseClient):
    """네이버 주문 관리 클라이언트"""
    
    def get_orders(self, start_date: str, end_date: Optional[str] = None,
                  status: Optional[str] = None, page: int = 1, 
                  size: int = 100) -> Dict:
        """주문 목록 조회
        
        Args:
            start_date: 조회 시작일 (YYYY-MM-DD)
            end_date: 조회 종료일 (기본: 시작일과 동일)
            status: 주문 상태 필터
            page: 페이지 번호
            size: 페이지 크기 (최대 100)
        
        Returns:
            주문 목록 및 페이징 정보
        """
        params = {
            'startDate': start_date,
            'endDate': end_date or start_date,
            'page': page,
            'size': min(size, 100)
        }
        
        if status:
            params['orderStatus'] = status
        
        return self.get('/external/v2/orders', params=params)
    
    def get_order_detail(self, order_no: str) -> Dict:
        """주문 상세 조회
        
        Args:
            order_no: 주문 번호
        
        Returns:
            주문 상세 정보
        """
        return self.get(f'/external/v2/orders/{order_no}')
    
    def confirm_order(self, order_no: str) -> Dict:
        """주문 확인 (발주확인)
        
        Args:
            order_no: 주문 번호
        
        Returns:
            처리 결과
        """
        return self.post(f'/external/v2/orders/{order_no}/confirm', {})
    
    def cancel_order(self, order_no: str, reason: str, 
                    detailed_reason: Optional[str] = None) -> Dict:
        """주문 취소
        
        Args:
            order_no: 주문 번호
            reason: 취소 사유 코드
            detailed_reason: 상세 사유
        
        Returns:
            처리 결과
        """
        data = {
            'cancelReason': reason
        }
        if detailed_reason:
            data['cancelDetailedReason'] = detailed_reason
        
        return self.post(f'/external/v2/orders/{order_no}/cancel', data)
    
    def ship_order(self, order_no: str, delivery_data: Dict) -> Dict:
        """배송 처리 (송장 등록)
        
        Args:
            order_no: 주문 번호
            delivery_data: 배송 정보
                - deliveryCompanyCode: 택배사 코드
                - trackingNumber: 송장 번호
                - sendDate: 발송일 (YYYY-MM-DD)
        
        Returns:
            처리 결과
        """
        required_fields = ['deliveryCompanyCode', 'trackingNumber', 'sendDate']
        for field in required_fields:
            if field not in delivery_data:
                raise ValueError(f"Required field missing: {field}")
        
        return self.post(f'/external/v2/orders/{order_no}/ship', delivery_data)
    
    def update_tracking(self, order_no: str, tracking_number: str,
                       delivery_company_code: str) -> Dict:
        """송장 번호 수정
        
        Args:
            order_no: 주문 번호
            tracking_number: 새 송장 번호
            delivery_company_code: 택배사 코드
        
        Returns:
            처리 결과
        """
        data = {
            'trackingNumber': tracking_number,
            'deliveryCompanyCode': delivery_company_code
        }
        return self.patch(f'/external/v2/orders/{order_no}/tracking', data)
    
    def delay_order(self, order_no: str, delay_reason: str,
                   dispatch_due_date: str) -> Dict:
        """발송 지연 처리
        
        Args:
            order_no: 주문 번호
            delay_reason: 지연 사유
            dispatch_due_date: 발송 예정일 (YYYY-MM-DD)
        
        Returns:
            처리 결과
        """
        data = {
            'delayReason': delay_reason,
            'dispatchDueDate': dispatch_due_date
        }
        return self.post(f'/external/v2/orders/{order_no}/delay', data)
    
    def get_delivery_companies(self) -> List[Dict]:
        """택배사 목록 조회
        
        Returns:
            택배사 목록
        """
        result = self.get('/external/v2/delivery-companies')
        return result.get('deliveryCompanies', [])
    
    def get_order_statistics(self, date: str) -> Dict:
        """주문 통계 조회
        
        Args:
            date: 조회 날짜 (YYYY-MM-DD)
        
        Returns:
            주문 통계 정보
        """
        params = {'date': date}
        return self.get('/external/v2/orders/statistics', params=params)
    
    def get_returns(self, start_date: str, end_date: Optional[str] = None,
                   status: Optional[str] = None, page: int = 1, 
                   size: int = 100) -> Dict:
        """반품 목록 조회
        
        Args:
            start_date: 조회 시작일
            end_date: 조회 종료일
            status: 반품 상태
            page: 페이지 번호
            size: 페이지 크기
        
        Returns:
            반품 목록
        """
        params = {
            'startDate': start_date,
            'endDate': end_date or start_date,
            'page': page,
            'size': min(size, 100)
        }
        
        if status:
            params['returnStatus'] = status
        
        return self.get('/external/v2/returns', params=params)
    
    def approve_return(self, return_no: str) -> Dict:
        """반품 승인
        
        Args:
            return_no: 반품 번호
        
        Returns:
            처리 결과
        """
        return self.post(f'/external/v2/returns/{return_no}/approve', {})
    
    def reject_return(self, return_no: str, reason: str) -> Dict:
        """반품 거부
        
        Args:
            return_no: 반품 번호
            reason: 거부 사유
        
        Returns:
            처리 결과
        """
        data = {'rejectReason': reason}
        return self.post(f'/external/v2/returns/{return_no}/reject', data)