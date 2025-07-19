import { NextRequest, NextResponse } from 'next/server';
import { getLogger } from '@/lib/logger/structured-logger';

const logger = getLogger('monitoring-api');

interface ApiMetricsData {
  [endpoint: string]: {
    count: number;
    totalTime: number;
    errors: number;
    statuses: { [status: string]: number };
  };
}

// 메모리 내 메트릭 저장 (실제로는 Redis 사용 권장)
let apiMetrics: ApiMetricsData = {};
let lastReset = Date.now();

// 메트릭 리셋 (1시간마다)
function checkAndResetMetrics() {
  const now = Date.now();
  if (now - lastReset > 3600000) { // 1시간
    apiMetrics = {};
    lastReset = now;
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get('range') || '1h';

    checkAndResetMetrics();

    // 메트릭 집계
    let totalRequests = 0;
    let totalErrors = 0;
    let totalTime = 0;
    const endpoints = [];

    for (const [endpoint, data] of Object.entries(apiMetrics)) {
      totalRequests += data.count;
      totalErrors += data.errors;
      totalTime += data.totalTime;

      endpoints.push({
        endpoint,
        count: data.count,
        avgTime: data.count > 0 ? data.totalTime / data.count : 0,
        errorRate: data.count > 0 ? (data.errors / data.count) * 100 : 0,
        statuses: data.statuses
      });
    }

    // 상위 10개 엔드포인트만 반환 (요청 수 기준)
    endpoints.sort((a, b) => b.count - a.count);
    const topEndpoints = endpoints.slice(0, 10);

    return NextResponse.json({
      requestCount: totalRequests,
      errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0,
      avgResponseTime: totalRequests > 0 ? totalTime / totalRequests : 0,
      endpoints: topEndpoints,
      timeRange: range,
      lastReset: new Date(lastReset).toISOString()
    });

  } catch (error) {
    logger.error('Failed to fetch API metrics', error as Error);
    return NextResponse.json(
      { error: 'Failed to fetch API metrics' },
      { status: 500 }
    );
  }
}

// 메트릭 기록 API (내부 사용)
export async function POST(request: NextRequest) {
  try {
    const data = await request.json();
    const { endpoint, method, status, duration } = data;

    const key = `${method} ${endpoint}`;
    
    if (!apiMetrics[key]) {
      apiMetrics[key] = {
        count: 0,
        totalTime: 0,
        errors: 0,
        statuses: {}
      };
    }

    apiMetrics[key].count++;
    apiMetrics[key].totalTime += duration;
    
    if (status >= 400) {
      apiMetrics[key].errors++;
    }

    const statusGroup = `${Math.floor(status / 100)}xx`;
    apiMetrics[key].statuses[statusGroup] = (apiMetrics[key].statuses[statusGroup] || 0) + 1;

    return NextResponse.json({ success: true });

  } catch (error) {
    logger.error('Failed to record API metric', error as Error);
    return NextResponse.json(
      { error: 'Failed to record metric' },
      { status: 500 }
    );
  }
}