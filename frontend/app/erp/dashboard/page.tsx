'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  Database, Package, ShoppingCart, Users, TrendingUp, 
  FileSpreadsheet, BarChart3, PieChart, Activity, Download,
  Upload, RefreshCw, Settings, Search, Filter
} from 'lucide-react';
import { DatePickerWithRange } from '@/components/ui/date-picker-with-range';
import { useToast } from '@/hooks/use-toast';

interface ERPStats {
  database: {
    total_size: string;
    table_count: number;
    record_counts: {
      products: number;
      orders: number;
      customers: number;
      suppliers: number;
    };
    last_backup: string;
  };
  inventory: {
    total_products: number;
    total_value: number;
    low_stock: number;
    out_of_stock: number;
    by_market: Record<string, number>;
  };
  sales: {
    today: number;
    this_week: number;
    this_month: number;
    growth_rate: number;
    by_market: Record<string, number>;
  };
  operations: {
    pending_orders: number;
    processing_orders: number;
    pending_shipments: number;
    returns_to_process: number;
  };
}

export default function ERPDashboardPage() {
  const [stats, setStats] = useState<ERPStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    to: new Date()
  });
  const { toast } = useToast();

  useEffect(() => {
    fetchERPStats();
  }, []);

  const fetchERPStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/erp/stats');
      const data = await response.json();
      
      if (data.success) {
        setStats(data.data);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: 'ERP 통계를 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('ko-KR').format(value);
  };

  // 모의 데이터 (실제 API 구현 전)
  const mockStats: ERPStats = {
    database: {
      total_size: '2.3 GB',
      table_count: 24,
      record_counts: {
        products: 156234,
        orders: 45678,
        customers: 12345,
        suppliers: 89
      },
      last_backup: '2024-01-15 03:00:00'
    },
    inventory: {
      total_products: 156234,
      total_value: 4567890000,
      low_stock: 234,
      out_of_stock: 45,
      by_market: {
        'coupang': 45678,
        'naver': 34567,
        'eleven': 23456,
        'ownerclan': 52533
      }
    },
    sales: {
      today: 3456789,
      this_week: 24567890,
      this_month: 98765432,
      growth_rate: 12.5,
      by_market: {
        'coupang': 45678900,
        'naver': 23456780,
        'eleven': 12345670,
        'ownerclan': 16985082
      }
    },
    operations: {
      pending_orders: 234,
      processing_orders: 567,
      pending_shipments: 189,
      returns_to_process: 45
    }
  };

  const currentStats = stats || mockStats;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Database className="h-8 w-8 animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">ERP 데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">ERP 통합 대시보드</h1>
          <p className="text-muted-foreground">전체 비즈니스 데이터 관리 및 분석</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchERPStats}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            보고서 다운로드
          </Button>
        </div>
      </div>

      {/* 데이터베이스 상태 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">데이터베이스</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentStats.database.total_size}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {currentStats.database.table_count}개 테이블
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">총 상품 수</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(currentStats.database.record_counts.products)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              재고 가치: {formatCurrency(currentStats.inventory.total_value)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">총 주문 수</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(currentStats.database.record_counts.orders)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              처리 대기: {currentStats.operations.pending_orders}건
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">고객 수</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(currentStats.database.record_counts.customers)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              공급사: {currentStats.database.record_counts.suppliers}개
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 메인 탭 */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="inventory">재고 관리</TabsTrigger>
          <TabsTrigger value="sales">매출 분석</TabsTrigger>
          <TabsTrigger value="operations">운영 현황</TabsTrigger>
          <TabsTrigger value="reports">보고서</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 마켓별 상품 분포 */}
            <Card>
              <CardHeader>
                <CardTitle>마켓별 상품 분포</CardTitle>
                <CardDescription>등록된 상품 수 기준</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(currentStats.inventory.by_market).map(([market, count]) => (
                    <div key={market} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{market.toUpperCase()}</Badge>
                        <span className="text-sm">{formatNumber(count)}개</span>
                      </div>
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${(count / currentStats.inventory.total_products) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 매출 현황 */}
            <Card>
              <CardHeader>
                <CardTitle>매출 현황</CardTitle>
                <CardDescription>기간별 매출 추이</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">오늘</span>
                    <span className="font-medium">{formatCurrency(currentStats.sales.today)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">이번 주</span>
                    <span className="font-medium">{formatCurrency(currentStats.sales.this_week)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">이번 달</span>
                    <span className="font-medium">{formatCurrency(currentStats.sales.this_month)}</span>
                  </div>
                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">성장률</span>
                      <Badge variant={currentStats.sales.growth_rate > 0 ? "default" : "destructive"}>
                        {currentStats.sales.growth_rate > 0 ? '+' : ''}{currentStats.sales.growth_rate}%
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 운영 현황 요약 */}
          <Card>
            <CardHeader>
              <CardTitle>운영 현황</CardTitle>
              <CardDescription>처리가 필요한 작업</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {currentStats.operations.pending_orders}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">주문 확인 대기</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {currentStats.operations.processing_orders}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">처리 중</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {currentStats.operations.pending_shipments}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">배송 대기</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {currentStats.operations.returns_to_process}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">반품 처리</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="inventory" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>재고 관리</CardTitle>
                  <CardDescription>상품 재고 현황 및 관리</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Upload className="mr-2 h-4 w-4" />
                    재고 업로드
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    재고 다운로드
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">총 재고 가치</p>
                      <p className="text-2xl font-bold mt-1">{formatCurrency(currentStats.inventory.total_value)}</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">재고 부족</p>
                      <p className="text-2xl font-bold text-orange-600 mt-1">{currentStats.inventory.low_stock}개</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">품절</p>
                      <p className="text-2xl font-bold text-red-600 mt-1">{currentStats.inventory.out_of_stock}개</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input placeholder="상품명, SKU, 바코드 검색..." className="flex-1" />
                  <Button variant="outline">
                    <Search className="mr-2 h-4 w-4" />
                    검색
                  </Button>
                  <Button variant="outline">
                    <Filter className="mr-2 h-4 w-4" />
                    필터
                  </Button>
                </div>

                <div className="border rounded-lg p-4">
                  <p className="text-sm text-muted-foreground text-center">
                    재고 데이터 테이블이 여기에 표시됩니다
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sales" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>매출 분석</CardTitle>
                  <CardDescription>기간별, 마켓별 매출 상세 분석</CardDescription>
                </div>
                <DatePickerWithRange 
                  date={dateRange} 
                  onSelect={(date) => {
                    if (date) {
                      setDateRange(date as { from: Date; to: Date });
                    }
                  }} 
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 마켓별 매출 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">마켓별 매출 비중</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(currentStats.sales.by_market).map(([market, amount]) => {
                        const percentage = (amount / Object.values(currentStats.sales.by_market).reduce((a, b) => a + b, 0)) * 100;
                        return (
                          <div key={market}>
                            <div className="flex justify-between text-sm mb-1">
                              <span>{market.toUpperCase()}</span>
                              <span>{formatCurrency(amount)} ({percentage.toFixed(1)}%)</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* 매출 추이 차트 영역 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">매출 추이</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 flex items-center justify-center border rounded">
                      <BarChart3 className="h-8 w-8 text-muted-foreground" />
                      <p className="ml-2 text-sm text-muted-foreground">차트가 여기에 표시됩니다</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="operations" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>주문 처리 현황</CardTitle>
                <CardDescription>실시간 주문 상태</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Button className="w-full justify-between" variant="outline">
                    <span>신규 주문 확인</span>
                    <Badge>{currentStats.operations.pending_orders}</Badge>
                  </Button>
                  <Button className="w-full justify-between" variant="outline">
                    <span>처리 중인 주문</span>
                    <Badge variant="secondary">{currentStats.operations.processing_orders}</Badge>
                  </Button>
                  <Button className="w-full justify-between" variant="outline">
                    <span>배송 준비</span>
                    <Badge variant="secondary">{currentStats.operations.pending_shipments}</Badge>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>데이터 관리</CardTitle>
                <CardDescription>일괄 처리 및 동기화</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Button className="w-full" variant="outline">
                    <Database className="mr-2 h-4 w-4" />
                    전체 데이터 동기화
                  </Button>
                  <Button className="w-full" variant="outline">
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    대량 데이터 가져오기
                  </Button>
                  <Button className="w-full" variant="outline">
                    <Settings className="mr-2 h-4 w-4" />
                    자동화 규칙 설정
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>보고서 생성</CardTitle>
              <CardDescription>맞춤형 비즈니스 보고서</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <PieChart className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                      <h3 className="font-medium">매출 분석 보고서</h3>
                      <p className="text-sm text-muted-foreground mt-1">기간별, 상품별 매출 분석</p>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <Activity className="h-8 w-8 mx-auto mb-2 text-green-600" />
                      <h3 className="font-medium">재고 현황 보고서</h3>
                      <p className="text-sm text-muted-foreground mt-1">재고 회전율 및 적정 재고</p>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <TrendingUp className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                      <h3 className="font-medium">성과 분석 보고서</h3>
                      <p className="text-sm text-muted-foreground mt-1">KPI 및 성장 지표 분석</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 하단 정보 */}
      <div className="mt-6 flex justify-between items-center text-sm text-muted-foreground">
        <span>마지막 백업: {currentStats.database.last_backup}</span>
        <span>데이터베이스 크기: {currentStats.database.total_size}</span>
      </div>
    </div>
  );
}