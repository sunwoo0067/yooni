import { NextRequest, NextResponse } from 'next/server';

// 시계열 데이터 생성 (실제로는 데이터베이스나 시계열 DB에서 가져옴)
function generateTimeseriesData(range: string) {
  const now = new Date();
  const data = {
    system: [] as { timestamp: string; cpu: number; memory: number; disk: number }[],
    network: [] as { timestamp: string; inbound: number; outbound: number }[],
    database: [] as { timestamp: string; connections: number; queries: number; slow_queries: number }[],
    business: [] as { timestamp: string; orders: number; revenue: number; users: number }[]
  };

  // 데이터 포인트 수 결정
  let points = 60;
  let interval = 60000; // 1분
  
  switch (range) {
    case '5m':
      points = 30;
      interval = 10000; // 10초
      break;
    case '1h':
      points = 60;
      interval = 60000; // 1분
      break;
    case '24h':
      points = 144;
      interval = 600000; // 10분
      break;
    case '7d':
      points = 168;
      interval = 3600000; // 1시간
      break;
  }

  // 시스템 메트릭 시계열
  for (let i = points - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - (i * interval));
    
    data.system.push({
      timestamp: timestamp.toISOString(),
      cpu: 30 + Math.random() * 40 + Math.sin(i / 10) * 10,
      memory: 50 + Math.random() * 30 + Math.cos(i / 10) * 5,
      disk: 60 + Math.random() * 20
    });

    data.network.push({
      timestamp: timestamp.toISOString(),
      inbound: Math.floor(Math.random() * 1000 + 500),
      outbound: Math.floor(Math.random() * 800 + 300)
    });

    data.database.push({
      timestamp: timestamp.toISOString(),
      connections: Math.floor(5 + Math.random() * 10),
      queries: Math.floor(Math.random() * 100 + 50),
      slow_queries: Math.floor(Math.random() * 5)
    });

    data.business.push({
      timestamp: timestamp.toISOString(),
      orders: Math.floor(Math.random() * 50 + 20),
      revenue: Math.floor(Math.random() * 500000 + 100000),
      users: Math.floor(Math.random() * 1000 + 500)
    });
  }

  return data;
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get('range') || '1h';
    
    // 실제로는 데이터베이스나 Redis에서 메트릭 데이터를 가져옴
    const timeseriesData = generateTimeseriesData(range);
    
    return NextResponse.json(timeseriesData);

  } catch (error) {
    console.error('Timeseries data error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch timeseries data' },
      { status: 500 }
    );
  }
}