import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// 데이터베이스 연결 풀
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5434'),
  database: process.env.DB_NAME || 'yoonni',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '1234',
});

// GET: 설정 변경 이력 조회
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get('category');
  const key = searchParams.get('key');
  const limit = parseInt(searchParams.get('limit') || '100');

  try {
    let query = `
      SELECT 
        h.id,
        h.config_id,
        h.category,
        h.key,
        h.old_value,
        h.new_value,
        h.changed_at,
        h.changed_by,
        h.change_reason,
        c.description,
        c.data_type,
        c.encrypted
      FROM system_config_history h
      LEFT JOIN system_configs c ON h.config_id = c.id
      WHERE 1=1
    `;
    const params: any[] = [];
    let paramCount = 0;

    if (category) {
      paramCount++;
      query += ` AND h.category = $${paramCount}`;
      params.push(category);
    }

    if (key) {
      paramCount++;
      query += ` AND h.key = $${paramCount}`;
      params.push(key);
    }

    paramCount++;
    query += ` ORDER BY h.changed_at DESC LIMIT $${paramCount}`;
    params.push(limit);

    const result = await pool.query(query, params);

    // 민감한 정보 마스킹
    const maskedRows = result.rows.map((row: any) => {
      if (row.encrypted || (row.key && (row.key.includes('SECRET') || row.key.includes('PASSWORD')))) {
        if (row.old_value) row.old_value = '********';
        if (row.new_value) row.new_value = '********';
        row.masked = true;
      }
      return row;
    });

    return NextResponse.json({
      success: true,
      data: maskedRows,
      total: maskedRows.length
    });
  } catch (error) {
    console.error('이력 조회 오류:', error);
    return NextResponse.json(
      { success: false, error: '이력 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}