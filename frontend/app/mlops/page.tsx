'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  GitBranch,
  Package,
  Play,
  RefreshCcw,
  Rocket,
  TrendingUp,
  Upload,
  X,
  BarChart3,
  Activity,
  AlertTriangle
} from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

interface Model {
  model_id: string;
  version: string;
  status: string;
  created_at: string;
  metadata: {
    model_type: string;
    metrics: Record<string, number>;
    params: Record<string, any>;
  };
}

interface Deployment {
  deployment_id: string;
  model_id: string;
  version: string;
  status: string;
  endpoint?: string;
  created_at: string;
  config: Record<string, any>;
}

interface MonitoringData {
  timestamp: string;
  accuracy?: number;
  latency?: number;
  error_rate?: number;
  requests?: number;
}

interface Experiment {
  run_id: string;
  experiment_name: string;
  status: string;
  metrics: Record<string, number>;
  params: Record<string, any>;
  created_at: string;
}

const statusColors: Record<string, string> = {
  training: 'bg-blue-500',
  validating: 'bg-yellow-500',
  staging: 'bg-purple-500',
  production: 'bg-green-500',
  archived: 'bg-gray-500',
  failed: 'bg-red-500',
  deployed: 'bg-green-500',
  deploying: 'bg-blue-500',
  rolled_back: 'bg-orange-500'
};

export default function MLOpsDashboard() {
  const [models, setModels] = useState<Model[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [monitoringData, setMonitoringData] = useState<MonitoringData[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState(false);
  const [deployDialogOpen, setDeployDialogOpen] = useState(false);
  const [trainDialogOpen, setTrainDialogOpen] = useState(false);

  // 새 모델 학습 폼
  const [newModelForm, setNewModelForm] = useState({
    model_id: '',
    model_type: 'classification',
    algorithm: 'xgboost',
    epochs: 100,
    learning_rate: 0.001,
    batch_size: 32
  });

  // 배포 설정 폼
  const [deploymentConfig, setDeploymentConfig] = useState({
    deployment_type: 'api',
    replicas: 1,
    memory_limit: '2Gi',
    cpu_limit: '1000m',
    traffic_percentage: 100
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // 10초마다 업데이트
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 모델 목록 (시뮬레이션)
      setModels([
        {
          model_id: 'sales_predictor',
          version: '2.1.0',
          status: 'production',
          created_at: new Date().toISOString(),
          metadata: {
            model_type: 'time_series',
            metrics: { rmse: 0.082, mae: 0.065, r2: 0.94 },
            params: { algorithm: 'LSTM', epochs: 100 }
          }
        },
        {
          model_id: 'customer_churn',
          version: '1.3.2',
          status: 'staging',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          metadata: {
            model_type: 'classification',
            metrics: { accuracy: 0.92, f1_score: 0.89, precision: 0.91 },
            params: { algorithm: 'XGBoost', max_depth: 6 }
          }
        },
        {
          model_id: 'price_optimizer',
          version: '3.0.0',
          status: 'training',
          created_at: new Date().toISOString(),
          metadata: {
            model_type: 'regression',
            metrics: {},
            params: { algorithm: 'RandomForest', n_estimators: 100 }
          }
        }
      ]);

      // 배포 목록
      setDeployments([
        {
          deployment_id: 'dep-001',
          model_id: 'sales_predictor',
          version: '2.1.0',
          status: 'deployed',
          endpoint: 'https://api.example.com/predict/sales',
          created_at: new Date().toISOString(),
          config: { replicas: 3, memory_limit: '4Gi' }
        },
        {
          deployment_id: 'dep-002',
          model_id: 'customer_churn',
          version: '1.3.1',
          status: 'deployed',
          endpoint: 'https://api.example.com/predict/churn',
          created_at: new Date(Date.now() - 172800000).toISOString(),
          config: { replicas: 2, memory_limit: '2Gi' }
        }
      ]);

      // 모니터링 데이터 생성
      const monitoring = [];
      for (let i = 0; i < 24; i++) {
        monitoring.push({
          timestamp: new Date(Date.now() - i * 3600000).toISOString(),
          accuracy: 0.85 + Math.random() * 0.1,
          latency: 50 + Math.random() * 30,
          error_rate: Math.random() * 0.05,
          requests: Math.floor(1000 + Math.random() * 500)
        });
      }
      setMonitoringData(monitoring.reverse());

      // 실험 목록
      setExperiments([
        {
          run_id: 'exp-001',
          experiment_name: 'hyperparameter_tuning',
          status: 'completed',
          metrics: { accuracy: 0.93, loss: 0.045 },
          params: { learning_rate: 0.001, batch_size: 64 },
          created_at: new Date().toISOString()
        },
        {
          run_id: 'exp-002',
          experiment_name: 'feature_engineering',
          status: 'running',
          metrics: { accuracy: 0.91 },
          params: { features: 'v2', preprocessing: 'standard' },
          created_at: new Date().toISOString()
        }
      ]);

    } catch (error) {
      console.error('데이터 로드 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (!selectedModel) return;
    
    console.log('배포 설정:', {
      model: selectedModel,
      config: deploymentConfig
    });
    
    // API 호출 시뮬레이션
    setDeployDialogOpen(false);
    fetchData();
  };

  const handleTrain = async () => {
    console.log('새 모델 학습:', newModelForm);
    
    // API 호출 시뮬레이션
    setTrainDialogOpen(false);
    fetchData();
  };

  const getStatusBadge = (status: string) => {
    return (
      <Badge className={`${statusColors[status] || 'bg-gray-500'} text-white`}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">MLOps 대시보드</h1>
        <p className="text-muted-foreground mt-2">
          AI/ML 모델 생명주기 관리 플랫폼
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 모델</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.length}</div>
            <p className="text-xs text-muted-foreground">
              {models.filter(m => m.status === 'production').length} 프로덕션
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">활성 배포</CardTitle>
            <Rocket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {deployments.filter(d => d.status === 'deployed').length}
            </div>
            <p className="text-xs text-muted-foreground">
              {deployments.length} 전체 배포
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 정확도</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(monitoringData[monitoringData.length - 1]?.accuracy || 0).toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              최근 24시간
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">실험</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{experiments.length}</div>
            <p className="text-xs text-muted-foreground">
              {experiments.filter(e => e.status === 'running').length} 진행 중
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="models" className="space-y-4">
        <TabsList>
          <TabsTrigger value="models">모델 관리</TabsTrigger>
          <TabsTrigger value="deployments">배포 관리</TabsTrigger>
          <TabsTrigger value="monitoring">모니터링</TabsTrigger>
          <TabsTrigger value="experiments">실험 추적</TabsTrigger>
        </TabsList>

        {/* 모델 관리 탭 */}
        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>모델 레지스트리</CardTitle>
                <Dialog open={trainDialogOpen} onOpenChange={setTrainDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Upload className="mr-2 h-4 w-4" />
                      새 모델 학습
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>새 모델 학습</DialogTitle>
                      <DialogDescription>
                        새로운 ML 모델을 학습하고 등록합니다.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                      <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="model_id" className="text-right">
                          모델 ID
                        </Label>
                        <Input
                          id="model_id"
                          value={newModelForm.model_id}
                          onChange={(e) => setNewModelForm({
                            ...newModelForm,
                            model_id: e.target.value
                          })}
                          className="col-span-3"
                        />
                      </div>
                      <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="model_type" className="text-right">
                          모델 유형
                        </Label>
                        <Select
                          value={newModelForm.model_type}
                          onValueChange={(value) => setNewModelForm({
                            ...newModelForm,
                            model_type: value
                          })}
                        >
                          <SelectTrigger className="col-span-3">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="classification">분류</SelectItem>
                            <SelectItem value="regression">회귀</SelectItem>
                            <SelectItem value="time_series">시계열</SelectItem>
                            <SelectItem value="nlp">NLP</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="epochs" className="text-right">
                          에폭 수
                        </Label>
                        <Input
                          id="epochs"
                          type="number"
                          value={newModelForm.epochs}
                          onChange={(e) => setNewModelForm({
                            ...newModelForm,
                            epochs: parseInt(e.target.value)
                          })}
                          className="col-span-3"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={handleTrain}>학습 시작</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>모델 ID</TableHead>
                    <TableHead>버전</TableHead>
                    <TableHead>유형</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>메트릭</TableHead>
                    <TableHead>생성일</TableHead>
                    <TableHead>작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.map((model) => (
                    <TableRow key={`${model.model_id}-${model.version}`}>
                      <TableCell className="font-medium">
                        {model.model_id}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{model.version}</Badge>
                      </TableCell>
                      <TableCell>{model.metadata.model_type}</TableCell>
                      <TableCell>{getStatusBadge(model.status)}</TableCell>
                      <TableCell>
                        {Object.keys(model.metadata.metrics).length > 0 ? (
                          <div className="text-sm">
                            {Object.entries(model.metadata.metrics).slice(0, 2).map(([key, value]) => (
                              <div key={key}>
                                {key}: {typeof value === 'number' ? value.toFixed(3) : value}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">학습 중...</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {format(new Date(model.created_at), 'PPP', { locale: ko })}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedModel(model);
                              setDeployDialogOpen(true);
                            }}
                            disabled={model.status === 'training'}
                          >
                            배포
                          </Button>
                          <Button variant="outline" size="sm">
                            상세
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 배포 관리 탭 */}
        <TabsContent value="deployments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>활성 배포</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {deployments.map((deployment) => (
                  <Card key={deployment.deployment_id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold">
                            {deployment.model_id} v{deployment.version}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            배포 ID: {deployment.deployment_id}
                          </p>
                        </div>
                        {getStatusBadge(deployment.status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-medium">엔드포인트</p>
                          <p className="text-muted-foreground">
                            {deployment.endpoint || 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="font-medium">배포 시간</p>
                          <p className="text-muted-foreground">
                            {format(new Date(deployment.created_at), 'PPpp', { locale: ko })}
                          </p>
                        </div>
                        <div>
                          <p className="font-medium">복제본 수</p>
                          <p className="text-muted-foreground">
                            {deployment.config.replicas || 1}
                          </p>
                        </div>
                        <div>
                          <p className="font-medium">메모리 제한</p>
                          <p className="text-muted-foreground">
                            {deployment.config.memory_limit || 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <Button variant="outline" size="sm">
                          <RefreshCcw className="mr-2 h-4 w-4" />
                          재시작
                        </Button>
                        <Button variant="outline" size="sm">
                          롤백
                        </Button>
                        <Button variant="outline" size="sm" className="text-red-600">
                          중지
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 모니터링 탭 */}
        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>모델 정확도</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={monitoringData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis domain={[0.8, 1]} />
                    <Tooltip
                      labelFormatter={(value) => format(new Date(value), 'PPpp', { locale: ko })}
                    />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>응답 시간</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={monitoringData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => format(new Date(value), 'PPpp', { locale: ko })}
                    />
                    <Area
                      type="monotone"
                      dataKey="latency"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>오류율</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={monitoringData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
                    <Tooltip
                      labelFormatter={(value) => format(new Date(value), 'PPpp', { locale: ko })}
                      formatter={(value: any) => `${(value * 100).toFixed(2)}%`}
                    />
                    <Line
                      type="monotone"
                      dataKey="error_rate"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>요청 수</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monitoringData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => format(new Date(value), 'PPpp', { locale: ko })}
                    />
                    <Bar dataKey="requests" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* 알림 */}
          <Card>
            <CardHeader>
              <CardTitle>최근 알림</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm">
                    customer_churn 모델의 정확도가 10% 하락했습니다.
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    5분 전
                  </span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm">
                    데이터 드리프트가 감지되었습니다.
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    1시간 전
                  </span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">
                    sales_predictor v2.1.0이 성공적으로 배포되었습니다.
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    2시간 전
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 실험 추적 탭 */}
        <TabsContent value="experiments" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>실험 목록</CardTitle>
                <Button>
                  <Play className="mr-2 h-4 w-4" />
                  새 실험
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>실험 ID</TableHead>
                    <TableHead>실험 이름</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>메트릭</TableHead>
                    <TableHead>파라미터</TableHead>
                    <TableHead>시작 시간</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {experiments.map((experiment) => (
                    <TableRow key={experiment.run_id}>
                      <TableCell className="font-mono text-sm">
                        {experiment.run_id}
                      </TableCell>
                      <TableCell>{experiment.experiment_name}</TableCell>
                      <TableCell>
                        <Badge
                          variant={experiment.status === 'running' ? 'default' : 'secondary'}
                        >
                          {experiment.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {Object.entries(experiment.metrics).map(([key, value]) => (
                            <div key={key}>
                              {key}: {typeof value === 'number' ? value.toFixed(3) : value}
                            </div>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {Object.entries(experiment.params).slice(0, 2).map(([key, value]) => (
                            <div key={key}>
                              {key}: {value}
                            </div>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        {format(new Date(experiment.created_at), 'PPpp', { locale: ko })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 배포 다이얼로그 */}
      <Dialog open={deployDialogOpen} onOpenChange={setDeployDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>모델 배포</DialogTitle>
            <DialogDescription>
              {selectedModel?.model_id} v{selectedModel?.version}을 배포합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="deployment_type" className="text-right">
                배포 유형
              </Label>
              <Select
                value={deploymentConfig.deployment_type}
                onValueChange={(value) => setDeploymentConfig({
                  ...deploymentConfig,
                  deployment_type: value
                })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="batch">Batch</SelectItem>
                  <SelectItem value="stream">Stream</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="replicas" className="text-right">
                복제본 수
              </Label>
              <Input
                id="replicas"
                type="number"
                value={deploymentConfig.replicas}
                onChange={(e) => setDeploymentConfig({
                  ...deploymentConfig,
                  replicas: parseInt(e.target.value)
                })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="memory" className="text-right">
                메모리 제한
              </Label>
              <Input
                id="memory"
                value={deploymentConfig.memory_limit}
                onChange={(e) => setDeploymentConfig({
                  ...deploymentConfig,
                  memory_limit: e.target.value
                })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="traffic" className="text-right">
                트래픽 비율
              </Label>
              <div className="col-span-3 flex items-center gap-2">
                <Input
                  id="traffic"
                  type="number"
                  value={deploymentConfig.traffic_percentage}
                  onChange={(e) => setDeploymentConfig({
                    ...deploymentConfig,
                    traffic_percentage: parseInt(e.target.value)
                  })}
                  min="0"
                  max="100"
                />
                <span>%</span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeployDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleDeploy}>
              <Rocket className="mr-2 h-4 w-4" />
              배포
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}