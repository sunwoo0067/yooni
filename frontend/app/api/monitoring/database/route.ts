import { NextResponse } from 'next/server';
import { getPoolStats, query } from '@/lib/db';

export async function GET() {
  try {
    // 연결 풀 상태 - 통합 함수 사용
    const poolStats = await getPoolStats();
    const poolSize = 10; // 설정에서 가져온 max 값
    const totalCount = poolStats?.totalCount || 0;
    const idleCount = poolStats?.idleCount || 0; 
    const waitingCount = poolStats?.waitingCount || 0;
    
    // 데이터베이스 통계 쿼리
    const statsQuery = `
      SELECT 
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
        (SELECT count(*) FROM pg_stat_activity) as total_connections,
        (SELECT sum(numbackends) FROM pg_stat_database) as total_backends,
        (SELECT sum(xact_commit + xact_rollback) FROM pg_stat_database) as total_transactions,
        (SELECT sum(blks_read) FROM pg_stat_database) as blocks_read,
        (SELECT sum(blks_hit) FROM pg_stat_database) as blocks_hit,
        (SELECT avg(mean_exec_time) FROM pg_stat_statements LIMIT 100) as avg_query_time
    `;
    
    let stats;
    try {
      const result = await query(statsQuery);
      stats = result[0];
    } catch (error) {
      // pg_stat_statements가 없을 수 있으므로 기본값 사용
      stats = {
        active_connections: totalCount - idleCount,
        total_connections: totalCount,
        avg_query_time: 0
      };
    }
    
    // 캐시 히트율 계산
    const blocksHit = parseInt(stats.blocks_hit) || 0;
    const blocksRead = parseInt(stats.blocks_read) || 0;
    const cacheHitRate = (blocksHit + blocksRead) > 0 
      ? Math.round((blocksHit / (blocksHit + blocksRead)) * 100) 
      : 0;
    
    return NextResponse.json({
      poolSize,
      activeConnections: totalCount - idleCount,
      availableConnections: poolSize - (totalCount - idleCount),
      waitingConnections: waitingCount,
      totalConnections: stats.total_connections || totalCount,
      queryCount: stats.total_transactions || 0,
      avgQueryTime: parseFloat(stats.avg_query_time) || 0,
      cacheHitRate,
      status: 'healthy'
    });

  } catch (error) {
    console.error('Database metrics error:', error);
    return NextResponse.json({
      poolSize: 0,
      activeConnections: 0,
      availableConnections: 0,
      waitingConnections: 0,
      totalConnections: 0,
      queryCount: 0,
      avgQueryTime: 0,
      cacheHitRate: 0,
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}