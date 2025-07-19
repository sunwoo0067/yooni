"""
11번가 주문 관리 API
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from .base_client import ElevenBaseClient

class ElevenOrderClient(ElevenBaseClient):
    """11번가 주문 관리 클라이언트"""
    
    def get_orders(self, start_date: str, end_date: Optional[str] = None,
                  status: Optional[str] = None) -> Dict:
        """주문 목록 조회
        
        Args:
            start_date: 조회 시작일 (YYYY-MM-DD)
            end_date: 조회 종료일
            status: 주문 상태 (101: 주문접수, 102: 결제완료, 201: 배송준비중 등)
        
        Returns:
            주문 목록
        """
        params = {
            'dateType': '01',  # 01: 주문일 기준
            'startDate': start_date.replace('-', ''),  # YYYYMMDD 형식
            'endDate': (end_date or start_date).replace('-', '')
        }
        
        if status:
            params['ordStat'] = status
        
        result = self.get('orderservices/order', params)
        
        # 응답 구조 정규화
        if 'Orders' in result and 'Order' in result['Orders']:
            orders = result['Orders']['Order']
            if not isinstance(orders, list):
                orders = [orders]
            result['Orders']['Order'] = orders
        
        return result
    
    def get_order_detail(self, order_no: str) -> Dict:
        """주문 상세 조회
        
        Args:
            order_no: 주문 번호
        
        Returns:
            주문 상세 정보
        """
        params = {
            'ordNo': order_no
        }
        
        return self.get('orderservices/order/detail', params)
    
    def get_order_status_codes(self) -> Dict[str, str]:
        """주문 상태 코드 정보
        
        Returns:
            상태 코드와 설명
        """
        return {
            '101': '주문접수',
            '102': '결제완료',
            '103': '배송지시',
            '104': '배송중',
            '105': '배송완료',
            '106': '구매확정',
            '201': '배송준비중',
            '202': '배송보류',
            '301': '취소신청',
            '302': '취소완료',
            '401': '반품신청',
            '402': '반품완료',
            '501': '교환신청',
            '502': '교환완료'
        }
    
    def confirm_order(self, order_no: str) -> Dict:
        """발송처리 (API 미지원)
        
        Args:
            order_no: 주문 번호
        
        Returns:
            처리 결과
        
        Note:
            11번가는 API를 통한 발송처리를 지원하지 않음
        """
        raise NotImplementedError("11번가는 API를 통한 발송처리를 지원하지 않습니다.")
    
    def get_delivery_info(self, order_no: str) -> Dict:
        """배송 정보 조회
        
        Args:
            order_no: 주문 번호
        
        Returns:
            배송 정보
        """
        params = {
            'ordNo': order_no
        }
        
        return self.get('orderservices/order/delivery', params)
    
    def get_cancellations(self, start_date: str, end_date: Optional[str] = None) -> Dict:
        """취소 목록 조회
        
        Args:
            start_date: 조회 시작일
            end_date: 조회 종료일
        
        Returns:
            취소 목록
        """
        params = {
            'dateType': '02',  # 02: 클레임일 기준
            'startDate': start_date.replace('-', ''),
            'endDate': (end_date or start_date).replace('-', ''),
            'ordStat': '302'  # 취소완료
        }
        
        return self.get('orderservices/order', params)
    
    def get_returns(self, start_date: str, end_date: Optional[str] = None) -> Dict:
        """반품 목록 조회
        
        Args:
            start_date: 조회 시작일
            end_date: 조회 종료일
        
        Returns:
            반품 목록
        """
        params = {
            'dateType': '02',  # 02: 클레임일 기준
            'startDate': start_date.replace('-', ''),
            'endDate': (end_date or start_date).replace('-', ''),
            'ordStat': '402'  # 반품완료
        }
        
        return self.get('orderservices/order', params)
    
    def get_exchanges(self, start_date: str, end_date: Optional[str] = None) -> Dict:
        """교환 목록 조회
        
        Args:
            start_date: 조회 시작일
            end_date: 조회 종료일
        
        Returns:
            교환 목록
        """
        params = {
            'dateType': '02',  # 02: 클레임일 기준
            'startDate': start_date.replace('-', ''),
            'endDate': (end_date or start_date).replace('-', ''),
            'ordStat': '502'  # 교환완료
        }
        
        return self.get('orderservices/order', params)