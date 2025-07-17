import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supplierId = parseInt(params.id);
    
    const accounts = await query(
      `SELECT * FROM supplier_accounts 
       WHERE supplier_id = $1 
       ORDER BY created_at DESC`,
      [supplierId]
    );
    
    return NextResponse.json(accounts);
  } catch (error) {
    console.error('Error fetching supplier accounts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch accounts' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supplierId = parseInt(params.id);
    const { account_name, api_key, api_secret, is_active } = await request.json();
    
    // 동일한 계정명 중복 확인
    const existing = await getOne(
      'SELECT id FROM supplier_accounts WHERE supplier_id = $1 AND account_name = $2',
      [supplierId, account_name]
    );
    
    if (existing) {
      return NextResponse.json(
        { error: '이미 존재하는 계정명입니다.' },
        { status: 400 }
      );
    }
    
    // 새 계정 생성
    const result = await getOne(
      `INSERT INTO supplier_accounts 
       (supplier_id, account_name, api_key, api_secret, is_active)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [supplierId, account_name, api_key, api_secret, is_active]
    );
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error creating supplier account:', error);
    return NextResponse.json(
      { error: 'Failed to create account' },
      { status: 500 }
    );
  }
}