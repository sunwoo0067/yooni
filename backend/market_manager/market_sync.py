from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from psycopg2.extras import RealDictCursor, Json
from .market_base import MarketBase
from .market_product import MarketProduct
from .market_order import MarketOrder

class MarketSync(MarketBase):
    """마켓 데이터 동기화 관리"""
    
    def __init__(self):
        super().__init__()
        self.product_manager = MarketProduct()
        self.order_manager = MarketOrder()
    
    def sync_coupang_products(self, account_name: str, products: List[Dict]) -> Dict:
        """쿠팡 상품 동기화"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            try:
                # 쿠팡 데이터를 공통 형식으로 변환
                common_product = {
                    'market_product_id': str(product.get('sellerProductId', '')),
                    'product_name': product.get('sellerProductName', ''),
                    'brand': product.get('brand', ''),
                    'manufacturer': product.get('manufacture', ''),
                    'model_name': product.get('modelName', ''),
                    'original_price': product.get('originalPrice'),
                    'sale_price': product.get('salePrice'),
                    'discount_rate': self._calculate_discount_rate(
                        product.get('originalPrice'), 
                        product.get('salePrice')
                    ),
                    'status': self._convert_coupang_status(product.get('statusName')),
                    'stock_quantity': product.get('productStock', 0),
                    'category_code': product.get('displayCategoryCode'),
                    'category_name': product.get('displayCategoryName'),
                    'shipping_type': 'free' if product.get('freeShipment') else 'paid',
                    'market_data': product
                }
                
                self.product_manager.save_product('coupang', account_name, common_product)
                results['updated'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Product {product.get('sellerProductId')}: {str(e)}")
            
            results['total'] += 1
        
        return results
    
    def sync_coupang_orders(self, account_name: str, orders: List[Dict]) -> Dict:
        """쿠팡 주문 동기화"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for order in orders:
            try:
                # 쿠팡 주문 데이터를 공통 형식으로 변환
                common_order = {
                    'market_order_id': str(order.get('orderId', '')),
                    'order_date': self._parse_date(order.get('orderedAt')),
                    'payment_date': self._parse_date(order.get('paidAt')),
                    'buyer_name': order.get('ordererName'),
                    'buyer_email': order.get('ordererEmail'),
                    'buyer_phone': order.get('ordererPhoneNumber'),
                    'receiver_name': order.get('receiverName'),
                    'receiver_phone': order.get('receiverPhoneNumber'),
                    'receiver_address': order.get('receiverAddr1', '') + ' ' + order.get('receiverAddr2', ''),
                    'receiver_zipcode': order.get('receiverPostCode'),
                    'delivery_message': order.get('parcelPrintMessage'),
                    'order_status': self._convert_coupang_order_status(order.get('status')),
                    'payment_method': order.get('paymentMethod'),
                    'total_price': order.get('totalPrice'),
                    'product_price': order.get('orderPrice'),
                    'discount_amount': order.get('discountPrice', 0),
                    'shipping_fee': order.get('shippingPrice', 0),
                    'market_data': order,
                    'items': self._convert_coupang_order_items(order.get('orderItems', []))
                }
                
                self.order_manager.save_order('coupang', account_name, common_order)
                results['updated'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Order {order.get('orderId')}: {str(e)}")
            
            results['total'] += 1
        
        return results
    
    def sync_ownerclan_products(self, account_name: str, products: List[Dict]) -> Dict:
        """오너클랜 상품 동기화"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            try:
                # 오너클랜 데이터를 공통 형식으로 변환
                common_product = {
                    'market_product_id': str(product.get('id', '')),
                    'product_name': product.get('name', ''),
                    'brand': product.get('brand'),
                    'manufacturer': product.get('manufacturer'),
                    'model_name': product.get('modelName'),
                    'original_price': product.get('originalPrice'),
                    'sale_price': product.get('price'),
                    'discount_rate': self._calculate_discount_rate(
                        product.get('originalPrice'), 
                        product.get('price')
                    ),
                    'status': 'active' if product.get('status') == 'ACTIVE' else 'inactive',
                    'stock_quantity': product.get('stockQuantity', 0),
                    'category_code': product.get('category', {}).get('id'),
                    'category_name': product.get('category', {}).get('name'),
                    'shipping_type': 'free',  # 오너클랜은 기본 무료배송
                    'market_data': product
                }
                
                self.product_manager.save_product('ownerclan', account_name, common_product)
                results['updated'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Product {product.get('id')}: {str(e)}")
            
            results['total'] += 1
        
        return results
    
    def sync_naver_products(self, account_name: str, products: List[Dict]) -> Dict:
        """네이버 스마트스토어 상품 동기화"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            try:
                # 네이버 데이터를 공통 형식으로 변환
                common_product = {
                    'market_product_id': str(product.get('id', '')),
                    'product_name': product.get('name', ''),
                    'brand': product.get('brand'),
                    'manufacturer': product.get('manufacturer'),
                    'model_name': product.get('modelName'),
                    'original_price': product.get('originalPrice'),
                    'sale_price': product.get('price'),
                    'discount_rate': self._calculate_discount_rate(
                        product.get('originalPrice'), 
                        product.get('price')
                    ),
                    'status': self._convert_naver_status(product.get('status')),
                    'stock_quantity': product.get('stockQuantity', 0),
                    'category_code': product.get('category', {}).get('id'),
                    'category_name': product.get('category', {}).get('name'),
                    'shipping_type': 'free',  # 네이버는 기본 무료배송
                    'market_data': product.get('original_data', product)
                }
                
                self.product_manager.save_product('naver', account_name, common_product)
                results['updated'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Product {product.get('id')}: {str(e)}")
            
            results['total'] += 1
        
        return results
    
    def _convert_naver_status(self, status: Optional[str]) -> str:
        """네이버 상품 상태 변환"""
        if not status:
            return 'inactive'
        
        status_map = {
            'ACTIVE': 'active',
            'SALE': 'active',
            'INACTIVE': 'inactive',
            'OUTOFSTOCK': 'soldout',
            'SUSPENSION': 'suspended',
            'CLOSE': 'inactive',
            'PROHIBITION': 'suspended'
        }
        
        return status_map.get(status.upper(), 'inactive')
    
    def sync_eleven_products(self, account_name: str, products: List[Dict]) -> Dict:
        """11번가 상품 동기화"""
        results = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            try:
                # 11번가 데이터를 공통 형식으로 변환
                common_product = {
                    'market_product_id': str(product.get('id', '')),
                    'product_name': product.get('name', ''),
                    'brand': product.get('brand'),
                    'manufacturer': product.get('manufacturer'),
                    'model_name': product.get('modelName'),
                    'original_price': product.get('originalPrice'),
                    'sale_price': product.get('price'),
                    'discount_rate': self._calculate_discount_rate(
                        product.get('originalPrice'), 
                        product.get('price')
                    ),
                    'status': self._convert_eleven_status(product.get('status')),
                    'stock_quantity': product.get('stockQuantity', 0),
                    'category_code': product.get('category', {}).get('id'),
                    'category_name': product.get('category', {}).get('name'),
                    'shipping_type': 'paid',  # 11번가는 기본 유료배송
                    'market_data': product.get('original_data', product)
                }
                
                self.product_manager.save_product('11st', account_name, common_product)
                results['updated'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Product {product.get('id')}: {str(e)}")
            
            results['total'] += 1
        
        return results
    
    def _convert_eleven_status(self, status: Optional[str]) -> str:
        """11번가 상품 상태 변환"""
        if not status:
            return 'inactive'
        
        status_map = {
            'ACTIVE': 'active',
            'INACTIVE': 'inactive',
            'SOLDOUT': 'soldout'
        }
        
        return status_map.get(status.upper(), 'inactive')
    
    def _calculate_discount_rate(self, original_price: Optional[float], 
                                sale_price: Optional[float]) -> Optional[float]:
        """할인율 계산"""
        if not original_price or not sale_price or original_price <= 0:
            return None
        if original_price <= sale_price:
            return 0
        return round((original_price - sale_price) / original_price * 100, 2)
    
    def _convert_coupang_status(self, status_name: Optional[str]) -> str:
        """쿠팡 상품 상태 변환"""
        if not status_name:
            return 'inactive'
        
        status_map = {
            'SALE': 'active',
            '판매중': 'active',
            'SOLDOUT': 'soldout',
            '품절': 'soldout',
            'SUSPENDED': 'suspended',
            '판매중지': 'suspended'
        }
        
        return status_map.get(status_name, 'inactive')
    
    def _convert_coupang_order_status(self, status: Optional[str]) -> str:
        """쿠팡 주문 상태 변환"""
        if not status:
            return 'pending'
        
        status_map = {
            'ACCEPT': 'confirmed',
            'INSTRUCT': 'confirmed',
            'DEPARTURE': 'shipped',
            'DELIVERING': 'shipped',
            'FINAL_DELIVERY': 'delivered',
            'NONE_TRACKING': 'shipped',
            'CANCEL': 'cancelled',
            'RETURNS': 'cancelled'
        }
        
        return status_map.get(status, 'pending')
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        
        try:
            # ISO 8601 형식
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # YYYY-MM-DD 형식
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
    
    def _convert_coupang_order_items(self, items: List[Dict]) -> List[Dict]:
        """쿠팡 주문 상품 변환"""
        converted_items = []
        
        for item in items:
            converted_items.append({
                'market_product_id': str(item.get('sellerProductId', '')),
                'product_name': item.get('sellerProductName'),
                'option_name': item.get('sellerProductItemName'),
                'quantity': item.get('shippingCount', 1),
                'unit_price': item.get('orderPrice'),
                'total_price': item.get('orderPrice', 0) * item.get('shippingCount', 1),
                'item_status': self._convert_coupang_order_status(item.get('status')),
                'tracking_company': item.get('deliveryCompanyName'),
                'tracking_number': item.get('invoiceNumber'),
                'shipped_date': self._parse_date(item.get('shippedAt')),
                'delivered_date': self._parse_date(item.get('deliveredAt')),
                'item_data': item
            })
        
        return converted_items
    
    def get_sync_status(self, market_code: Optional[str] = None) -> List[Dict]:
        """동기화 상태 조회"""
        query = """
            SELECT 
                m.code as market_code,
                m.name as market_name,
                ma.account_name,
                COUNT(DISTINCT mp.id) as product_count,
                COUNT(DISTINCT mo.id) as order_count,
                MAX(mp.last_synced_at) as last_product_sync,
                MAX(mo.last_synced_at) as last_order_sync
            FROM markets m
            LEFT JOIN market_accounts ma ON ma.market_id = m.id
            LEFT JOIN market_products mp ON mp.market_account_id = ma.id
            LEFT JOIN market_orders mo ON mo.market_account_id = ma.id
            WHERE ma.is_active = true
        """
        params = []
        
        if market_code:
            query += " AND m.code = %s"
            params.append(market_code)
        
        query += """
            GROUP BY m.code, m.name, ma.account_name
            ORDER BY m.code, ma.account_name
        """
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def close(self):
        """연결 종료"""
        super().close()
        if hasattr(self, 'product_manager'):
            self.product_manager.close()
        if hasattr(self, 'order_manager'):
            self.order_manager.close()