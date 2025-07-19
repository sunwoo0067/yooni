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

// GET: 설정 조회
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get('category');
  const key = searchParams.get('key');

  try {
    let query = `
      SELECT 
        sc.id,
        sc.category,
        sc.key,
        sc.value,
        sc.description,
        sc.data_type,
        sc.is_active,
        sc.created_at,
        sc.updated_at,
        sc.encrypted
      FROM system_configs sc
      WHERE sc.is_active = true
    `;
    const params: any[] = [];

    if (category) {
      query += ' AND sc.category = $1';
      params.push(category);
    }

    if (key) {
      query += category ? ' AND sc.key = $2' : ' AND sc.key = $1';
      params.push(key);
    }

    query += ' ORDER BY sc.category, sc.key';

    const result = await pool.query(query, params);

    // 카테고리별로 그룹화
    const grouped = result.rows.reduce((acc: any, row: any) => {
      if (!acc[row.category]) {
        acc[row.category] = [];
      }
      
      // 민감한 정보는 마스킹
      if (row.encrypted || row.key.includes('SECRET') || row.key.includes('PASSWORD')) {
        row.value = row.value ? '********' : null;
        row.masked = true;
      }
      
      acc[row.category].push(row);
      return acc;
    }, {});

    return NextResponse.json({
      success: true,
      data: grouped,
      total: result.rows.length
    });
  } catch (error) {
    console.error('설정 조회 오류:', error);
    return NextResponse.json(
      { success: false, error: '설정 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

// POST: 설정 저장/업데이트
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { category, key, value, description, data_type = 'string', user = 'api' } = body;

    if (!category || !key) {
      return NextResponse.json(
        { success: false, error: '카테고리와 키는 필수입니다.' },
        { status: 400 }
      );
    }

    // 값 검증 (데이터 타입에 따라)
    let processedValue = value;
    if (data_type === 'integer' && value) {
      processedValue = parseInt(value);
      if (isNaN(processedValue)) {
        return NextResponse.json(
          { success: false, error: '정수 값이 유효하지 않습니다.' },
          { status: 400 }
        );
      }
    } else if (data_type === 'boolean' && value !== null) {
      processedValue = ['true', '1', 'yes', 'on'].includes(String(value).toLowerCase());
    } else if (data_type === 'json' && value) {
      try {
        JSON.parse(value);
      } catch {
        return NextResponse.json(
          { success: false, error: 'JSON 값이 유효하지 않습니다.' },
          { status: 400 }
        );
      }
    }

    const query = `
      INSERT INTO system_configs 
      (category, key, value, description, data_type, created_by, updated_by)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      ON CONFLICT (category, key) 
      DO UPDATE SET 
        value = EXCLUDED.value,
        description = COALESCE(EXCLUDED.description, system_configs.description),
        data_type = EXCLUDED.data_type,
        updated_at = CURRENT_TIMESTAMP,
        updated_by = EXCLUDED.updated_by
      RETURNING *
    `;

    const result = await pool.query(query, [
      category,
      key,
      String(processedValue),
      description,
      data_type,
      user,
      user
    ]);

    return NextResponse.json({
      success: true,
      data: result.rows[0]
    });
  } catch (error) {
    console.error('설정 저장 오류:', error);
    return NextResponse.json(
      { success: false, error: '설정 저장 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

// DELETE: 설정 비활성화
export async function DELETE(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get('category');
  const key = searchParams.get('key');

  if (!category || !key) {
    return NextResponse.json(
      { success: false, error: '카테고리와 키는 필수입니다.' },
      { status: 400 }
    );
  }

  try {
    const query = `
      UPDATE system_configs 
      SET is_active = false, 
          updated_at = CURRENT_TIMESTAMP,
          updated_by = 'api'
      WHERE category = $1 AND key = $2
      RETURNING *
    `;

    const result = await pool.query(query, [category, key]);

    if (result.rows.length === 0) {
      return NextResponse.json(
        { success: false, error: '설정을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result.rows[0]
    });
  } catch (error) {
    console.error('설정 삭제 오류:', error);
    return NextResponse.json(
      { success: false, error: '설정 삭제 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}