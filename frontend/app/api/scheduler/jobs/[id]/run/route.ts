import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5434'),
  database: process.env.DB_NAME || 'yoonni',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '1234',
});

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const jobId = parseInt(params.id);
    
    // 즉시 실행을 위해 next_run_at을 현재 시간으로 설정
    const query = `
      UPDATE schedule_jobs
      SET next_run_at = CURRENT_TIMESTAMP
      WHERE id = $1 AND is_active = true
      RETURNING name
    `;
    
    const result = await pool.query(query, [jobId]);
    
    if (result.rowCount === 0) {
      return NextResponse.json(
        { success: false, error: '작업을 찾을 수 없거나 비활성 상태입니다.' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      message: `"${result.rows[0].name}" 작업이 실행 대기열에 추가되었습니다.`
    });
    
  } catch (error) {
    console.error('Failed to run scheduler job:', error);
    return NextResponse.json(
      { success: false, error: '작업 실행 요청 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}