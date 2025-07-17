import { NextRequest, NextResponse } from 'next/server';
import { getOne } from '@/lib/db';
import { Product } from '@/lib/types/product';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const productId = params.id;
    
    const query = `
      SELECT 
        id,
        supplier_id,
        supplier_product_id,
        product_name,
        brand,
        manufacturer,
        origin,
        category,
        status,
        price,
        list_price,
        shipping_fee,
        stock_quantity,
        images,
        options,
        description,
        created_at,
        updated_at
      FROM products 
      WHERE id = $1
    `;
    
    const product = await getOne<Product>(query, [productId]);
    
    if (!product) {
      return NextResponse.json(
        { error: '상품을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(product);
  } catch (error) {
    console.error('Error fetching product:', error);
    return NextResponse.json(
      { error: '상품 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const productId = params.id;
    const body = await request.json();
    
    const updateFields = [];
    const values = [];
    let paramIndex = 1;
    
    // 업데이트 가능한 필드들
    const allowedFields = [
      'product_name', 'brand', 'manufacturer', 'origin', 
      'category', 'status', 'price', 'list_price', 
      'shipping_fee', 'stock_quantity', 'description'
    ];
    
    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        updateFields.push(`${field} = $${paramIndex}`);
        values.push(body[field]);
        paramIndex++;
      }
    }
    
    if (updateFields.length === 0) {
      return NextResponse.json(
        { error: '업데이트할 필드가 없습니다.' },
        { status: 400 }
      );
    }
    
    values.push(productId);
    
    const query = `
      UPDATE products 
      SET ${updateFields.join(', ')}, updated_at = NOW()
      WHERE id = $${paramIndex}
      RETURNING *
    `;
    
    const product = await getOne<Product>(query, values);
    
    if (!product) {
      return NextResponse.json(
        { error: '상품을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(product);
  } catch (error) {
    console.error('Error updating product:', error);
    return NextResponse.json(
      { error: '상품 업데이트 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}