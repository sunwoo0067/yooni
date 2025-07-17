import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { Order } from '@/lib/types/order';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const search = searchParams.get('search') || '';
    const supplier = searchParams.get('supplier') || '';
    const status = searchParams.get('status') || '';
    const startDate = searchParams.get('startDate') || '';
    const endDate = searchParams.get('endDate') || '';
    
    const offset = (page - 1) * limit;
    
    // 조건절 구성
    const conditions = ['1=1'];
    const params: any[] = [];
    let paramIndex = 1;
    
    if (search) {
      conditions.push(`(order_number ILIKE $${paramIndex} OR customer_name ILIKE $${paramIndex} OR customer_phone ILIKE $${paramIndex})`);
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
    
    if (startDate) {
      conditions.push(`created_at >= $${paramIndex}`);
      params.push(startDate);
      paramIndex++;
    }
    
    if (endDate) {
      conditions.push(`created_at <= $${paramIndex}`);
      params.push(endDate + ' 23:59:59');
      paramIndex++;
    }
    
    const whereClause = conditions.join(' AND ');
    
    // 전체 개수 조회
    const countQuery = `SELECT COUNT(*) FROM orders WHERE ${whereClause}`;
    const countResult = await query<{ count: string }>(countQuery, params);
    const totalCount = parseInt(countResult[0].count);
    
    // 주문 목록 조회
    params.push(limit);
    params.push(offset);
    
    const ordersQuery = `
      SELECT 
        o.id,
        o.order_number,
        o.supplier_id,
        o.status,
        o.total_amount,
        o.shipping_fee,
        o.customer_name,
        o.customer_phone,
        o.customer_email,
        o.shipping_address,
        o.shipping_postcode,
        o.created_at,
        o.updated_at,
        COUNT(oi.id) as item_count,
        SUM(oi.quantity) as total_quantity
      FROM orders o
      LEFT JOIN order_items oi ON o.id = oi.order_id
      WHERE ${whereClause}
      GROUP BY o.id
      ORDER BY o.created_at DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;
    
    const orders = await query<Order & { item_count: string; total_quantity: string }>(ordersQuery, params);
    
    return NextResponse.json({
      orders,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    });
  } catch (error) {
    console.error('Error fetching orders:', error);
    return NextResponse.json(
      { error: 'Failed to fetch orders' },
      { status: 500 }
    );
  }
}