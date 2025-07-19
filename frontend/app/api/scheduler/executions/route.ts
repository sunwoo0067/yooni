import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5434'),
  database: process.env.DB_NAME || 'yoonni',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '1234',
});

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');
    
    const query = `
      SELECT 
        e.id,
        e.job_id,
        j.name as job_name,
        j.job_type,
        e.status,
        e.started_at,
        e.completed_at,
        e.duration_seconds,
        e.records_processed,
        e.error_message,
        e.result_summary
      FROM job_executions e
      JOIN schedule_jobs j ON e.job_id = j.id
      ORDER BY e.started_at DESC
      LIMIT $1 OFFSET $2
    `;
    
    const result = await pool.query(query, [limit, offset]);
    
    return NextResponse.json({
      success: true,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Failed to fetch job executions:', error);
    return NextResponse.json(
      { success: false, error: '실행 기록 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}