import { NextResponse } from 'next/server';
import os from 'os';

export async function GET() {
  try {
    // CPU 사용률 계산
    const cpus = os.cpus();
    let totalIdle = 0;
    let totalTick = 0;

    cpus.forEach(cpu => {
      for (const type in cpu.times) {
        totalTick += cpu.times[type as keyof typeof cpu.times];
      }
      totalIdle += cpu.times.idle;
    });

    const idle = totalIdle / cpus.length;
    const total = totalTick / cpus.length;
    const cpuUsage = 100 - ~~(100 * idle / total);

    // 메모리 사용률
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memoryUsage = ((totalMem - freeMem) / totalMem) * 100;

    // 디스크 사용률 (간단한 추정)
    // 실제로는 node-disk-info 같은 패키지 사용 권장
    const diskUsage = 65; // 임시 값

    // 네트워크 정보
    const networkInterfaces = os.networkInterfaces();
    let bytesIn = 0;
    let bytesOut = 0;

    // 실제로는 시스템 모니터링 도구나 /proc/net/dev 파일을 읽어야 함
    // 여기서는 더미 데이터 사용
    bytesIn = Math.floor(Math.random() * 1000000);
    bytesOut = Math.floor(Math.random() * 1000000);

    return NextResponse.json({
      cpu: cpuUsage,
      memory: memoryUsage,
      disk: diskUsage,
      network: {
        bytesIn,
        bytesOut
      },
      uptime: os.uptime(),
      loadAverage: os.loadavg(),
      platform: os.platform(),
      hostname: os.hostname()
    });

  } catch (error) {
    console.error('System metrics error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch system metrics' },
      { status: 500 }
    );
  }
}