'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  RefreshCw, Package, ShoppingCart, TrendingUp, AlertCircle, 
  CheckCircle, Clock, XCircle, Users, BarChart, Truck
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface DashboardData {
  today: {
    date: string;
    orders: { total: number; new: number; processing: number; shipped: number };
    sales: { amount: number; count: number };
    cs: { total: number; pending: number; answered: number };
    returns: { requested: number; approved: number; rejected: number };
  };
  recent: {
    period: string;
    orders: { total: number; daily_avg: number };
    sales: { total_amount: number; daily_avg: number };
    products: { active: number; soldout: number; suspended: number };
    settlement: { pending: number; completed: number };
  };
  alerts: Array<{
    type: string;
    level: string;
    message: string;
    action: string;
  }>;
}

export default function CoupangDashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchDashboardData();
    fetchPerformanceData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/coupang/dashboard?type=summary');
      const result = await response.json();
      
      if (result.success && result.data) {
        setDashboardData(result.data);
      } else {
        throw new Error(result.error || '데이터 로드 실패');
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '대시보드 데이터를 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch('/api/coupang/dashboard?type=performance');
      const result = await response.json();
      
      if (result.success && result.data) {
        setPerformanceData(result.data);
      }
    } catch (error) {
      console.error('Performance data error:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    await fetchPerformanceData();
    setRefreshing(false);
    toast({
      title: '새로고침 완료',
      description: '대시보드가 업데이트되었습니다.',
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(value);
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'cs': return <Users className="h-4 w-4" />;
      case 'product': return <Package className="h-4 w-4" />;
      case 'order': return <ShoppingCart className="h-4 w-4" />;
      case 'return': return <XCircle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getAlertVariant = (level: string) => {
    switch (level) {
      case 'warning': return 'destructive';
      case 'info': return 'default';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">대시보드 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="container mx-auto py-10">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>오류</AlertTitle>
          <AlertDescription>대시보드 데이터를 불러올 수 없습니다.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-10">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">쿠팡 대시보드</h1>
          <p className="text-muted-foreground">실시간 판매 현황 및 관리</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          새로고침
        </Button>
      </div>

      {/* 알림 */}
      {dashboardData.alerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {dashboardData.alerts.map((alert, index) => (
            <Alert key={index} variant={getAlertVariant(alert.level)}>
              {getAlertIcon(alert.type)}
              <AlertTitle className="ml-2">{alert.message}</AlertTitle>
            </Alert>
          ))}
        </div>
      )}

      {/* 오늘의 현황 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">오늘 주문</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.today.orders.total}건</div>
            <div className="text-xs text-muted-foreground mt-1">
              신규 {dashboardData.today.orders.new} | 
              처리중 {dashboardData.today.orders.processing} | 
              배송 {dashboardData.today.orders.shipped}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">오늘 매출</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(dashboardData.today.sales.amount)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              주문 {dashboardData.today.sales.count}건
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">고객 문의</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.today.cs.total}건</div>
            <div className="text-xs text-muted-foreground mt-1">
              대기 {dashboardData.today.cs.pending} | 답변 {dashboardData.today.cs.answered}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">반품 요청</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.today.returns.requested}건</div>
            <div className="text-xs text-muted-foreground mt-1">
              승인 {dashboardData.today.returns.approved} | 거절 {dashboardData.today.returns.rejected}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 탭 컨텐츠 */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="orders">주문 관리</TabsTrigger>
          <TabsTrigger value="products">상품 관리</TabsTrigger>
          <TabsTrigger value="shipping">배송 관리</TabsTrigger>
          <TabsTrigger value="cs">고객 서비스</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* 최근 통계 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>최근 7일 실적</CardTitle>
                <CardDescription>주간 판매 현황</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">총 주문</span>
                  <span className="font-medium">{dashboardData.recent.orders.total}건</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">일평균 주문</span>
                  <span className="font-medium">{dashboardData.recent.orders.daily_avg.toFixed(1)}건</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">총 매출</span>
                  <span className="font-medium">{formatCurrency(dashboardData.recent.sales.total_amount)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">일평균 매출</span>
                  <span className="font-medium">{formatCurrency(dashboardData.recent.sales.daily_avg)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>상품 현황</CardTitle>
                <CardDescription>등록 상품 상태</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">판매중</span>
                  <Badge variant="default">{dashboardData.recent.products.active}개</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">품절</span>
                  <Badge variant="secondary">{dashboardData.recent.products.soldout}개</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">판매중지</span>
                  <Badge variant="destructive">{dashboardData.recent.products.suspended}개</Badge>
                </div>
                <Progress 
                  value={(dashboardData.recent.products.active / 
                    (dashboardData.recent.products.active + 
                     dashboardData.recent.products.soldout + 
                     dashboardData.recent.products.suspended)) * 100} 
                  className="mt-2"
                />
              </CardContent>
            </Card>
          </div>

          {/* 성과 지표 */}
          {performanceData && (
            <Card>
              <CardHeader>
                <CardTitle>성과 지표</CardTitle>
                <CardDescription>최근 30일 기준</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">평균 주문 금액</p>
                  <p className="text-2xl font-bold">{formatCurrency(performanceData.average_order_value)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">주문 처리율</p>
                  <p className="text-2xl font-bold">{performanceData.fulfillment_rate}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">반품율</p>
                  <p className="text-2xl font-bold">{performanceData.return_rate}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">고객 만족도</p>
                  <p className="text-2xl font-bold">{performanceData.customer_satisfaction}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">CS 응답 시간</p>
                  <p className="text-2xl font-bold">{performanceData.response_time}시간</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">전환율</p>
                  <p className="text-2xl font-bold">{performanceData.conversion_rate}%</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="orders">
          <Card>
            <CardHeader>
              <CardTitle>주문 관리</CardTitle>
              <CardDescription>주문 처리 및 상태 관리</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button className="w-full">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  신규 주문 확인 ({dashboardData.today.orders.new}건)
                </Button>
                <Button variant="outline" className="w-full">
                  <Truck className="mr-2 h-4 w-4" />
                  배송 준비 ({dashboardData.today.orders.processing}건)
                </Button>
                <Button variant="outline" className="w-full">
                  <BarChart className="mr-2 h-4 w-4" />
                  주문 통계 상세보기
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="products">
          <Card>
            <CardHeader>
              <CardTitle>상품 관리</CardTitle>
              <CardDescription>상품 등록 및 재고 관리</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button className="w-full">
                  <Package className="mr-2 h-4 w-4" />
                  품절 상품 확인 ({dashboardData.recent.products.soldout}개)
                </Button>
                <Button variant="outline" className="w-full">
                  상품 일괄 수정
                </Button>
                <Button variant="outline" className="w-full">
                  가격 일괄 변경
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="shipping">
          <Card>
            <CardHeader>
              <CardTitle>배송 관리</CardTitle>
              <CardDescription>송장 등록 및 배송 추적</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button className="w-full">
                  <Truck className="mr-2 h-4 w-4" />
                  송장 일괄 등록
                </Button>
                <Button variant="outline" className="w-full">
                  배송 라벨 출력
                </Button>
                <Button variant="outline" className="w-full">
                  배송 현황 조회
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cs">
          <Card>
            <CardHeader>
              <CardTitle>고객 서비스</CardTitle>
              <CardDescription>고객 문의 및 클레임 처리</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button className="w-full">
                  <Users className="mr-2 h-4 w-4" />
                  미답변 문의 확인 ({dashboardData.today.cs.pending}건)
                </Button>
                <Button variant="outline" className="w-full">
                  반품 요청 처리 ({dashboardData.today.returns.requested}건)
                </Button>
                <Button variant="outline" className="w-full">
                  자동 응답 설정
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}