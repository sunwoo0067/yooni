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
    // 데이터베이스 통계 조회
    const statsQuery = `
      SELECT 
        pg_database_size(current_database()) as database_size_bytes,
        pg_size_pretty(pg_database_size(current_database())) as database_size,
        (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count,
        (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as connection_count,
        (SELECT sum(xact_commit + xact_rollback) FROM pg_stat_database WHERE datname = current_database()) as transaction_count,
        (SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()) as deadlock_count
    `;
    
    const cacheQuery = `
      SELECT 
        CASE 
          WHEN blks_hit + blks_read = 0 THEN 0
          ELSE (blks_hit::float / (blks_hit + blks_read) * 100)
        END as cache_hit_ratio
      FROM pg_stat_database 
      WHERE datname = current_database()
    `;
    
    const slowQueryQuery = `
      SELECT count(*) as slow_query_count
      FROM pg_stat_statements
      WHERE mean_exec_time > 1000  -- 1초 이상
    `;
    
    const [statsResult, cacheResult] = await Promise.all([
      pool.query(statsQuery),
      pool.query(cacheQuery)
    ]);
    
    let slowQueryCount = 0;
    try {
      const slowQueryResult = await pool.query(slowQueryQuery);
      slowQueryCount = parseInt(slowQueryResult.rows[0].slow_query_count);
    } catch (e) {
      // pg_stat_statements 확장이 없을 수 있음
    }
    
    const stats = statsResult.rows[0];
    const cache = cacheResult.rows[0];
    
    return NextResponse.json({
      success: true,
      data: {
        database_size: stats.database_size,
        table_count: parseInt(stats.table_count),
        connection_count: parseInt(stats.connection_count),
        cache_hit_ratio: parseFloat(cache.cache_hit_ratio),
        transaction_count: parseInt(stats.transaction_count),
        deadlock_count: parseInt(stats.deadlock_count),
        slow_query_count: slowQueryCount
      }
    });
    
  } catch (error) {
    console.error('Failed to fetch database stats:', error);
    return NextResponse.json(
      { success: false, error: '데이터베이스 통계 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}