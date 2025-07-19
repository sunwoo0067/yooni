import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5434'),
  database: process.env.DB_NAME || 'yoonni',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '1234',
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { table_name, months_ahead = 3 } = body;
    
    if (!table_name) {
      return NextResponse.json(
        { success: false, error: '테이블 이름을 지정해주세요.' },
        { status: 400 }
      );
    }
    
    // 파티션 생성 함수 호출
    const query = `SELECT create_monthly_partition_${table_name}()`;
    
    await pool.query(query);
    
    return NextResponse.json({
      success: true,
      message: `${table_name} 테이블의 파티션이 생성되었습니다.`
    });
    
  } catch (error) {
    console.error('Failed to create partitions:', error);
    return NextResponse.json(
      { success: false, error: '파티션 생성 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}