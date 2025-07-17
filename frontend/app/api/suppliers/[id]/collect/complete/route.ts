import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supplierId = parseInt(params.id);
    const result = await request.json();
    
    // 수집 로그 업데이트
    await query(
      `UPDATE collection_logs 
       SET completed_at = NOW(), 
           status = $1,
           total_products = $2,
           new_products = $3,
           updated_products = $4,
           failed_products = $5,
           error_message = $6,
           details = $7
       WHERE supplier_id = $8 
         AND status = 'running'
         AND completed_at IS NULL`,
      [
        result.success ? 'completed' : 'failed',
        result.totalProducts,
        result.newProducts,
        result.updatedProducts,
        result.failedProducts,
        result.errors.join('\n'),
        JSON.stringify(result),
        supplierId
      ]
    );
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error completing collection:', error);
    return NextResponse.json(
      { error: '수집 완료 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}