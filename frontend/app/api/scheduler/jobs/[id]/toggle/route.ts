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
    const body = await request.json();
    const isActive = body.is_active;
    
    const query = `
      UPDATE schedule_jobs
      SET status = $1, updated_at = CURRENT_TIMESTAMP
      WHERE id = $2
    `;
    
    const status = isActive ? 'active' : 'paused';
    await pool.query(query, [status, jobId]);
    
    return NextResponse.json({
      success: true,
      message: `작업이 ${isActive ? '활성화' : '비활성화'}되었습니다.`
    });
    
  } catch (error) {
    console.error('Failed to toggle scheduler job:', error);
    return NextResponse.json(
      { success: false, error: '작업 상태 변경 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}