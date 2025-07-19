'use client';

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, TrendingDown, AlertCircle, DollarSign,
  Target, Activity, ShoppingCart, AlertTriangle
} from 'lucide-react';

interface DashboardData {
  profitability: {
    total_products: number;
    average_margin: number;
    high_margin_products: number;
  };
  competition: {
    active_alerts: number;
    undercut_products: number;
    price_wars: number;
  };
  market_trends: string[];
}

interface CategoryProfitability {
  category: string;
  product_count: number;
  net_margin: number;
  roi: number;
  profitability_score: number;
}

interface PriceAlert {
  product_id: number;
  product_name: string;
  alert_type: string;
  our_price: number;
  competitor_price: number;
  competitor_name: string;
  price_difference: number;
  recommendation: string;
}

interface MarketTrend {
  category: string;
  trend_type: string;
  trend_score: number;
  avg_growth_rate: number;
  competitive_index: number;
  opportunity_score: number;
}

export default function BIDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [categoryProfitability, setCategoryProfitability] = useState<CategoryProfitability[]>([]);
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);
  const [marketTrends, setMarketTrends] = useState<MarketTrend[]>([]);
  const [selectedTab, setSelectedTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000); // 1분마다 갱신
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setError(null);
      
      const [summaryRes, categoriesRes, alertsRes, trendsRes] = await Promise.all([
        fetch('http://localhost:8005/api/bi/dashboard/summary'),
        fetch('http://localhost:8005/api/bi/profitability/categories'),
        fetch('http://localhost:8005/api/bi/competitors/alerts?limit=10'),
        fetch('http://localhost:8005/api/bi/trends/categories')
      ]);

      if (!summaryRes.ok) {
        throw new Error('대시보드 요약 데이터를 불러오는데 실패했습니다');
      }

      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setDashboardData(summary);
      }

      if (categoriesRes.ok) {
        const categories = await categoriesRes.json();
        setCategoryProfitability(categories.categories?.slice(0, 10) || []);
      }

      if (alertsRes.ok) {
        const alerts = await alertsRes.json();
        setPriceAlerts(alerts.alerts || []);
      }

      if (trendsRes.ok) {
        const trends = await trendsRes.json();
        setMarketTrends(trends.trends?.slice(0, 10) || []);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch BI data:', error);
      setError(error instanceof Error ? error.message : 'BI 데이터를 불러오는데 실패했습니다');
      setLoading(false);
    }
  };

  const runCompetitorMonitoring = async () => {
    try {
      const response = await fetch('http://localhost:8005/api/bi/competitors/monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monitor_all: false })
      });

      if (response.ok) {
        alert('경쟁사 모니터링이 시작되었습니다');
      }
    } catch (error) {
      console.error('Failed to start monitoring:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4">비즈니스 인텔리전스 데이터 로딩중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>오류:</strong> {error}
            <br />
            <Button 
              onClick={() => fetchDashboardData()} 
              className="mt-4"
              size="sm"
            >
              다시 시도
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const profitabilityChartData = categoryProfitability.map(cat => ({
    name: cat.category.substring(0, 15),
    margin: cat.net_margin,
    roi: cat.roi,
    score: cat.profitability_score
  }));

  const trendTypeColors: Record<string, string> = {
    rising_star: '#10B981',
    steady_seller: '#3B82F6',
    declining: '#EF4444',
    stable: '#6B7280'
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">비즈니스 인텔리전스 대시보드</h1>
        <p className="text-gray-600 mt-2">실시간 수익성 분석, 경쟁사 모니터링, 시장 트렌드</p>
      </div>

      {/* 핵심 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">전체 상품</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.profitability.total_products || 0}</div>
            <p className="text-xs text-muted-foreground">활성 상품 수</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">평균 마진율</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center">
              {dashboardData?.profitability.average_margin.toFixed(1)}%
              <TrendingUp className="ml-2 h-4 w-4 text-green-500" />
            </div>
            <p className="text-xs text-muted-foreground">전체 평균</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">가격 알림</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center">
              {dashboardData?.competition.active_alerts || 0}
              {(dashboardData?.competition.active_alerts || 0) > 0 && (
                <AlertCircle className="ml-2 h-4 w-4 text-red-500" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">대응 필요</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">가격 전쟁</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center">
              {dashboardData?.competition.price_wars || 0}
              {(dashboardData?.competition.price_wars || 0) > 0 && (
                <AlertTriangle className="ml-2 h-4 w-4 text-orange-500" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">진행 중</p>
          </CardContent>
        </Card>
      </div>

      {/* 시장 인사이트 */}
      {dashboardData?.market_trends && dashboardData.market_trends.length > 0 && (
        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>오늘의 시장 인사이트:</strong>
            <ul className="mt-2 space-y-1">
              {dashboardData.market_trends.map((insight, idx) => (
                <li key={idx}>{insight}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* 탭 컨텐츠 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">전체 현황</TabsTrigger>
          <TabsTrigger value="profitability">수익성 분석</TabsTrigger>
          <TabsTrigger value="competition">경쟁사 모니터링</TabsTrigger>
          <TabsTrigger value="trends">시장 트렌드</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 카테고리별 수익성 차트 */}
            <Card>
              <CardHeader>
                <CardTitle>카테고리별 수익성</CardTitle>
                <CardDescription>순마진율과 ROI 비교</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={profitabilityChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="margin" fill="#8884d8" name="마진율(%)" />
                    <Bar dataKey="roi" fill="#82ca9d" name="ROI(%)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 시장 트렌드 분포 */}
            <Card>
              <CardHeader>
                <CardTitle>시장 트렌드 분포</CardTitle>
                <CardDescription>카테고리별 트렌드 현황</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(
                    marketTrends.reduce((acc, trend) => {
                      acc[trend.trend_type] = (acc[trend.trend_type] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div
                          className="w-3 h-3 rounded-full mr-2"
                          style={{ backgroundColor: trendTypeColors[type] || '#6B7280' }}
                        />
                        <span className="text-sm">
                          {type === 'rising_star' && '급성장'}
                          {type === 'steady_seller' && '스테디셀러'}
                          {type === 'declining' && '하락세'}
                          {type === 'stable' && '안정적'}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <span className="font-semibold mr-2">{count}</span>
                        <Progress value={(count / marketTrends.length) * 100} className="w-24" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="profitability" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>카테고리별 상세 수익성</CardTitle>
              <CardDescription>수익성 점수 기준 상위 카테고리</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {categoryProfitability.map((cat, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-semibold">{cat.category}</h4>
                        <p className="text-sm text-gray-600">{cat.product_count}개 상품</p>
                      </div>
                      <Badge variant={cat.profitability_score > 70 ? 'default' : 'secondary'}>
                        점수: {cat.profitability_score.toFixed(1)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">순마진율:</span>
                        <span className="font-semibold ml-2">{cat.net_margin.toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-gray-600">ROI:</span>
                        <span className="font-semibold ml-2">{cat.roi.toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-gray-600">상품 수:</span>
                        <span className="font-semibold ml-2">{cat.product_count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="competition" className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">가격 알림</h3>
            <Button onClick={runCompetitorMonitoring}>
              경쟁사 모니터링 실행
            </Button>
          </div>

          <div className="space-y-4">
            {priceAlerts.map((alert, idx) => (
              <Alert key={idx} variant={alert.alert_type === 'undercut' ? 'destructive' : 'default'}>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex justify-between items-start">
                    <div>
                      <strong>{alert.product_name}</strong>
                      <p className="text-sm mt-1">
                        우리 가격: {alert.our_price.toLocaleString()}원 | 
                        {alert.competitor_name} 가격: {alert.competitor_price.toLocaleString()}원
                        (차이: {alert.price_difference.toLocaleString()}원)
                      </p>
                      <p className="text-sm mt-1 text-gray-600">{alert.recommendation}</p>
                    </div>
                    <Badge variant={alert.alert_type === 'undercut' ? 'destructive' : 'outline'}>
                      {alert.alert_type === 'undercut' ? '가격 하락' : '가격 전쟁'}
                    </Badge>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>카테고리별 성장 트렌드</CardTitle>
              <CardDescription>성장률과 기회 점수 분석</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={marketTrends.map(trend => ({
                    name: trend.category.substring(0, 20),
                    growth: trend.avg_growth_rate,
                    opportunity: trend.opportunity_score,
                    competitive: trend.competitive_index
                  }))}
                  margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="growth" fill="#8884d8" name="성장률(%)" />
                  <Bar dataKey="opportunity" fill="#82ca9d" name="기회점수" />
                  <Bar dataKey="competitive" fill="#ffc658" name="경쟁지수" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}