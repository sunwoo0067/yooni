import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const supplierId = parseInt(params.id);
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '10');
    
    const logs = await query(
      `SELECT * FROM collection_logs 
       WHERE supplier_id = $1 
       ORDER BY started_at DESC 
       LIMIT $2`,
      [supplierId, limit]
    );
    
    return NextResponse.json(logs);
  } catch (error) {
    console.error('Error fetching collection logs:', error);
    return NextResponse.json(
      { error: '로그 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}