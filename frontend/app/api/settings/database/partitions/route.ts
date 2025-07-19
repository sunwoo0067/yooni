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
    // 파티션 정보 조회
    const query = `
      WITH partition_info AS (
        SELECT 
          parent.relname as parent_table,
          child.relname as partition_name,
          pg_relation_size(child.oid) as size_bytes,
          pg_size_pretty(pg_relation_size(child.oid)) as size,
          pg_stat_get_live_tuples(child.oid) as row_count,
          pg_stat_get_dead_tuples(child.oid) as dead_rows,
          pg_get_expr(child.relpartbound, child.oid) as partition_bound,
          CASE 
            WHEN child.relname ~ '\\d{4}_\\d{2}$' THEN
              to_date(right(child.relname, 7), 'YYYY_MM')
            ELSE NULL
          END as partition_date
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        JOIN pg_namespace n ON n.oid = parent.relnamespace
        WHERE n.nspname = 'public'
        AND parent.relkind = 'p'  -- partitioned table
      )
      SELECT 
        parent_table,
        json_agg(json_build_object(
          'name', partition_name,
          'size', size,
          'rows', row_count,
          'dead_rows', dead_rows,
          'date', partition_date
        ) ORDER BY partition_name) as partitions,
        COUNT(*) as partition_count,
        SUM(row_count) as total_rows,
        pg_size_pretty(SUM(size_bytes)) as total_size
      FROM partition_info
      GROUP BY parent_table
      ORDER BY parent_table;
    `;
    
    const result = await pool.query(query);
    
    return NextResponse.json({
      success: true,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Failed to fetch partition info:', error);
    return NextResponse.json(
      { success: false, error: '파티션 정보 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}