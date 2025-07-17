import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

export async function POST(request: NextRequest) {
  try {
    const { supplierId, productData } = await request.json();
    
    // 기존 상품 확인
    const existingProduct = await getOne(
      'SELECT id FROM products WHERE supplier_id = $1 AND product_key = $2',
      [supplierId, productData.product_key]
    );
    
    if (existingProduct) {
      // 기존 상태 조회 (재고 컬럼이 없을 수 있으므로 status만 확인)
      const currentProduct = await getOne(
        'SELECT status FROM products WHERE id = $1',
        [existingProduct.id]
      );
      
      // 기존 상품 업데이트 (재고 컬럼 없이)
      await query(
        `UPDATE products 
         SET name = $1, price = $2, status = $3, 
             metadata = $4, updated_at = NOW()
         WHERE id = $5`,
        [
          productData.name,
          productData.price,
          productData.status,
          JSON.stringify(productData.metadata),
          existingProduct.id
        ]
      );
      
      // 재고 상태 변경 시 알림 생성
      if (currentProduct && productData.stock_status && 
          currentProduct.stock_status !== productData.stock_status) {
        
        let alertType = null;
        let message = '';
        
        if (productData.stock_status === 'out_of_stock') {
          alertType = 'out_of_stock';
          message = `${productData.name} 상품이 품절되었습니다.`;
        } else if (productData.stock_status === 'low_stock') {
          alertType = 'low_stock';
          message = `${productData.name} 상품의 재고가 부족합니다. (남은 수량: ${productData.stock_quantity})`;
        } else if (currentProduct.stock_status === 'out_of_stock' && 
                   productData.stock_status === 'in_stock') {
          alertType = 'back_in_stock';
          message = `${productData.name} 상품이 재입고되었습니다.`;
        }
        
        if (alertType) {
          await query(
            `INSERT INTO stock_alerts (product_id, alert_type, message)
             VALUES ($1, $2, $3)`,
            [existingProduct.id, alertType, message]
          );
        }
        
        // 재고 이력 기록
        await query(
          `INSERT INTO stock_history 
           (product_id, previous_status, new_status, previous_quantity, new_quantity, change_reason)
           VALUES ($1, $2, $3, $4, $5, 'api_sync')`,
          [
            existingProduct.id,
            currentProduct.stock_status,
            productData.stock_status,
            currentProduct.stock_quantity,
            productData.stock_quantity
          ]
        );
      }
      
      return NextResponse.json({ 
        success: true, 
        action: 'updated',
        productId: existingProduct.id 
      });
    } else {
      // 새 상품 생성
      const result = await getOne(
        `INSERT INTO products (supplier_id, product_key, name, price, status, 
                              stock_status, stock_quantity, last_stock_check, metadata)
         VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
         RETURNING id`,
        [
          supplierId,
          productData.product_key,
          productData.name,
          productData.price,
          productData.status,
          productData.stock_status || 'in_stock',
          productData.stock_quantity || 0,
          JSON.stringify(productData.metadata)
        ]
      );
      
      // 새 상품이 품절 또는 저재고인 경우 알림 생성
      if (productData.stock_status === 'out_of_stock') {
        await query(
          `INSERT INTO stock_alerts (product_id, alert_type, message)
           VALUES ($1, 'out_of_stock', $2)`,
          [result?.id, `신규 상품 ${productData.name}이(가) 품절 상태로 등록되었습니다.`]
        );
      } else if (productData.stock_status === 'low_stock') {
        await query(
          `INSERT INTO stock_alerts (product_id, alert_type, message)
           VALUES ($1, 'low_stock', $2)`,
          [result?.id, `신규 상품 ${productData.name}이(가) 저재고 상태로 등록되었습니다. (수량: ${productData.stock_quantity})`]
        );
      }
      
      return NextResponse.json({ 
        success: true, 
        action: 'created',
        productId: result?.id 
      });
    }
  } catch (error) {
    console.error('Error importing product:', error);
    return NextResponse.json(
      { error: 'Failed to import product' },
      { status: 500 }
    );
  }
}