import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';
import { Supplier } from '@/lib/types/supplier';

export async function GET(request: NextRequest) {
  try {
    const suppliersQuery = `
      SELECT 
        s.id,
        s.name,
        s.contact_info,
        s.business_number,
        s.address,
        s.created_at,
        s.updated_at,
        COUNT(DISTINCT p.id) as product_count,
        COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'active') as active_products,
        MAX(p.created_at) as last_product_update,
        COUNT(DISTINCT sa.id) > 0 as has_multiple_accounts
      FROM suppliers s
      LEFT JOIN products p ON s.id = p.supplier_id
      LEFT JOIN supplier_accounts sa ON s.id = sa.supplier_id
      GROUP BY s.id, s.name, s.contact_info, s.business_number, s.address, s.created_at, s.updated_at
      ORDER BY s.id
    `;
    
    const suppliers = await query<Supplier & { 
      product_count: string; 
      active_products: string;
      last_product_update: Date;
      has_multiple_accounts: boolean;
    }>(suppliersQuery);
    
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