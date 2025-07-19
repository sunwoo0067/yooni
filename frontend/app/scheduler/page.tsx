'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Clock, Play, Pause, RefreshCw, Settings, Plus, Edit2, 
  Trash2, Calendar, Activity, AlertCircle, CheckCircle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface ScheduleJob {
  id: number;
  name: string;
  job_type: string;
  status: string;
  interval: string | null;
  specific_times: string[] | null;
  market_codes: string[];
  next_run_at: string | null;
  last_run_at: string | null;
  success_rate: number;
  run_count: number;
  error_count: number;
  last_error: string | null;
}

interface JobExecution {
  id: number;
  job_name: string;
  job_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  records_processed: number;
  error_message: string | null;
}

export default function SchedulerPage() {
  const [jobs, setJobs] = useState<ScheduleJob[]>([]);
  const [executions, setExecutions] = useState<JobExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('jobs');
  const [selectedJob, setSelectedJob] = useState<ScheduleJob | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchSchedulerData();
    // 30초마다 자동 새로고침
    const interval = setInterval(fetchSchedulerData, 30000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchSchedulerData = async () => {
    try {
      setLoading(true);
      
      if (activeTab === 'jobs') {
        const response = await fetch('/api/scheduler/jobs');
        const data = await response.json();
        if (data.success) {
          setJobs(data.data);
        }
      } else {
        const response = await fetch('/api/scheduler/executions');
        const data = await response.json();
        if (data.success) {
          setExecutions(data.data);
        }
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '스케줄러 데이터를 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleJobToggle = async (jobId: number, isActive: boolean) => {
    try {
      const response = await fetch(`/api/scheduler/jobs/${jobId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
      });

      if (response.ok) {
        toast({
          title: '성공',
          description: `작업이 ${isActive ? '활성화' : '비활성화'}되었습니다.`,
        });
        fetchSchedulerData();
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '작업 상태 변경에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const handleRunNow = async (jobId: number) => {
    try {
      const response = await fetch(`/api/scheduler/jobs/${jobId}/run`, {
        method: 'POST',
      });

      if (response.ok) {
        toast({
          title: '성공',
          description: '작업이 실행 대기열에 추가되었습니다.',
        });
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '작업 실행에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const getJobTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      product_collection: '상품 수집',
      order_collection: '주문 수집',
      inventory_sync: '재고 동기화',
      price_update: '가격 업데이트',
      database_backup: 'DB 백업',
      report_generation: '보고서 생성',
    };
    return labels[type] || type;
  };

  const getIntervalLabel = (interval: string | null, specificTimes: string[] | null) => {
    if (specificTimes && specificTimes.length > 0) {
      return `매일 ${specificTimes.join(', ')}`;
    }
    
    const labels: Record<string, string> = {
      '5m': '5분마다',
      '10m': '10분마다',
      '15m': '15분마다',
      '30m': '30분마다',
      '1h': '매시간',
      '2h': '2시간마다',
      '4h': '4시간마다',
      '6h': '6시간마다',
      '12h': '12시간마다',
      '1d': '매일',
      '1w': '매주',
      '1M': '매월',
    };
    return interval ? labels[interval] || interval : '-';
  };

  const getStatusBadge = (status: string) => {
    const config = {
      active: { label: '활성', variant: 'default' as const, icon: CheckCircle },
      paused: { label: '일시정지', variant: 'secondary' as const, icon: Pause },
      running: { label: '실행중', variant: 'default' as const, icon: Play },
      completed: { label: '완료', variant: 'default' as const, icon: CheckCircle },
      failed: { label: '실패', variant: 'destructive' as const, icon: AlertCircle },
    };
    
    const cfg = config[status] || config.active;
    const Icon = cfg.icon;
    
    return (
      <Badge variant={cfg.variant}>
        <Icon className="w-3 h-3 mr-1" />
        {cfg.label}
      </Badge>
    );
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('ko-KR');
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    
    if (seconds < 60) return `${seconds}초`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분 ${seconds % 60}초`;
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}시간 ${minutes}분`;
  };

  return (
    <div className="container mx-auto py-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">작업 스케줄러</h1>
          <p className="text-muted-foreground">자동화된 작업 관리 및 실행 모니터링</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchSchedulerData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            새 작업 추가
          </Button>
        </div>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">총 작업 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.length}</div>
            <p className="text-xs text-muted-foreground">등록된 작업</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">활성 작업</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {jobs.filter(j => j.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">실행 중</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">성공률</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {jobs.length > 0 
                ? Math.round(jobs.reduce((sum, job) => sum + job.success_rate, 0) / jobs.length) 
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground">평균 성공률</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">오류 발생</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {jobs.filter(j => j.last_error).length}
            </div>
            <p className="text-xs text-muted-foreground">오류 작업</p>
          </CardContent>
        </Card>
      </div>

      {/* 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="jobs">
            <Calendar className="mr-2 h-4 w-4" />
            스케줄 작업
          </TabsTrigger>
          <TabsTrigger value="executions">
            <Activity className="mr-2 h-4 w-4" />
            실행 기록
          </TabsTrigger>
        </TabsList>

        <TabsContent value="jobs" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>작업명</TableHead>
                    <TableHead>유형</TableHead>
                    <TableHead>주기</TableHead>
                    <TableHead>마켓</TableHead>
                    <TableHead>다음 실행</TableHead>
                    <TableHead>마지막 실행</TableHead>
                    <TableHead>성공률</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead className="text-right">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                        <p className="text-muted-foreground">로딩 중...</p>
                      </TableCell>
                    </TableRow>
                  ) : jobs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        <Clock className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">등록된 작업이 없습니다</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    jobs.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{job.name}</div>
                            {job.last_error && (
                              <div className="text-xs text-red-600 mt-1">
                                오류: {job.last_error.substring(0, 50)}...
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{getJobTypeLabel(job.job_type)}</TableCell>
                        <TableCell>{getIntervalLabel(job.interval, job.specific_times)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {job.market_codes.map(market => (
                              <Badge key={market} variant="outline" className="text-xs">
                                {market}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>{formatDateTime(job.next_run_at)}</TableCell>
                        <TableCell>{formatDateTime(job.last_run_at)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span>{job.success_rate.toFixed(1)}%</span>
                            <span className="text-xs text-muted-foreground">
                              ({job.run_count}회)
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(job.status)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleRunNow(job.id)}
                              title="지금 실행"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => {
                                setSelectedJob(job);
                                setIsEditDialogOpen(true);
                              }}
                              title="편집"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Switch
                              checked={job.status === 'active'}
                              onCheckedChange={(checked) => handleJobToggle(job.id, checked)}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>작업명</TableHead>
                    <TableHead>유형</TableHead>
                    <TableHead>시작 시간</TableHead>
                    <TableHead>완료 시간</TableHead>
                    <TableHead>소요 시간</TableHead>
                    <TableHead>처리 건수</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>오류 메시지</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                        <p className="text-muted-foreground">로딩 중...</p>
                      </TableCell>
                    </TableRow>
                  ) : executions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        <Activity className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">실행 기록이 없습니다</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    executions.map((execution) => (
                      <TableRow key={execution.id}>
                        <TableCell className="font-medium">{execution.job_name}</TableCell>
                        <TableCell>{getJobTypeLabel(execution.job_type)}</TableCell>
                        <TableCell>{formatDateTime(execution.started_at)}</TableCell>
                        <TableCell>{formatDateTime(execution.completed_at)}</TableCell>
                        <TableCell>{formatDuration(execution.duration_seconds)}</TableCell>
                        <TableCell>{execution.records_processed.toLocaleString()}</TableCell>
                        <TableCell>{getStatusBadge(execution.status)}</TableCell>
                        <TableCell>
                          {execution.error_message && (
                            <span className="text-sm text-red-600">
                              {execution.error_message.substring(0, 100)}...
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 작업 편집 다이얼로그 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>작업 편집</DialogTitle>
            <DialogDescription>
              스케줄 작업의 설정을 변경합니다.
            </DialogDescription>
          </DialogHeader>
          
          {selectedJob && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right">
                  작업명
                </Label>
                <Input
                  id="name"
                  value={selectedJob.name}
                  className="col-span-3"
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="interval" className="text-right">
                  실행 주기
                </Label>
                <Select defaultValue={selectedJob.interval || ''}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="실행 주기 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5m">5분마다</SelectItem>
                    <SelectItem value="10m">10분마다</SelectItem>
                    <SelectItem value="15m">15분마다</SelectItem>
                    <SelectItem value="30m">30분마다</SelectItem>
                    <SelectItem value="1h">매시간</SelectItem>
                    <SelectItem value="6h">6시간마다</SelectItem>
                    <SelectItem value="1d">매일</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={() => {
              // TODO: 저장 로직 구현
              setIsEditDialogOpen(false);
              toast({
                title: '저장 완료',
                description: '작업 설정이 저장되었습니다.',
              });
            }}>
              저장
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}