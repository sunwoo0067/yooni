'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  RefreshCw, 
  PlayCircle, 
  Calendar, 
  TrendingUp,
  Package,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
  Brain,
  BarChart3,
  Database
} from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface Supplier {
  id: number
  name: string
  status: string
  last_collection: string | null
  next_collection: string | null
  total_products: number
  active_products: number
  success_rate: number
  avg_collection_time: number
}

interface CollectionStatus {
  running_jobs: any[]
  recent_jobs: any[]
  scheduler_status: string
}

interface DashboardStats {
  overall: {
    total_suppliers: number
    total_products: number
    active_products: number
    analyzed_products: number
    avg_demand_score: number
  }
  recent_24h: {
    collections_24h: number
    products_collected_24h: number
    avg_processing_time: number
    successful_collections: number
  }
}

interface AIInsight {
  product_id: number
  product_name: string
  supplier_name: string
  category: string
  current_price: number
  predicted_price: string
  demand_score: string
  demand_grade: string
  price_diff: number
  demand_level_group: string
}

export default function SupplierManagementPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus | null>(null)
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [aiInsights, setAIInsights] = useState<AIInsight[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  // 데이터 불러오기
  const fetchData = async () => {
    try {
      const [suppliersRes, statusRes, statsRes, insightsRes] = await Promise.all([
        fetch('http://localhost:8004/api/suppliers'),
        fetch('http://localhost:8004/api/collection/status'),
        fetch('http://localhost:8004/api/dashboard/stats'),
        fetch('http://localhost:8004/api/ai/insights?limit=10')
      ])

      const suppliersData = await suppliersRes.json()
      const statusData = await statusRes.json()
      const statsData = await statsRes.json()
      const insightsData = await insightsRes.json()

      setSuppliers(suppliersData)
      setCollectionStatus(statusData)
      setDashboardStats(statsData)
      setAIInsights(insightsData.product_insights || [])
    } catch (error) {
      console.error('데이터 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // 30초마다 갱신
    return () => clearInterval(interval)
  }, [])

  // 수집 트리거
  const triggerCollection = async (supplierName: string) => {
    setTriggering(supplierName)
    try {
      const response = await fetch('http://localhost:8004/api/collection/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ supplier_name: supplierName })
      })

      if (response.ok) {
        alert(`${supplierName} 수집이 시작되었습니다`)
        setTimeout(fetchData, 2000) // 2초 후 데이터 갱신
      } else {
        const error = await response.json()
        alert(`수집 시작 실패: ${error.detail}`)
      }
    } catch (error) {
      alert('수집 트리거 실패')
    } finally {
      setTriggering(null)
    }
  }

  // 상태별 배지 색상
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-blue-500">실행중</Badge>
      case 'completed':
        return <Badge className="bg-green-500">완료</Badge>
      case 'failed':
        return <Badge className="bg-red-500">실패</Badge>
      default:
        return <Badge variant="secondary">대기</Badge>
    }
  }

  // 성공률에 따른 색상
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600'
    if (rate >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  // 수요 등급 색상
  const getDemandGradeBadge = (grade: string) => {
    const colors: Record<string, string> = {
      A: 'bg-red-500',
      B: 'bg-orange-500',
      C: 'bg-yellow-500',
      D: 'bg-blue-500',
      E: 'bg-gray-500'
    }
    return <Badge className={colors[grade] || 'bg-gray-500'}>{grade}등급</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">공급사 통합 관리</h1>
          <p className="text-gray-600 mt-1">실시간 수집 상태와 AI 분석 결과를 확인하세요</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button onClick={() => triggerCollection('all')} variant="default">
            <PlayCircle className="mr-2 h-4 w-4" />
            전체 수집
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="dashboard">
            <BarChart3 className="mr-2 h-4 w-4" />
            대시보드
          </TabsTrigger>
          <TabsTrigger value="suppliers">
            <Database className="mr-2 h-4 w-4" />
            공급사 현황
          </TabsTrigger>
          <TabsTrigger value="collection">
            <Activity className="mr-2 h-4 w-4" />
            수집 모니터링
          </TabsTrigger>
          <TabsTrigger value="insights">
            <Brain className="mr-2 h-4 w-4" />
            AI 인사이트
          </TabsTrigger>
        </TabsList>

        {/* 대시보드 탭 */}
        <TabsContent value="dashboard" className="space-y-4">
          {dashboardStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">전체 상품</CardTitle>
                  <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardStats.overall.total_products.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    활성: {dashboardStats.overall.active_products.toLocaleString()} (
                    {((dashboardStats.overall.active_products / dashboardStats.overall.total_products) * 100).toFixed(1)}%)
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">AI 분석</CardTitle>
                  <Brain className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardStats.overall.analyzed_products.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    평균 수요점수: {dashboardStats.overall.avg_demand_score?.toFixed(1) || 'N/A'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">24시간 수집</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardStats.recent_24h.collections_24h}회
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardStats.recent_24h.products_collected_24h?.toLocaleString() || 0}개 수집
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">성공률</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardStats.recent_24h.collections_24h > 0
                      ? Math.round((dashboardStats.recent_24h.successful_collections / dashboardStats.recent_24h.collections_24h) * 100)
                      : 0}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    평균 {dashboardStats.recent_24h.avg_processing_time?.toFixed(0) || 0}초 소요
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 실시간 수집 상태 */}
          {collectionStatus?.running_jobs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 animate-pulse" />
                  실시간 수집 현황
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {collectionStatus.running_jobs.map((job: any) => (
                    <div key={job.id} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
                        <div>
                          <p className="font-medium">{job.supplier_name}</p>
                          <p className="text-sm text-gray-600">
                            시작: {format(new Date(job.started_at), 'HH:mm:ss', { locale: ko })}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-blue-600">
                          {Math.floor(job.duration_seconds / 60)}분 {job.duration_seconds % 60}초 경과
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 공급사 현황 탭 */}
        <TabsContent value="suppliers" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {suppliers.map((supplier) => (
              <Card key={supplier.id}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg">{supplier.name}</CardTitle>
                    {getStatusBadge(supplier.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">전체 상품</p>
                      <p className="font-semibold">{supplier.total_products.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">활성 상품</p>
                      <p className="font-semibold">{supplier.active_products.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">성공률</p>
                      <p className={`font-semibold ${getSuccessRateColor(supplier.success_rate)}`}>
                        {supplier.success_rate.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">평균 시간</p>
                      <p className="font-semibold">{supplier.avg_collection_time.toFixed(0)}초</p>
                    </div>
                  </div>

                  {supplier.last_collection && (
                    <div className="pt-3 border-t">
                      <p className="text-xs text-muted-foreground mb-1">마지막 수집</p>
                      <p className="text-sm">{format(new Date(supplier.last_collection), 'yyyy-MM-dd HH:mm', { locale: ko })}</p>
                    </div>
                  )}

                  <Button
                    className="w-full"
                    variant={supplier.status === 'running' ? 'secondary' : 'default'}
                    onClick={() => triggerCollection(supplier.name)}
                    disabled={supplier.status === 'running' || triggering === supplier.name}
                  >
                    {triggering === supplier.name ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <PlayCircle className="mr-2 h-4 w-4" />
                    )}
                    {supplier.status === 'running' ? '수집 중...' : '수집 시작'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* 수집 모니터링 탭 */}
        <TabsContent value="collection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>최근 수집 내역</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {collectionStatus?.recent_jobs.map((job: any) => (
                  <div key={job.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      {job.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : job.status === 'failed' ? (
                        <XCircle className="h-5 w-5 text-red-500" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-yellow-500" />
                      )}
                      <div>
                        <p className="font-medium">{job.supplier_name}</p>
                        <p className="text-sm text-gray-600">
                          {format(new Date(job.completed_at), 'yyyy-MM-dd HH:mm:ss', { locale: ko })}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {job.collected_count.toLocaleString()}개 수집
                        {job.failed_count > 0 && (
                          <span className="text-red-600"> ({job.failed_count}개 실패)</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500">
                        {job.duration_seconds}초 소요
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI 인사이트 탭 */}
        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI 가격/수요 분석 결과</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">상품명</th>
                      <th className="text-left p-2">공급사</th>
                      <th className="text-right p-2">현재가</th>
                      <th className="text-right p-2">예측가</th>
                      <th className="text-center p-2">수요등급</th>
                      <th className="text-right p-2">수요점수</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aiInsights.map((insight, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="p-2">
                          <p className="font-medium truncate max-w-xs" title={insight.product_name}>
                            {insight.product_name}
                          </p>
                          <p className="text-xs text-gray-500">{insight.category}</p>
                        </td>
                        <td className="p-2 text-sm">{insight.supplier_name}</td>
                        <td className="p-2 text-right">{insight.current_price.toLocaleString()}원</td>
                        <td className="p-2 text-right">
                          <span className={insight.price_diff > 0 ? 'text-green-600' : 'text-red-600'}>
                            {Number(insight.predicted_price).toLocaleString()}원
                          </span>
                        </td>
                        <td className="p-2 text-center">
                          {getDemandGradeBadge(insight.demand_grade)}
                        </td>
                        <td className="p-2 text-right font-medium">
                          {Number(insight.demand_score).toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}