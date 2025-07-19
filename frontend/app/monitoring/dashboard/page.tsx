'use client'

import { useState, useEffect, useRef } from 'react'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface RealtimeMetrics {
  timestamp: string
  sales: {
    today: {
      today_orders: number
      today_revenue: number
      unique_customers: number
    }
    weekly_trend: Array<{
      date: string
      orders: number
      revenue: number
    }>
    hourly_trend: Array<{
      hour: number
      orders: number
      revenue: number
    }>
  }
  orders: {
    status_counts: Record<string, number>
    by_market: Array<{
      market_code: string
      orders: number
      revenue: number
    }>
    pending: number
    processing: number
    completed: number
  }
  inventory: {
    total_products: number
    low_stock: number
    out_of_stock: number
    inventory_value: number
  }
  system: {
    error_rate: number
    warning_count: number
    api_metrics: {
      avg_response_time: number
      max_response_time: number
      total_requests: number
    }
    scheduled_jobs: Array<{
      job_type: string
      status: string
      last_run_at: string
      next_run_at: string
    }>
  }
  api_status: Record<string, {
    status: string
    last_check: string | null
    response_time: number | null
  }>
}

export default function RealtimeMonitoringDashboard() {
  const [metrics, setMetrics] = useState<RealtimeMetrics | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket 연결
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765')
        
        ws.onopen = () => {
          console.log('WebSocket 연결됨')
          setConnected(true)
          setError(null)
        }
        
        ws.onmessage = (event) => {
          const message = JSON.parse(event.data)
          
          if (message.type === 'initial' || message.type === 'update') {
            setMetrics(message.data)
          }
        }
        
        ws.onerror = (event) => {
          console.error('WebSocket 에러:', event)
          setError('실시간 연결 오류')
        }
        
        ws.onclose = () => {
          console.log('WebSocket 연결 종료')
          setConnected(false)
          
          // 5초 후 재연결 시도
          setTimeout(connectWebSocket, 5000)
        }
        
        wsRef.current = ws
      } catch (err) {
        console.error('WebSocket 연결 실패:', err)
        setError('WebSocket 연결 실패')
      }
    }
    
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">실시간 데이터를 불러오는 중...</p>
          {error && <p className="mt-2 text-red-600">{error}</p>}
        </div>
      </div>
    )
  }

  // 차트 데이터 준비
  const hourlyChartData = {
    labels: Array.from({ length: 24 }, (_, i) => `${i}시`),
    datasets: [{
      label: '시간별 매출',
      data: Array.from({ length: 24 }, (_, hour) => {
        const hourData = metrics.sales.hourly_trend.find(h => h.hour === hour)
        return hourData?.revenue || 0
      }),
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true
    }]
  }

  const orderStatusChartData = {
    labels: ['대기중', '처리중', '완료'],
    datasets: [{
      data: [metrics.orders.pending, metrics.orders.processing, metrics.orders.completed],
      backgroundColor: ['#FDE047', '#60A5FA', '#34D399'],
      borderWidth: 0
    }]
  }

  const marketRevenueData = {
    labels: metrics.orders.by_market.map(m => m.market_code),
    datasets: [{
      label: '마켓별 매출',
      data: metrics.orders.by_market.map(m => m.revenue),
      backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
      borderWidth: 1
    }]
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* 헤더 */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">실시간 모니터링</h1>
          <p className="text-gray-600 mt-1">
            마지막 업데이트: {new Date(metrics.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
          <span className="text-sm text-gray-600">{connected ? '연결됨' : '연결 끊김'}</span>
        </div>
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">오늘 주문</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.sales.today.today_orders.toLocaleString()}건
              </p>
            </div>
            <div className="text-blue-600 bg-blue-100 p-3 rounded-full">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">오늘 매출</p>
              <p className="text-2xl font-bold text-gray-900">
                ₩{metrics.sales.today.today_revenue.toLocaleString()}
              </p>
            </div>
            <div className="text-green-600 bg-green-100 p-3 rounded-full">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">재고 부족</p>
              <p className="text-2xl font-bold text-yellow-600">
                {metrics.inventory.low_stock}개
              </p>
            </div>
            <div className="text-yellow-600 bg-yellow-100 p-3 rounded-full">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">에러율</p>
              <p className="text-2xl font-bold text-red-600">
                {metrics.system.error_rate}건/시간
              </p>
            </div>
            <div className="text-red-600 bg-red-100 p-3 rounded-full">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">시간별 매출 추이</h2>
          <Line 
            data={hourlyChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: {
                    callback: function(value) {
                      return '₩' + value.toLocaleString()
                    }
                  }
                }
              }
            }}
            height={300}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">주문 상태</h2>
          <div className="flex items-center justify-center" style={{ height: 300 }}>
            <Doughnut 
              data={orderStatusChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom'
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 마켓별 매출 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">마켓별 매출</h2>
          <Bar 
            data={marketRevenueData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: {
                    callback: function(value) {
                      return '₩' + value.toLocaleString()
                    }
                  }
                }
              }
            }}
            height={250}
          />
        </div>

        {/* API 상태 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">외부 API 상태</h2>
          <div className="space-y-3">
            {Object.entries(metrics.api_status).map(([market, status]) => (
              <div key={market} className="flex items-center justify-between">
                <span className="text-sm font-medium">{market.toUpperCase()}</span>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    status.status === 'healthy' ? 'bg-green-500' : 
                    status.status === 'degraded' ? 'bg-yellow-500' : 'bg-gray-400'
                  }`}></div>
                  <span className="text-sm text-gray-600">
                    {status.response_time ? `${status.response_time}ms` : '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 시스템 메트릭 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">시스템 성능</h2>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">평균 응답시간</span>
                <span className="text-sm font-medium">
                  {metrics.system.api_metrics?.avg_response_time?.toFixed(2) || 0}ms
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.min((metrics.system.api_metrics?.avg_response_time || 0) / 1000 * 100, 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="pt-2">
              <p className="text-sm text-gray-600">총 요청 수</p>
              <p className="text-lg font-semibold">{metrics.system.api_metrics?.total_requests || 0}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}