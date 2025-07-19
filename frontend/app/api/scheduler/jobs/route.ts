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
    const query = `
      SELECT 
        j.id,
        j.name,
        j.job_type,
        j.status,
        j.interval,
        j.specific_times,
        j.market_codes,
        j.next_run_at,
        j.last_run_at,
        j.last_success_at,
        j.run_count,
        j.success_count,
        j.error_count,
        j.last_error,
        CASE 
          WHEN j.run_count > 0 THEN (j.success_count::FLOAT / j.run_count * 100)::NUMERIC(5,2)
          ELSE 0
        END as success_rate
      FROM schedule_jobs j
      WHERE j.is_active = true
      ORDER BY j.priority DESC, j.name ASC
    `;
    
    const result = await pool.query(query);
    
    return NextResponse.json({
      success: true,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Failed to fetch scheduler jobs:', error);
    return NextResponse.json(
      { success: false, error: '스케줄 작업 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const query = `
      INSERT INTO schedule_jobs (
        name, job_type, status, interval, cron_expression,
        specific_times, market_codes, account_ids, parameters,
        max_retries, timeout_minutes, priority
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
      ) RETURNING id
    `;
    
    const values = [
      body.name,
      body.job_type,
      body.status || 'active',
      body.interval,
      body.cron_expression,
      body.specific_times,
      body.market_codes,
      body.account_ids,
      body.parameters || {},
      body.max_retries || 3,
      body.timeout_minutes || 30,
      body.priority || 5
    ];
    
    const result = await pool.query(query, values);
    
    return NextResponse.json({
      success: true,
      data: { id: result.rows[0].id }
    });
    
  } catch (error) {
    console.error('Failed to create scheduler job:', error);
    return NextResponse.json(
      { success: false, error: '스케줄 작업 생성 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}