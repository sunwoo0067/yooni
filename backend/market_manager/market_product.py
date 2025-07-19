from typing import Dict, List, Optional, Any
from datetime import datetime
from psycopg2.extras import RealDictCursor, Json, execute_values
from .market_base import MarketBase

class MarketProduct(MarketBase):
    """마켓 상품 통합 관리"""
    
    def save_product(self, market_code: str, account_name: str, product_data: Dict) -> int:
        """마켓 상품 저장 (생성 또는 업데이트)"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO market_products (
                    market_id, market_account_id, market_product_id,
                    product_name, brand, manufacturer, model_name,
                    original_price, sale_price, discount_rate,
                    status, stock_quantity,
                    category_code, category_name, category_path,
                    shipping_type, shipping_fee,
                    market_data, last_synced_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (market_account_id, market_product_id)
                DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    brand = EXCLUDED.brand,
                    manufacturer = EXCLUDED.manufacturer,
                    model_name = EXCLUDED.model_name,
                    original_price = EXCLUDED.original_price,
                    sale_price = EXCLUDED.sale_price,
                    discount_rate = EXCLUDED.discount_rate,
                    status = EXCLUDED.status,
                    stock_quantity = EXCLUDED.stock_quantity,
                    category_code = EXCLUDED.category_code,
                    category_name = EXCLUDED.category_name,
                    category_path = EXCLUDED.category_path,
                    shipping_type = EXCLUDED.shipping_type,
                    shipping_fee = EXCLUDED.shipping_fee,
                    market_data = EXCLUDED.market_data,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                account['market_id'],
                account['id'],
                product_data['market_product_id'],
                product_data['product_name'],
                product_data.get('brand'),
                product_data.get('manufacturer'),
                product_data.get('model_name'),
                product_data.get('original_price'),
                product_data.get('sale_price'),
                product_data.get('discount_rate'),
                product_data.get('status', 'active'),
                product_data.get('stock_quantity', 0),
                product_data.get('category_code'),
                product_data.get('category_name'),
                product_data.get('category_path'),
                product_data.get('shipping_type'),
                product_data.get('shipping_fee'),
                Json(product_data.get('market_data', {}))
            ))
            self.connection.commit()
            return cursor.fetchone()[0]
    
    def save_products_batch(self, market_code: str, account_name: str, products: List[Dict]):
        """마켓 상품 일괄 저장"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        # 데이터 준비
        values = []
        for product in products:
            values.append((
                account['market_id'],
                account['id'],
                product['market_product_id'],
                product['product_name'],
                product.get('brand'),
                product.get('manufacturer'),
                product.get('model_name'),
                product.get('original_price'),
                product.get('sale_price'),
                product.get('discount_rate'),
                product.get('status', 'active'),
                product.get('stock_quantity', 0),
                product.get('category_code'),
                product.get('category_name'),
                product.get('category_path'),
                product.get('shipping_type'),
                product.get('shipping_fee'),
                Json(product.get('market_data', {}))
            ))
        
        with self.connection.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO market_products (
                    market_id, market_account_id, market_product_id,
                    product_name, brand, manufacturer, model_name,
                    original_price, sale_price, discount_rate,
                    status, stock_quantity,
                    category_code, category_name, category_path,
                    shipping_type, shipping_fee, market_data
                ) VALUES %s
                ON CONFLICT (market_account_id, market_product_id)
                DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    brand = EXCLUDED.brand,
                    manufacturer = EXCLUDED.manufacturer,
                    model_name = EXCLUDED.model_name,
                    original_price = EXCLUDED.original_price,
                    sale_price = EXCLUDED.sale_price,
                    discount_rate = EXCLUDED.discount_rate,
                    status = EXCLUDED.status,
                    stock_quantity = EXCLUDED.stock_quantity,
                    category_code = EXCLUDED.category_code,
                    category_name = EXCLUDED.category_name,
                    category_path = EXCLUDED.category_path,
                    shipping_type = EXCLUDED.shipping_type,
                    shipping_fee = EXCLUDED.shipping_fee,
                    market_data = EXCLUDED.market_data,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                values
            )
            self.connection.commit()
    
    def get_products(self, market_code: str, account_name: Optional[str] = None, 
                    status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """마켓 상품 조회"""
        query = """
            SELECT mp.*, m.code as market_code, m.name as market_name,
                   ma.account_name
            FROM market_products mp
            JOIN markets m ON m.id = mp.market_id
            JOIN market_accounts ma ON ma.id = mp.market_account_id
            WHERE m.code = %s
        """
        params = [market_code]
        
        if account_name:
            query += " AND ma.account_name = %s"
            params.append(account_name)
        
        if status:
            query += " AND mp.status = %s"
            params.append(status)
        
        query += " ORDER BY mp.updated_at DESC LIMIT %s"
        params.append(limit)
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def update_stock(self, market_code: str, account_name: str, 
                    market_product_id: str, stock_quantity: int):
        """재고 수량 업데이트"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE market_products
                SET stock_quantity = %s,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE market_account_id = %s AND market_product_id = %s
            """, (stock_quantity, account['id'], market_product_id))
            self.connection.commit()
    
    def update_price(self, market_code: str, account_name: str,
                    market_product_id: str, sale_price: float,
                    original_price: Optional[float] = None):
        """가격 업데이트"""
        account = self.get_market_account(market_code, account_name)
        if not account:
            raise ValueError(f"Account not found: {market_code}/{account_name}")
        
        with self.connection.cursor() as cursor:
            if original_price:
                discount_rate = ((original_price - sale_price) / original_price * 100) if original_price > 0 else 0
                cursor.execute("""
                    UPDATE market_products
                    SET sale_price = %s,
                        original_price = %s,
                        discount_rate = %s,
                        last_synced_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE market_account_id = %s AND market_product_id = %s
                """, (sale_price, original_price, discount_rate, account['id'], market_product_id))
            else:
                cursor.execute("""
                    UPDATE market_products
                    SET sale_price = %s,
                        last_synced_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE market_account_id = %s AND market_product_id = %s
                """, (sale_price, account['id'], market_product_id))
            self.connection.commit()
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """재고 부족 상품 조회"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT mp.*, m.code as market_code, m.name as market_name,
                       ma.account_name
                FROM market_products mp
                JOIN markets m ON m.id = mp.market_id
                JOIN market_accounts ma ON ma.id = mp.market_account_id
                WHERE mp.stock_quantity < %s AND mp.status = 'active'
                ORDER BY mp.stock_quantity ASC, mp.updated_at DESC
            """, (threshold,))
            return cursor.fetchall()