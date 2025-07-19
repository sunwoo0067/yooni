'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Search, Filter, Download, RefreshCw, Truck, Clock, 
  CheckCircle, XCircle, Package, FileText, ChevronDown
} from 'lucide-react';
import { DatePickerWithRange } from '@/components/ui/date-picker-with-range';
import { useToast } from '@/hooks/use-toast';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface OrderItem {
  id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  status: string;
}

interface Order {
  id: string;
  market_order_id: string;
  market: string;
  order_date: string;
  buyer_name: string;
  buyer_email: string;
  buyer_phone: string;
  total_price: number;
  status: string;
  payment_method: string;
  shipping_address: string;
  items: OrderItem[];
  tracking_number?: string;
  tracking_company?: string;
}

export default function ERPOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [expandedOrders, setExpandedOrders] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('all');
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    to: new Date()
  });
  const { toast } = useToast();

  useEffect(() => {
    fetchOrders();
  }, [activeTab, dateRange]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      // 실제 API 호출
      const params = new URLSearchParams({
        status: activeTab === 'all' ? '' : activeTab,
        from: dateRange.from.toISOString(),
        to: dateRange.to.toISOString(),
        search: searchTerm
      });
      
      const response = await fetch(`/api/erp/orders?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setOrders(data.data);
      }
    } catch (error) {
      // 모의 데이터
      setOrders(getMockOrders());
    } finally {
      setLoading(false);
    }
  };

  const getMockOrders = (): Order[] => {
    return [
      {
        id: '1',
        market_order_id: 'CP2024011500001',
        market: 'coupang',
        order_date: '2024-01-15T10:30:00',
        buyer_name: '김철수',
        buyer_email: 'kim@example.com',
        buyer_phone: '010-1234-5678',
        total_price: 438000,
        status: 'pending',
        payment_method: '신용카드',
        shipping_address: '서울특별시 강남구 테헤란로 123',
        items: [
          {
            id: '1-1',
            product_name: '삼성 갤럭시 버즈2 프로',
            quantity: 2,
            unit_price: 219000,
            total_price: 438000,
            status: 'pending'
          }
        ]
      },
      {
        id: '2',
        market_order_id: 'NV2024011500002',
        market: 'naver',
        order_date: '2024-01-15T11:45:00',
        buyer_name: '이영희',
        buyer_email: 'lee@example.com',
        buyer_phone: '010-2345-6789',
        total_price: 1290000,
        status: 'confirmed',
        payment_method: '네이버페이',
        shipping_address: '경기도 성남시 분당구 판교로 234',
        items: [
          {
            id: '2-1',
            product_name: 'LG 스탠바이미 27인치',
            quantity: 1,
            unit_price: 1290000,
            total_price: 1290000,
            status: 'confirmed'
          }
        ],
        tracking_number: '1234567890',
        tracking_company: 'CJ대한통운'
      },
      {
        id: '3',
        market_order_id: 'EL2024011500003',
        market: '11st',
        order_date: '2024-01-15T09:00:00',
        buyer_name: '박민수',
        buyer_email: 'park@example.com',
        buyer_phone: '010-3456-7890',
        total_price: 689000,
        status: 'shipped',
        payment_method: '무통장입금',
        shipping_address: '부산광역시 해운대구 마린시티로 345',
        items: [
          {
            id: '3-1',
            product_name: '다이슨 에어랩 컴플리트',
            quantity: 1,
            unit_price: 689000,
            total_price: 689000,
            status: 'shipped'
          }
        ],
        tracking_number: '9876543210',
        tracking_company: '롯데택배'
      }
    ];
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: '주문확인', variant: 'outline' as const, icon: Clock },
      confirmed: { label: '확인완료', variant: 'default' as const, icon: CheckCircle },
      processing: { label: '처리중', variant: 'secondary' as const, icon: Package },
      shipped: { label: '배송중', variant: 'default' as const, icon: Truck },
      delivered: { label: '배송완료', variant: 'default' as const, icon: CheckCircle },
      cancelled: { label: '취소', variant: 'destructive' as const, icon: XCircle },
      returned: { label: '반품', variant: 'destructive' as const, icon: XCircle }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const getMarketBadge = (market: string) => {
    const colors: Record<string, string> = {
      coupang: 'bg-yellow-100 text-yellow-800',
      naver: 'bg-green-100 text-green-800',
      '11st': 'bg-red-100 text-red-800',
      ownerclan: 'bg-blue-100 text-blue-800'
    };
    
    return (
      <Badge className={colors[market] || 'bg-gray-100 text-gray-800'}>
        {market.toUpperCase()}
      </Badge>
    );
  };

  const handleBulkAction = async (action: string) => {
    if (selectedOrders.length === 0) {
      toast({
        title: '알림',
        description: '선택된 주문이 없습니다.',
        variant: 'destructive',
      });
      return;
    }

    toast({
      title: '처리 중',
      description: `${selectedOrders.length}개 주문을 ${action} 처리 중입니다.`,
    });
  };

  const toggleOrderExpansion = (orderId: string) => {
    setExpandedOrders(prev =>
      prev.includes(orderId)
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    );
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(value);
  };

  const orderCounts = {
    all: orders.length,
    pending: orders.filter(o => o.status === 'pending').length,
    confirmed: orders.filter(o => o.status === 'confirmed').length,
    processing: orders.filter(o => o.status === 'processing').length,
    shipped: orders.filter(o => o.status === 'shipped').length,
    completed: orders.filter(o => o.status === 'delivered').length,
    cancelled: orders.filter(o => ['cancelled', 'returned'].includes(o.status)).length
  };

  return (
    <div className="container mx-auto py-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">통합 주문 관리</h1>
          <p className="text-muted-foreground">전체 마켓플레이스 주문 처리 및 관리</p>
        </div>
        <div className="flex gap-2">
          <DatePickerWithRange 
            date={dateRange} 
            onSelect={(date) => {
              if (date) {
                setDateRange(date as { from: Date; to: Date });
              }
            }} 
          />
          <Button variant="outline" onClick={fetchOrders}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            내보내기
          </Button>
        </div>
      </div>

      {/* 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-7 mb-6">
          <TabsTrigger value="all">
            전체 ({orderCounts.all})
          </TabsTrigger>
          <TabsTrigger value="pending">
            주문확인 ({orderCounts.pending})
          </TabsTrigger>
          <TabsTrigger value="confirmed">
            확인완료 ({orderCounts.confirmed})
          </TabsTrigger>
          <TabsTrigger value="processing">
            처리중 ({orderCounts.processing})
          </TabsTrigger>
          <TabsTrigger value="shipped">
            배송중 ({orderCounts.shipped})
          </TabsTrigger>
          <TabsTrigger value="completed">
            완료 ({orderCounts.completed})
          </TabsTrigger>
          <TabsTrigger value="cancelled">
            취소/반품 ({orderCounts.cancelled})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {/* 검색 및 필터 */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Label htmlFor="search" className="sr-only">검색</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      id="search"
                      placeholder="주문번호, 구매자명, 상품명으로 검색..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && fetchOrders()}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Button onClick={fetchOrders}>
                  <Filter className="mr-2 h-4 w-4" />
                  검색
                </Button>
              </div>
              
              {selectedOrders.length > 0 && (
                <div className="mt-4 flex items-center gap-4">
                  <span className="text-sm text-muted-foreground">
                    {selectedOrders.length}개 선택됨
                  </span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleBulkAction('confirm')}>
                      주문 확인
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleBulkAction('print')}>
                      송장 출력
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleBulkAction('ship')}>
                      일괄 발송
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 주문 목록 */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox />
                    </TableHead>
                    <TableHead>주문번호</TableHead>
                    <TableHead>마켓</TableHead>
                    <TableHead>주문일시</TableHead>
                    <TableHead>구매자</TableHead>
                    <TableHead className="text-right">금액</TableHead>
                    <TableHead>결제</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>배송</TableHead>
                    <TableHead className="w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={10} className="text-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                        <p className="text-muted-foreground">로딩 중...</p>
                      </TableCell>
                    </TableRow>
                  ) : orders.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={10} className="text-center py-8">
                        <Package className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">주문이 없습니다</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    orders.map((order) => (
                      <>
                        <TableRow key={order.id}>
                          <TableCell>
                            <Checkbox
                              checked={selectedOrders.includes(order.id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedOrders([...selectedOrders, order.id]);
                                } else {
                                  setSelectedOrders(selectedOrders.filter(id => id !== order.id));
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {order.market_order_id}
                          </TableCell>
                          <TableCell>{getMarketBadge(order.market)}</TableCell>
                          <TableCell>
                            {new Date(order.order_date).toLocaleString('ko-KR')}
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{order.buyer_name}</div>
                              <div className="text-sm text-muted-foreground">{order.buyer_phone}</div>
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(order.total_price)}
                          </TableCell>
                          <TableCell>{order.payment_method}</TableCell>
                          <TableCell>{getStatusBadge(order.status)}</TableCell>
                          <TableCell>
                            {order.tracking_number ? (
                              <div className="text-sm">
                                <div>{order.tracking_company}</div>
                                <div className="font-mono">{order.tracking_number}</div>
                              </div>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Collapsible>
                              <CollapsibleTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleOrderExpansion(order.id)}
                                >
                                  <ChevronDown className={`h-4 w-4 transition-transform ${expandedOrders.includes(order.id) ? 'rotate-180' : ''}`} />
                                </Button>
                              </CollapsibleTrigger>
                            </Collapsible>
                          </TableCell>
                        </TableRow>
                        
                        {expandedOrders.includes(order.id) && (
                          <TableRow>
                            <TableCell colSpan={10} className="bg-muted/50">
                              <div className="p-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                  <div>
                                    <h4 className="font-medium mb-2">배송 정보</h4>
                                    <p className="text-sm">{order.shipping_address}</p>
                                  </div>
                                  <div>
                                    <h4 className="font-medium mb-2">구매자 정보</h4>
                                    <p className="text-sm">{order.buyer_email}</p>
                                  </div>
                                </div>
                                
                                <h4 className="font-medium mb-2">주문 상품</h4>
                                <Table>
                                  <TableHeader>
                                    <TableRow>
                                      <TableHead>상품명</TableHead>
                                      <TableHead className="text-right">수량</TableHead>
                                      <TableHead className="text-right">단가</TableHead>
                                      <TableHead className="text-right">금액</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {order.items.map((item) => (
                                      <TableRow key={item.id}>
                                        <TableCell>{item.product_name}</TableCell>
                                        <TableCell className="text-right">{item.quantity}</TableCell>
                                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                                        <TableCell className="text-right">{formatCurrency(item.total_price)}</TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                                
                                <div className="flex gap-2 mt-4">
                                  <Button size="sm">주문 상세</Button>
                                  <Button size="sm" variant="outline">
                                    <FileText className="mr-2 h-4 w-4" />
                                    거래명세서
                                  </Button>
                                  {order.status === 'pending' && (
                                    <Button size="sm" variant="outline">주문 확인</Button>
                                  )}
                                  {order.status === 'confirmed' && (
                                    <Button size="sm" variant="outline">
                                      <Truck className="mr-2 h-4 w-4" />
                                      송장 등록
                                    </Button>
                                  )}
                                </div>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}