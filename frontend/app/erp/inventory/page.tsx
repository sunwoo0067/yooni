'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  Search, Filter, Download, Upload, RefreshCw, Package, 
  AlertTriangle, TrendingDown, Edit, MoreVertical, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface InventoryItem {
  id: string;
  market_product_id: string;
  product_name: string;
  brand: string;
  category_name: string;
  market: string;
  sku: string;
  barcode: string;
  stock_quantity: number;
  safety_stock: number;
  sale_price: number;
  cost_price: number;
  status: string;
  last_updated: string;
  location: string;
}

export default function ERPInventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMarket, setFilterMarket] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { toast } = useToast();

  useEffect(() => {
    fetchInventory();
  }, [currentPage, filterMarket, filterStatus]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      // 실제 API 호출
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20',
        market: filterMarket,
        status: filterStatus,
        search: searchTerm
      });
      
      const response = await fetch(`/api/erp/inventory?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setInventory(data.data.items);
        setTotalPages(data.data.totalPages);
      }
    } catch (error) {
      // 모의 데이터
      setInventory(getMockInventory());
      setTotalPages(5);
    } finally {
      setLoading(false);
    }
  };

  const getMockInventory = (): InventoryItem[] => {
    return [
      {
        id: '1',
        market_product_id: 'CP123456',
        product_name: '삼성 갤럭시 버즈2 프로',
        brand: 'Samsung',
        category_name: '이어폰',
        market: 'coupang',
        sku: 'SKU-001',
        barcode: '8801234567890',
        stock_quantity: 45,
        safety_stock: 20,
        sale_price: 219000,
        cost_price: 150000,
        status: 'active',
        last_updated: '2024-01-15 14:30:00',
        location: 'A-01-03'
      },
      {
        id: '2',
        market_product_id: 'NV789012',
        product_name: 'LG 스탠바이미 27인치',
        brand: 'LG',
        category_name: '모니터',
        market: 'naver',
        sku: 'SKU-002',
        barcode: '8802345678901',
        stock_quantity: 3,
        safety_stock: 10,
        sale_price: 1290000,
        cost_price: 950000,
        status: 'low_stock',
        last_updated: '2024-01-15 13:45:00',
        location: 'B-02-15'
      },
      {
        id: '3',
        market_product_id: 'EL345678',
        product_name: '다이슨 에어랩 컴플리트',
        brand: 'Dyson',
        category_name: '헤어드라이어',
        market: '11st',
        sku: 'SKU-003',
        barcode: '8803456789012',
        stock_quantity: 0,
        safety_stock: 5,
        sale_price: 689000,
        cost_price: 520000,
        status: 'out_of_stock',
        last_updated: '2024-01-15 12:00:00',
        location: 'C-03-08'
      }
    ];
  };

  const handleSearch = () => {
    setCurrentPage(1);
    fetchInventory();
  };

  const handleBulkUpdate = async (action: string) => {
    if (selectedItems.length === 0) {
      toast({
        title: '알림',
        description: '선택된 상품이 없습니다.',
        variant: 'destructive',
      });
      return;
    }

    try {
      // 실제 API 호출
      toast({
        title: '처리 중',
        description: `${selectedItems.length}개 상품을 ${action} 처리 중입니다.`,
      });
    } catch (error) {
      toast({
        title: '오류',
        description: '처리 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  };

  const handleExport = () => {
    toast({
      title: '내보내기',
      description: '재고 데이터를 다운로드합니다.',
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(value);
  };

  const getStatusBadge = (status: string, quantity: number, safetyStock: number) => {
    if (quantity === 0) {
      return <Badge variant="destructive">품절</Badge>;
    } else if (quantity <= safetyStock) {
      return <Badge variant="outline" className="border-orange-500 text-orange-600">재고부족</Badge>;
    } else {
      return <Badge variant="default">정상</Badge>;
    }
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

  const toggleSelectAll = () => {
    if (selectedItems.length === inventory.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(inventory.map(item => item.id));
    }
  };

  const toggleSelectItem = (id: string) => {
    setSelectedItems(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    );
  };

  return (
    <div className="container mx-auto py-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">통합 재고 관리</h1>
          <p className="text-muted-foreground">전체 마켓플레이스 재고 현황 및 관리</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchInventory}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            가져오기
          </Button>
          <Button onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            내보내기
          </Button>
        </div>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">총 상품 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">15,234</div>
            <p className="text-xs text-muted-foreground">활성 상품</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">총 재고 가치</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₩4.5B</div>
            <p className="text-xs text-muted-foreground">원가 기준</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-orange-600">재고 부족</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">234</div>
            <p className="text-xs text-muted-foreground">안전재고 미달</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-600">품절</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">45</div>
            <p className="text-xs text-muted-foreground">즉시 보충 필요</p>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Label htmlFor="search" className="sr-only">검색</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="search"
                  placeholder="상품명, SKU, 바코드로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select 
              value={filterMarket} 
              onChange={(e) => setFilterMarket(e.target.value)}
              className="w-[180px]"
            >
              <option value="all">전체 마켓</option>
              <option value="coupang">쿠팡</option>
              <option value="naver">네이버</option>
              <option value="11st">11번가</option>
              <option value="ownerclan">오너클랜</option>
            </Select>
            
            <Select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-[180px]"
            >
              <option value="all">전체 상태</option>
              <option value="active">정상</option>
              <option value="low_stock">재고부족</option>
              <option value="out_of_stock">품절</option>
            </Select>
            
            <Button onClick={handleSearch}>
              <Filter className="mr-2 h-4 w-4" />
              필터 적용
            </Button>
          </div>
          
          {selectedItems.length > 0 && (
            <div className="mt-4 flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {selectedItems.length}개 선택됨
              </span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleBulkUpdate('update_stock')}>
                  재고 수정
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleBulkUpdate('update_price')}>
                  가격 수정
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleBulkUpdate('deactivate')}>
                  비활성화
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 재고 테이블 */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedItems.length === inventory.length && inventory.length > 0}
                    onChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>상품명</TableHead>
                <TableHead>마켓</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead className="text-right">재고</TableHead>
                <TableHead className="text-right">안전재고</TableHead>
                <TableHead className="text-right">판매가</TableHead>
                <TableHead className="text-right">원가</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>위치</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                    <p className="text-muted-foreground">로딩 중...</p>
                  </TableCell>
                </TableRow>
              ) : inventory.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8">
                    <Package className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-muted-foreground">검색 결과가 없습니다</p>
                  </TableCell>
                </TableRow>
              ) : (
                inventory.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedItems.includes(item.id)}
                        onChange={() => toggleSelectItem(item.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{item.product_name}</div>
                        <div className="text-sm text-muted-foreground">{item.brand}</div>
                      </div>
                    </TableCell>
                    <TableCell>{getMarketBadge(item.market)}</TableCell>
                    <TableCell className="font-mono text-sm">{item.sku}</TableCell>
                    <TableCell className="text-right">
                      <div className={item.stock_quantity <= item.safety_stock ? 'text-orange-600 font-medium' : ''}>
                        {item.stock_quantity}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{item.safety_stock}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.sale_price)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.cost_price)}</TableCell>
                    <TableCell>{getStatusBadge(item.status, item.stock_quantity, item.safety_stock)}</TableCell>
                    <TableCell className="font-mono text-sm">{item.location}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuLabel>작업</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Edit className="mr-2 h-4 w-4" />
                            재고 수정
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            가격 변경
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            이동 기록
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            비활성화
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 페이지네이션 */}
      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-muted-foreground">
          전체 {totalPages * 20}개 중 {(currentPage - 1) * 20 + 1}-{Math.min(currentPage * 20, totalPages * 20)}개 표시
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            이전
          </Button>
          <div className="flex items-center gap-1">
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              const pageNum = i + 1;
              return (
                <Button
                  key={pageNum}
                  variant={currentPage === pageNum ? "default" : "outline"}
                  size="sm"
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            다음
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}