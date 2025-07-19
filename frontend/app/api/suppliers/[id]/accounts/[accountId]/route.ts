import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string; accountId: string }> }
) {
  try {
    const params = await context.params;
    const supplierId = parseInt(params.id);
    const accountId = parseInt(params.accountId);
    const { account_name, api_key, api_secret, is_active } = await request.json();
    
    // 계정 확인
    const account = await getOne(
      'SELECT id FROM supplier_accounts WHERE id = $1 AND supplier_id = $2',
      [accountId, supplierId]
    );
    
    if (!account) {
      return NextResponse.json(
        { error: '계정을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // 계정 업데이트
    await query(
      `UPDATE supplier_accounts 
       SET account_name = $1, api_key = $2, api_secret = $3, 
           is_active = $4, updated_at = NOW()
       WHERE id = $5`,
      [account_name, api_key, api_secret, is_active, accountId]
    );
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error updating supplier account:', error);
    return NextResponse.json(
      { error: 'Failed to update account' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string; accountId: string }> }
) {
  try {
    const params = await context.params;
    const supplierId = parseInt(params.id);
    const accountId = parseInt(params.accountId);
    
    // 계정 확인
    const account = await getOne(
      'SELECT id FROM supplier_accounts WHERE id = $1 AND supplier_id = $2',
      [accountId, supplierId]
    );
    
    if (!account) {
      return NextResponse.json(
        { error: '계정을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // 계정 삭제
    await query(
      'DELETE FROM supplier_accounts WHERE id = $1',
      [accountId]
    );
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting supplier account:', error);
    return NextResponse.json(
      { error: 'Failed to delete account' },
      { status: 500 }
    );
  }
}