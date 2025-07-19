import { NextResponse } from 'next/server';
import { Pool } from 'pg';

export async function GET() {
  // 새로운 연결 풀을 생성하여 테스트
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    const client = await pool.connect();
    const result = await client.query('SELECT COUNT(*) as count FROM products');
    client.release();
    
    await pool.end();
    
    return NextResponse.json({
      success: true,
      count: result.rows[0].count,
      connectionString: process.env.DATABASE_URL ? 'SET' : 'NOT SET'
    });
  } catch (error) {
    await pool.end();
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : String(error),
      connectionString: process.env.DATABASE_URL || 'NOT SET'
    });
  }
}