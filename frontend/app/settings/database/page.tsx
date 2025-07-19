'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Database, HardDrive, Activity, AlertTriangle, CheckCircle,
  RefreshCw, Trash2, Plus, Settings, BarChart3, Info
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';

interface PartitionInfo {
  parent_table: string;
  partition_count: number;
  total_rows: number;
  total_size: string;
  partitions: Array<{
    name: string;
    size: string;
    rows: number;
    dead_rows: number;
    date: string | null;
  }>;
}

interface DatabaseStats {
  database_size: string;
  table_count: number;
  connection_count: number;
  cache_hit_ratio: number;
  transaction_count: number;
  deadlock_count: number;
  slow_query_count: number;
}

export default function DatabaseSettingsPage() {
  const [partitions, setPartitions] = useState<PartitionInfo[]>([]);
  const [dbStats, setDbStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('partitions');
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      if (activeTab === 'partitions') {
        const response = await fetch('/api/settings/database/partitions');
        const data = await response.json();
        if (data.success) {
          setPartitions(data.data);
        }
      } else if (activeTab === 'stats') {
        const response = await fetch('/api/settings/database/stats');
        const data = await response.json();
        if (data.success) {
          setDbStats(data.data);
        }
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '데이터베이스 정보를 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePartitions = async (tableName: string) => {
    try {
      const response = await fetch('/api/settings/database/partitions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_name: tableName, months_ahead: 3 }),
      });

      if (response.ok) {
        toast({
          title: '성공',
          description: '파티션이 생성되었습니다.',
        });
        fetchData();
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '파티션 생성에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const handleDropOldPartitions = async (tableName: string) => {
    if (!confirm('정말로 오래된 파티션을 삭제하시겠습니까?')) {
      return;
    }

    try {
      const response = await fetch('/api/settings/database/partitions/drop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_name: tableName, retention_months: 12 }),
      });

      if (response.ok) {
        toast({
          title: '성공',
          description: '오래된 파티션이 삭제되었습니다.',
        });
        fetchData();
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '파티션 삭제에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const handleAnalyze = async () => {
    try {
      const response = await fetch('/api/settings/database/analyze', {
        method: 'POST',
      });

      if (response.ok) {
        toast({
          title: '성공',
          description: '통계 업데이트가 완료되었습니다.',
        });
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '통계 업데이트에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
    });
  };

  const getDeadRowRatio = (rows: number, deadRows: number) => {
    if (rows === 0) return 0;
    return (deadRows / rows) * 100;
  };

  return (
    <div className="container mx-auto py-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">데이터베이스 관리</h1>
          <p className="text-muted-foreground">파티셔닝 및 성능 모니터링</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button onClick={handleAnalyze}>
            <Activity className="mr-2 h-4 w-4" />
            통계 업데이트
          </Button>
        </div>
      </div>

      {/* 알림 */}
      <Alert className="mb-6">
        <Info className="h-4 w-4" />
        <AlertTitle>파티셔닝 정보</AlertTitle>
        <AlertDescription>
          대용량 데이터 처리를 위해 주요 테이블은 월별로 파티셔닝되어 있습니다. 
          500만 레코드 이상의 데이터도 효율적으로 관리할 수 있습니다.
        </AlertDescription>
      </Alert>

      {/* 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="partitions">파티션 관리</TabsTrigger>
          <TabsTrigger value="stats">성능 통계</TabsTrigger>
          <TabsTrigger value="maintenance">유지보수</TabsTrigger>
        </TabsList>

        <TabsContent value="partitions" className="space-y-4">
          {loading ? (
            <Card>
              <CardContent className="py-8">
                <div className="text-center">
                  <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">로딩 중...</p>
                </div>
              </CardContent>
            </Card>
          ) : partitions.length === 0 ? (
            <Card>
              <CardContent className="py-8">
                <div className="text-center">
                  <Database className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-muted-foreground">파티션된 테이블이 없습니다</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            partitions.map((tableInfo) => (
              <Card key={tableInfo.parent_table}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{tableInfo.parent_table}</CardTitle>
                      <CardDescription>
                        {tableInfo.partition_count}개 파티션 | 
                        {tableInfo.total_rows.toLocaleString()}개 레코드 | 
                        {tableInfo.total_size}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleCreatePartitions(tableInfo.parent_table)}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        파티션 추가
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDropOldPartitions(tableInfo.parent_table)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        오래된 파티션 정리
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>파티션명</TableHead>
                        <TableHead>날짜</TableHead>
                        <TableHead className="text-right">레코드 수</TableHead>
                        <TableHead className="text-right">크기</TableHead>
                        <TableHead>Dead Rows</TableHead>
                        <TableHead>상태</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tableInfo.partitions
                        .sort((a, b) => (b.name > a.name ? 1 : -1))
                        .map((partition) => {
                          const deadRowRatio = getDeadRowRatio(partition.rows, partition.dead_rows);
                          
                          return (
                            <TableRow key={partition.name}>
                              <TableCell className="font-mono text-sm">
                                {partition.name}
                              </TableCell>
                              <TableCell>{formatDate(partition.date)}</TableCell>
                              <TableCell className="text-right">
                                {partition.rows.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-right">{partition.size}</TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Progress value={deadRowRatio} className="w-20" />
                                  <span className="text-sm text-muted-foreground">
                                    {deadRowRatio.toFixed(1)}%
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell>
                                {deadRowRatio > 20 ? (
                                  <Badge variant="outline" className="text-orange-600">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    VACUUM 필요
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-green-600">
                                    <CheckCircle className="w-3 h-3 mr-1" />
                                    정상
                                  </Badge>
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          {dbStats && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">데이터베이스 크기</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dbStats.database_size}</div>
                    <p className="text-xs text-muted-foreground">{dbStats.table_count}개 테이블</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">캐시 적중률</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dbStats.cache_hit_ratio.toFixed(1)}%</div>
                    <Progress value={dbStats.cache_hit_ratio} className="mt-2" />
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">활성 연결</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dbStats.connection_count}</div>
                    <p className="text-xs text-muted-foreground">현재 연결 수</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>성능 지표</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>트랜잭션 수</span>
                      <span className="font-medium">{dbStats.transaction_count.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>데드락 발생</span>
                      <Badge variant={dbStats.deadlock_count > 0 ? "destructive" : "default"}>
                        {dbStats.deadlock_count}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>느린 쿼리</span>
                      <Badge variant={dbStats.slow_query_count > 10 ? "destructive" : "default"}>
                        {dbStats.slow_query_count}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="maintenance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>유지보수 작업</CardTitle>
              <CardDescription>데이터베이스 최적화 및 정리 작업</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button className="w-full justify-start" variant="outline">
                <Database className="mr-2 h-4 w-4" />
                VACUUM 실행
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <BarChart3 className="mr-2 h-4 w-4" />
                인덱스 재구성
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Settings className="mr-2 h-4 w-4" />
                파라미터 최적화
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <HardDrive className="mr-2 h-4 w-4" />
                백업 실행
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>파티션 자동화 설정</CardTitle>
              <CardDescription>자동 파티션 생성 및 정리 규칙</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 border rounded">
                  <div>
                    <p className="font-medium">market_orders</p>
                    <p className="text-sm text-muted-foreground">월별 파티션, 24개월 보관</p>
                  </div>
                  <Badge>활성</Badge>
                </div>
                <div className="flex justify-between items-center p-4 border rounded">
                  <div>
                    <p className="font-medium">market_raw_data</p>
                    <p className="text-sm text-muted-foreground">월별 파티션, 6개월 보관</p>
                  </div>
                  <Badge>활성</Badge>
                </div>
                <div className="flex justify-between items-center p-4 border rounded">
                  <div>
                    <p className="font-medium">job_executions</p>
                    <p className="text-sm text-muted-foreground">월별 파티션, 3개월 보관</p>
                  </div>
                  <Badge>활성</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}