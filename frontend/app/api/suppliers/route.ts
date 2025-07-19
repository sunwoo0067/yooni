import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';
import { Supplier } from '@/lib/types/supplier';

export async function GET(request: NextRequest) {
  try {
    // 공급사 기본 정보와 상품 통계 조회
    const suppliers = await query(`
      SELECT 
        s.id,
        s.name,
        s.contact_info,
        s.business_number,
        s.address,
        s.created_at,
        s.updated_at,
        COALESCE(stats.product_count, 0) as product_count,
        COALESCE(stats.active_products, 0) as active_products,
        stats.last_product_update
      FROM suppliers s
      LEFT JOIN (
        SELECT 
          supplier_id,
          COUNT(*) as product_count,
          COUNT(CASE WHEN status = 'active' THEN 1 END) as active_products,
          MAX(updated_at) as last_product_update
        FROM products 
        GROUP BY supplier_id
      ) stats ON s.id = stats.supplier_id
      ORDER BY s.id
    `);
    
    return NextResponse.json(suppliers);
  } catch (error) {
    console.error('Error fetching suppliers:', error);
    return NextResponse.json(
      { error: 'Failed to fetch suppliers' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const { name, contact_info, business_number, address } = await request.json();
    
    // 공급사 이름 중복 확인
    const existing = await getOne(
      'SELECT id FROM suppliers WHERE name = $1',
      [name]
    );
    
    if (existing) {
      return NextResponse.json(
        { error: '이미 존재하는 공급사명입니다.' },
        { status: 400 }
      );
    }
    
    // 새 공급사 생성
    const result = await getOne(
      `INSERT INTO suppliers (name, contact_info, business_number, address)
       VALUES ($1, $2, $3, $4)
       RETURNING *`,
      [name, contact_info || '', business_number || '', address || '']
    );
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error creating supplier:', error);
    return NextResponse.json(
      { error: 'Failed to create supplier' },
      { status: 500 }
    );
  }
}