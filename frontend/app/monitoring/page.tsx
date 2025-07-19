'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Database, Cpu, HardDrive, Network, TrendingUp, ShoppingCart, Package, AlertCircle } from 'lucide-react';
import { Line, LineChart, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useSystemMetrics, useApiMetrics, useDatabaseMetrics, useBusinessMetrics, useTimeseriesData, useMetricAlerts } from '@/hooks/useMetrics';
import { MetricCard } from '@/components/monitoring/MetricCard';
import { AlertBanner } from '@/components/monitoring/AlertBanner';

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    bytesIn: number;
    bytesOut: number;
  };
}

interface ApiMetrics {
  requestCount: number;
  errorRate: number;
  avgResponseTime: number;
  endpoints: Array<{
    endpoint: string;
    count: number;
    avgTime: number;
    errorRate: number;
  }>;
}

interface DatabaseMetrics {
  poolSize: number;
  activeConnections: number;
  availableConnections: number;
  queryCount: number;
  avgQueryTime: number;
}

interface BusinessMetrics {
  totalOrders: number;
  totalRevenue: number;
  activeProducts: number;
  conversionRate: number;
}

export default function MonitoringPage() {
  const [timeRange, setTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 커스텀 훅 사용
  const { data: systemMetrics } = useSystemMetrics({ autoRefresh });
  const { data: apiMetrics } = useApiMetrics(timeRange, { autoRefresh });
  const { data: dbMetrics } = useDatabaseMetrics({ autoRefresh });
  const { data: businessMetrics } = useBusinessMetrics(timeRange, { autoRefresh });
  const { data: timeseriesData } = useTimeseriesData(timeRange, { autoRefresh });
  const { alerts, clearAlert } = useMetricAlerts();

  // 알림 생성
  const activeAlerts = [
    ...(systemMetrics?.cpu > 80 ? [{
      id: 'cpu-high',
      severity: systemMetrics.cpu > 90 ? 'critical' as const : 'warning' as const,
      title: 'CPU 사용률 높음',
      message: `CPU 사용률이 ${systemMetrics.cpu.toFixed(1)}%입니다.`,
      timestamp: new Date()
    }] : []),
    ...(dbMetrics?.availableConnections < 2 ? [{
      id: 'db-conn-low',
      severity: 'warning' as const,
      title: '데이터베이스 연결 부족',
      message: `사용 가능한 연결이 ${dbMetrics.availableConnections}개 남았습니다.`,
      timestamp: new Date()
    }] : []),
    ...(apiMetrics?.errorRate > 5 ? [{
      id: 'api-errors',
      severity: 'warning' as const,
      title: 'API 에러율 증가',
      message: `API 에러율이 ${apiMetrics.errorRate.toFixed(2)}%입니다.`,
      timestamp: new Date()
    }] : [])
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">시스템 모니터링</h1>
        <div className="flex gap-4 items-center">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="5m">최근 5분</option>
            <option value="1h">최근 1시간</option>
            <option value="24h">최근 24시간</option>
            <option value="7d">최근 7일</option>
          </select>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            자동 새로고침
          </label>
        </div>
      </div>

      {/* 알림 배너 */}
      <AlertBanner alerts={activeAlerts} onDismiss={clearAlert} />

      {/* 시스템 상태 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="CPU 사용률"
          value={systemMetrics?.cpu?.toFixed(1) || 0}
          suffix="%"
          icon={<Cpu className="h-4 w-4" />}
          progress={systemMetrics?.cpu}
          trend={{
            value: 5.2,
            isPositive: false
          }}
        />
        
        <MetricCard
          title="메모리 사용률"
          value={systemMetrics?.memory?.toFixed(1) || 0}
          suffix="%"
          icon={<Activity className="h-4 w-4" />}
          progress={systemMetrics?.memory}
          trend={{
            value: 2.1,
            isPositive: false
          }}
        />
        
        <MetricCard
          title="디스크 사용률"
          value={systemMetrics?.disk?.toFixed(1) || 0}
          suffix="%"
          icon={<HardDrive className="h-4 w-4" />}
          progress={systemMetrics?.disk}
        />
        
        <MetricCard
          title="DB 연결"
          value={`${dbMetrics?.activeConnections || 0}/${dbMetrics?.poolSize || 0}`}
          icon={<Database className="h-4 w-4" />}
          progress={(dbMetrics?.activeConnections || 0) / (dbMetrics?.poolSize || 1) * 100}
          description={`가용: ${dbMetrics?.availableConnections || 0}`}
        />
      </div>

      {/* 탭 컨텐츠 */}
      <Tabs defaultValue="api" className="space-y-4">
        <TabsList>
          <TabsTrigger value="api">API 모니터링</TabsTrigger>
          <TabsTrigger value="system">시스템 리소스</TabsTrigger>
          <TabsTrigger value="database">데이터베이스</TabsTrigger>
          <TabsTrigger value="business">비즈니스 메트릭</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              title="총 요청 수"
              value={apiMetrics?.requestCount || 0}
              icon={<Network className="h-4 w-4" />}
              trend={{
                value: 12.5,
                isPositive: true
              }}
            />
            
            <MetricCard
              title="평균 응답 시간"
              value={apiMetrics?.avgResponseTime?.toFixed(0) || 0}
              suffix="ms"
              icon={<Activity className="h-4 w-4" />}
              trend={{
                value: 3.2,
                isPositive: false
              }}
            />
            
            <MetricCard
              title="에러율"
              value={(apiMetrics?.errorRate || 0).toFixed(2)}
              suffix="%"
              icon={<AlertCircle className="h-4 w-4" />}
              trend={{
                value: 0.5,
                isPositive: false
              }}
            />
          </div>

          {/* API 엔드포인트별 통계 */}
          <Card>
            <CardHeader>
              <CardTitle>엔드포인트별 성능</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={apiMetrics?.endpoints}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="endpoint" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avgTime" fill="#8884d8" name="평균 응답시간 (ms)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          {/* 시스템 리소스 시계열 차트 */}
          <Card>
            <CardHeader>
              <CardTitle>시스템 리소스 추이</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeseriesData?.system}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                    <Line type="monotone" dataKey="disk" stroke="#ffc658" name="Disk %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 네트워크 I/O */}
          <Card>
            <CardHeader>
              <CardTitle>네트워크 I/O</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeseriesData?.network}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="bytesIn" stroke="#8884d8" name="수신 (KB/s)" />
                    <Line type="monotone" dataKey="bytesOut" stroke="#82ca9d" name="송신 (KB/s)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>연결 풀 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>전체 연결 수</span>
                    <span className="font-bold">{dbMetrics?.poolSize}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>활성 연결</span>
                    <span className="font-bold">{dbMetrics?.activeConnections}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>사용 가능</span>
                    <span className="font-bold">{dbMetrics?.availableConnections}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>쿼리 성능</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>총 쿼리 수</span>
                    <span className="font-bold">{dbMetrics?.queryCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>평균 쿼리 시간</span>
                    <span className="font-bold">{dbMetrics?.avgQueryTime.toFixed(2)}ms</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 쿼리 성능 추이 */}
          <Card>
            <CardHeader>
              <CardTitle>쿼리 성능 추이</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeseriesData?.database}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="queryTime" stroke="#8884d8" name="쿼리 시간 (ms)" />
                    <Line type="monotone" dataKey="connections" stroke="#82ca9d" name="활성 연결" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="business" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="총 주문 수"
              value={businessMetrics?.totalOrders || 0}
              icon={<ShoppingCart className="h-4 w-4" />}
              trend={{
                value: 8.3,
                isPositive: true
              }}
            />
            
            <MetricCard
              title="총 매출"
              value={businessMetrics?.totalRevenue || 0}
              prefix="₩"
              icon={<TrendingUp className="h-4 w-4" />}
              trend={{
                value: 15.2,
                isPositive: true
              }}
            />
            
            <MetricCard
              title="활성 상품"
              value={businessMetrics?.activeProducts || 0}
              icon={<Package className="h-4 w-4" />}
              description={`재고 없음: ${businessMetrics?.outOfStock || 0}`}
            />
            
            <MetricCard
              title="전환율"
              value={(businessMetrics?.conversionRate || 0).toFixed(2)}
              suffix="%"
              icon={<Activity className="h-4 w-4" />}
              trend={{
                value: 0.8,
                isPositive: true
              }}
            />
          </div>

          {/* 비즈니스 메트릭 추이 */}
          <Card>
            <CardHeader>
              <CardTitle>비즈니스 메트릭 추이</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeseriesData?.business}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Line yAxisId="left" type="monotone" dataKey="orders" stroke="#8884d8" name="주문 수" />
                    <Line yAxisId="right" type="monotone" dataKey="revenue" stroke="#82ca9d" name="매출" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

    </div>
  );
}