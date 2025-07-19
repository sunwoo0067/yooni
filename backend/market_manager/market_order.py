from typing import Dict, List, Optional, Any
from datetime import datetime
from psycopg2.extras import RealDictCursor, Json, execute_values
from .market_base import MarketBase

class MarketOrder(MarketBase):
    """마켓 주문 통합 관리"""
    
    def save_order(self, market_code: str, account_name: str, order_data: Dict) -> int:
        """마켓 주문 저장"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            # 주문 저장
            cursor.execute("""
                INSERT INTO market_orders (
                    market_id, market_account_id, market_order_id,
                    order_date, payment_date,
                    buyer_name, buyer_email, buyer_phone,
                    receiver_name, receiver_phone, receiver_address, 
                    receiver_zipcode, delivery_message,
                    order_status, payment_method,
                    total_price, product_price, discount_amount, shipping_fee,
                    market_data, last_synced_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (market_account_id, market_order_id)
                DO UPDATE SET
                    order_date = EXCLUDED.order_date,
                    payment_date = EXCLUDED.payment_date,
                    buyer_name = EXCLUDED.buyer_name,
                    buyer_email = EXCLUDED.buyer_email,
                    buyer_phone = EXCLUDED.buyer_phone,
                    receiver_name = EXCLUDED.receiver_name,
                    receiver_phone = EXCLUDED.receiver_phone,
                    receiver_address = EXCLUDED.receiver_address,
                    receiver_zipcode = EXCLUDED.receiver_zipcode,
                    delivery_message = EXCLUDED.delivery_message,
                    order_status = EXCLUDED.order_status,
                    payment_method = EXCLUDED.payment_method,
                    total_price = EXCLUDED.total_price,
                    product_price = EXCLUDED.product_price,
                    discount_amount = EXCLUDED.discount_amount,
                    shipping_fee = EXCLUDED.shipping_fee,
                    market_data = EXCLUDED.market_data,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                account['market_id'],
                account['id'],
                order_data['market_order_id'],
                order_data['order_date'],
                order_data.get('payment_date'),
                order_data.get('buyer_name'),
                order_data.get('buyer_email'),
                order_data.get('buyer_phone'),
                order_data.get('receiver_name'),
                order_data.get('receiver_phone'),
                order_data.get('receiver_address'),
                order_data.get('receiver_zipcode'),
                order_data.get('delivery_message'),
                order_data.get('order_status', 'pending'),
                order_data.get('payment_method'),
                order_data.get('total_price'),
                order_data.get('product_price'),
                order_data.get('discount_amount'),
                order_data.get('shipping_fee'),
                Json(order_data.get('market_data', {}))
            ))
            order_id = cursor.fetchone()[0]
            
            # 주문 상품 저장
            if 'items' in order_data:
                self._save_order_items(cursor, order_id, order_data['items'])
            
            self.connection.commit()
            return order_id
    
    def _save_order_items(self, cursor, order_id: int, items: List[Dict]):
        """주문 상품 저장"""
        values = []
        for item in items:
            values.append((
                order_id,
                item.get('market_product_id'),
                item.get('product_name'),
                item.get('option_name'),
                item.get('quantity', 1),
                item.get('unit_price'),
                item.get('total_price'),
                item.get('item_status', 'pending'),
                item.get('tracking_company'),
                item.get('tracking_number'),
                item.get('shipped_date'),
                item.get('delivered_date'),
                Json(item.get('item_data', {}))
            ))
        
        execute_values(
            cursor,
            """
            INSERT INTO market_order_items (
                market_order_id, market_product_id,
                product_name, option_name,
                quantity, unit_price, total_price,
                item_status, tracking_company, tracking_number,
                shipped_date, delivered_date, item_data
            ) VALUES %s
            """,
            values
        )
    
    def update_order_status(self, market_code: str, account_name: str,
                          market_order_id: str, status: str):
        """주문 상태 업데이트"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE market_orders
                SET order_status = %s,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE market_account_id = %s AND market_order_id = %s
            """, (status, account['id'], market_order_id))
            self.connection.commit()
    
    def update_tracking(self, market_code: str, account_name: str,
                       market_order_id: str, item_index: int,
                       tracking_company: str, tracking_number: str):
        """배송 추적 정보 업데이트"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            # 주문 ID 조회
            cursor.execute("""
                SELECT id FROM market_orders
                WHERE market_account_id = %s AND market_order_id = %s
            """, (account['id'], market_order_id))
            order = cursor.fetchone()
            
            if not order:
                raise ValueError(f"Order not found: {market_order_id}")
            
            # 주문 상품 업데이트
            cursor.execute("""
                UPDATE market_order_items
                SET tracking_company = %s,
                    tracking_number = %s,
                    item_status = 'shipped',
                    shipped_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE market_order_id = %s
                ORDER BY id
                LIMIT 1 OFFSET %s
            """, (tracking_company, tracking_number, order[0], item_index))
            
            # 배송 정보 테이블에도 저장
            cursor.execute("""
                INSERT INTO market_shipments (
                    market_order_id, shipment_type,
                    tracking_company, tracking_number,
                    shipment_status, shipped_date
                ) VALUES (%s, 'normal', %s, %s, 'shipped', CURRENT_TIMESTAMP)
            """, (order[0], tracking_company, tracking_number))
            
            self.connection.commit()
    
    def get_orders(self, market_code: str, account_name: Optional[str] = None,
                  status: Optional[str] = None, date_from: Optional[datetime] = None,
                  date_to: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """주문 조회"""
        query = """
            SELECT mo.*, m.code as market_code, m.name as market_name,
                   ma.account_name,
                   COUNT(moi.id) as item_count,
                   SUM(moi.quantity) as total_quantity
            FROM market_orders mo
            JOIN markets m ON m.id = mo.market_id
            JOIN market_accounts ma ON ma.id = mo.market_account_id
            LEFT JOIN market_order_items moi ON moi.market_order_id = mo.id
            WHERE m.code = %s
        """
        params = [market_code]
        
        if account_name:
            query += " AND ma.account_name = %s"
            params.append(account_name)
        
        if status:
            query += " AND mo.order_status = %s"
            params.append(status)
        
        if date_from:
            query += " AND mo.order_date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND mo.order_date <= %s"
            params.append(date_to)
        
        query += """
            GROUP BY mo.id, m.code, m.name, ma.account_name
            ORDER BY mo.order_date DESC
            LIMIT %s
        """
        params.append(limit)
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_order_items(self, market_code: str, account_name: str,
                       market_order_id: str) -> List[Dict]:
        """주문 상품 조회"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT moi.*
                FROM market_order_items moi
                JOIN market_orders mo ON mo.id = moi.market_order_id
                WHERE mo.market_account_id = %s AND mo.market_order_id = %s
                ORDER BY moi.id
            """, (account['id'], market_order_id))
            return cursor.fetchall()
    
    def get_pending_shipments(self, market_code: Optional[str] = None) -> List[Dict]:
        """배송 대기 주문 조회"""
        query = """
            SELECT mo.*, m.code as market_code, m.name as market_name,
                   ma.account_name, moi.id as item_id,
                   moi.product_name, moi.option_name, moi.quantity
            FROM market_orders mo
            JOIN markets m ON m.id = mo.market_id
            JOIN market_accounts ma ON ma.id = mo.market_account_id
            JOIN market_order_items moi ON moi.market_order_id = mo.id
            WHERE moi.item_status = 'pending'
            AND mo.order_status IN ('confirmed', 'pending')
        """
        params = []
        
        if market_code:
            query += " AND m.code = %s"
            params.append(market_code)
        
        query += " ORDER BY mo.order_date ASC"
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_order_statistics(self, market_code: str, account_name: Optional[str] = None,
                           date_from: datetime = None, date_to: datetime = None) -> Dict:
        """주문 통계 조회"""
        query = """
            SELECT 
                COUNT(DISTINCT mo.id) as total_orders,
                COUNT(moi.id) as total_items,
                SUM(moi.quantity) as total_quantity,
                SUM(mo.total_price) as total_revenue,
                SUM(mo.product_price) as total_product_price,
                SUM(mo.shipping_fee) as total_shipping_fee,
                SUM(mo.discount_amount) as total_discount,
                COUNT(DISTINCT CASE WHEN mo.order_status = 'delivered' THEN mo.id END) as delivered_orders,
                COUNT(DISTINCT CASE WHEN mo.order_status = 'cancelled' THEN mo.id END) as cancelled_orders
            FROM market_orders mo
            JOIN markets m ON m.id = mo.market_id
            JOIN market_accounts ma ON ma.id = mo.market_account_id
            LEFT JOIN market_order_items moi ON moi.market_order_id = mo.id
            WHERE m.code = %s
        """
        params = [market_code]
        
        if account_name:
            query += " AND ma.account_name = %s"
            params.append(account_name)
        
        if date_from:
            query += " AND mo.order_date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND mo.order_date <= %s"
            params.append(date_to)
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()