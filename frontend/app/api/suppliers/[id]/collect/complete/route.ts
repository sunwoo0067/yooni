import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

// 수집 완료 API - Python 스크립트나 외부 프로세스에서 호출
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const { id } = params;
    const supplierId = parseInt(id);
    const body = await request.json();
    
    const { 
      logId, 
      success, 
      totalProducts, 
      newProducts, 
      updatedProducts, 
      failedProducts, 
      errors 
    } = body;
    
    // 로그 업데이트
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
       WHERE id = $8`,
      [
        success ? 'completed' : 'failed',
        totalProducts || 0,
        newProducts || 0,
        updatedProducts || 0,
        failedProducts || 0,
        errors ? errors.join('\n') : null,
        JSON.stringify(body),
        logId
      ]
    );
    
    return NextResponse.json({ success: true });
    
  } catch (error) {
    console.error('Complete API error:', error);
    return NextResponse.json(
      { error: '완료 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}