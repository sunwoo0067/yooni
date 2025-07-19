'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  TrendingUp, TrendingDown, AlertTriangle, Brain,
  Package, ShoppingCart, Users, DollarSign,
  RefreshCw, Play, BarChart3
} from 'lucide-react'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface Insight {
  type: string
  severity: 'positive' | 'warning' | 'info'
  message: string
  value?: number
  details?: any
  products?: any[]
}

interface Prediction {
  date: string
  product_id: number
  product_name: string
  predicted_sales: number
  predicted_revenue: number
}

interface Anomaly {
  date: string
  product_id: number
  product_name: string
  anomaly_score: number
  details: {
    sales: number
    quantity_sold: number
    order_count: number
  }
}

export default function AIInsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([])
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [modelStatus, setModelStatus] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)
  const [activeTab, setActiveTab] = useState('insights')

  useEffect(() => {
    fetchData()
    checkModelStatus()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      // 인사이트 가져오기
      const insightsRes = await fetch('http://localhost:8003/insights')
      if (insightsRes.ok) {
        const data = await insightsRes.json()
        setInsights(data.insights || [])
      }

      // 매출 예측 가져오기
      const predictRes = await fetch('http://localhost:8003/predict/sales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 7 })
      })
      if (predictRes.ok) {
        const data = await predictRes.json()
        setPredictions(data.predictions || [])
      }

      // 이상치 탐지 가져오기
      const anomalyRes = await fetch('http://localhost:8003/detect/anomalies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_type: 'sales' })
      })
      if (anomalyRes.ok) {
        const data = await anomalyRes.json()
        setAnomalies(data.anomalies || [])
      }
    } catch (error) {
      console.error('Error fetching AI data:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkModelStatus = async () => {
    try {
      const res = await fetch('http://localhost:8003/models/status')
      if (res.ok) {
        const status = await res.json()
        setModelStatus(status)
      }
    } catch (error) {
      console.error('Error checking model status:', error)
    }
  }

  const trainModels = async () => {
    setTraining(true)
    try {
      const res = await fetch('http://localhost:8003/train-models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_types: ['sales_prediction', 'anomaly_detection'] })
      })

      if (res.ok) {
        // 학습이 완료될 때까지 대기 후 데이터 다시 가져오기
        setTimeout(() => {
          checkModelStatus()
          fetchData()
          setTraining(false)
        }, 30000) // 30초 후 확인
      }
    } catch (error) {
      console.error('Error training models:', error)
      setTraining(false)
    }
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'revenue_growth':
        return <TrendingUp className="w-5 h-5 text-green-500" />
      case 'revenue_decline':
        return <TrendingDown className="w-5 h-5 text-red-500" />
      case 'low_stock_alert':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'best_sellers':
        return <ShoppingCart className="w-5 h-5 text-blue-500" />
      case 'top_category':
        return <Package className="w-5 h-5 text-purple-500" />
      default:
        return <Brain className="w-5 h-5 text-gray-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'positive':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'info':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // 차트 데이터 준비
  const predictionChartData = {
    labels: [...new Set(predictions.map(p => p.date))],
    datasets: [{
      label: '예상 매출',
      data: predictions.reduce((acc: any, p) => {
        const date = p.date
        if (!acc[date]) acc[date] = 0
        acc[date] += p.predicted_revenue
        return acc
      }, {}),
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4
    }]
  }

  const categoryData = insights
    .find(i => i.type === 'best_sellers')
    ?.products?.reduce((acc: any, p: any) => {
      const cat = p.category || 'Unknown'
      if (!acc[cat]) acc[cat] = 0
      acc[cat] += p.revenue
      return acc
    }, {}) || {}

  const categoryChartData = {
    labels: Object.keys(categoryData),
    datasets: [{
      label: '카테고리별 매출',
      data: Object.values(categoryData),
      backgroundColor: [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(153, 102, 255, 0.5)'
      ]
    }]
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">AI 비즈니스 인텔리전스</h1>
            <p className="text-gray-600">
              인공지능 기반 비즈니스 분석 및 예측
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => fetchData()}
              disabled={loading}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              새로고침
            </Button>
            <Button
              onClick={trainModels}
              disabled={training}
            >
              <Brain className="w-4 h-4 mr-2" />
              {training ? 'AI 학습 중...' : 'AI 모델 학습'}
            </Button>
          </div>
        </div>
      </div>

      {/* 모델 상태 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">매출 예측 모델</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={modelStatus.sales_prediction?.is_trained ? 'default' : 'secondary'}>
              {modelStatus.sales_prediction?.is_trained ? '학습됨' : '미학습'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">이상 탐지 모델</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={modelStatus.anomaly_detection?.is_trained ? 'default' : 'secondary'}>
              {modelStatus.anomaly_detection?.is_trained ? '학습됨' : '미학습'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">추천 시스템</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={modelStatus.recommendation_engine?.is_initialized ? 'default' : 'secondary'}>
              {modelStatus.recommendation_engine?.product_count || 0}개 상품
            </Badge>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="insights">비즈니스 인사이트</TabsTrigger>
          <TabsTrigger value="predictions">매출 예측</TabsTrigger>
          <TabsTrigger value="anomalies">이상 탐지</TabsTrigger>
        </TabsList>

        <TabsContent value="insights">
          {loading ? (
            <div className="text-center py-8">로딩 중...</div>
          ) : insights.length === 0 ? (
            <Alert>
              <Brain className="h-4 w-4" />
              <AlertDescription>
                AI 모델을 학습하면 비즈니스 인사이트를 확인할 수 있습니다.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {insights.map((insight, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getInsightIcon(insight.type)}
                        <CardTitle className="text-lg">
                          {insight.type.replace(/_/g, ' ').toUpperCase()}
                        </CardTitle>
                      </div>
                      <Badge className={getSeverityColor(insight.severity)}>
                        {insight.severity}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="mb-4">{insight.message}</p>
                    
                    {insight.products && (
                      <div className="space-y-2">
                        {insight.products.slice(0, 3).map((product, idx) => (
                          <div key={idx} className="flex justify-between text-sm">
                            <span>{product.name}</span>
                            <span className="font-medium">
                              ₩{product.revenue?.toLocaleString() || product.days_remaining + '일'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {insight.details && (
                      <div className="mt-4 p-3 bg-gray-50 rounded">
                        <p className="text-sm">
                          <strong>{insight.details.category}</strong>
                          <br />
                          매출: ₩{insight.details.revenue?.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="predictions">
          {predictions.length === 0 ? (
            <Alert>
              <Brain className="h-4 w-4" />
              <AlertDescription>
                매출 예측 모델을 학습하면 미래 매출을 예측할 수 있습니다.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>7일 매출 예측</CardTitle>
                  <CardDescription>
                    AI 모델을 통한 향후 7일간의 매출 예측
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Line
                      data={predictionChartData}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          y: {
                            beginAtZero: true,
                            ticks: {
                              callback: (value) => `₩${value.toLocaleString()}`
                            }
                          }
                        }
                      }}
                    />
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {predictions.slice(0, 6).map((pred, index) => (
                  <Card key={index}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">{pred.product_name}</CardTitle>
                      <CardDescription>
                        {format(new Date(pred.date), 'MM월 dd일', { locale: ko })}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">예상 판매량</span>
                          <span className="font-medium">{Math.round(pred.predicted_sales)}개</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">예상 매출</span>
                          <span className="font-medium">₩{pred.predicted_revenue.toLocaleString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="anomalies">
          {anomalies.length === 0 ? (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                현재 탐지된 이상 패턴이 없습니다.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              {anomalies.map((anomaly, index) => (
                <Card key={index} className="border-yellow-200">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{anomaly.product_name}</CardTitle>
                        <CardDescription>
                          {format(new Date(anomaly.date), 'yyyy년 MM월 dd일', { locale: ko })}
                        </CardDescription>
                      </div>
                      <Badge variant="destructive">
                        이상 점수: {anomaly.anomaly_score.toFixed(3)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">매출</p>
                        <p className="font-medium">₩{anomaly.details.sales.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">판매량</p>
                        <p className="font-medium">{anomaly.details.quantity_sold}개</p>
                      </div>
                      <div>
                        <p className="text-gray-500">주문 수</p>
                        <p className="font-medium">{anomaly.details.order_count}건</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}