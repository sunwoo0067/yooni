"""
쿠팡 배송 관리자
송장 등록 및 배송 처리
"""
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from market.coupang.order import OrderClient
from market.coupang.common import BaseCoupangClient
from market_manager import MarketOrder

logger = logging.getLogger(__name__)

class CoupangShippingManager(BaseCoupangClient):
    """쿠팡 배송 관리 클래스"""
    
    def __init__(self, vendor_id: Optional[str] = None):
        super().__init__(vendor_id=vendor_id)
        self.order_client = OrderClient(vendor_id=vendor_id)
        self.order_manager = MarketOrder()
    
    def register_shipment(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """송장 등록
        
        Args:
            shipment_data: {
                'order_id': 주문 ID,
                'vendor_item_id': 벤더 아이템 ID,
                'delivery_company_code': 택배사 코드,
                'invoice_number': 송장 번호,
                'split_invoice': 분할 배송 여부 (선택)
            }
        
        Returns:
            처리 결과
        """
        try:
            # API 엔드포인트
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/orders/{shipment_data['order_id']}/ordersheets/{shipment_data['vendor_item_id']}/shipments"
            
            # 요청 데이터
            request_data = {
                'vendorId': self.vendor_id,
                'orderId': shipment_data['order_id'],
                'vendorItemId': shipment_data['vendor_item_id'],
                'deliveryCompanyCode': shipment_data['delivery_company_code'],
                'invoiceNumber': shipment_data['invoice_number']
            }
            
            if shipment_data.get('split_invoice'):
                request_data['splitInvoice'] = True
            
            # API 호출
            response = self._make_request('POST', path, json_data=request_data)
            
            if response and response.get('code') == 'SUCCESS':
                # DB 업데이트
                self._update_shipment_in_db(shipment_data)
                
                return {
                    'success': True,
                    'message': '송장이 등록되었습니다.',
                    'data': response.get('data')
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', '송장 등록 실패'),
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"송장 등록 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def register_bulk_shipments(self, shipments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """대량 송장 등록
        
        Args:
            shipments: 송장 정보 리스트
        
        Returns:
            처리 결과
        """
        results = {
            'total': len(shipments),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for shipment in shipments:
            result = self.register_shipment(shipment)
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'order_id': shipment['order_id'],
                'vendor_item_id': shipment['vendor_item_id'],
                'success': result['success'],
                'message': result.get('message')
            })
        
        return results
    
    def stop_shipment(self, order_id: str, vendor_item_id: str, reason: str) -> Dict[str, Any]:
        """출고 중지
        
        Args:
            order_id: 주문 ID
            vendor_item_id: 벤더 아이템 ID
            reason: 중지 사유
        
        Returns:
            처리 결과
        """
        try:
            path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/orders/{order_id}/ordersheets/{vendor_item_id}/stop-shipment"
            
            request_data = {
                'vendorId': self.vendor_id,
                'orderId': order_id,
                'vendorItemId': vendor_item_id,
                'stopReason': reason
            }
            
            response = self._make_request('POST', path, json_data=request_data)
            
            if response and response.get('code') == 'SUCCESS':
                return {
                    'success': True,
                    'message': '출고가 중지되었습니다.',
                    'data': response.get('data')
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', '출고 중지 실패'),
                    'error': response
                }
                
        except Exception as e:
            logger.error(f"출고 중지 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_pending_shipments(self, status: str = 'ACCEPT') -> List[Dict[str, Any]]:
        """발송 대기 주문 조회
        
        Args:
            status: 주문 상태 (ACCEPT, INSTRUCT 등)
        
        Returns:
            발송 대기 주문 목록
        """
        try:
            # 오늘 날짜
            today = datetime.now().date().isoformat()
            
            # 주문 조회
            orders = self.order_client.get_orders_by_date(
                search_from=today,
                search_to=today,
                status=status
            )
            
            pending_shipments = []
            
            if orders and 'data' in orders:
                for order in orders['data']:
                    for item in order.get('orderItems', []):
                        if item.get('status') == status:
                            pending_shipments.append({
                                'order_id': order['orderId'],
                                'vendor_item_id': item['vendorItemId'],
                                'product_id': item['sellerProductId'],
                                'product_name': item['sellerProductName'],
                                'option_name': item.get('sellerProductItemName'),
                                'quantity': item['shippingCount'],
                                'buyer_name': order['ordererName'],
                                'receiver_name': order['receiverName'],
                                'receiver_phone': order['receiverPhoneNumber'],
                                'receiver_address': f"{order['receiverAddr1']} {order.get('receiverAddr2', '')}",
                                'receiver_zipcode': order['receiverPostCode'],
                                'delivery_message': order.get('parcelPrintMessage', ''),
                                'ordered_at': order['orderedAt']
                            })
            
            return pending_shipments
            
        except Exception as e:
            logger.error(f"발송 대기 주문 조회 오류: {e}")
            return []
    
    def get_delivery_companies(self) -> List[Dict[str, str]]:
        """택배사 목록 조회
        
        Returns:
            택배사 목록
        """
        # 쿠팡에서 지원하는 주요 택배사
        return [
            {'code': 'CJGLS', 'name': 'CJ대한통운'},
            {'code': 'LOTTE', 'name': '롯데택배'},
            {'code': 'HANJIN', 'name': '한진택배'},
            {'code': 'LOGEN', 'name': '로젠택배'},
            {'code': 'KGB', 'name': '로젯컨베이'},
            {'code': 'EPOST', 'name': '우체국택배'},
            {'code': 'KDEXP', 'name': '경동택배'},
            {'code': 'CHUNIL', 'name': '천일택배'},
            {'code': 'HDEXP', 'name': '합동택배'},
            {'code': 'CVSNET', 'name': 'GS편의점택배'},
            {'code': 'CU', 'name': 'CU편의점택배'},
            {'code': 'DIRECT', 'name': '업체직송'},
            {'code': 'QUICK', 'name': '퀵서비스'}
        ]
    
    def _update_shipment_in_db(self, shipment_data: Dict[str, Any]):
        """DB에 배송 정보 업데이트"""
        try:
            # market_shipments 테이블에 저장
            with self.order_manager.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO market_shipments 
                    (market_order_id, tracking_company, tracking_number, shipped_at, status)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (market_order_id) 
                    DO UPDATE SET 
                        tracking_company = EXCLUDED.tracking_company,
                        tracking_number = EXCLUDED.tracking_number,
                        shipped_at = EXCLUDED.shipped_at,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    shipment_data['order_id'],
                    shipment_data['delivery_company_code'],
                    shipment_data['invoice_number'],
                    datetime.now(),
                    'shipped'
                ))
                self.order_manager.connection.commit()
                
        except Exception as e:
            logger.error(f"DB 업데이트 오류: {e}")
    
    def generate_shipping_labels(self, order_ids: List[str]) -> Dict[str, Any]:
        """배송 라벨 생성 (예시)
        
        Args:
            order_ids: 주문 ID 리스트
        
        Returns:
            라벨 생성 결과
        """
        # 실제 구현 시 라벨 생성 로직 필요
        return {
            'success': True,
            'message': f'{len(order_ids)}개 주문의 배송 라벨이 생성되었습니다.',
            'labels': []  # 실제로는 라벨 데이터나 URL
        }
    
    def close(self):
        """리소스 정리"""
        if hasattr(self, 'order_manager'):
            self.order_manager.close()