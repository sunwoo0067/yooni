import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { Product } from '@/lib/types/product';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const search = searchParams.get('search') || '';
    const supplier = searchParams.get('supplier') || '';
    const status = searchParams.get('status') || '';
    const sortBy = searchParams.get('sortBy') || 'created_at';
    const sortOrder = searchParams.get('sortOrder') || 'DESC';
    
    const offset = (page - 1) * limit;
    
    // 조건절 구성
    const conditions = ['1=1'];
    const params: any[] = [];
    let paramIndex = 1;
    
    if (search) {
      conditions.push(`(name ILIKE $${paramIndex} OR product_key ILIKE $${paramIndex})`);
      params.push(`%${search}%`);
      paramIndex++;
    }
    
    if (supplier) {
      conditions.push(`supplier_id = $${paramIndex}`);
      params.push(supplier);
      paramIndex++;
    }
    
    if (status) {
      conditions.push(`status = $${paramIndex}`);
      params.push(status);
      paramIndex++;
    }
    
    const whereClause = conditions.join(' AND ');
    
    // 전체 개수 조회
    const countQuery = `SELECT COUNT(*) FROM products WHERE ${whereClause}`;
    const countResult = await query<{ count: string }>(countQuery, params);
    const totalCount = parseInt(countResult[0].count);
    
    // 상품 목록 조회
    params.push(limit);
    params.push(offset);
    
    const productsQuery = `
      SELECT 
        id,
        raw_data_id,
        supplier_id,
        product_key,
        name,
        price,
        status,
        stock_status,
        stock_quantity,
        last_stock_check,
        stock_sync_enabled,
        metadata,
        created_at,
        updated_at
      FROM products 
      WHERE ${whereClause}
      ORDER BY ${sortBy} ${sortOrder}
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;
    
    const products = await query<Product>(productsQuery, params);
    
    return NextResponse.json({
      products,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    });
  } catch (error) {
    console.error('Error fetching products:', error);
    return NextResponse.json(
      { error: 'Failed to fetch products' },
      { status: 500 }
    );
  }
}