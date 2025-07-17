import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const supplier = searchParams.get('supplier');
    const status = searchParams.get('status');
    const limit = parseInt(searchParams.get('limit') || '100');
    
    // 조건절 구성
    const conditions = ['1=1'];
    const params: any[] = [];
    let paramIndex = 1;
    
    if (supplier) {
      conditions.push(`cl.supplier_id = $${paramIndex}`);
      params.push(supplier);
      paramIndex++;
    }
    
    if (status) {
      conditions.push(`cl.status = $${paramIndex}`);
      params.push(status);
      paramIndex++;
    }
    
    const whereClause = conditions.join(' AND ');
    
    // 로그 조회 (공급사명 포함)
    const logs = await query(
      `SELECT 
        cl.*,
        s.name as supplier_name
       FROM collection_logs cl
       LEFT JOIN suppliers s ON cl.supplier_id = s.id
       WHERE ${whereClause}
       ORDER BY cl.started_at DESC
       LIMIT $${paramIndex}`,
      [...params, limit]
    );
    
    return NextResponse.json(logs);
  } catch (error) {
    console.error('Error fetching collection logs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch collection logs' },
      { status: 500 }
    );
  }
}